import json
import os
import re
from pypinyin import pinyin, Style

ALL_BASIC_HANZI_FILE = r'all_basic_hanzi.json'
NYU_HANZI_FILE = r'nyu_hanzi.json'
MAPPING_FILE = r'mapping.json'

# Ideographic Description Characters (IDC)
# 1. Unicode range: [\u2FF0-\u2FFF]
# 2. Extended IDC pattern: &U-i001+2FF1; &U-i001+2FFB; &U-i002+2FF1;
# 这些将被视作结构符移除，不作为组件。
IDC_REGEX = r'[\u2FF0-\u2FFF]|&U-i\d+\+2FF[1B];'

def get_components(ids_str):
    """
    将 IDS 字符串解析为组件集合。
    1. 移除指定的 IDC 结构符（包括 Unicode IDC 和 Extended IDC）。
    2. 将剩余部分中的 &...; 实体视为一个完整的组件。
    3. 将剩余的普通汉字视为组件。
    4. 返回一个字符集合 set。
    """
    if not ids_str:
        return set()
    
    # 1. 移除结构符 (IDC)
    cleaned = re.sub(IDC_REGEX, '', ids_str)
    
    # 2. 提取实体组件 (例如 &CDP-8BBF;)
    # 使用 findall 找到所有 &...; 格式的字符串
    entities = set(re.findall(r'&[^;]+;', cleaned))
    
    # 3. 为了提取普通汉字，先将实体从字符串中移除，避免 & c d p ; 被拆成单字
    temp_str = re.sub(r'&[^;]+;', '', cleaned)
    
    # 4. 提取普通字符组件
    chars = set(temp_str)
    
    # 5. 合并实体集合和字符集合
    return chars | entities

def get_body_after_removing_target(ids_str, target_char='女'):
    """
    从 IDS 中移除目标字符（如 '女'）和 IDC。
    返回剩余的组件集合（frozenset），无论剩下一个还是多个。
    如果为空则返回 None。
    """
    components = get_components(ids_str)
    
    # 移除目标字符
    if target_char in components:
        components.remove(target_char)
    
    # 修改点：不再检查 len == 1，只要有剩余组件就返回
    # 使用 frozenset 是因为集合是不可哈希的，不能作为字典的键，而 frozenset 可以
    if components:
        return frozenset(components)
    return None

def build_nyu_body_map(nyu_filepath):
    """
    遍历 nyu_hanzi.json，建立 { frozenset(主体组件): ['含女主体的字', ...] } 的映射。
    """
    print("正在构建 '女' 字旁汉字的反向索引...")
    with open(nyu_filepath, 'r', encoding='utf-8') as f:
        nyu_data = json.load(f)
        
    body_map = {}
    
    for char, info in nyu_data.items():
        # 尝试从 IDS 提取主体
        body = get_body_after_removing_target(info.get('IDS', ''))
        
        # 如果 IDS 没提取到，尝试 IDS_apparent
        if not body:
            body = get_body_after_removing_target(info.get('IDS_apparent', ''))
            
        if body:
            # body 现在是一个 frozenset
            if body not in body_map:
                body_map[body] = []
            if char not in body_map[body]:
                body_map[body].append(char)
                
    print(f"索引构建完成，共找到 {len(body_map)} 个唯一主体组合。")
    return body_map

def infer_body_from_context(curr_ids, neighbor_ids):
    """
    比较当前字和相邻字的 IDS。
    如果发现共同部分（偏旁），则从当前字中移除共同部分。
    返回剩余的所有组件（frozenset）。
    """
    curr_comps = get_components(curr_ids)
    neigh_comps = get_components(neighbor_ids)
    
    if not curr_comps or not neigh_comps:
        return None
        
    # 计算交集（共同的偏旁）
    common = curr_comps.intersection(neigh_comps)
    
    if common:
        # 从当前字中移除共同部分
        remainder = curr_comps - common
        
        # 修改点：不再检查 len == 1，直接返回剩余部分的 frozenset
        if remainder:
            return frozenset(remainder)
            
    return None

def get_pinyin_base(char):
    """获取一个字的无声调拼音。"""
    # 获取拼音，不带音调
    py_list = pinyin(char, heteronym=False, style=Style.NORMAL)
    if py_list and py_list[0]:
        return py_list[0][0]
    return None

def get_body_by_sound(char, ids_str):
    """
    根据字和组件的拼音比对，推断声旁组件。
    如果字的拼音与某个组件的拼音相同，且该组件是IDS中的唯一“非声旁”组件，
    则该组件被视为声旁/主体。
    """
    if not ids_str:
        return None
        
    char_py = get_pinyin_base(char)
    if not char_py:
        return None
        
    components = get_components(ids_str)
    
    # 移除结构符/IDC/目标字符后的剩余组件
    # 注意：这里不能简单移除 '女'，因为我们不知道这个字是否是女字旁的
    
    sound_matches = []
    
    for comp in components:
        # 排除 &...; 实体，只比对普通字符
        if not comp.startswith('&'):
            comp_py = get_pinyin_base(comp)
            # 如果字和组件拼音相同，则认为该组件是声旁
            if char_py == comp_py:
                sound_matches.append(comp)

    # 简单策略：如果恰好有一个组件拼音匹配，则认为它是主体
    if len(sound_matches) == 1:
        # 从总组件中移除这个声旁，剩下的作为 '主体' 似乎不合理
        # 更好的做法是直接返回这个声旁作为主体
        # 因为在你的nyu_body_map中，主体是 '子'，而不是 '宀'
        # 我们希望返回 {'子'} 作为主体，以便匹配到 '好' 和 '𡥃' 中的 '子'
        return frozenset(sound_matches)
        
    # 如果有多个组件拼音匹配，或者没有匹配，则不进行声旁推断
    return None

def process_advanced_mapping():
    # 1. 检查文件是否存在
    # 注意：这里假设你使用的是 count_mapping_2.py 或者类似名称，请根据实际情况调整 import
    if not all(os.path.exists(f) for f in [ALL_BASIC_HANZI_FILE, NYU_HANZI_FILE, MAPPING_FILE]):
        print("错误：缺少必要的输入文件。")
        return

    # 2. 构建 nyu 反向映射表
    nyu_body_map = build_nyu_body_map(NYU_HANZI_FILE)
    
    # 3. 读取 mapping.json
    print(f"读取 {MAPPING_FILE}...")
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    # 4. 读取 all_basic_hanzi.json
    print(f"读取 {ALL_BASIC_HANZI_FILE}...")
    with open(ALL_BASIC_HANZI_FILE, 'r', encoding='utf-8') as f:
        all_basic_hanzi = json.load(f)
    
    # 排序
    sorted_chars = sorted(all_basic_hanzi.keys(), key=lambda k: int(all_basic_hanzi[k]['Codepoint'][2:], 16))
    
    print(f"开始遍历 {len(sorted_chars)} 个汉字进行上下文比对...")
    
    update_count = 0
    
    # 5. 遍历并比对上下文
    for i in range(len(sorted_chars)):
        curr_char = sorted_chars[i]
        curr_data = all_basic_hanzi[curr_char]
        curr_ids = curr_data.get('IDS', '')
        
        inferred_body = None

        # === 核心修改点：优先级 1. 拼音推断声旁 ===
        # 尝试通过拼音推断主体/声旁
        inferred_body = get_body_by_sound(curr_char, curr_ids)
        # ============================================

        if not inferred_body:
            # 获取上下文
            prev_data = all_basic_hanzi[sorted_chars[i-1]] if i > 0 else None
            next_data = all_basic_hanzi[sorted_chars[i+1]] if i < len(sorted_chars) - 1 else None
        
            # 尝试与上一个字比对
            if prev_data:
                inferred_body = infer_body_from_context(curr_ids, prev_data.get('IDS', ''))
                
            # 如果没结果，尝试与下一个字比对
            if not inferred_body and next_data:
                inferred_body = infer_body_from_context(curr_ids, next_data.get('IDS', ''))
            
        # 6. 核心匹配逻辑
        # inferred_body 是一个 frozenset，可以直接在字典中查找
        if inferred_body and inferred_body in nyu_body_map:
            targets = nyu_body_map[inferred_body]
            
            if curr_char not in mapping:
                mapping[curr_char] = ""
            
            current_val = mapping[curr_char]
            added_new = False
            for t in targets:
                if t not in current_val:
                    current_val += t
                    added_new = True
            
            if added_new:
                mapping[curr_char] = current_val
                update_count += 1
                # 调试打印 (可选)
                # comps_str = "+".join(inferred_body)
                # print(f"关联: {curr_char} (主体[{comps_str}]) -> { ''.join(targets)}")

    # 7. 保存结果
    print(f"比对完成。共更新了 {update_count} 个汉字的映射关系。")
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
    
    print(f"结果已保存至 {MAPPING_FILE}")

if __name__ == "__main__":
    process_advanced_mapping()
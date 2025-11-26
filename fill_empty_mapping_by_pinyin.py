import json
import os
from pypinyin import pinyin, Style

MAPPING_FILE = r'mapping.json'
NYU_HANZI_FILE = r'nyu_hanzi.json'

def get_pinyin_list(character):
    """
    使用 pypinyin 获取汉字的所有拼音（带声调，多音字）。
    返回一个扁平化的不重复的拼音列表。
    """
    try:
        pinyin_result = pinyin(character, heteronym=False, style=Style.TONE3)
        
        if pinyin_result:
            flat_pinyin = [item for sublist in pinyin_result for item in sublist]
            return sorted(list(set(flat_pinyin)))
        return []
    except Exception:
        return []

def build_pinyin_index(nyu_data):
    """
    建立倒排索引：拼音 -> 含该拼音的'女'字旁汉字列表
    例如: { 'qi1': {'妻', '娸'}, 'qi2': {'䶒'}, ... }
    """
    print("正在构建 nyu_hanzi 的拼音索引...")
    index = {}
    
    for char, info in nyu_data.items():
        pinyins_nested = pinyin(char, heteronym=False, style=Style.TONE3) 
        
        for sublist in pinyins_nested:
            for p_str in sublist: 
                if p_str not in index:
                    index[p_str] = set()
                index[p_str].add(char)
            
    print(f"拼音索引构建完成，包含 {len(index)} 个不同的读音。")
    return index

def fill_empty_by_pinyin():
    # 1. 检查文件
    if not os.path.exists(MAPPING_FILE) or not os.path.exists(NYU_HANZI_FILE):
        print("错误：找不到 mapping.json 或 nyu_hanzi.json 文件。")
        return

    # 2. 读取数据
    print(f"读取 {NYU_HANZI_FILE}...")
    with open(NYU_HANZI_FILE, 'r', encoding='utf-8') as f:
        nyu_hanzi = json.load(f)

    print(f"读取 {MAPPING_FILE}...")
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    # 3. 构建索引
    pinyin_index = build_pinyin_index(nyu_hanzi)
    
    update_count = 0
    processed_count = 0
    
    # 4. 遍历 mapping 寻找空值
    print("开始遍历 mapping.json 填充空缺...")
    
    # 获取所有键的列表，用于循环
    keys = list(mapping.keys())
    
    for char in keys:
        current_val = mapping[char]
        
        # 仅处理空值
        if current_val == "":
            processed_count += 1
            
            # 获取当前汉字的拼音
            target_pinyins = get_pinyin_list(char)
            
            # 寻找匹配的同音字
            matched_chars = set()
            for p in target_pinyins:
                if p in pinyin_index:
                    matched_chars.update(pinyin_index[p])
            
            # 如果找到了同音字
            if matched_chars:
                # 排除自己（如果自己在 nyu_hanzi 中）
                if char in matched_chars:
                    matched_chars.remove(char)
                
                if matched_chars:
                    # 转为字符串并排序，保持美观
                    result_str = "".join(sorted(list(matched_chars)))
                    mapping[char] = result_str
                    update_count += 1
                    # print(f"填充: {char} ({'/'.join(target_pinyins)}) -> {result_str}")

    # 5. 保存结果
    print(f"处理完成。")
    print(f"共检查了 {processed_count} 个空值项。")
    print(f"成功通过同音关系填充了 {update_count} 个项。")
    
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
        
    print(f"更新已写入 {MAPPING_FILE}")

    # 6. 统计
    try:
        from count_mapping import count_mapping_stats 
        count_mapping_stats(MAPPING_FILE)
    except ImportError:
        pass

if __name__ == "__main__":
    fill_empty_by_pinyin()
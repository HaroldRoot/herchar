import json
import re
import os

# Ideographic Description Characters (U+2FF0 to U+2FFF) 正则表达式
# 这些字符是：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿
IDC_REGEX = r'[\u2FF0-\u2FFF]'

def extract_single_component(ids_string, target_char='女'):
    """
    从 IDS 字符串中，去除 IDC 字符和 target_char 后，如果只剩下一个汉字，则返回该汉字。
    否则返回 None。
    """
    if not ids_string:
        return None
        
    # 1. 移除 ⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿
    cleaned_ids = re.sub(IDC_REGEX, '', ids_string)
    
    # 2. 移除 CDP 引用，例如 &CDP-8CB5;
    # Non-abstract IDC 例如 &U-i001+2FF1;
    cleaned_ids = re.sub(r'&[A-Za-z0-9-]+;', '', cleaned_ids)

    # 3. 移除目标字符
    component = cleaned_ids.replace(target_char, '')
    
    # 4. 检查是否只剩下一个汉字（长度为 1）
    if len(component) == 1:
        return component
    
    return None

def remove_existing_keys_from_mapping(mapping_data, reference_keys_set):
    """
    从 mapping_data 字典中删除在 reference_keys_set 中已有的键。
    """
    removed_count = 0
    # 遍历时创建键的列表副本，以便安全地修改字典
    for key in list(mapping_data.keys()):
        if key in reference_keys_set:
            del mapping_data[key]
            removed_count += 1
            
    return removed_count

def update_mapping_file(nyu_hanzi_filepath, mapping_filepath):
    """
    遍历 nyu_hanzi.json，检查汉字的 IDS 和 IDS_apparent，
    找出剩下的单一组件，并更新 mapping.json。
    """
    
    if not os.path.exists(nyu_hanzi_filepath):
        print(f"错误：找不到文件 {nyu_hanzi_filepath}")
        return
        
    print(f"开始读取文件 {nyu_hanzi_filepath} 并更新 {mapping_filepath}")

    # 1. 读取 nyu_hanzi.json (参考文件)
    try:
        with open(nyu_hanzi_filepath, 'r', encoding='utf-8') as f:
            nyu_hanzi = json.load(f)
        nyu_hanzi_keys = set(nyu_hanzi.keys()) # 获取参考键集合
    except json.JSONDecodeError:
        print(f"错误：{nyu_hanzi_filepath} 不是有效的 JSON 文件。")
        return
    except Exception as e:
        print(f"读取 {nyu_hanzi_filepath} 发生错误: {e}")
        return

    # 2. 读取 mapping.json (待修改文件)
    try:
        if os.path.exists(mapping_filepath):
            with open(mapping_filepath, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        else:
            print(f"警告：找不到 {mapping_filepath}，初始化为空字典。")
            mapping = {}
    except json.JSONDecodeError:
        print(f"错误：{mapping_filepath} 不是有效的 JSON 文件，初始化为空字典。")
        mapping = {}
    except Exception as e:
        print(f"读取 {mapping_filepath} 发生错误: {e}")
        return
    
    original_mapping_count = len(mapping)
    removed_count = remove_existing_keys_from_mapping(mapping, nyu_hanzi_keys)
    print(f"从 mapping.json 中移除了 {removed_count} 个已存在于 nyu_hanzi.json 的键。")
    print(f"mapping 字典当前键数量：{original_mapping_count} -> {len(mapping)}")

    update_count = 0

    # 3. 遍历 nyu_hanzi 并更新 mapping
    for hanzi, data in nyu_hanzi.items():
        # 检查 IDS
        ids_component = extract_single_component(data.get('IDS', ''))
        # 检查 IDS_apparent
        ids_apparent_component = extract_single_component(data.get('IDS_apparent', ''))
        
        # 优先使用 IDS 的结果
        component_to_update = ids_component
        
        # 如果 IDS 没有提取到，但 IDS_apparent 提取到了，则使用 IDS_apparent
        if not component_to_update and ids_apparent_component:
            component_to_update = ids_apparent_component

        if component_to_update:
            # component_to_update 是被抽出的单一部件，例如 '仁'
            # hanzi 是 '佞'
            
            key = component_to_update
            value_to_add = hanzi
            
            # 检查 key 是否已存在于 mapping
            if key in mapping:
                current_value = mapping[key].strip()
                
                if not current_value:
                    # 原来是空值，直接赋值
                    mapping[key] = value_to_add
                elif value_to_add not in current_value:
                    # 原来有值，且新值不在其中，追加
                    mapping[key] += value_to_add
                # 如果已存在，则不操作（避免重复）
            else:
                # 不存在，则追加新键值对
                mapping[key] = value_to_add
                
            update_count += 1
            # print(f"更新：{key}: '{mapping[key]}' (来自 {hanzi})") # 可选：打印更新详情
            
    # 4. 将更新后的 mapping 写回文件
    with open(mapping_filepath, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)
        
    print(f"成功更新 {mapping_filepath}。")
    print(f"总计找到 {update_count} 个符合条件的汉字并更新了组件的映射值。")


if __name__ == "__main__":
    NYU_HANZI_FILE = r'nyu_hanzi.json'
    MAPPING_FILE = r'mapping.json'
    
    update_mapping_file(NYU_HANZI_FILE, MAPPING_FILE)
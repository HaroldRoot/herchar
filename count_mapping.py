import json
import os

def count_mapping_stats(filepath):
    """
    遍历 mapping.json，统计键值对个数、有值无值的数量和占比。
    """
    
    if not os.path.exists(filepath):
        print(f"错误：找不到文件 {filepath}")
        return

    print(f"开始统计：{filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    except json.JSONDecodeError:
        print(f"错误：{filepath} 不是有效的 JSON 文件。")
        return
    
    total_count = len(mapping)
    valued_count = 0
    empty_count = 0
    
    for _, value in mapping.items():
        if value and value.strip() != "":
            valued_count += 1
        else:
            empty_count += 1
            
    # 计算占比
    valued_percentage = (valued_count / total_count) * 100 if total_count > 0 else 0
    empty_percentage = (empty_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"总键值对个数：{total_count}")
    print(f"有值的数量：{valued_count} (占比: {valued_percentage:.2f}%)")
    print(f"无值的数量：{empty_count} (占比: {empty_percentage:.2f}%)")

    return total_count, valued_count, empty_count

if __name__ == "__main__":
    MAPPING_FILE = r'mapping.json'
    count_mapping_stats(MAPPING_FILE)
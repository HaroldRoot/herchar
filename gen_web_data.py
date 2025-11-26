import json
import os

INPUT_FILE = r'mapping.json'
BASIC_HANZI_FILE = r'all_basic_hanzi.json'  # 基础汉字文件路径
OUTPUT_FILE = r'web_mapping.json'
OUTPUT_LESS_FILE = r'web_mapping_less.json'  # 删减后的输出文件路径

def load_basic_hanzi(filepath):
    """加载基础汉字集合"""
    if not os.path.exists(filepath):
        print(f"错误：找不到 {filepath}")
        return None

    print(f"正在读取 {filepath} (基础汉字)...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            basic_data = json.load(f)
        # 基础汉字集合就是 JSON 的所有键
        return set(basic_data.keys())
    except Exception as e:
        print(f"读取或解析 {filepath} 时出错: {e}")
        return None

def generate_web_data():
    if not os.path.exists(INPUT_FILE):
        print(f"错误：找不到 {INPUT_FILE}")
        return

    # 1. 加载基础汉字集合
    basic_hanzi_set = load_basic_hanzi(BASIC_HANZI_FILE)
    if basic_hanzi_set is None:
        return

    print(f"基础汉字集加载完成，共 {len(basic_hanzi_set)} 个字。")
    print(f"正在读取 {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取或解析 {INPUT_FILE} 时出错: {e}")
        return

    web_data = {}        # 完整的映射 (web_mapping.json)
    web_data_less = {}   # 删减的映射 (web_mapping_less.json)
    count = 0
    count_less = 0

    for char, candidates in data.items():
        # 1. 确保有候选字
        # 2. 确保 candidates 是字符串
        if candidates and isinstance(candidates, str) and len(candidates) > 0:
            # 只取第一个字
            first_candidate = candidates[0]
            
            # --- 完整的映射 ---
            web_data[char] = first_candidate
            count += 1
            
            # --- 删减的映射：检查目标字是否在基础汉字集合中 ---
            if first_candidate in basic_hanzi_set:
                web_data_less[char] = first_candidate
                count_less += 1

    # 2. 写入 web_mapping.json (完整的)
    print(f"正在写入 {OUTPUT_FILE}...")
    # 使用 separators 去除空格和换行，最小化文件体积
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(web_data, f, ensure_ascii=False, separators=(',', ':'))

    # 3. 写入 web_mapping_less.json (删减的)
    print(f"正在写入 {OUTPUT_LESS_FILE}...")
    # 使用 separators 去除空格和换行，最小化文件体积
    with open(OUTPUT_LESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(web_data_less, f, ensure_ascii=False, separators=(',', ':'))

    print(f"\n--- 报告 ---")
    print(f"完整映射已生成为 {OUTPUT_FILE}，共提取了 {count} 个映射关系。")
    print(f"删减映射已生成为 {OUTPUT_LESS_FILE}，共提取了 {count_less} 个映射关系。")
    print(f"目标字非基础汉字的映射关系数量：{count - count_less}。")
    print(f"请将生成的文件与 index.html 放在同一目录下。")


if __name__ == "__main__":
    generate_web_data()
import json
import os

def generate_all_basic_hanzi_json(input_filepath, output_filepath):
    """
    遍历 IDS-UCS-Basic.txt，生成包含 Codepoint, IDS, IDS_apparent, Pinyin 的 all_basic_hanzi.json。
    Pinyin 使用 pypinyin 库生成。
    """
    all_basic_hanzi = {}
    
    if not os.path.exists(input_filepath):
        print(f"错误：找不到文件 {input_filepath}")
        return

    print(f"数据来源：{input_filepath}")

    with open(input_filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            if line.startswith(';;') or not line:
                continue
                
            parts = line.split('\t')
            
            if len(parts) < 3:
                continue

            codepoint = parts[0]
            character = parts[1]
            ids = parts[2]
            ids_apparent = ""
            
            # 检查是否有 @apparent 信息
            for part in parts[3:]:
                if part.startswith('@apparent='):
                    ids_apparent = part.split('=', 1)[1]
                    break
            
            # 只有单个汉字的字符才加入
            if len(character) == 1:
                all_basic_hanzi[character] = {
                    "Codepoint": codepoint,
                    "IDS": ids,
                    "IDS_apparent": ids_apparent 
                }

    # 将结果写入 JSON 文件
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(all_basic_hanzi, f, ensure_ascii=False, indent=4)
        
    print(f"成功生成文件：{output_filepath}")
    print(f"总计处理了 {len(all_basic_hanzi)} 个汉字。")

if __name__ == "__main__":
    INPUT_FILE = r'raw_data\IDS-UCS-Basic.txt'
    OUTPUT_FILE = r'all_basic_hanzi.json'
    generate_all_basic_hanzi_json(INPUT_FILE, OUTPUT_FILE)
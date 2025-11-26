import json
import os
import glob
from pypinyin import pinyin, Style

def generate_nyu_hanzi_json(input_dir, output_filepath):
    """
    遍历指定目录下所有 TXT 文件，仅提取 IDS 或 IDS_apparent 中含有 '女' 字的汉字，
    并生成 nyu_hanzi.json。
    """
    nyu_hanzi = {}
    file_count = 0
    
    input_files = glob.glob(os.path.join(input_dir, '*.txt'))
    
    if not input_files:
        print(f"错误：在目录 {input_dir} 中找不到任何 .txt 文件。")
        return

    print(f"开始处理 {len(input_files)} 个输入文件，筛选含 '女' 的汉字...")

    for input_filepath in input_files:
        file_count += 1
        print(f"  > 正在处理文件 ({file_count}/{len(input_files)}): {os.path.basename(input_filepath)}")
        
        try:
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
                    
                    # 1. 筛选条件：IDS 或 IDS_apparent 中含有 '女' 
                    # 2. 确保是单个汉字
                    if len(character) == 1 and ('女' in ids or '女' in ids_apparent):
                        
                        # 避免重复：如果已在其他文件中处理过，则跳过
                        if character in nyu_hanzi:
                            continue

                        nyu_hanzi[character] = {
                            "Codepoint": codepoint,
                            "IDS": ids,
                            "IDS_apparent": ids_apparent,
                        }

        except FileNotFoundError:
            print(f"警告：文件未找到 {input_filepath}")
        except Exception as e:
            print(f"处理文件 {input_filepath} 第 {line_num} 行时发生错误: {e}")


    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(nyu_hanzi, f, ensure_ascii=False, indent=4)
        
    print(f"成功生成文件：{output_filepath}")
    print(f"总计从 {len(input_files)} 个文件中提取了 {len(nyu_hanzi)} 个含 '女' 的汉字。")

if __name__ == "__main__":
    INPUT_DIR = r'raw_data'
    OUTPUT_FILE = r'nyu_hanzi.json' 
    
    output_dir = os.path.dirname(OUTPUT_FILE)
    
    if output_dir:
        print(f"检查并创建目录: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    generate_nyu_hanzi_json(INPUT_DIR, OUTPUT_FILE)
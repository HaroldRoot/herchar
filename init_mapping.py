import json

def generate_initial_mapping(input_filepath, output_filepath):
    """
    遍历 IDS-UCS-Basic.txt，将所有的 CHARACTER 作为键，值为空字符串，
    形成一个初始的 mapping.json 文件。
    """
    mapping = {}
    
    print(f"开始处理文件：{input_filepath}")
    
    with open(input_filepath, 'r', encoding='utf-8') as f:
        for _, line in enumerate(f, 1):
            line = line.strip()
            
            if line.startswith(';;'):
                continue
            
            if not line:
                continue
            
            parts = line.split('\t')
            mapping[parts[1]] = ""

    with open(output_filepath, 'w', encoding='utf-8') as f:
        # 使用 ensure_ascii=False 保证汉字以可读的形式写入
        json.dump(mapping, f, ensure_ascii=False, indent=4)
        
    print(f"成功生成初始文件：{output_filepath}")
    print(f"总计处理了 {len(mapping)} 个汉字。")

if __name__ == "__main__":
    INPUT_FILE = r'raw_data\IDS-UCS-Basic.txt'
    OUTPUT_FILE = r'mapping.json'
    generate_initial_mapping(INPUT_FILE, OUTPUT_FILE)
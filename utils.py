import re
import os
from datetime import datetime
import logging


# Ideographic Description Characters (IDC)
# 表意文字描述字符
# 1. Unicode range: [\u2FF0-\u2FFF] ⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿
# 2. Extended IDC (Non-abstract IDC): &U-i001+2FF1; &U-i001+2FFB; &U-i002+2FF1;
# 3. 不在 IDC 区块的: U+303E 形似但不相等, U+31EF 减去笔画, U+2B1A 指无法分割的整体字
# 4. 全角问号字符 U+FF1F ？ 例如 IDS-UCS-Ext-D.txt U-0002B756	𫝖	⿸厃？
IDC_REGEX = r'[\u2FF0-\u2FFF]|&U-i\d+\+2FF[1B];|\u303E|\u31EF|\u2B1A|\uFF1F'


def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成带时间戳的日志文件名，例如: logs/mapping_update_20231027.log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"mapping_update_{timestamp}.log")
    
    logger = logging.getLogger("MappingUpdater")
    logger.setLevel(logging.INFO)
    
    # 清除旧的 handlers 避免重复打印
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler (写入文件)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Stream Handler (输出到控制台)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(message)s') # 控制台只打印简略信息
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"日志已初始化，写入文件: {log_filename}")
    return logger


def get_ids_components_list(ids_str, remove_char=None):
    """
    将 IDS 字符串解析为组件列表 (List)。
    """
    if not ids_str:
        return []
    
    # 1. 移除 IDC
    cleaned = re.sub(IDC_REGEX, '', ids_str)
    
    # 2. 提取实体组件 (例如 &CDP-8BBF;)
    entities = re.findall(r'&[^;]+;', cleaned)
    
    # 3. 提取普通汉字 (移除实体后剩余的部分)
    temp_str = re.sub(r'&[^;]+;', '', cleaned)
    chars = list(temp_str) # 转为 list，保留重复项
    
    # 4. 合并
    all_comps = chars + entities
    
    # 5. 如果需要移除目标字符 (例如 '女')
    if remove_char:
        # 使用列表推导式过滤，保留其他重复的组件
        all_comps = [c for c in all_comps if c != remove_char]
        
    return all_comps


def get_components_except_target_char(ids_str, target_char='女'):
    """
    将 IDS 字符串解析为组件集合。
    1. 移除指定的 IDC 结构符（包括 Unicode IDC 和 Extended IDC）。
    2. 将剩余部分中的 &...; 实体视为一个完整的组件。
    3. 将剩余的普通汉字视为组件。
    4. 返回一个字符集合 set。
    """
    if not ids_str:
        return set()
    
    # 1. 移除 IDC
    cleaned = re.sub(IDC_REGEX, '', ids_str)
    
    # 2. 提取实体组件 (例如 &CDP-8BBF;)
    # 使用 findall 找到所有 &...; 格式的字符串
    entities = set(re.findall(r'&[^;]+;', cleaned))
    
    # 3. 为了提取普通汉字，先将实体从字符串中移除，避免 & c d p ; 被拆成单字
    temp_str = re.sub(r'&[^;]+;', '', cleaned)
    
    # 4. 提取普通字符组件，并移除目标字符
    chars = set(temp_str)
    chars.discard(target_char)
    
    # 5. 合并实体集合和字符集合
    return chars | entities


def extract_single_component(ids_str, target_char='女'):
    """
    从 IDS 字符串中，去除 IDC 字符和 target_char 后，如果只剩下一个汉字，则返回该汉字。
    否则返回 None。
    """
    comps = get_ids_components_list(ids_str, target_char)
    if len(comps) == 1 and len(comps[0]) == 1:
        return comps[0]
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
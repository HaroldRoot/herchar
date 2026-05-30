"""
build.py — herchar 数据管线唯一入口

用法:
    python build.py              # 全流程（nyu → basic → mapping → web）
    python build.py --stage nyu      # 仅生成 nyu_hanzi.json
    python build.py --stage basic    # 仅生成 all_basic_hanzi.json
    python build.py --stage mapping  # 仅更新 mapping.json（需先有 nyu 和 basic）
    python build.py --stage web      # 仅生成 web_mapping*.json（需先有 mapping 和 basic）

依赖:
    pip install pypinyin
"""

import argparse
import collections
import glob
import json
import os
import re
import sys

from utils import (
    IDC_REGEX,
    extract_single_component,
    get_components_except_target_char,
    get_ids_components_list,
)

# ──────────────────────────────────────────────
# 文件路径常量
# ──────────────────────────────────────────────
RAW_DATA_DIR = "raw_data"
NYU_HANZI_FILE = "nyu_hanzi.json"
ALL_BASIC_HANZI_FILE = "all_basic_hanzi.json"
MAPPING_FILE = "mapping.json"
WEB_MAPPING_FILE = "web_mapping.json"
WEB_MAPPING_LESS_FILE = "web_mapping_less.json"


# ──────────────────────────────────────────────
# 公共 I/O 工具
# ──────────────────────────────────────────────

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path, compact=False):
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)


def parse_ids_file(filepath):
    """解析单个 IDS .txt 文件，返回 { char: {Codepoint, IDS, IDS_apparent} } 字典。"""
    records = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(";;") or not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            codepoint, character, ids = parts[0], parts[1], parts[2]
            if len(character) != 1:
                continue
            ids_apparent = ""
            for part in parts[3:]:
                if part.startswith("@apparent="):
                    ids_apparent = part.split("=", 1)[1]
                    break
            records[character] = {
                "Codepoint": codepoint,
                "IDS": ids,
                "IDS_apparent": ids_apparent,
            }
    return records


# ──────────────────────────────────────────────
# Stage 1: 生成 nyu_hanzi.json
# ──────────────────────────────────────────────

def stage_nyu():
    print("=== Stage: nyu_hanzi ===")
    input_files = sorted(glob.glob(os.path.join(RAW_DATA_DIR, "*.txt")))
    if not input_files:
        sys.exit(f"错误：在 {RAW_DATA_DIR} 中找不到 .txt 文件")

    nyu_hanzi = {}
    for filepath in input_files:
        print(f"  处理: {os.path.basename(filepath)}")
        for char, info in parse_ids_file(filepath).items():
            if char in nyu_hanzi:
                continue
            ids, ids_apparent = info["IDS"], info["IDS_apparent"]
            if "女" not in ids and "女" not in ids_apparent:
                continue
            nyu_hanzi[char] = {
                "Codepoint": info["Codepoint"],
                "IDS": ids,
                "IDS_components": get_ids_components_list(ids, remove_char="女"),
                "IDS_apparent": ids_apparent,
                "IDS_apparent_components": get_ids_components_list(
                    ids_apparent, remove_char="女"
                ),
            }

    save_json(nyu_hanzi, NYU_HANZI_FILE)
    print(f"生成 {NYU_HANZI_FILE}：{len(nyu_hanzi)} 个含「女」的汉字\n")


# ──────────────────────────────────────────────
# Stage 2: 生成 all_basic_hanzi.json
# ──────────────────────────────────────────────

def stage_basic():
    print("=== Stage: all_basic_hanzi ===")
    input_file = os.path.join(RAW_DATA_DIR, "IDS-UCS-Basic.txt")
    if not os.path.exists(input_file):
        sys.exit(f"错误：找不到 {input_file}")

    nyu_keys = set()
    if os.path.exists(NYU_HANZI_FILE):
        nyu_keys = set(load_json(NYU_HANZI_FILE).keys())

    all_basic = {}
    for char, info in parse_ids_file(input_file).items():
        if char in nyu_keys:
            continue
        ids, ids_apparent = info["IDS"], info["IDS_apparent"]
        all_basic[char] = {
            "Codepoint": info["Codepoint"],
            "IDS": ids,
            "IDS_components": get_ids_components_list(ids),
            "IDS_apparent": ids_apparent,
            "IDS_apparent_components": get_ids_components_list(ids_apparent),
        }

    save_json(all_basic, ALL_BASIC_HANZI_FILE)
    print(f"生成 {ALL_BASIC_HANZI_FILE}：{len(all_basic)} 个基础汉字\n")


# ──────────────────────────────────────────────
# Stage 3: 生成/更新 mapping.json
# ──────────────────────────────────────────────

def _get_component_tuple(data, key):
    comps = data.get(key)
    if not comps:
        return None
    return tuple(comps)


def stage_mapping():
    print("=== Stage: mapping ===")

    for f in [ALL_BASIC_HANZI_FILE, NYU_HANZI_FILE]:
        if not os.path.exists(f):
            sys.exit(f"错误：缺少 {f}，请先运行 --stage basic/nyu")

    basic_hanzi = load_json(ALL_BASIC_HANZI_FILE)
    nyu_hanzi = load_json(NYU_HANZI_FILE)

    try:
        mapping = load_json(MAPPING_FILE)
    except (FileNotFoundError, json.JSONDecodeError):
        mapping = {}

    # 加载现有 mapping 到 buffer（集合去重）
    buffer = collections.defaultdict(set)
    for k, v in mapping.items():
        if v:
            buffer[k].update(list(v))

    # 构建 basic 汉字组件倒排索引
    print("  构建部件倒排索引...")
    basic_ids_lookup = collections.defaultdict(set)
    for char, data in basic_hanzi.items():
        for key in ("IDS_components", "IDS_apparent_components"):
            t = _get_component_tuple(data, key)
            if t:
                basic_ids_lookup[t].add(char)

    # 遍历 nyu_hanzi 进行匹配
    print("  匹配含「女」汉字...")
    single_count = match_count = 0

    for hanzi, data in nyu_hanzi.items():
        # A. 单部件提取法
        comp = extract_single_component(data.get("IDS", ""))
        if not comp:
            comp = extract_single_component(data.get("IDS_apparent", ""))
        if comp:
            buffer[comp].add(hanzi)
            single_count += 1
            continue

        # B. 部件整体匹配法
        matched = set()
        for key in ("IDS_components", "IDS_apparent_components"):
            t = _get_component_tuple(data, key)
            if t and t in basic_ids_lookup:
                matched.update(basic_ids_lookup[t])
        if matched:
            match_count += 1
            for target in matched:
                buffer[target].add(hanzi)

    # 转回普通 dict，排序字符串保持确定性，移除与 nyu 重叠的键
    nyu_keys = set(nyu_hanzi.keys())
    final = {
        k: "".join(sorted(v))
        for k, v in buffer.items()
        if k not in nyu_keys
    }

    save_json(final, MAPPING_FILE)
    print(
        f"  单部件匹配: {single_count}  组件整体匹配: {match_count}  "
        f"最终键数: {len(final)}"
    )

    # 拼音兜底（需要 pypinyin）
    _fill_by_pinyin(nyu_hanzi, final)

    # 上下文/拼音声旁推断
    _advanced_mapping(basic_hanzi, nyu_hanzi, final)

    save_json(final, MAPPING_FILE)
    nonempty = sum(1 for v in final.values() if v)
    print(
        f"生成 {MAPPING_FILE}：总键数 {len(final)}，"
        f"有映射 {nonempty}，空值 {len(final) - nonempty}\n"
    )


def _fill_by_pinyin(nyu_hanzi, mapping):
    try:
        from pypinyin import Style, pinyin
    except ImportError:
        print("  [跳过] pypinyin 未安装，跳过同音字兜底")
        return

    print("  构建拼音索引（同音字兜底）...")

    pinyin_index = collections.defaultdict(set)
    for char in nyu_hanzi:
        for sublist in pinyin(char, heteronym=False, style=Style.TONE3):
            for p in sublist:
                pinyin_index[p].add(char)

    def get_pinyins(char):
        result = pinyin(char, heteronym=False, style=Style.TONE3)
        return sorted({p for sub in result for p in sub})

    filled = 0
    for char, val in mapping.items():
        if val:
            continue
        matched = set()
        for p in get_pinyins(char):
            matched.update(pinyin_index.get(p, set()))
        matched.discard(char)
        if matched:
            mapping[char] = "".join(sorted(matched))
            filled += 1
    print(f"  同音字兜底填充: {filled} 个")


def _advanced_mapping(basic_hanzi, nyu_hanzi, mapping):
    try:
        from pypinyin import Style, pinyin
    except ImportError:
        print("  [跳过] pypinyin 未安装，跳过声旁/上下文推断")
        return

    print("  声旁/上下文推断...")

    def get_body(ids_str):
        comps = get_components_except_target_char(ids_str)
        return frozenset(comps) if comps else None

    # 构建 nyu 反向映射：{ frozenset(主体): [含女字, ...] }
    nyu_body_map = {}
    for char, info in nyu_hanzi.items():
        body = get_body(info.get("IDS", "")) or get_body(info.get("IDS_apparent", ""))
        if body:
            nyu_body_map.setdefault(body, [])
            if char not in nyu_body_map[body]:
                nyu_body_map[body].append(char)

    def get_yinjie(char):
        res = pinyin(char, heteronym=False, style=Style.NORMAL)
        return res[0][0] if res and res[0] else None

    def get_yunmu(char):
        res = pinyin(char, heteronym=False, style=Style.FINALS)
        return res[0][0] if res and res[0] else None

    def get_shengmu(char):
        res = pinyin(char, heteronym=False, style=Style.FIRST_LETTER)
        return res[0][0] if res and res[0] else None

    def sound_body(char, ids_str):
        if not ids_str:
            return None
        cy, cyu, csm = get_yinjie(char), get_yunmu(char), get_shengmu(char)
        comps = get_components_except_target_char(ids_str)
        matches = []
        for c in comps:
            if c.startswith("&"):
                continue
            if cy == get_yinjie(c) or cyu == get_yunmu(c) or csm == get_shengmu(c):
                matches.append(c)
        return frozenset(matches) if len(matches) == 1 else None

    sorted_chars = sorted(
        basic_hanzi.keys(),
        key=lambda k: int(basic_hanzi[k]["Codepoint"][2:], 16),
    )

    updated = 0
    for i, curr_char in enumerate(sorted_chars):
        curr_ids = basic_hanzi[curr_char].get("IDS", "")
        inferred = sound_body(curr_char, curr_ids)

        if not inferred:
            def ctx_body(curr_ids, neighbor_ids):
                c = get_components_except_target_char(curr_ids)
                n = get_components_except_target_char(neighbor_ids)
                if not c or not n:
                    return None
                common = c & n
                remainder = c - common
                return frozenset(remainder) if common and remainder else None

            if i > 0:
                inferred = ctx_body(curr_ids, basic_hanzi[sorted_chars[i - 1]].get("IDS", ""))
            if not inferred and i < len(sorted_chars) - 1:
                inferred = ctx_body(curr_ids, basic_hanzi[sorted_chars[i + 1]].get("IDS", ""))

        if inferred and inferred in nyu_body_map:
            targets = nyu_body_map[inferred]
            cur_val = mapping.get(curr_char, "")
            new_val = cur_val
            for t in targets:
                if t not in new_val:
                    new_val += t
            if new_val != cur_val:
                mapping[curr_char] = new_val
                updated += 1

    print(f"  声旁/上下文更新: {updated} 个")


# ──────────────────────────────────────────────
# Stage 4: 生成 web_mapping*.json
# ──────────────────────────────────────────────

def rank_candidate(char):
    cp = ord(char)
    in_bmp_cjk = 0x4E00 <= cp <= 0x9FFF
    return (0 if in_bmp_cjk else 1, cp)


def stage_web():
    print("=== Stage: web_mapping ===")

    for f in [MAPPING_FILE]:
        if not os.path.exists(f):
            sys.exit(f"错误：缺少 {f}，请先运行 --stage mapping")

    mapping = load_json(MAPPING_FILE)

    web_full = {}
    web_less = {}

    for char, candidates in mapping.items():
        if not candidates or not isinstance(candidates, str):
            continue
        # 按优先级排序：BMP常用区优先，再按码点升序
        best = min(candidates, key=rank_candidate)
        web_full[char] = best
        # 兼容映射：目标字必须在 BMP CJK 常用区（大多数字体可渲染）
        if 0x4E00 <= ord(best) <= 0x9FFF:
            web_less[char] = best

    save_json(web_full, WEB_MAPPING_FILE, compact=True)
    save_json(web_less, WEB_MAPPING_LESS_FILE, compact=True)

    print(
        f"生成 {WEB_MAPPING_FILE}：{len(web_full)} 个映射\n"
        f"生成 {WEB_MAPPING_LESS_FILE}：{len(web_less)} 个映射（兼容）\n"
    )

    # 展示改进效果示例
    test_chars = ["宁", "它", "亮", "亩", "享", "主", "丽", "久"]
    print("  候选字排序示例（改进后）：")
    for c in test_chars:
        if c in web_full:
            print(f"    {c} → {web_full[c]}  {'(兼容)' if c in web_less else '(仅全量)'}")


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

STAGES = {
    "nyu": stage_nyu,
    "basic": stage_basic,
    "mapping": stage_mapping,
    "web": stage_web,
}

FULL_PIPELINE = ["nyu", "basic", "mapping", "web"]


def main():
    parser = argparse.ArgumentParser(
        description="herchar 数据管线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--stage",
        choices=list(STAGES.keys()),
        help="只运行指定阶段（默认：全流程）",
    )
    args = parser.parse_args()

    if args.stage:
        STAGES[args.stage]()
    else:
        for stage in FULL_PIPELINE:
            STAGES[stage]()
        print("全流程完成。")


if __name__ == "__main__":
    main()

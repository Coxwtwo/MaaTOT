# -*- coding: utf-8 -*-
"""
从 Excel 表格读取异常副本关卡数据，更新 MAA 任务配置文件 T_异常副本.json
"""
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any

import openpyxl

# ==================== 常量配置 ====================
RESOURCE_TYPES = ["思绪残影", "角色材料", "印象材料"]
CHAR_ORDER = ["夏彦", "左然", "莫弈", "陆景和"]  # 角色显示顺序
MATERIAL_ORDER = ["逻辑", "共情", "直觉"]  # 印象材料显示顺序
GRADE_ORDER = ["初级", "中级", "高级"]  # 材料等级显示顺序
IMP_MAP = {"印象I": "初级", "印象II": "中级", "印象III": "高级"}  # 印象列名到等级映射
TEXT_REPLACEMENTS = [("海奥森篇", "海.森篇")]  # 文本替换映射


def load_json(file_path: Path) -> Dict[str, Any]:
    """加载 JSON 文件"""
    if not file_path.exists():
        print(f"错误：找不到源文件 {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"错误：读取或解析 JSON 文件失败 {file_path}，{e}")
        return None


def write_json(data: Dict[str, Any], file_path: Path):
    """写入 JSON 文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"已写入文件：{file_path}")
    except Exception as e:
        print(f"错误：写入 JSON 文件失败 {file_path}，{e}")


def clean_old_options(base_data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
    """
    清理 base_data["option"] 中所有包含"关卡"或"级别选择"的旧选项，
    并记录清理前的原始键顺序。
    返回 (清理后的数据, 原始键列表)
    """
    option = base_data.get("option", {})
    original_keys = list(option.keys())

    # 找出需要删除的键
    keys_to_remove = [k for k in option if "关卡" in k or "级别选择" in k]
    for k in keys_to_remove:
        option.pop(k, None)

    base_data["option"] = option
    return base_data, original_keys


def parse_excel_to_tree(excel_path: Path) -> Dict[str, Any]:
    """
    解析 Excel 文件，构建数据树。
    """
    if not excel_path.exists():
        print(f"错误：找不到 {excel_path}")
        return {}

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = wb.active
        rows = list(sheet.rows)
    except Exception as e:
        print(f"错误：读取 Excel 文件失败 {excel_path}，{e}")
        return {}

    if len(rows) < 2:
        return {}

    headers = [cell.value for cell in rows[0]]

    # 使用 defaultdict 自动创建嵌套字典
    tree = {
        "思绪残影": defaultdict(lambda: defaultdict(list)),
        "角色材料": defaultdict(lambda: defaultdict(list)),
        "印象材料": defaultdict(lambda: defaultdict(list)),
    }

    for row in rows[1:]:
        # 提取行数据，将所有单元格值转为字符串（避免整数/None导致的 strip 错误）
        data = {}
        for i, header in enumerate(headers):
            if header:
                cell_val = row[i].value
                data[header] = str(cell_val) if cell_val is not None else ""

        ep_id = data.get("episode_id", "").strip()
        if not ep_id:
            continue  # 跳过无关卡ID的行

        # 统一格式化为 XX-XX
        ep_id_str = ep_id.zfill(2)
        level_int = data.get("level_int", "").strip().zfill(2)
        display_code = f"{ep_id_str}-{level_int}"

        char = data.get("角色", "").strip()
        shard = data.get("思绪残影", "").strip()
        imp_type = data.get("所属印象", "").strip()

        # 构建关卡条目
        entry = build_level_entry(data, display_code, display_code)

        # --- 处理思绪残影 ---
        if char and shard:
            tree["思绪残影"][char][shard].append(entry)

        # --- 处理角色材料 ---
        if char and not shard:
            for grade in GRADE_ORDER:
                col_name = f"角色{grade}"
                # 原始逻辑：判断该列是否为 "1"（字符串或数字）
                if data.get(col_name, "") == "1":
                    tree["角色材料"][char][grade].append(entry)

        # --- 处理印象材料 ---
        if imp_type and not shard:
            for col, grade in IMP_MAP.items():
                if data.get(col, "") == "1":
                    tree["印象材料"][imp_type][grade].append(entry)

    # 将 defaultdict 转换为普通 dict 以便后续 JSON 序列化
    for res_type in RESOURCE_TYPES:
        tree[res_type] = {k: dict(v) for k, v in tree[res_type].items()}
    return tree


def build_level_entry(
    row_data: Dict[str, Any], full_name: str, display_code: str
) -> Dict[str, Any]:
    """根据行数据构建单个关卡条目（pipeline_override）"""
    ep_id = row_data.get("episode_id", "").strip()
    session = row_data.get("session", "").strip()
    vol_name = row_data.get("volume_name", "").strip()

    # 关卡模板图片：优先使用手动指定的模板，否则自动生成路径
    manual_template = row_data.get("episode_template", "").strip()
    auto_template = f"Debate/E{ep_id}P{session}.png" if session else ""
    final_template = manual_template or auto_template

    # 构建 pipeline_override
    pipeline_override = {"Click_选择主线篇章": {"expected": vol_name}}

    if final_template:
        pipeline_override["Click_进入异常副本"] = {
            "recognition": "TemplateMatch",
            "template": final_template,
            "threshold": 0.93,
        }
    else:
        pipeline_override["Click_进入异常副本"] = {"expected": f"Episode.{ep_id}"}

    pipeline_override["Click_进入异常关卡"] = {"expected": display_code}

    # 处理滑动标记（最上/最下）
    for k, v in {"max_idx": "最下", "min_idx": "最上"}.items():
        val = row_data.get(k, "").strip()
        if val:
            pipeline_override[f"Flag_异常关卡列表{v}端"] = {"expected": val}

    return {"name": full_name, "pipeline_override": pipeline_override}


def sort_items(items, order_list):
    """通用排序函数"""
    if isinstance(order_list, list):
        # 使用自定义顺序排序
        return sorted(
            items, key=lambda x: order_list.index(x) if x in order_list else 999
        )
    else:
        # 保持原顺序
        return list(items)  # 返回新列表避免修改原对象


def generate_new_options(data_tree: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据数据树生成新的 option 字典。
    返回字典格式：{选项键: 选项内容}
    """
    new_options = {}

    for res_type, sub_dict in data_tree.items():
        if not sub_dict:
            continue

        res_key = f"异常关卡{res_type}"
        new_options[res_key] = {"type": "select", "label": res_type, "cases": []}

        # 确定二级菜单的排序规则
        if res_type == "印象材料":
            # 印象材料按类型名称排序
            sorted_names = sort_items(sub_dict.keys(), MATERIAL_ORDER)
        else:
            # 角色材料或思绪残影按固定角色顺序排序
            sorted_names = sort_items(sub_dict.keys(), CHAR_ORDER)

        for name_key in sorted_names:
            content = sub_dict[name_key]  # content 是 {二级名称: 关卡列表} 的字典

            level_2_id = f"{name_key}{res_type}选择"
            new_options[res_key]["cases"].append(
                {"name": name_key, "option": [level_2_id]}
            )
            new_options[level_2_id] = {
                "type": "select",
                "label": "角色" if res_type != "印象材料" else "类型",
                "cases": [],
            }

            # 确定三级菜单的排序规则
            sub_names = content.keys()
            if res_type in ("角色材料", "印象材料"):
                # 材料按等级排序
                sorted_sub_names = sort_items(sub_names, GRADE_ORDER)
            else:
                # 思绪残影按 Excel 行号顺序（即构建时的插入顺序），不排序
                sorted_sub_names = sort_items(sub_names, [])

            for sub_name in sorted_sub_names:
                levels = content[sub_name]  # 关卡条目列表
                level_3_id = f"{name_key}{sub_name}{res_type}关卡"
                new_options[level_2_id]["cases"].append(
                    {"name": sub_name, "option": [level_3_id]}
                )
                new_options[level_3_id] = {
                    "type": "select",
                    "label": sub_name,
                    "cases": levels,
                }

    return new_options


def merge_options(
    original_keys: List[str], old_options: Dict[str, Any], new_options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    按原始键顺序合并新旧选项。
    规则：
    1. 先按 original_keys 顺序插入旧选项中保留的键和新选项中对应的键。
    2. 再插入新选项中尚未出现的键（放在末尾）。
    """
    final_options = {}

    # 按原顺序插入
    for k in original_keys:
        if k in old_options:
            final_options[k] = old_options[k]
        elif k in new_options:
            final_options[k] = new_options[k]

    # 插入剩余的新选项
    for k, v in new_options.items():
        if k not in final_options:
            final_options[k] = v

    return final_options


# ==================== 修改函数：替换 expected 字段中的特定文本 ====================
def replace_expected_text(obj):
    """
    递归遍历对象，将所有字典中键为 'expected' 的字符串值中的 TEXT_REPLACEMENTS 映射进行替换。
    支持嵌套的字典和列表结构。
    """
    if isinstance(obj, dict):
        # 如果是字典，遍历每个键值对
        for key, value in list(obj.items()):
            if key == "expected" and isinstance(value, str):
                for old_text, new_text in TEXT_REPLACEMENTS:
                    obj[key] = obj[key].replace(old_text, new_text)
            else:
                replace_expected_text(value)
    elif isinstance(obj, list):
        for item in obj:
            replace_expected_text(item)
    # 其他类型不处理


def main():
    """主函数：执行完整更新流程"""
    # 使用 pathlib 处理路径
    base_dir = Path(__file__).parent
    root_dir = base_dir.parent.parent  # 项目根目录（tools/autojson 的上两级）

    excel_path = base_dir / "levels.xlsx"
    source_json_path = root_dir / "assets" / "resource" / "tasks" / "T_异常副本.json"
    target_json_path = base_dir / "T_异常副本.json"

    # 1. 加载源 JSON
    base_data = load_json(source_json_path)
    if base_data is None:
        return

    # 2. 清理旧选项
    base_data, original_keys = clean_old_options(base_data)

    # 3. 解析 Excel 构建数据树
    data_tree = parse_excel_to_tree(excel_path)
    if not data_tree or all(not v for v in data_tree.values()):
        print("数据树为空，无更新内容")
        return

    # 4. 生成新选项
    new_options = generate_new_options(data_tree)

    # 5. 合并新旧选项
    final_options = merge_options(
        original_keys, base_data.get("option", {}), new_options
    )
    base_data["option"] = final_options

    # ==================== 修改：写入前替换 expected 中的特定文本 ====================
    replace_expected_text(base_data)

    # 6. 写入目标文件
    write_json(base_data, target_json_path)


if __name__ == "__main__":
    main()

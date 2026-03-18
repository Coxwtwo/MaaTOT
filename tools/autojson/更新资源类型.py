# -*- coding: utf-8 -*-
import json
import os
import openpyxl


def update_maa_json_from_excel(excel_path, source_json_path, target_json_path):
    if not os.path.exists(source_json_path):
        print(f"错误：找不到源文件 {source_json_path}")
        return
    if not os.path.exists(excel_path):
        print(f"错误：找不到 {excel_path}")
        return

    # 1. 加载源 JSON
    with open(source_json_path, 'r', encoding='utf-8') as f:
        base_data = json.load(f)

    # 记录原始 option 的键顺序，用于最后恢复顺序
    original_option_keys = list(base_data["option"].keys())

    # 清理动态生成的旧关卡项（匹配所有包含“关卡”或“级别选择”的键）
    # 同时也清理掉我们要重新生成的“异常关卡XX”键，确保它们能重新插入
    keys_to_remove = [k for k in base_data["option"] if "关卡" in k or "级别选择" in k]
    for k in keys_to_remove:
        if k in base_data["option"]:
            del base_data["option"][k]

    # 2. 读取 Excel 数据并构建树状结构
    # data_tree 结构示例: 
    # {"思绪残影": {"夏彦": {"彼时少年": [关卡列表], "长夜微明": []}}, 
    #  "角色材料": {"夏彦": {"初级": [], "中级": [], "高级": []}},
    #  "印象材料": {"逻辑": {"初级": [], "中级": [], "高级": []}}}
    data_tree = {"思绪残影": {}, "角色材料": {}, "印象材料": {}}

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active
    rows = list(sheet.rows)
    if len(rows) < 2: return
    headers = [cell.value for cell in rows[0]]

    for row in rows[1:]:
        data = {headers[i]: row[i].value for i in range(len(headers)) if headers[i]}
        if data.get('episode_id') is None: continue

        char = str(data.get('角色', '') or '').strip()
        shard = str(data.get('思绪残影', '') or '').strip()
        imp_type = str(data.get('所属印象', '') or '').strip()

        # 统一格式化为 XX-XX (例如 01-08)
        ep_id_str = str(data['episode_id']).strip().zfill(2)
        lv_int_str = str(data['level_int']).strip().zfill(2)
        display_code = f"{ep_id_str}-{lv_int_str}"

        # --- A. 处理思绪残影 (升级为四层结构) ---
        if char and shard:
            if char not in data_tree["思绪残影"]: data_tree["思绪残影"][char] = {}
            if shard not in data_tree["思绪残影"][char]: data_tree["思绪残影"][char][shard] = []
            data_tree["思绪残影"][char][shard].append(build_level_entry(data, display_code, display_code))

        # --- B. 处理角色材料 (四层结构) ---
        # 仅当没有指定思绪残影时，才将其计入角色材料分类
        if char and not shard:
            for grade in ["初级", "中级", "高级"]:
                if str(data.get(f'角色{grade}', '')).strip() == "1":
                    if char not in data_tree["角色材料"]: data_tree["角色材料"][char] = {}
                    if grade not in data_tree["角色材料"][char]: data_tree["角色材料"][char][grade] = []
                    data_tree["角色材料"][char][grade].append(build_level_entry(data, display_code, display_code))

        # --- C. 处理印象材料 (四层结构) ---
        # 仅当没有指定思绪残影时，才将其计入印象材料分类
        if imp_type and not shard:
            imp_map = {"印象I": "初级", "印象II": "中级", "印象III": "高级"}
            for col, grade_label in imp_map.items():
                if str(data.get(col, '')).strip() == "1":
                    if imp_type not in data_tree["印象材料"]: data_tree["印象材料"][imp_type] = {}
                    if grade_label not in data_tree["印象材料"][imp_type]: data_tree["印象材料"][imp_type][grade_label] = []
                    data_tree["印象材料"][imp_type][grade_label].append(build_level_entry(data, display_code, display_code))

    # 3. 递归/分层注入 JSON 选项
    # 定义角色的固定排序顺序
    char_order = ["夏彦", "左然", "莫弈", "陆景和"]
    
    new_options = {}

    for res_type, sub_dict in data_tree.items():
        res_key = f"异常关卡{res_type}"
        new_options[res_key] = {"type": "select", "label": res_type, "cases": []}

        # 按照 char_order 排序二级菜单名
        sorted_names = sorted(sub_dict.keys(), key=lambda x: char_order.index(x) if x in char_order else 999)

        for name_key in sorted_names:
            content = sub_dict[name_key]
            level_2_id = f"{name_key}{res_type}选择"
            new_options[res_key]["cases"].append({"name": name_key, "option": [level_2_id]})
            new_options[level_2_id] = {"type": "select", "label": "角色" if res_type != "印象材料" else "类型", "cases": []}
            
            sub_names = content.keys()
            if res_type == "角色材料" or res_type == "印象材料":
                grade_order = ["初级", "中级", "高级"]
                sorted_sub_names = sorted(sub_names, key=lambda x: grade_order.index(x) if x in grade_order else 999)
            else:
                sorted_sub_names = sorted(sub_names)

            for sub_name in sorted_sub_names:
                levels = content[sub_name]
                level_3_id = f"{name_key}{sub_name}{res_type}关卡"
                new_options[level_2_id]["cases"].append({"name": sub_name, "option": [level_3_id]})
                new_options[level_3_id] = {"type": "select", "label": sub_name, "cases": levels}

    # 合并并排序 option：保持原有顺序，新生成的放在对应位置或末尾
    final_options = {}
    
    # 首先按原顺序填充已存在的 key (包括可能被清理掉但我们重新生成的 key)
    for k in original_option_keys:
        if k in base_data["option"]:
            final_options[k] = base_data["option"][k]
        elif k in new_options:
            final_options[k] = new_options[k]
    
    # 填充剩余新生成的 key (那些原版 JSON 中完全不存在的键)
    for k, v in new_options.items():
        if k not in final_options:
            final_options[k] = v
            
    base_data["option"] = final_options

    # 4. 回写 JSON
    with open(target_json_path, 'w', encoding='utf-8') as f:
        json.dump(base_data, f, ensure_ascii=False, indent=4)
    print(f"已读取源文件并更新至 {target_json_path}")


def build_level_entry(row_data, full_name, display_code):
    ep_id = str(row_data.get('episode_id', '') or '').strip()
    session = str(row_data.get('session', '') or '').strip()
    vol_name = str(row_data.get('volume_name', '') or '').strip()

    manual_template = str(row_data.get('episode_template', '') or '').strip()
    auto_template = f"Debate/E{ep_id}P{session}.png" if session else ""
    final_template = manual_template or auto_template

    # 按照老版 JSON 的 pipeline_override 顺序构建字典
    pipeline_override = {}
    pipeline_override["Click_选择主线篇章"] = {"expected": vol_name}

    if final_template:
        pipeline_override["Click_进入异常副本"] = {"recognition": "TemplateMatch", "template": final_template, "threshold": 0.93}
    else:
        pipeline_override["Click_进入异常副本"] = {"expected": f"Episode.{ep_id}"}

    pipeline_override["Click_进入异常关卡"] = {"expected": display_code}

    # 处理 Flag 字段
    for k, v in {'max_idx': '最下', 'min_idx': '最上'}.items():
        val = str(row_data.get(k, '') or '').strip()
        if val:
            pipeline_override[f"Flag_异常关卡列表{v}端"] = {"expected": val}

    entry = {
        "name": full_name,
        "pipeline_override": pipeline_override
    }
    return entry


def case_name_format(name):
    return name  # 预留格式化函数


if __name__ == "__main__":
    # 获取脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录 (tools/autojson 的上两级)
    root_dir = os.path.dirname(os.path.dirname(base_dir))
    
    excel_path = os.path.join(base_dir, 'levels.xlsx')
    # 读取源文件：assets/resource/tasks/T_异常副本.json
    source_json_path = os.path.join(root_dir, 'assets', 'resource', 'tasks', 'T_异常副本.json')
    # 生成的目标文件仍放在 autojson 目录下
    target_json_path = os.path.join(base_dir, 'T_异常副本.json')
    
    update_maa_json_from_excel(excel_path, source_json_path, target_json_path)
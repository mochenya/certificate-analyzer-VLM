import os
import pandas as pd
from datetime import datetime
import glob
from certificate_analyzer import analyze_certificate
from typing import Dict, Any, Union, Optional
from dotenv import load_dotenv

def format_list_field(value: Union[list, str, None]) -> str:
    """
    辅助函数：将列表字段用'、'连接，如果是字符串则直接返回，None返回空字符串
    """
    if isinstance(value, list):
        # 过滤掉 None 或空字符串，然后连接
        return "、".join([str(v) for v in value if v])
    if value is None:
        return ""
    return str(value)

def process_single_result(file_path: str, api_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 API 返回的嵌套字典转换为符合 CSV 表头的扁平字典
    """
    # 默认空值
    row_data = {
        "文件路径": file_path,
        "获奖人员": "",
        "赛事名称": "",
        "赛道": "",
        "赛级": "",
        "奖级": "",
        "作品名称": "",
        "团体或个体": "",
        "队名": "",
        "指导教师": "",
        "颁发时间": "",
        "颁发机构": ""
    }

    # 如果不是证书或解析失败，直接返回包含路径的空行
    if not api_result or not api_result.get("is_certificate", False):
        return row_data

    data = api_result.get("data", {})
    if not data:
        return row_data

    # 映射字段并处理列表格式
    row_data["获奖人员"] = format_list_field(data.get("members"))
    row_data["赛事名称"] = str(data.get("competition_name") or "")
    row_data["赛道"] = str(data.get("group_category") or "")
    row_data["赛级"] = str(data.get("level") or "")
    row_data["奖级"] = str(data.get("award_name") or "")
    row_data["作品名称"] = str(data.get("project_name") or "")

    is_team_value = data.get("is_team")
    if is_team_value in [True, "true", "True", "TRUE"]:
        row_data["团体或个体"] = "团体"
    elif is_team_value in [False, "false", "False", "FALSE"]:
        row_data["团体或个体"] = "个体"
    else:
        # 如果既不是布尔值也不是布尔字符串，保留原值
        row_data["团体或个体"] = str(is_team_value or "")
    
    row_data["队名"] = str(data.get("team_name") or "")
    row_data["指导教师"] = format_list_field(data.get("advisors"))
    row_data["颁发时间"] = str(data.get("issue_date") or "")
    row_data["颁发机构"] = format_list_field(data.get("issuing_authority"))

    return row_data

def batch_process_images(
    api_key: str,
    base_url: str,
    model: str,
    input_folder: str = "images",
    output_folder: str = "out"
):
    """
    批量解析文件夹图片并实时写入CSV
    """

    # 从参数或环境变量获取配置
    model = model or os.getenv("MODEL")
    api_key = api_key or os.getenv("API_KEY")
    base_url = base_url or os.getenv("BASE_URL")
    
    # 验证必要配置
    if not all([model, api_key, base_url]):
        raise ValueError("缺少必要的配置参数：请提供 model、api_key、base_url 或设置对应的环境变量")
    
    # 1. 准备输出环境
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = os.path.join(output_folder, f"certificate_records_{timestamp}.csv")
    
    # 定义CSV表头顺序
    columns = [
        "文件路径", "获奖人员", "赛事名称", "赛道", "赛级", 
        "奖级", "作品名称", "团体或个体", "队名", "指导教师", 
        "颁发时间", "颁发机构"
    ]

    # 2. 初始化 CSV (写入表头)
    # 使用 utf-8-sig 以实现 UTF-8-BOM 编码，防止 Excel 打开乱码
    pd.DataFrame(columns=columns).to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print(f"[-] 任务开始，结果将保存至: {csv_filename}")

    # 3. 获取所有图片文件
    # 支持常见格式，可根据需要添加
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
    image_files = []
    for ext in image_extensions:
        # 递归查找或仅查找当前目录，此处示例为仅查找当前目录，如需递归可用 ** 和 recursive=True
        image_files.extend(glob.glob(os.path.join(input_folder, ext)))
    
    total_files = len(image_files)
    print(f"[-] 共发现 {total_files} 张图片，开始处理...")

    # 4. 循环处理
    for index, img_path in enumerate(image_files, 1):
        print(f"[{index}/{total_files}] 正在处理: {img_path}")
        
        try:
            # 调用你原有的解析函数
            result = analyze_certificate(
                image_path=img_path,
                model=model,
                api_key=api_key,
                base_url=base_url
            )
            
            # 格式化数据
            flat_data = process_single_result(img_path, result)
            
            # 转为 DataFrame
            df_row = pd.DataFrame([flat_data])
            
            # 5. 增量写入 CSV (mode='a', header=False)
            df_row.to_csv(
                csv_filename, 
                mode='a', 
                header=False, 
                index=False, 
                encoding="utf-8-sig"
            )
            
        except Exception as e:
            print(f"[!] 处理失败 {img_path}: {e}")
            # 即使失败也可以选择记录一条只有路径的错误记录
            error_row = pd.DataFrame([{"文件路径": img_path, "赛事名称": f"处理出错: {str(e)}"}])
            error_row.to_csv(csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")

    print("[-] 批量处理完成。")


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取配置
    API_KEY = os.getenv("API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    MODEL_NAME = os.getenv("MODEL")
    
    # 验证配置是否齐全
    if not all([API_KEY, BASE_URL, MODEL_NAME]):
        print("错误：请设置 API_KEY、BASE_URL、MODEL 环境变量或在代码中硬编码")
        exit(1)
    
    # 确保 images 文件夹存在并放入了图片
    if not os.path.exists("images"):
        os.makedirs("images")
        print("请在 'images' 文件夹中放入图片后重试。")
    else:
        batch_process_images(
            api_key=API_KEY,
            base_url=BASE_URL,
            model=MODEL_NAME,
            input_folder="images",
            output_folder="out"
        )

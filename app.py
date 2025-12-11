import gradio as gr
import pandas as pd
import os
import glob
import time
from datetime import datetime
from dotenv import load_dotenv
from certificate_analyzer import analyze_certificate
from csv_batch_exporter import process_single_result

# 加载环境变量
load_dotenv()

DEFAULT_API_KEY = os.getenv("API_KEY", "")
DEFAULT_BASE_URL = os.getenv("BASE_URL", "https://api-inference.modelscope.cn/v1")
DEFAULT_MODEL = os.getenv("MODEL", "Qwen/Qwen3-VL-8B-Instruct")

# === 获取默认 images 绝对路径 ===
CURRENT_DIR = os.getcwd()
DEFAULT_IMAGES_DIR = os.path.join(CURRENT_DIR, "images")

if not os.path.exists(DEFAULT_IMAGES_DIR):
    os.makedirs(DEFAULT_IMAGES_DIR)

COLUMNS = [
    "文件路径", "获奖人员", "赛事名称", "赛道", "赛级", 
    "奖级", "作品名称", "团体或个体", "队名", "指导教师", 
    "颁发时间", "颁发机构"
]

# --- 核心处理逻辑 ---

def batch_process_generator(image_paths, api_key, base_url, model, temperature, progress=gr.Progress()):
    if not image_paths:
        raise gr.Error("未找到任何图片文件")

    total_files = len(image_paths)
    processed_rows = []
    logs = []

    output_dir = "out"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = os.path.join(output_dir, f"batch_export_{timestamp}.csv")

    # 初始化 CSV
    empty_df = pd.DataFrame(columns=COLUMNS)
    empty_df.to_csv(csv_filename, index=False, encoding="utf-8-sig")

    # 初始状态 yield
    yield empty_df, csv_filename, "🚀 任务启动..."

    for i, file_path in enumerate(image_paths):
        file_name = os.path.basename(file_path)
        
        # 这里只更新顶部的进度条，不影响文本框
        progress((i / total_files), desc=f"正在分析: {file_name}")
        
        log_prefix = f"[{i+1}/{total_files}] {file_name}"

        try:
            # API 分析
            result = analyze_certificate(
                image_path=file_path,
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            
            # 格式化
            row_data = process_single_result(file_path, result)
            
            if result.get("is_certificate"):
                logs.append(f"✅ {log_prefix} -> 成功")
            else:
                logs.append(f"⚠️ {log_prefix} -> 非证书/无效")

        except Exception as e:
            logs.append(f"❌ {log_prefix} -> 错误: {str(e)}")
            row_data = {col: "" for col in COLUMNS}
            row_data["文件路径"] = file_path
            row_data["赛事名称"] = f"Error: {str(e)}"

        # 增量保存
        processed_rows.append(row_data)
        current_df_row = pd.DataFrame([row_data]).reindex(columns=COLUMNS)
        current_df_row.to_csv(csv_filename, mode='a', header=False, index=False, encoding="utf-8-sig")

        # 实时刷新界面
        # 1. 表格倒序（新在前）
        display_df = pd.DataFrame(processed_rows).reindex(columns=COLUMNS).iloc[::-1]
        # 2. 日志倒序显示最近 20 条
        display_logs = "\n".join(logs[-20:])
        
        yield display_df, csv_filename, display_logs

    # 完成状态
    progress(1.0, desc="完成")
    final_log = f"🎉 全部完成！共处理 {total_files} 张。\n" + "\n".join(logs[-10:])
    final_df = pd.DataFrame(processed_rows).reindex(columns=COLUMNS).iloc[::-1]
    
    yield final_df, csv_filename, final_log


# --- 界面回调 ---

def run_single_analysis(image_path, api_key, base_url, model, temperature):
    if not image_path: raise gr.Error("请上传图片")
    if not api_key: raise gr.Error("请配置 API Key")
    try:
        result = analyze_certificate(image_path, model, api_key, base_url, temperature)
        if not result.get("is_certificate"):
            summary = "❌ 识别结果：不是有效的获奖证书。"
        else:
            d = result.get("data", {})
            summary = f"✅ **{d.get('competition_name')}**\n奖项: {d.get('award_name')}\n人员: {', '.join(d.get('members', []))}"
        return result, summary
    except Exception as e:
        raise gr.Error(f"错误: {e}")

def run_folder_batch(folder_path, api_key, base_url, model, temperature):
    if not folder_path: raise gr.Error("请输入路径")
    clean_path = folder_path.strip().strip('"').strip("'")
    if not os.path.exists(clean_path): raise gr.Error("路径不存在")
    
    exts = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp', '*.JPG', '*.PNG']
    paths = []
    for ext in exts:
        paths.extend(glob.glob(os.path.join(clean_path, ext)))
    if not paths: raise gr.Error("文件夹内无图片")
    
    yield from batch_process_generator(paths, api_key, base_url, model, temperature)

def run_upload_batch(files, api_key, base_url, model, temperature):
    if not files: raise gr.Error("请上传文件")
    paths = [f.name for f in files]
    yield from batch_process_generator(paths, api_key, base_url, model, temperature)

# --- 界面构建 ---

with gr.Blocks(title="荣誉证书解析", theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🏆 荣誉证书智能批量解析")
    
    with gr.Accordion("⚙️ 设置", open=False):
        with gr.Row():
            ak = gr.Textbox(value=DEFAULT_API_KEY, label="API Key", type="password")
            url = gr.Textbox(value=DEFAULT_BASE_URL, label="Base URL")
            mod = gr.Textbox(value=DEFAULT_MODEL, label="Model")
        temp = gr.Slider(0, 1, 0.1, label="Temperature")

    with gr.Tabs():
        # Tab 1: 单图
        with gr.TabItem("🖼️ 单图测试"):
            with gr.Row():
                img = gr.Image(type="filepath", height=400)
                with gr.Column():
                    btn1 = gr.Button("分析", variant="primary")
                    out_md = gr.Markdown()
                    out_json = gr.JSON()
            btn1.click(run_single_analysis, [img, ak, url, mod, temp], [out_json, out_md])

        # Tab 2: 文件夹扫描
        with gr.TabItem("📂 本地文件夹"):
            with gr.Row():
                fp = gr.Textbox(value=DEFAULT_IMAGES_DIR, label="文件夹路径", scale=4)
                with gr.Column(scale=1):
                    btn_start_local = gr.Button("🚀 开始", variant="primary")
                    btn_stop_local = gr.Button("🛑 停止", variant="stop")
            
            # 日志框
            log_box = gr.Textbox(label="运行日志", lines=8, max_lines=8, interactive=False)
            
            # 结果展示
            with gr.Row():
                df_view = gr.Dataframe(label="实时结果 (倒序)", headers=COLUMNS, interactive=False)
            file_down = gr.File(label="下载 CSV")

            evt_local = btn_start_local.click(
                run_folder_batch, 
                [fp, ak, url, mod, temp], 
                [df_view, file_down, log_box],
                show_progress="hidden"  # 防止日志框被遮挡
            )
            btn_stop_local.click(None, cancels=[evt_local])

        # Tab 3: 上传
        with gr.TabItem("☁️ 批量上传"):
            up_files = gr.File(file_count="multiple", label="图片上传")
            with gr.Row():
                btn_start_up = gr.Button("开始", variant="primary")
                btn_stop_up = gr.Button("停止", variant="stop")
            
            log_box_up = gr.Textbox(label="日志", lines=5, interactive=False)
            df_view_up = gr.Dataframe(headers=COLUMNS, interactive=False)
            file_down_up = gr.File(label="下载 CSV")

            evt_up = btn_start_up.click(
                run_upload_batch, 
                [up_files, ak, url, mod, temp], 
                [df_view_up, file_down_up, log_box_up],
                show_progress="hidden" # 防止日志框被遮挡
            )
            btn_stop_up.click(None, cancels=[evt_up])

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True, server_name="0.0.0.0")
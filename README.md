# 🏆 荣誉证书智能解析系统 (Certificate Intelligent Analyzer)

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/UI-Gradio-orange)](https://www.gradio.app/)
[![Model](https://img.shields.io/badge/Model-Qwen--VL-violet)](https://qwenlm.github.io/)

**基于视觉语言大模型（VLM）的获奖证书自动识别与结构化提取工具。**
能够将非结构化的证书图片一键转换为标准的 Excel/CSV 数据。

</div>

---

## 📖 项目简介

本项目利用先进的多模态大模型（如 **Qwen-VL**），解决了传统 OCR 难以处理的复杂排版、印章重叠、艺术字体等证书识别难题。系统支持单图测试、文件夹批量扫描及 CSV 导出，非常适合学校、企业进行档案数字化管理。

## ✨ 功能特性

- **🧠 智能识别**：依托 Qwen-VL 等多模态模型，精准提取姓名、奖项、机构等关键信息。
- **📂 批量处理**：支持文件夹自动扫描，一键处理成百上千张证书图片。
- **📊 结构化输出**：自动将非结构化文本转换为标准 CSV 表格，直接兼容 Excel。
- **👁️ 实时预览**：基于 Gradio 的 Web 界面，提供所见即所得的解析体验。

---

## 🚀 快速开始

本项目使用 [uv](https://github.com/astral-sh/uv) 进行极速依赖管理。

### 1. 环境准备

如果尚未安装 `uv`，请执行以下命令：

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装依赖

```bash
# 1. 克隆项目（如果已下载代码请跳过）
git clone https://github.com/yourusername/certificate-analyzer.git
cd certificate-analyzer

# 2. 创建虚拟环境并安装依赖（全自动）
uv sync
```

### 3. API 配置

本项目需要兼容 OpenAI 格式的 VLM API（推荐使用 ModelScope 提供的 Qwen API）。

1.  复制配置文件模板：
    ```bash
    cp .env.example .env
    ```
2.  编辑 `.env` 文件，填入你的 Key：
    ```ini
    API_KEY=your_api_key_here
    BASE_URL=https://api-inference.modelscope.cn/v1
    MODEL=Qwen/Qwen2.5-VL-72B-Instruct  # 推荐使用最新版本
    TEMPERATURE=0.1
    ```

### 4. 运行程序

#### 方式 A：启动 Web 可视化界面 (推荐)
适合交互式测试和少量数据处理。
```bash
uv run python app.py
```
> 启动后访问终端显示的地址：`http://localhost:7860`

#### 方式 B：命令行批量处理
适合后台处理大量图片。
```bash
# 确保图片已放入 images/ 目录
uv run python csv_batch_exporter.py
```

---

## 📁 项目结构

```text
certificate-analyzer/
├── app.py                   # 🌐 Gradio Web 界面入口
├── csv_batch_exporter.py    # ⚙️ 核心批量处理脚本
├── certificate_analyzer.py  # 🧠 大模型调用与解析核心类
├── config.py                # ⚙️ 统一列配置管理模块
├── temple.csv               # 📊 CSV 列名模板文件（可自定义）
├── pyproject.toml           # 📦 UV 依赖配置文件
├── .env                     # 🔑 环境变量（需自行创建）
├── prompt/
│   └── general.md          # 📝 系统提示词（Prompt Engineering）
├── images/                  # 🖼️ 待处理图片目录
└── out/                     # 📂 结果输出目录
```

---

## 📊 输出字段说明

系统将自动提取以下字段，并保存为 `UTF-8 BOM` 编码的 CSV 文件，**Excel 可直接打开不乱码**。

| 字段名 | 说明 | 示例 |
| :--- | :--- | :--- |
| **获奖人员** | 姓名，多人用顿号分隔 | 张三、李四 |
| **赛事名称** | 比赛全称 | 全国大学生数学建模竞赛 |
| **赛道/组别** | 具体的赛道或组别 | 本科组、人工智能赛道 |
| **赛级** | 比赛级别 | 国家级、省部级 |
| **奖级** | 具体获奖等级 | 一等奖、金奖 |
| **作品名称** | 参赛作品名（如有） | 基于AI的智慧农业系统 |
| **形式** | 参赛形式 | 团体、个人 |
| **指导教师** | 教师姓名 | 王老师 |
| **颁发时间** | 格式化日期 (YYYYMMDD) | 20230815 |
| **颁发机构** | 落款印章单位 | 教育部高等教育司 |

---

## ⚙️ 高级配置与调优

### 模型参数微调
在 `.env` 中调整 `TEMPERATURE`：
*   **0.0 - 0.3** (推荐0.1): 结果更确定，适合严格的信息提取。
*   **0.5+**: 结果更多样，但在 OCR 任务中可能导致幻觉。

### 提示词优化
如果你发现某些特定类型的证书识别率低，可以编辑 `prompt/general.md`。该文件包含了发送给大模型的 System Prompt，通过增加 Few-Shot（少样本）示例可以显著提升效果。

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

## 🤝 贡献与反馈

如果你有好的想法或发现了 Bug，欢迎提交 [Issue](https://github.com/mochenya/certificate-analyzer-VLM/issues) 或发起 Pull Request！

**如果不嫌弃，给个 ⭐ Star 吧！**

---

**作者**: [MoChenYa](https://github.com/mochenya)
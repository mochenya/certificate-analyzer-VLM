import base64
import json
import os
import mimetypes
import re
from typing import Dict, Any, Union, Optional
from openai import OpenAI
from dotenv import load_dotenv

def encode_image(image_path: str) -> str:
    """
    读取图片文件并将其编码为 Base64 字符串。

    Args:
        image_path (str): 图片文件的本地绝对路径或相对路径。

    Returns:
        str: 图片内容的 Base64 编码字符串。

    Raises:
        FileNotFoundError: 当指定的图片路径不存在时抛出。
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"错误：图片文件不存在 -> {image_path}")
        
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_image_media_type(image_path: str) -> str:
    """
    根据文件扩展名自动推断 MIME type (如 image/jpeg, image/png)。

    Args:
        image_path (str): 图片文件的路径。

    Returns:
        str: 对应的 MIME 类型字符串。如果无法识别，默认返回 'image/jpeg'。
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    # 定义支持的常见图片格式列表
    valid_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
    
    if mime_type in valid_types:
        return mime_type
    return 'image/jpeg' 

def parse_json_result(raw_text: str) -> Dict[str, Any]:
    """
    清洗大模型返回的文本，提取并解析其中的 JSON 数据。
    自动处理 Markdown 代码块标记 (```json) 和多余的闲聊文本。
    
    Args:
        raw_text (str): 模型返回的原始响应字符串。
        
    Returns:
        Dict[str, Any]: 解析后的字典数据。如果解析失败，返回空字典。
    """
    if not raw_text:
        return {}

    # 1. 尝试使用正则提取 Markdown 代码块内容
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    
    if match:
        json_str = match.group(1)
    else:
        # 2. 如果没有代码块，尝试截取最外层大括号
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = raw_text[start:end+1]
        else:
            json_str = raw_text

    # 3. 反序列化
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"[警告] JSON解析失败: {e}")
        return {}

def analyze_certificate(
    image_path: str, 
    model: str, 
    api_key: str, 
    base_url: str, 
    temperature: float = 0.1
) -> Dict[str, Any]:
    """
    调用大模型 API 分析获奖荣誉证书图片，并结构化提取字段信息。

    Args:
        image_path (str): 图片文件路径。
        model (str): 调用的模型名称 (如 Qwen/Qwen3-VL-8B-Instruct)。
        api_key (str): API 访问密钥。
        base_url (str): API 服务端点地址。
        temperature (float, optional): 模型输出的随机性温度，默认 0.1。

    Returns:
        Dict[str, Any]: 解析后的结构化字典数据。
        
        **返回字典结构示例 (Example Return):**
        ```python
        {
          "is_certificate": True,  # 布尔值：是否为有效证书
          "data": {
            "is_team": False,      # 布尔值：是否为团队赛
            "competition_name": "第十二届全国大学生数字媒体科技作品及创意竞赛",
            "group_category": "江西省赛区",
            "level": "省部级",      # 枚举：国家级/省部级/校级/None
            "award_name": "一等奖",
            "project_name": "个人轻量级爬虫框架", # 若无具体作品名则为空字符串
            "issuing_authority": [ # 数组：颁发机构
                "中国人工智能学会", 
                "全国大学生数字媒体科技作品及创意竞赛组委会"
            ],
            "issue_date": "20230815", # 字符串：yyyyMMdd
            "advisors": ["陈导师"],   # 数组：指导老师
            "team_name": None,        # 字符串或 None
            "members": ["赵六"]       # 数组：获奖成员
          }
        }
        ```
        *注意：若 `is_certificate` 为 False，则 `data` 字段为 None。*

    Raises:
        FileNotFoundError: 如果提示词文件或图片文件不存在。
        RuntimeError: 如果 API 调用过程中发生错误。
    """
    
    # 从参数或环境变量获取配置
    model = model or os.getenv("MODEL")
    api_key = api_key or os.getenv("API_KEY")
    base_url = base_url or os.getenv("BASE_URL")
    temperature = temperature or float(os.getenv("TEMPERATURE", 0.1))
    
    # 验证必要配置
    if not all([model, api_key, base_url]):
        raise ValueError("缺少必要的配置参数：请提供 model、api_key、base_url 或设置对应的环境变量")
    
    # 加载 System Prompt
    prompt_file_path = os.path.join("prompt", "general.md")
    
    if not os.path.exists(prompt_file_path):
        raise FileNotFoundError(f"错误：提示词文件未找到 -> {prompt_file_path}")

    with open(prompt_file_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    # 初始化客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 处理图片
    base64_image = encode_image(image_path)
    mime_type = get_image_media_type(image_path)

    # 构建请求
    messages = [
        {
            "role": "system",
            "content": prompt_text
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析提供的证书图片并结构化提取信息返回："},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}"
                    }
                }
            ]
        }
    ]

    # 调用 API
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2000,
            temperature=temperature
        )
        
        result_text = response.choices[0].message.content
        return parse_json_result(result_text)

    except Exception as e:
        raise RuntimeError(f"API调用失败: {str(e)}")


if __name__ == "__main__":
    # 配置参数
    API_KEY = ""
    BASE_URL = ""
    MODEL = ""
    
    # 图片路径
    img_path = r""
    
    print(f"正在处理图片: {img_path} ...")
    
    try:
        result = analyze_certificate(
            image_path=img_path,
            model=MODEL,
            api_key=API_KEY,
            base_url=BASE_URL,
            temperature=0.01
        )
        
        print("-" * 50)
        print("【识别结果】")
        # 打印格式化后的 JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("-" * 50)
        
        # 简单的数据访问演示
        if result.get("is_certificate"):
            data = result.get("data", {})
            print(f"赛事名称: {data.get('competition_name')}")
            print(f"获奖成员: {', '.join(data.get('members', []))}")
        else:
            print("这不是一张有效的获奖证书。")

    except Exception as e:
        print(f"执行出错: {e}")
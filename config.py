"""
配置模块：统一管理 COLUMNS 配置
通过读取 temple.csv 获取列定义
"""
import os
import pandas as pd
from typing import List

def get_columns_from_templte() -> List[str]:
    """
    从 temple.csv 读取列名配置

    Returns:
        List[str]: 列名列表

    Raises:
        FileNotFoundError: 如果 temple.csv 不存在
        ValueError: 如果文件为空或无列名
    """
    template_path = os.path.join(os.path.dirname(__file__), "temple.csv")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件未找到: {template_path}")

    # 读取 CSV，只读取 header
    try:
        df = pd.read_csv(template_path, nrows=0)
        columns = df.columns.tolist()

        if not columns:
            raise ValueError("temple.csv 为空或没有列名")

        return columns
    except Exception as e:
        raise ValueError(f"读取 temple.csv 失败: {e}")


# 模块加载时自动读取配置
try:
    COLUMNS = get_columns_from_templte()
except FileNotFoundError:
    # 如果文件不存在，使用默认配置（用于首次初始化）
    COLUMNS = [
        "文件路径", "获奖人员", "赛事名称", "赛道", "赛级",
        "奖级", "作品名称", "团体或个体", "队名", "指导教师",
        "颁发时间", "颁发机构"
    ]
except Exception as e:
    print(f"⚠️ 警告: 读取 temple.csv 失败 ({e})，使用默认配置")
    COLUMNS = [
        "文件路径", "获奖人员", "赛事名称", "赛道", "赛级",
        "奖级", "作品名称", "团体或个体", "队名", "指导教师",
        "颁发时间", "颁发机构"
    ]

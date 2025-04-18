#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 基于优化预处理数据的意图识别测试
使用最新增强预处理数据运行方法C（上下文增强识别法）
"""

import json
import os
import time
from intent_recognition_method_c import method_c_analyze_all_dialogs
from intent_recognition_common import generate_report

# 文件路径
PREPROCESSED_DATA_FILE = '/Users/boxie/cursor/intent_test/enhanced_preprocessing_20250418_093512/preprocessed_dialogs.json'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

def load_preprocessed_dialogs():
    """加载预处理后的对话数据"""
    print(f"正在加载增强预处理数据: {PREPROCESSED_DATA_FILE}")
    with open(PREPROCESSED_DATA_FILE, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)
    print(f"数据加载完成，共 {len(dialogs)} 个对话")
    return dialogs

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 基于增强预处理数据的意图识别测试")
    print("=" * 50)
    
    # 当前时间戳，用于区分不同测试结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # 1. 加载预处理后的对话数据
    dialogs = load_preprocessed_dialogs()
    
    # 2. 使用方法C进行意图分析
    print("使用方法C（上下文增强识别法）进行意图分析...")
    intent_results = method_c_analyze_all_dialogs(dialogs)
    
    # 3. 生成分析报告
    report_name = f"方法C_增强预处理数据_{timestamp}"
    generate_report(intent_results, report_name)
    
    print("=" * 50)
    print(f"增强测试完成！结果保存在 intent_analysis_report_{report_name}.json")
    print("=" * 50)

if __name__ == "__main__":
    main()

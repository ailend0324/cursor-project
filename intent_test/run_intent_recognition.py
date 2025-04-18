#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回收宝智能客服系统 - 意图识别测试脚本
该脚本用于测试完整维度数据预处理后的意图识别效果
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from intent_recognition_method_c import method_c_analyze_all_dialogs as recognize_intents_c
from intent_recognition_common import generate_report

def run_intent_recognition(preprocessed_data_path):
    """
    运行意图识别测试
    
    Args:
        preprocessed_data_path: 预处理数据文件路径
    """
    print("="*50)
    print("回收宝智能客服系统 - 意图识别测试")
    print("="*50)
    print(f"预处理数据文件: {preprocessed_data_path}")
    
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"/Users/boxie/cursor/intent_test/intent_recognition_results_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载预处理数据
    print("加载预处理数据...")
    with open(preprocessed_data_path, 'r', encoding='utf-8') as f:
        dialogs = json.load(f)
    
    print(f"加载了 {len(dialogs)} 个对话")
    
    # 运行意图识别方法C（上下文增强识别法）
    print("\n运行意图识别方法C（上下文增强识别法）...")
    start_time = time.time()
    results_c = recognize_intents_c(dialogs)
    end_time = time.time()
    print(f"方法C处理完成，耗时: {end_time - start_time:.2f}秒")
    
    # 评估并保存结果，直接打印摘要
    method_name = "方法C_完整维度预处理数据"
    report = generate_report(results_c, method_name, output_dir)
    print("\n结果已保存至: {}".format(output_dir))
    print("\n意图识别测试完成!")
    print("="*50)
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python run_intent_recognition.py <预处理数据文件路径>")
        sys.exit(1)
    
    preprocessed_data_path = sys.argv[1]
    run_intent_recognition(preprocessed_data_path)

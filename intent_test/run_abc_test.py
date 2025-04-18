#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - A/B/C测试主脚本
运行三种不同的意图识别方法并比较结果
"""

import os
import json
import subprocess
from intent_recognition_common import compare_methods

# 测试方法列表
methods = [
    {"name": "方法A_基础规则匹配法", "script": "intent_recognition_method_a.py"},
    {"name": "方法B_多维度混合识别框架", "script": "intent_recognition_test.py"},
    {"name": "方法C_上下文增强识别法", "script": "intent_recognition_method_c.py"}
]

# 输出目录
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - A/B/C测试")
    print("=" * 50)
    
    # 运行各方法
    for method in methods:
        print(f"\n运行 {method['name']}...")
        subprocess.run(['python', method['script']], check=True)
    
    # 收集各方法的报告
    reports = {}
    for method in methods:
        report_path = f"{OUTPUT_DIR}/intent_analysis_report_{method['name']}.json"
        # 如果方法B的报告文件名不同，需要特殊处理
        if method['name'] == "方法B_多维度混合识别框架":
            report_path = f"{OUTPUT_DIR}/intent_analysis_report.json"
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                reports[method['name']] = json.load(f)
        else:
            print(f"警告：找不到 {method['name']} 的报告文件")
    
    # 比较方法效果
    if len(reports) > 1:
        compare_methods(reports)
    else:
        print("错误：至少需要两个方法的报告才能进行比较")
    
    print("=" * 50)
    print("A/B/C测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 增强版数据预处理测试
使用优化后的数据预处理函数处理原始数据
"""

import os
import json
import time
from data_preprocessing import preprocess_data

# 文件路径
DATA_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 增强版数据预处理测试")
    print("=" * 50)
    
    # 当前时间戳，用于区分不同测试结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_DIR, f"enhanced_preprocessing_{timestamp}")
    
    print(f"原始数据文件: {DATA_FILE}")
    print(f"输出目录: {output_dir}")
    
    # 使用增强版数据预处理函数处理原始数据
    print("\n开始增强版数据预处理...")
    dialogs = preprocess_data(
        file_path=DATA_FILE,
        output_dir=output_dir,
        filter_quality=True  # 启用低质量对话过滤
    )
    
    # 保存预处理结果统计信息
    stats = {
        "timestamp": timestamp,
        "total_dialogs": len(dialogs),
        "total_messages": sum(len(dialog["messages"]) for dialog in dialogs),
        "avg_dialog_length": sum(len(dialog["messages"]) for dialog in dialogs) / max(1, len(dialogs)),
        "min_dialog_length": min(len(dialog["messages"]) for dialog in dialogs) if dialogs else 0,
        "max_dialog_length": max(len(dialog["messages"]) for dialog in dialogs) if dialogs else 0,
        "user_messages_ratio": sum(1 for dialog in dialogs for msg in dialog["messages"] if msg["sender_type"] == 1) / 
                              max(1, sum(len(dialog["messages"]) for dialog in dialogs)),
    }
    
    # 保存统计信息
    stats_file = os.path.join(output_dir, "preprocessing_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("\n增强版数据预处理完成!")
    print(f"预处理结果统计:")
    print(f"  - 总对话数: {stats['total_dialogs']}")
    print(f"  - 总消息数: {stats['total_messages']}")
    print(f"  - 平均对话长度: {stats['avg_dialog_length']:.2f}")
    print(f"  - 最短对话长度: {stats['min_dialog_length']}")
    print(f"  - 最长对话长度: {stats['max_dialog_length']}")
    print(f"  - 用户消息比例: {stats['user_messages_ratio']:.2%}")
    print(f"  - 详细统计信息已保存至: {stats_file}")
    
    print("\n接下来可以运行意图识别测试:")
    print("python run_optimized_test.py")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

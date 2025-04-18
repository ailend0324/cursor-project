#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 完整维度数据预处理
保留所有原始数据维度，确保数据完整性
"""

import os
import json
import time
import pandas as pd
from data_preprocessing import preprocess_data

# 文件路径
DATA_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

def save_sample_csv(dialogs, output_file, sample_size=100):
    """
    保存预处理数据样本为CSV文件
    
    参数:
    - dialogs: 预处理后的对话列表
    - output_file: 输出文件路径
    - sample_size: 样本大小
    """
    print(f"生成预处理数据样本CSV: {output_file}")
    
    # 创建样本数据
    sample_data = []
    
    # 取前sample_size个对话
    for dialog in dialogs[:sample_size]:
        conversation_id = dialog["conversation_id"]
        
        # 获取元数据
        metadata = dialog["metadata"]
        
        # 添加每条消息
        for msg in dialog["messages"]:
            # 提取结构化信息
            structured_info = ""
            if "order_number" in msg:
                structured_info += f"订单号: {msg['order_number']}; "
            if "logistics_number" in msg:
                structured_info += f"物流单号: {msg['logistics_number']}; "
            
            # 创建行数据，保持与源文件相同的列名
            row = {
                "touch_id": conversation_id,
                "user_name": metadata.get("user_name", ""),
                "user_start_time": metadata.get("user_start_time", ""),
                "user_end_time": metadata.get("user_end_time", ""),
                "servicer_name": metadata.get("servicer_name", ""),
                "new_feedback_name": metadata.get("new_feedback_name", ""),
                "create_time": metadata.get("create_time", ""),
                "group_name": metadata.get("group_name", ""),
                "send_time": msg["send_time"],
                "sender_type": msg["sender_type"],
                "send_content": msg["content"],
                "seq_no": msg["seq_no"],
                # 添加处理后的额外字段
                "clean_content": msg["clean_content"],
                "enhanced_content": msg.get("enhanced_content", ""),
                "structured_info": structured_info
            }
            sample_data.append(row)
    
    # 创建DataFrame并保存为CSV
    df = pd.DataFrame(sample_data)
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"样本数据已保存至: {output_file}")
    
    # 另外保存一个中文列名版本的CSV，方便用户查看
    chinese_columns = {
        "touch_id": "对话ID",
        "user_name": "用户名",
        "user_start_time": "用户开始时间",
        "user_end_time": "用户结束时间",
        "servicer_name": "客服名",
        "new_feedback_name": "满意度评价",
        "create_time": "创建时间",
        "group_name": "分组名称",
        "send_time": "发送时间",
        "sender_type": "发送者类型",
        "send_content": "原始消息内容",
        "seq_no": "消息序号",
        "clean_content": "清洗后内容",
        "enhanced_content": "增强清洗内容",
        "structured_info": "结构化信息"
    }
    
    df_chinese = df.copy()
    df_chinese.columns = [chinese_columns.get(col, col) for col in df.columns]
    # 转换发送者类型为更易读的形式
    df_chinese["发送者类型"] = df_chinese["发送者类型"].map({1: "用户", 2: "客服"})
    
    chinese_file = output_file.replace('.csv', '_中文列名.csv')
    df_chinese.to_csv(chinese_file, index=False, encoding='utf-8')
    print(f"中文列名版本已保存至: {chinese_file}")

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 完整维度数据预处理")
    print("=" * 50)
    
    # 当前时间戳，用于区分不同测试结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_DIR, f"complete_preprocessing_{timestamp}")
    
    print(f"原始数据文件: {DATA_FILE}")
    print(f"输出目录: {output_dir}")
    
    # 使用增强版数据预处理函数处理原始数据
    print("\n开始完整维度数据预处理...")
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
    
    # 生成样本CSV
    sample_csv_file = os.path.join(OUTPUT_DIR, "完整维度预处理数据样本.csv")
    save_sample_csv(dialogs, sample_csv_file)
    
    print("\n完整维度数据预处理完成!")
    print(f"预处理结果统计:")
    print(f"  - 总对话数: {stats['total_dialogs']}")
    print(f"  - 总消息数: {stats['total_messages']}")
    print(f"  - 平均对话长度: {stats['avg_dialog_length']:.2f}")
    print(f"  - 最短对话长度: {stats['min_dialog_length']}")
    print(f"  - 最长对话长度: {stats['max_dialog_length']}")
    print(f"  - 用户消息比例: {stats['user_messages_ratio']:.2%}")
    print(f"  - 详细统计信息已保存至: {stats_file}")
    print(f"  - 样本数据已保存至: {sample_csv_file}")
    
    print("\n接下来可以运行意图识别测试:")
    print(f"python run_intent_recognition.py {output_dir}/preprocessed_dialogs.json")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
from datetime import datetime
import re
import json

def load_data(file_path):
    """加载Excel文件"""
    return pd.read_excel(file_path)

def preprocess_conversation(df):
    """预处理对话数据"""
    # 按touch_id分组，重建对话
    conversations = {}
    
    for _, row in df.iterrows():
        touch_id = row['touch_id']
        if touch_id not in conversations:
            conversations[touch_id] = {
                'dialogue': [],
                'user_name': row['user_name'],
                'servicer_name': row['servicer_name'],
                'start_time': row['user_start_time'],
                'end_time': row['user_end_time'],
                'group_name': row['group_name']
            }
        
        conversations[touch_id]['dialogue'].append({
            'sender_type': row['sender_type'],
            'content': row['send_content'],
            'send_time': row['send_time'],
            'seq_no': row['seq_no']
        })

    return conversations

def analyze_conversation_topics(conversations):
    """分析对话主题和意图"""
    for touch_id, conv in conversations.items():
        # 初始化分析结果
        conv['analysis'] = {
            'main_topic': None,
            'user_intent': None,
            'conversation_length': len(conv['dialogue']),
            'response_time': [],
            'keywords': set()
        }
        
        # 提取关键词和计算响应时间
        for i, msg in enumerate(conv['dialogue']):
            if i > 0:
                time_diff = (pd.to_datetime(msg['send_time']) - 
                           pd.to_datetime(conv['dialogue'][i-1]['send_time'])).total_seconds()
                conv['analysis']['response_time'].append(time_diff)

    return conversations

def main():
    # 读取数据
    file_path = '/Users/boxie/cursor/ai_service/250407.xlsx'
    df = load_data(file_path)
    
    # 预处理对话
    conversations = preprocess_conversation(df)
    
    # 分析对话
    analyzed_conversations = analyze_conversation_topics(conversations)
    
    # 保存处理后的数据
    with open('customer_service_data/data/processed/conversations.json', 'w', encoding='utf-8') as f:
        json.dump(analyzed_conversations, f, ensure_ascii=False, indent=2, default=str)
    
    # 输出基本统计信息
    print(f"总对话数: {len(conversations)}")
    
if __name__ == "__main__":
    main() 
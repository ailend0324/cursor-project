import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import jieba
import numpy as np
from datetime import datetime

def analyze_conversations(file_path, sample_size=1000):
    """深入分析客服对话数据"""
    try:
        # 读取Excel文件
        print(f"正在读取文件: {file_path}")
        df = pd.read_excel(file_path)
        print(f"数据加载完成，共 {df.shape[0]} 行，{df.shape[1]} 列")
        
        # 数据预处理
        # 转换时间列
        for col in ['user_start_time', 'user_end_time', 'create_time', 'send_time']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 转换sender_type为分类
        if 'sender_type' in df.columns:
            df['sender_type'] = df['sender_type'].fillna(-1).astype(int)
            # 判断sender_type可能的含义
            unique_sender_types = df['sender_type'].unique()
            print(f"发送者类型唯一值: {unique_sender_types}")
            
            # 假设: 1=用户，2=客服，4=系统消息 (需要根据数据实际情况调整)
            sender_mapping = {
                1: '用户',
                2: '客服',
                4: '系统',
                -1: '未知'
            }
            df['sender_category'] = df['sender_type'].map(lambda x: sender_mapping.get(x, f'其他({x})'))
        
        # 1. 基本统计分析
        print("\n=== 基本统计分析 ===")
        # 对话数量
        conversation_count = df['touch_id'].nunique()
        print(f"总对话数量: {conversation_count}")
        
        # 按组统计
        if 'group_name' in df.columns:
            group_stats = df.groupby('group_name')['touch_id'].nunique().sort_values(ascending=False)
            print("\n各业务组对话数量:")
            print(group_stats.head(10))
        
        # 2. 对话长度分析
        print("\n=== 对话长度分析 ===")
        conv_lengths = df.groupby('touch_id').size()
        print(f"平均对话轮次: {conv_lengths.mean():.2f}")
        print(f"对话轮次中位数: {conv_lengths.median()}")
        print(f"最短对话轮次: {conv_lengths.min()}")
        print(f"最长对话轮次: {conv_lengths.max()}")
        
        # 3. 对话时长分析
        print("\n=== 对话时长分析 ===")
        if 'user_start_time' in df.columns and 'user_end_time' in df.columns:
            # 创建一个包含唯一对话的DataFrame
            conv_df = df.drop_duplicates('touch_id')[['touch_id', 'user_start_time', 'user_end_time']]
            # 计算对话时长（分钟）
            conv_df['duration_min'] = (conv_df['user_end_time'] - conv_df['user_start_time']).dt.total_seconds() / 60
            # 移除异常值
            conv_df = conv_df[conv_df['duration_min'] >= 0]
            
            print(f"平均对话时长: {conv_df['duration_min'].mean():.2f} 分钟")
            print(f"对话时长中位数: {conv_df['duration_min'].median():.2f} 分钟")
            print(f"最短对话时长: {conv_df['duration_min'].min():.2f} 分钟")
            print(f"最长对话时长: {conv_df['duration_min'].max():.2f} 分钟")
        
        # 4. 常见问题/关键词分析
        print("\n=== 常见问题分析 ===")
        # 提取用户消息
        if 'sender_category' in df.columns:
            user_msgs = df[df['sender_category'] == '用户']['send_content'].dropna().astype(str)
            
            # 提取高频词（使用jieba分词）
            words = []
            for msg in user_msgs.sample(min(len(user_msgs), sample_size)):
                words.extend([w for w in jieba.cut(msg) if len(w) > 1 and not w.isdigit()])
            
            word_freq = Counter(words).most_common(20)
            print("用户消息高频词:")
            for word, count in word_freq:
                print(f"- {word}: {count}")
        
        # 5. 抽样对话分析
        print("\n=== 典型对话示例 ===")
        # 随机抽取3个中等长度的对话
        mid_length_convs = conv_lengths[(conv_lengths > 5) & (conv_lengths < 20)].sample(min(3, len(conv_lengths)))
        
        for conv_id in mid_length_convs.index:
            print(f"\n对话ID: {conv_id}")
            conv_messages = df[df['touch_id'] == conv_id].sort_values('seq_no')
            for _, msg in conv_messages.iterrows():
                sender = msg.get('sender_category', '未知')
                content = msg.get('send_content', '')
                if pd.isna(content):
                    content = '[空消息]'
                print(f"{sender}: {content}")
                
        return df
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "/Users/boxie/cursor/ai_service/data/merged_chat_records.xlsx"
    
    df = analyze_conversations(file_path) 
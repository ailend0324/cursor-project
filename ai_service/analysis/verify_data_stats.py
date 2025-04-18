#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from collections import Counter

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def analyze_sample(sample_size):
    """分析指定样本量的数据"""
    print(f"\n=== 分析 {sample_size} 条样本 ===")
    
    # 加载数据
    file_path = os.path.join(PROJECT_ROOT, "data", "merged_chat_records.xlsx")
    df = pd.read_excel(file_path, nrows=sample_size)
    print(f"实际读取：{len(df)}行")
    
    # 字段缺失率
    print("\n字段缺失率:")
    missing = df.isnull().sum() / len(df) * 100
    for col in df.columns:
        print(f"{col}: {missing[col]:.2f}%")
    
    # 业务场景分布
    print("\n业务场景分布:")
    scene_dist = df['group_name'].value_counts(normalize=True).mul(100)
    for scene, pct in scene_dist.items():
        print(f"{scene}: {pct:.2f}%")
    
    # 发送者类型分布
    print("\n发送者类型分布:")
    sender_dist = df['sender_type'].value_counts(normalize=True).mul(100)
    for sender, pct in sender_dist.items():
        print(f"{sender}: {pct:.2f}%")
    
    # 对话轮次分析
    print("\n对话轮次分析:")
    conv_lengths = df.groupby('touch_id').size()
    print(f"平均轮次: {conv_lengths.mean():.2f}")
    print(f"最大轮次: {conv_lengths.max()}")
    print(f"最小轮次: {conv_lengths.min()}")
    
    # 反馈评价分析
    print("\n反馈评价分析:")
    feedback_rate = df['new_feedback_name'].notna().sum() / df['touch_id'].nunique() * 100
    print(f"有反馈评价的对话比例: {feedback_rate:.2f}%")
    if feedback_rate > 0:
        feedback_dist = df['new_feedback_name'].value_counts(normalize=True).mul(100)
        for feedback, pct in feedback_dist.items():
            print(f"{feedback}: {pct:.2f}%")
    
    # 分析无客服回复对话
    print("\n无客服回复对话分析:")
    conv_senders = df.groupby('touch_id')['sender_type'].apply(set)
    no_service = conv_senders.apply(lambda x: 2.0 not in x)
    no_service_rate = no_service.mean() * 100
    print(f"无客服回复对话比例: {no_service_rate:.2f}%")
    
    # 转人工分析
    print("\n转人工分析:")
    transfer_msgs = df[df['send_content'].str.contains('人工|客服', na=False)]
    transfer_rate = len(transfer_msgs) / len(df) * 100
    print(f"包含人工/客服关键词的消息比例: {transfer_rate:.2f}%")
    
    # 对话时长分析
    print("\n对话时长分析:")
    df['user_start_time'] = pd.to_datetime(df['user_start_time'])
    df['user_end_time'] = pd.to_datetime(df['user_end_time'])
    durations = (df.groupby('touch_id')['user_end_time'].first() - df.groupby('touch_id')['user_start_time'].first()).dt.total_seconds() / 60
    print(f"平均对话时长(分钟): {durations.mean():.2f}")
    print(f"最大对话时长(分钟): {durations.max():.2f}")
    print(f"最小对话时长(分钟): {durations.min():.2f}")
    
    # 时长分布
    duration_bins = [0, 5, 10, 15, 30, 60, float('inf')]
    duration_labels = ['0-5分钟', '5-10分钟', '10-15分钟', '15-30分钟', '30-60分钟', '60分钟以上']
    duration_dist = pd.cut(durations, bins=duration_bins, labels=duration_labels).value_counts(normalize=True).mul(100).sort_index()
    print("\n对话时长分布:")
    for bin_name, pct in duration_dist.items():
        print(f"{bin_name}: {pct:.2f}%")
    
    # 消息内容长度分析
    print("\n消息内容长度分析:")
    df['content_length'] = df['send_content'].fillna('').astype(str).apply(len)
    print(f"平均内容长度: {df['content_length'].mean():.2f}字符")
    print(f"最大内容长度: {df['content_length'].max()}字符")
    print(f"最小内容长度: {df['content_length'].min()}字符")
    
    # 内容长度分布
    print("\n消息内容长度分布:")
    length_bins = [0, 10, 20, 50, 100, 200, float('inf')]
    length_labels = ['0-10字符', '10-20字符', '20-50字符', '50-100字符', '100-200字符', '200字符以上']
    length_dist = pd.cut(df['content_length'], bins=length_bins, labels=length_labels).value_counts(normalize=True).mul(100).sort_index()
    for bin_name, pct in length_dist.items():
        print(f"{bin_name}: {pct:.2f}%")
    
    # 根据发送者类型分析内容长度
    print("\n不同发送者的消息长度:")
    for sender_type in df['sender_type'].dropna().unique():
        sender_length = df[df['sender_type'] == sender_type]['content_length']
        print(f"发送者类型 {sender_type}: 平均长度 {sender_length.mean():.2f}字符, 最大长度 {sender_length.max()}字符")
    
    # 常见客服回复模板
    print("\n常见客服回复模板TOP10:")
    service_msgs = df[df['sender_type'] == 2.0]['send_content'].fillna('')
    common_replies = service_msgs.value_counts().head(10)
    for reply, count in common_replies.items():
        # 限制输出长度，避免过长输出
        if len(reply) > 50:
            reply = reply[:47] + "..."
        print(f"{count}次: {reply}")
    
    # 常见系统消息
    print("\n常见系统消息TOP5:")
    system_msgs = df[df['sender_type'] == 4.0]['send_content'].fillna('')
    common_system = system_msgs.value_counts().head(5)
    for msg, count in common_system.items():
        if len(msg) > 50:
            msg = msg[:47] + "..."
        print(f"{count}次: {msg}")
    
    # 常见用户问题分析
    print("\n常见用户问题TOP10:")
    user_msgs = df[df['sender_type'] == 1.0]['send_content'].fillna('')
    common_questions = user_msgs.value_counts().head(10)
    for question, count in common_questions.items():
        if len(question) > 50:
            question = question[:47] + "..."
        print(f"{count}次: {question}")
    
    # 分析用户首次咨询问题
    print("\n用户首次咨询问题类型:")
    
    def categorize_question(text):
        if not isinstance(text, str) or not text:
            return '其他'
        
        text = text.lower()
        if re.search(r'价格|多少钱|报价|估价|值多少', text):
            return '价格咨询'
        elif re.search(r'怎么用|如何使用|操作|步骤', text):
            return '使用指导'
        elif re.search(r'订单|物流|快递|发货|收货|查询', text):
            return '订单物流'
        elif re.search(r'退款|退货|换货|取消', text):
            return '退换货'
        elif re.search(r'账号|密码|登录|注册', text):
            return '账号问题'
        elif re.search(r'质量|保修|维修|坏了|故障|问题', text):
            return '质量问题'
        elif re.search(r'人工|客服', text):
            return '人工请求'
        elif re.search(r'你好|您好|早上好|下午好|晚上好', text):
            return '问候语'
        else:
            return '其他'
    
    first_msgs = df[df['sender_type'] == 1.0].groupby('touch_id').first()['send_content']
    first_msg_categories = first_msgs.apply(categorize_question)
    category_counts = first_msg_categories.value_counts(normalize=True).mul(100)
    print("首次咨询问题分类:")
    for category, pct in category_counts.items():
        print(f"{category}: {pct:.2f}%")
    
    return df

def main():
    """主函数"""
    # 分析不同大小的样本
    sample_sizes = [10000, 50000, 100000]
    for size in sample_sizes:
        analyze_sample(size)

if __name__ == "__main__":
    main() 
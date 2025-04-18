#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 意图识别公共函数
包含数据加载、预处理和评估等共用功能
"""

import pandas as pd
import re
import json
import jieba
import jieba.analyse
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime

# 文件路径
DATA_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

# ================ 数据加载与预处理 ================

def load_data(file_path):
    """加载Excel数据文件"""
    print(f"正在加载数据: {file_path}")
    df = pd.read_excel(file_path)
    print(f"数据加载完成，共 {len(df)} 行")
    return df

def preprocess_data(df):
    """数据预处理：清洗、结构化和发送者识别"""
    # 复制数据，避免修改原始数据
    processed_df = df.copy()
    
    # 处理缺失值
    processed_df = processed_df.dropna(subset=['send_content'])
    
    # 统一时间格式
    if 'send_time' in processed_df.columns:
        processed_df['send_time'] = pd.to_datetime(processed_df['send_time'], errors='coerce')
    
    # 按对话ID和序号排序
    if 'touch_id' in processed_df.columns and 'seq_no' in processed_df.columns:
        processed_df = processed_df.sort_values(['touch_id', 'seq_no'])
    
    # 提取结构化信息
    processed_df['order_number'] = processed_df['send_content'].apply(extract_order_number)
    processed_df['logistics_number'] = processed_df['send_content'].apply(extract_logistics_number)
    
    # 清理文本内容
    processed_df['clean_content'] = processed_df['send_content'].apply(clean_text)
    
    # 识别发送者类型（如果没有sender_type字段）
    if 'sender_type' not in processed_df.columns:
        processed_df = identify_sender_types(processed_df)
    
    print(f"数据预处理完成，处理后 {len(processed_df)} 行")
    return processed_df

def extract_order_number(text):
    """提取订单号"""
    if not isinstance(text, str):
        return None
    
    # 常见订单号模式
    patterns = [
        r'订单号[:：]?\s*(\d{20,25})',  # 匹配"订单号:1234567890123456789"格式
        r'订单\s*[号#]?\s*[为是]?\s*(\d{20,25})',  # 匹配"订单号是1234567890123456789"格式
        r'(\d{20,25})'  # 匹配独立的长数字（可能是订单号）
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def extract_logistics_number(text):
    """提取物流单号"""
    if not isinstance(text, str):
        return None
    
    # 常见物流单号模式
    patterns = [
        r'快递单号[:：]?\s*([A-Za-z0-9]{10,15})',  # 匹配"快递单号:SF1234567890"格式
        r'物流单号[:：]?\s*([A-Za-z0-9]{10,15})',  # 匹配"物流单号:SF1234567890"格式
        r'运单号[:：]?\s*([A-Za-z0-9]{10,15})',    # 匹配"运单号:SF1234567890"格式
        r'SF(\d{10,12})',                        # 匹配顺丰单号格式
        r'YT(\d{10,12})',                        # 匹配圆通单号格式
        r'ZTO(\d{10,12})'                        # 匹配中通单号格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def clean_text(text):
    """清理文本内容，保留语义信息"""
    if not isinstance(text, str):
        return ""
    
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 处理表情符号，保留语义
    text = re.sub(r'\[ww:天使\]', '[微笑]', text)
    text = re.sub(r'\[ww:飞吻\]', '[亲吻]', text)
    text = re.sub(r'\[ww:.*?\]', '', text)
    
    # 处理图片链接
    text = re.sub(r'<img\s+src="[^"]*"[^>]*>', '[图片]', text)
    
    # 敏感信息脱敏
    text = re.sub(r'1[3-9]\d{9}', '[手机号]', text)
    text = re.sub(r'\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', '[邮箱]', text)
    
    return text.strip()

def identify_sender_types(df):
    """识别发送者类型"""
    # 客服特征词
    service_keywords = ['您好', '感谢', '请问', '祝您', '很高兴为您服务', '请稍等', 
                        '亲', '已经进入人工服务', '回收宝', '小宝', '客服', 
                        '有什么可以帮到您', '请问有什么可以帮到您']
    
    # 用户特征词
    user_keywords = ['怎么', '什么时候', '多久', '多少钱', '谢谢', '我的', 
                     '订单号', '快递', '物流', '取消', '退款']
    
    # 添加发送者类型列
    if 'sender_type' not in df.columns:
        df['sender_type'] = None
    
    # 按对话分组处理
    for touch_id, group in df.groupby('touch_id'):
        prev_type = None
        
        for idx, row in group.iterrows():
            content = str(row['clean_content'])
            
            # 根据内容特征判断发送者类型
            service_score = sum([1 for word in service_keywords if word in content])
            user_score = sum([1 for word in user_keywords if word in content])
            
            # 初步判断
            if service_score > user_score:
                current_type = 2  # 客服
            elif user_score > service_score:
                current_type = 1  # 用户
            else:
                # 如果无法通过关键词判断，则考虑交替规则
                if prev_type == 1:
                    current_type = 2
                elif prev_type == 2:
                    current_type = 1
                else:
                    # 默认第一条是客服消息
                    current_type = 2
            
            df.at[idx, 'sender_type'] = current_type
            prev_type = current_type
    
    return df

def organize_dialogs(df):
    """将扁平数据组织为对话结构"""
    dialogs = []
    
    for touch_id, group in df.groupby('touch_id'):
        # 按seq_no排序
        group = group.sort_values('seq_no')
        
        # 提取用户消息
        user_messages = group[group['sender_type'] == 1]
        
        # 创建对话结构
        dialog = {
            "conversation_id": touch_id,
            "metadata": {
                "group_name": group['group_name'].iloc[0] if 'group_name' in group.columns else "",
                "start_time": group['send_time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
                "end_time": group['send_time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
            },
            "statistics": {
                "message_count": len(group),
                "user_message_count": len(user_messages),
                "service_message_count": len(group) - len(user_messages),
            },
            "messages": [],
            "user_messages": [],
            "structured_info": {
                "order_numbers": list(filter(None, group['order_number'].unique())),
                "logistics_numbers": list(filter(None, group['logistics_number'].unique())),
            }
        }
        
        # 添加消息
        for _, row in group.iterrows():
            message = {
                "seq_no": row['seq_no'],
                "sender_type": row['sender_type'],
                "content": row['send_content'],
                "clean_content": row['clean_content'],
                "send_time": row['send_time'].strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in row else "",
            }
            dialog["messages"].append(message)
            
            # 收集用户消息
            if row['sender_type'] == 1:
                dialog["user_messages"].append(message)
        
        dialogs.append(dialog)
    
    print(f"对话组织完成，共 {len(dialogs)} 个对话")
    return dialogs

def extract_keywords(text, topK=5):
    """提取文本关键词"""
    if not isinstance(text, str) or not text.strip():
        return []
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=topK)
    return keywords

# ================ 评估与报告 ================

def generate_report(intent_results, method_name):
    """生成意图分析报告"""
    # 保存详细结果
    with open(f"{OUTPUT_DIR}/intent_analysis_results_{method_name}.json", "w", encoding="utf-8") as f:
        json.dump(intent_results, f, ensure_ascii=False, indent=2)
    
    # 统计业务场景分布
    scenario_counts = Counter([result["business_scenario"] for result in intent_results])
    total_dialogs = len(intent_results)
    
    # 统计意图分布
    intent_counts = Counter([result["intent"] for result in intent_results])
    
    # 统计置信度分布
    confidence_levels = {
        "高 (>0.8)": len([r for r in intent_results if r["confidence"] > 0.8]),
        "中 (0.6-0.8)": len([r for r in intent_results if 0.6 <= r["confidence"] <= 0.8]),
        "低 (<0.6)": len([r for r in intent_results if r["confidence"] < 0.6])
    }
    
    # 生成报告
    report = {
        "方法": method_name,
        "总对话数": total_dialogs,
        "业务场景分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in scenario_counts.items()},
        "意图分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in intent_counts.items()},
        "置信度分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in confidence_levels.items()},
        "其他类别占比": f"{intent_counts.get('其他查询', 0)/total_dialogs*100:.2f}%",
        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存报告
    with open(f"{OUTPUT_DIR}/intent_analysis_report_{method_name}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印报告摘要
    print("\n" + "=" * 50)
    print(f"意图分析报告摘要 - {method_name}")
    print("=" * 50)
    print(f"总对话数: {total_dialogs}")
    print("\n业务场景分布:")
    for scenario, count in scenario_counts.most_common():
        print(f"  - {scenario}: {count} ({count/total_dialogs*100:.2f}%)")
    
    print("\n意图分布:")
    for intent, count in intent_counts.most_common():
        print(f"  - {intent}: {count} ({count/total_dialogs*100:.2f}%)")
    
    print(f"\n'其他'类别占比: {intent_counts.get('其他查询', 0)/total_dialogs*100:.2f}%")
    print("=" * 50)
    
    return report

def compare_methods(reports):
    """比较不同方法的效果"""
    print("\n" + "=" * 50)
    print("A/B/C测试结果比较")
    print("=" * 50)
    
    methods = list(reports.keys())
    
    # 比较"其他"类别占比
    print("'其他'类别占比比较:")
    for method in methods:
        other_ratio = reports[method]["其他类别占比"]
        print(f"  - {method}: {other_ratio}")
    
    # 比较置信度分布
    print("\n高置信度(>0.8)比例比较:")
    for method in methods:
        high_conf = reports[method]["置信度分布"]["高 (>0.8)"]["占比"]
        print(f"  - {method}: {high_conf}")
    
    # 比较业务场景覆盖
    print("\n业务场景覆盖数量比较:")
    for method in methods:
        scenario_count = len(reports[method]["业务场景分布"])
        print(f"  - {method}: {scenario_count}个场景")
    
    # 比较意图覆盖
    print("\n意图覆盖数量比较:")
    for method in methods:
        intent_count = len(reports[method]["意图分布"])
        print(f"  - {method}: {intent_count}个意图")
    
    print("=" * 50)
    
    # 保存比较结果
    comparison = {
        "方法": methods,
        "其他类别占比": {method: reports[method]["其他类别占比"] for method in methods},
        "高置信度比例": {method: reports[method]["置信度分布"]["高 (>0.8)"]["占比"] for method in methods},
        "业务场景覆盖": {method: len(reports[method]["业务场景分布"]) for method in methods},
        "意图覆盖": {method: len(reports[method]["意图分布"]) for method in methods},
        "比较时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(f"{OUTPUT_DIR}/intent_methods_comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

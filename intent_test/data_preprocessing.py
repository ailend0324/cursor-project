#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 数据预处理增强
实现更全面的数据预处理，包括数据清洗、质量过滤和结构优化
"""

import pandas as pd
import numpy as np
import re
import json
from datetime import datetime
import matplotlib.pyplot as plt
from collections import Counter
import os

# 文件路径
DATA_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

def load_data(file_path):
    """加载Excel数据文件"""
    print(f"正在加载数据: {file_path}")
    df = pd.read_excel(file_path)
    print(f"数据加载完成，共 {len(df)} 行")
    return df

def analyze_raw_data(df):
    """分析原始数据基本特征"""
    # 基本统计
    total_rows = len(df)
    total_conversations = df['touch_id'].nunique()
    avg_messages_per_conv = total_rows / total_conversations
    
    # 检查缺失值
    missing_values = df.isnull().sum()
    missing_ratio = missing_values / len(df) * 100
    
    # 发送者类型分布
    if 'sender_type' in df.columns:
        sender_type_dist = df['sender_type'].value_counts(normalize=True) * 100
    else:
        sender_type_dist = "未找到sender_type字段"
    
    # 消息长度分布
    df['content_length'] = df['send_content'].apply(lambda x: len(str(x)) if isinstance(x, str) else 0)
    length_stats = df['content_length'].describe()
    
    # 对话长度分布（每个对话的消息数）
    conv_length = df.groupby('touch_id').size()
    conv_length_stats = conv_length.describe()
    
    # 生成报告
    report = {
        "总行数": total_rows,
        "总对话数": total_conversations,
        "平均每对话消息数": avg_messages_per_conv,
        "缺失值统计": {col: {"缺失数": int(missing_values[col]), "缺失率": f"{missing_ratio[col]:.2f}%"} 
                   for col in missing_values.index},
        "发送者类型分布": sender_type_dist.to_dict() if isinstance(sender_type_dist, pd.Series) else sender_type_dist,
        "消息长度统计": {stat: length_stats[stat] for stat in length_stats.index},
        "对话长度统计": {stat: conv_length_stats[stat] for stat in conv_length_stats.index},
        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存报告
    with open(f"{OUTPUT_DIR}/raw_data_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印报告摘要
    print("\n" + "=" * 50)
    print("原始数据分析摘要")
    print("=" * 50)
    print(f"总行数: {total_rows}")
    print(f"总对话数: {total_conversations}")
    print(f"平均每对话消息数: {avg_messages_per_conv:.2f}")
    
    print("\n缺失值情况:")
    for col in missing_values.index:
        if missing_values[col] > 0:
            print(f"  - {col}: {missing_values[col]} ({missing_ratio[col]:.2f}%)")
    
    print("\n对话长度分布:")
    print(f"  - 最小值: {conv_length_stats['min']}")
    print(f"  - 25%分位: {conv_length_stats['25%']}")
    print(f"  - 中位数: {conv_length_stats['50%']}")
    print(f"  - 75%分位: {conv_length_stats['75%']}")
    print(f"  - 最大值: {conv_length_stats['max']}")
    print("=" * 50)
    
    # 生成对话长度分布图
    plt.figure(figsize=(10, 6))
    plt.hist(conv_length, bins=30, alpha=0.7)
    plt.title('对话长度分布')
    plt.xlabel('消息数')
    plt.ylabel('对话数')
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{OUTPUT_DIR}/conversation_length_distribution.png")
    
    return report

def clean_data(df):
    """
    数据清洗函数，处理原始数据中的各种问题
    
    参数:
    - df: 原始数据DataFrame
    
    返回:
    - 清洗后的DataFrame
    """
    print("开始数据清洗...")
    original_shape = df.shape
    
    # 1. 处理缺失值
    # 对于关键列，删除缺失的行
    for col in ['touch_id', 'seq_no', 'send_time']:
        if col in df.columns:
            df = df[~df[col].isna()]
    
    # 2. 标准化时间格式
    if 'send_time' in df.columns:
        df['send_time'] = pd.to_datetime(df['send_time'], errors='coerce')
        # 删除时间格式无效的行
        df = df[~df['send_time'].isna()]
    
    # 3. 清洗消息内容
    if 'send_content' in df.columns:
        # 将非字符串内容转换为字符串
        df['send_content'] = df['send_content'].apply(lambda x: str(x) if not pd.isna(x) else "")
        # 清洗文本内容
        df['clean_content'] = df['send_content'].apply(clean_text)
    
    # 4. 处理重复数据
    df = df.drop_duplicates(subset=['touch_id', 'seq_no'], keep='first')
    
    # 5. 确保数据类型正确
    if 'seq_no' in df.columns:
        df['seq_no'] = pd.to_numeric(df['seq_no'], errors='coerce')
    
    if 'sender_type' in df.columns:
        df['sender_type'] = pd.to_numeric(df['sender_type'], errors='coerce')
    
    # 6. 按对话ID和消息序号排序
    df = df.sort_values(by=['touch_id', 'seq_no'])
    
    # 7. 重置索引
    df = df.reset_index(drop=True)
    
    # 打印清洗结果
    cleaned_shape = df.shape
    removed_rows = original_shape[0] - cleaned_shape[0]
    print(f"数据清洗完成，移除了 {removed_rows} 行 ({removed_rows/original_shape[0]*100:.2f}%)，剩余 {cleaned_shape[0]} 行")
    
    return df

def clean_text(text):
    """
    清洗文本内容，保留语义信息
    
    参数:
    - text: 原始文本
    
    返回:
    - 清洗后的文本
    """
    if not text or pd.isna(text):
        return ""
    
    # 转为字符串
    text = str(text)
    
    # 1. 去除首尾空白字符
    text = text.strip()
    
    # 2. 替换多余空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 3. 去除特殊控制字符
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    # 4. 替换HTML实体
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    
    # 5. 去除URL
    text = re.sub(r'https?://\S+', '[URL]', text)
    
    return text

def identify_sender_type(df):
    """
    识别发送者类型（用户或客服）
    
    参数:
    - df: 数据DataFrame
    
    返回:
    - 添加或修正sender_type的DataFrame
    """
    print("识别发送者类型...")
    
    # 检查是否已有sender_type列
    if 'sender_type' in df.columns:
        # 检查现有的sender_type值是否有问题
        invalid_sender_types = df[~df['sender_type'].isin([1, 2])].shape[0]
        if invalid_sender_types > 0:
            print(f"发现 {invalid_sender_types} 行的sender_type值无效，将进行修正")
    else:
        # 如果没有sender_type列，创建一个
        df['sender_type'] = 0
        print("未找到sender_type列，将创建并填充该列")
    
    # 基于消息内容和其他特征识别发送者类型
    # 1 = 用户，2 = 客服
    
    # 1. 基于用户名和客服名识别
    if 'user_name' in df.columns and 'servicer_name' in df.columns:
        # 如果消息发送者与user_name相同，则为用户消息
        user_name_mask = df.apply(lambda row: not pd.isna(row['user_name']) and str(row['user_name']) in str(row['send_content']), axis=1)
        df.loc[user_name_mask & (df['sender_type'] == 0), 'sender_type'] = 1
        
        # 如果消息发送者与servicer_name相同，则为客服消息
        servicer_name_mask = df.apply(lambda row: not pd.isna(row['servicer_name']) and str(row['servicer_name']) in str(row['send_content']), axis=1)
        df.loc[servicer_name_mask & (df['sender_type'] == 0), 'sender_type'] = 2
    
    # 2. 基于消息内容特征识别
    # 客服常用语
    servicer_patterns = [
        r'您好',
        r'请问有什么可以帮到您',
        r'感谢您的咨询',
        r'请稍等',
        r'很高兴为您服务',
        r'请问还有其他问题吗',
        r'祝您生活愉快',
        r'回收宝客服'
    ]
    
    for pattern in servicer_patterns:
        pattern_mask = df['send_content'].str.contains(pattern, na=False)
        df.loc[pattern_mask & (df['sender_type'] == 0), 'sender_type'] = 2
    
    # 3. 基于对话模式识别
    # 通常对话是交替进行的，可以根据这个特点来推断
    for touch_id in df['touch_id'].unique():
        touch_df = df[df['touch_id'] == touch_id].sort_values('seq_no')
        
        # 如果第一条消息sender_type未知，假设为用户
        if touch_df.iloc[0]['sender_type'] == 0:
            df.loc[touch_df.iloc[0].name, 'sender_type'] = 1
        
        # 遍历该对话的所有消息
        prev_sender = None
        for idx, row in touch_df.iterrows():
            if row['sender_type'] == 0:  # 如果sender_type未知
                if prev_sender == 1:
                    df.loc[idx, 'sender_type'] = 2  # 如果上一条是用户消息，则这条是客服消息
                elif prev_sender == 2:
                    df.loc[idx, 'sender_type'] = 1  # 如果上一条是客服消息，则这条是用户消息
            prev_sender = df.loc[idx, 'sender_type']
    
    # 4. 处理剩余未识别的消息
    # 如果还有未识别的消息，根据整体分布进行推断
    if (df['sender_type'] == 0).any():
        # 计算已识别消息中用户和客服的比例
        identified_df = df[df['sender_type'] != 0]
        user_ratio = (identified_df['sender_type'] == 1).mean()
        
        # 根据比例随机分配
        unidentified_indices = df[df['sender_type'] == 0].index
        user_count = int(len(unidentified_indices) * user_ratio)
        
        # 随机选择一部分作为用户消息
        user_indices = np.random.choice(unidentified_indices, user_count, replace=False)
        df.loc[user_indices, 'sender_type'] = 1
        
        # 剩余的作为客服消息
        df.loc[df['sender_type'] == 0, 'sender_type'] = 2
    
    # 统计结果
    user_count = (df['sender_type'] == 1).sum()
    servicer_count = (df['sender_type'] == 2).sum()
    total_count = len(df)
    
    print(f"发送者类型识别完成:")
    print(f"  - 用户消息: {user_count} ({user_count/total_count*100:.2f}%)")
    print(f"  - 客服消息: {servicer_count} ({servicer_count/total_count*100:.2f}%)")
    
    return df

def extract_structured_info(df):
    """
    提取结构化信息（订单号、物流单号等）
    
    参数:
    - df: 数据DataFrame
    
    返回:
    - 添加结构化信息的DataFrame
    """
    print("提取结构化信息...")
    
    # 添加结构化信息列
    df['order_number'] = None
    df['logistics_number'] = None
    df['product_info'] = None
    df['price_info'] = None
    
    # 订单号模式（通常为18位数字）
    order_pattern = r'\b\d{18}\b'
    
    # 物流单号模式（常见快递公司的物流单号格式）
    logistics_patterns = [
        r'\b[A-Za-z]{2}\d{9}[A-Za-z]{2}\b',  # 顺丰
        r'\b\d{13}\b',  # 申通、圆通
        r'\b\d{10,12}\b',  # EMS、中通、韵达
        r'\b[A-Za-z0-9]{10,15}\b'  # 其他
    ]
    
    # 产品信息模式
    product_patterns = [
        r'(iPhone\s*\d+\s*[A-Za-z]*\s*[\d]*\s*[A-Za-z]*)',
        r'(华为|荣耀|小米|OPPO|vivo|三星|魅族|一加)[\s\S]{0,10}?[\w\d]+',
        r'(\d+GB|\d+TB|\d+寸|\d+英寸)'
    ]
    
    # 价格信息模式
    price_pattern = r'(\d+(?:\.\d+)?元|\d+(?:\.\d+)?块钱|\d+(?:\.\d+)?[元块]|\¥\s*\d+(?:\.\d+)?)'
    
    # 遍历每一行提取结构化信息
    for idx, row in df.iterrows():
        content = str(row['send_content']) if not pd.isna(row['send_content']) else ""
        
        # 提取订单号
        order_matches = re.findall(order_pattern, content)
        if order_matches:
            df.at[idx, 'order_number'] = order_matches[0]
        
        # 提取物流单号
        for pattern in logistics_patterns:
            logistics_matches = re.findall(pattern, content)
            if logistics_matches:
                # 过滤掉可能与订单号重复的物流单号
                if not order_matches or logistics_matches[0] not in order_matches:
                    df.at[idx, 'logistics_number'] = logistics_matches[0]
                    break
        
        # 提取产品信息
        for pattern in product_patterns:
            product_matches = re.findall(pattern, content)
            if product_matches:
                df.at[idx, 'product_info'] = product_matches[0]
                break
        
        # 提取价格信息
        price_matches = re.findall(price_pattern, content)
        if price_matches:
            df.at[idx, 'price_info'] = price_matches[0]
    
    # 在对话内传播结构化信息
    # 例如，如果一个对话中的某条消息提到了订单号，那么这个订单号应该与整个对话关联
    for touch_id, group in df.groupby('touch_id'):
        # 收集该对话中的所有结构化信息
        order_numbers = group['order_number'].dropna().unique()
        logistics_numbers = group['logistics_number'].dropna().unique()
        product_infos = group['product_info'].dropna().unique()
        price_infos = group['price_info'].dropna().unique()
        
        # 如果该对话中有结构化信息，将其传播到对话的所有消息中
        if len(order_numbers) > 0:
            df.loc[df['touch_id'] == touch_id, 'order_number'] = df.loc[df['touch_id'] == touch_id, 'order_number'].fillna(order_numbers[0])
        
        if len(logistics_numbers) > 0:
            df.loc[df['touch_id'] == touch_id, 'logistics_number'] = df.loc[df['touch_id'] == touch_id, 'logistics_number'].fillna(logistics_numbers[0])
        
        if len(product_infos) > 0:
            df.loc[df['touch_id'] == touch_id, 'product_info'] = df.loc[df['touch_id'] == touch_id, 'product_info'].fillna(product_infos[0])
        
        if len(price_infos) > 0:
            df.loc[df['touch_id'] == touch_id, 'price_info'] = df.loc[df['touch_id'] == touch_id, 'price_info'].fillna(price_infos[0])
    
    return df

def organize_dialogs(df):
    """
    将扁平数据组织为对话结构
    
    参数:
    - df: 预处理后的DataFrame
    
    返回:
    - 对话列表
    """
    print("组织对话...")
    
    # 确保所有必要的列都存在
    required_columns = ['touch_id', 'seq_no', 'sender_type', 'send_content', 'clean_content', 'send_time']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"缺少必要的列: {col}")
    
    # 获取所有原始列名
    original_columns = df.columns.tolist()
    
    # 按对话ID分组
    dialogs = []
    for touch_id, group in df.groupby('touch_id'):
        # 按消息序号排序
        group = group.sort_values('seq_no')
        
        # 创建元数据
        metadata = {
            "start_time": group['send_time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
            "end_time": group['send_time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
        }
        
        # 添加所有可能有用的元数据字段
        for col in ['group_name', 'servicer_name', 'user_name', 'new_feedback_name', 'create_time', 
                   'user_start_time', 'user_end_time']:
            if col in group.columns:
                # 确保值是JSON可序列化的
                value = group[col].iloc[0]
                if pd.isna(value):
                    metadata[col] = ""
                else:
                    # 将numpy类型转换为Python原生类型
                    if hasattr(value, 'item'):
                        metadata[col] = value.item()
                    else:
                        metadata[col] = str(value)
        
        # 创建消息列表
        messages = []
        for _, row in group.iterrows():
            message = {
                "id": str(row.name),
                "seq_no": float(row['seq_no']),
                "sender_type": int(row['sender_type']),
                "content": str(row['send_content']) if not pd.isna(row['send_content']) else "",
                "clean_content": str(row['clean_content']) if not pd.isna(row['clean_content']) else "",
                "send_time": row['send_time'].strftime('%Y-%m-%d %H:%M:%S') if not pd.isna(row['send_time']) else ""
            }
            
            # 添加结构化信息
            if 'order_number' in row and not pd.isna(row['order_number']):
                message["order_number"] = str(row['order_number'])
            
            if 'logistics_number' in row and not pd.isna(row['logistics_number']):
                message["logistics_number"] = str(row['logistics_number'])
            
            if 'product_info' in row and not pd.isna(row['product_info']):
                message["product_info"] = str(row['product_info'])
            
            if 'price_info' in row and not pd.isna(row['price_info']):
                message["price_info"] = str(row['price_info'])
            
            # 添加其他可能有用的字段
            for col in original_columns:
                if col not in ['touch_id', 'seq_no', 'sender_type', 'send_content', 'clean_content', 'send_time', 
                              'order_number', 'logistics_number', 'product_info', 'price_info']:
                    if col in row and not pd.isna(row[col]):
                        # 确保值是JSON可序列化的
                        value = row[col]
                        if hasattr(value, 'item'):
                            message[col] = value.item()
                        else:
                            message[col] = str(value)
            
            messages.append(message)
        
        # 创建对话结构
        dialog = {
            "conversation_id": str(touch_id),
            "metadata": metadata,
            "messages": messages,
            "structured_info": {
                "order_numbers": list(set([msg.get("order_number", "") for msg in messages if "order_number" in msg and msg["order_number"]])),
                "logistics_numbers": list(set([msg.get("logistics_number", "") for msg in messages if "logistics_number" in msg and msg["logistics_number"]])),
                "product_infos": list(set([msg.get("product_info", "") for msg in messages if "product_info" in msg and msg["product_info"]])),
                "price_infos": list(set([msg.get("price_info", "") for msg in messages if "price_info" in msg and msg["price_info"]]))
            },
            "original_data": {
                "total_messages": len(messages),
                "user_messages": sum(1 for msg in messages if msg["sender_type"] == 1),
                "service_messages": sum(1 for msg in messages if msg["sender_type"] == 2),
                "avg_message_length": float(sum(len(msg["content"]) for msg in messages) / max(1, len(messages)))
            }
        }
        
        # 添加原始数据统计
        for col in original_columns:
            if col not in ['touch_id', 'seq_no', 'sender_type', 'send_content', 'clean_content', 'send_time']:
                non_null_values = group[col].dropna()
                if len(non_null_values) > 0:
                    # 根据数据类型选择合适的统计方法
                    try:
                        # 尝试转换为数值型
                        numeric_values = pd.to_numeric(non_null_values)
                        # 确保值是JSON可序列化的
                        dialog["original_data"][col + "_avg"] = float(numeric_values.mean())
                        dialog["original_data"][col + "_min"] = float(numeric_values.min())
                        dialog["original_data"][col + "_max"] = float(numeric_values.max())
                    except:
                        # 如果不是数值型，则保存唯一值
                        unique_values = non_null_values.unique()
                        if len(unique_values) <= 5:  # 只保存少量唯一值
                            # 确保所有值都是JSON可序列化的
                            json_safe_values = []
                            for v in unique_values:
                                if hasattr(v, 'item'):
                                    json_safe_values.append(v.item())
                                else:
                                    json_safe_values.append(str(v))
                            dialog["original_data"][col + "_values"] = json_safe_values
                        else:
                            dialog["original_data"][col + "_unique_count"] = int(len(unique_values))
        
        dialogs.append(dialog)
    
    print(f"对话组织完成，共 {len(dialogs)} 个对话")
    return dialogs

def analyze_preprocessed_data(dialogs):
    """分析预处理后的数据特征"""
    # 基本统计
    total_dialogs = len(dialogs)
    message_counts = [d["original_data"]["total_messages"] for d in dialogs]
    user_message_counts = [d["original_data"]["user_messages"] for d in dialogs]
    service_message_counts = [d["original_data"]["service_messages"] for d in dialogs]
    
    # 结构化信息统计
    dialogs_with_order = sum(1 for d in dialogs if "order_numbers" in d["structured_info"] and d["structured_info"]["order_numbers"])
    dialogs_with_logistics = sum(1 for d in dialogs if "logistics_numbers" in d["structured_info"] and d["structured_info"]["logistics_numbers"])
    
    # 对话长度分布
    message_count_stats = {
        "min": min(message_counts),
        "max": max(message_counts),
        "mean": sum(message_counts) / len(message_counts),
        "median": sorted(message_counts)[len(message_counts) // 2]
    }
    
    # 用户/客服消息比例
    user_ratio = sum(user_message_counts) / sum(message_counts) if sum(message_counts) > 0 else 0
    
    # 生成报告
    report = {
        "总对话数": total_dialogs,
        "消息总数": sum(message_counts),
        "用户消息总数": sum(user_message_counts),
        "客服消息总数": sum(service_message_counts),
        "用户/客服消息比例": f"{user_ratio:.2f}",
        "包含订单号的对话数": dialogs_with_order,
        "包含物流单号的对话数": dialogs_with_logistics,
        "对话长度统计": message_count_stats,
        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存报告
    with open(f"{OUTPUT_DIR}/preprocessed_data_analysis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印报告摘要
    print("\n" + "=" * 50)
    print("预处理数据分析摘要")
    print("=" * 50)
    print(f"总对话数: {total_dialogs}")
    print(f"消息总数: {sum(message_counts)}")
    print(f"用户消息总数: {sum(user_message_counts)}")
    print(f"客服消息总数: {sum(service_message_counts)}")
    print(f"用户/客服消息比例: {user_ratio:.2f}")
    print(f"包含订单号的对话数: {dialogs_with_order} ({dialogs_with_order/total_dialogs*100:.2f}%)")
    print(f"包含物流单号的对话数: {dialogs_with_logistics} ({dialogs_with_logistics/total_dialogs*100:.2f}%)")
    
    print("\n对话长度统计:")
    print(f"  - 最小值: {message_count_stats['min']}")
    print(f"  - 最大值: {message_count_stats['max']}")
    print(f"  - 平均值: {message_count_stats['mean']:.2f}")
    print(f"  - 中位数: {message_count_stats['median']}")
    print("=" * 50)
    
    return report

def preprocess_data(df, min_messages=3, min_user_messages=1):
    """完整的数据预处理流程"""
    print("开始数据预处理...")
    
    # 保存原始列名，确保不丢失维度
    original_columns = df.columns.tolist()
    print(f"原始数据包含以下列: {original_columns}")
    
    # 1. 分析原始数据
    raw_analysis = analyze_raw_data(df)
    
    # 2. 处理缺失值
    df = df.dropna(subset=['send_content'])
    print(f"处理缺失值后，剩余 {len(df)} 行")
    
    # 3. 统一时间格式
    if 'send_time' in df.columns:
        df['send_time'] = pd.to_datetime(df['send_time'], errors='coerce')
    
    # 4. 按对话ID和序号排序
    if 'touch_id' in df.columns and 'seq_no' in df.columns:
        df = df.sort_values(['touch_id', 'seq_no'])
    
    # 5. 识别发送者类型
    df = identify_sender_type(df)
    
    # 6. 清理文本内容
    df['clean_content'] = df['send_content'].apply(clean_text)
    
    # 7. 提取结构化信息
    df = extract_structured_info(df)
    
    # 8. 过滤低质量对话
    filtered_df = filter_low_quality_conversations(df, min_messages, min_user_messages)
    
    # 9. 增强对话结构
    enhanced_df = enhance_dialog_structure(filtered_df)
    
    # 10. 组织为对话结构
    dialogs = organize_dialogs(enhanced_df)
    
    # 11. 分析预处理后的数据
    preprocessed_analysis = analyze_preprocessed_data(dialogs)
    
    # 12. 保存预处理后的数据
    with open(f"{OUTPUT_DIR}/preprocessed_dialogs.json", "w", encoding="utf-8") as f:
        json.dump(dialogs, f, ensure_ascii=False, indent=2)
    
    print("数据预处理完成！")
    return dialogs

def filter_low_quality_conversations(df, min_messages=3, min_user_messages=1):
    """过滤低质量对话"""
    # 计算每个对话的消息数
    conv_message_counts = df.groupby('touch_id').size()
    
    # 计算每个对话的用户消息数
    user_message_counts = df[df['sender_type'] == 1].groupby('touch_id').size()
    
    # 找出符合条件的对话ID
    valid_conv_ids = conv_message_counts[conv_message_counts >= min_messages].index
    valid_user_conv_ids = user_message_counts[user_message_counts >= min_user_messages].index
    
    # 取交集
    valid_ids = set(valid_conv_ids).intersection(set(valid_user_conv_ids))
    
    # 过滤数据
    filtered_df = df[df['touch_id'].isin(valid_ids)]
    
    # 统计过滤结果
    total_convs = df['touch_id'].nunique()
    filtered_convs = filtered_df['touch_id'].nunique()
    removed_convs = total_convs - filtered_convs
    
    print(f"\n过滤低质量对话:")
    print(f"  - 原始对话数: {total_convs}")
    print(f"  - 过滤后对话数: {filtered_convs}")
    print(f"  - 移除对话数: {removed_convs} ({removed_convs/total_convs*100:.2f}%)")
    
    return filtered_df

def enhance_dialog_structure(df):
    """增强对话结构（添加缺失的开场白、结束语等）"""
    # 按对话分组处理
    enhanced_df = df.copy()
    
    for touch_id, group in df.groupby('touch_id'):
        group = group.sort_values('seq_no')
        
        # 检查是否有开场白
        has_greeting = False
        for idx, row in group.iterrows():
            if row['sender_type'] == 2 and any(word in str(row['send_content']) for word in ['您好', '欢迎']):
                has_greeting = True
                break
        
        # 如果没有开场白，添加新的开场白消息，而不是混入现有消息
        if not has_greeting and len(group) > 0:
            # 创建新的开场白消息，而不是修改现有消息
            first_msg_time = group.iloc[0]['send_time']
            # 创建一个稍早的时间
            greeting_time = first_msg_time - pd.Timedelta(seconds=1)
            
            # 创建新行
            new_row = pd.Series({
                'touch_id': touch_id,
                'seq_no': group.iloc[0]['seq_no'] - 0.1,  # 确保排在第一位
                'sender_type': 2,  # 客服
                'send_content': "您好，欢迎咨询回收宝客服。",
                'clean_content': "您好，欢迎咨询回收宝客服。",
                'send_time': greeting_time
            })
            
            # 添加其他必要的列
            for col in enhanced_df.columns:
                if col not in new_row.index:
                    if col in group.iloc[0]:
                        new_row[col] = group.iloc[0][col]
                    else:
                        new_row[col] = None
            
            # 添加到DataFrame
            enhanced_df = pd.concat([enhanced_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # 检查是否有结束语
        has_closing = False
        for idx, row in group.iloc[::-1].iterrows():  # 从后往前检查
            if row['sender_type'] == 2 and any(word in str(row['send_content']) for word in ['感谢', '祝您', '再见']):
                has_closing = True
                break
        
        # 如果没有结束语，添加新的结束语消息，而不是混入现有消息
        if not has_closing and len(group) > 0:
            # 创建新的结束语消息
            last_msg_time = group.iloc[-1]['send_time']
            # 创建一个稍晚的时间
            closing_time = last_msg_time + pd.Timedelta(seconds=1)
            
            # 创建新行
            new_row = pd.Series({
                'touch_id': touch_id,
                'seq_no': group.iloc[-1]['seq_no'] + 0.1,  # 确保排在最后
                'sender_type': 2,  # 客服
                'send_content': "感谢您的咨询，祝您生活愉快！",
                'clean_content': "感谢您的咨询，祝您生活愉快！",
                'send_time': closing_time
            })
            
            # 添加其他必要的列
            for col in enhanced_df.columns:
                if col not in new_row.index:
                    if col in group.iloc[-1]:
                        new_row[col] = group.iloc[-1][col]
                    else:
                        new_row[col] = None
            
            # 添加到DataFrame
            enhanced_df = pd.concat([enhanced_df, pd.DataFrame([new_row])], ignore_index=True)
    
    return enhanced_df.sort_values(['touch_id', 'seq_no']).reset_index(drop=True)

def filter_low_quality_dialogs(dialogs, min_user_messages=2, min_content_length=5, min_dialog_quality_score=0.6):
    """
    过滤低质量对话，提高数据质量
    
    参数:
    - dialogs: 对话列表
    - min_user_messages: 最少用户消息数量
    - min_content_length: 最小有效内容长度
    - min_dialog_quality_score: 最小对话质量分数
    
    返回:
    - 过滤后的高质量对话列表
    """
    print(f"开始过滤低质量对话，原始对话数: {len(dialogs)}")
    filtered_dialogs = []
    filter_reasons = {
        "too_few_user_messages": 0,
        "no_substantial_content": 0,
        "no_business_context": 0,
        "low_quality_score": 0
    }
    
    for dialog in dialogs:
        # 1. 过滤用户消息过少的对话
        user_messages = [msg for msg in dialog["messages"] if msg["sender_type"] == 1]
        if len(user_messages) < min_user_messages:
            filter_reasons["too_few_user_messages"] += 1
            continue
            
        # 2. 过滤无实质内容的对话
        has_substantial_content = False
        for msg in user_messages:
            # 排除纯表情、纯标点符号、过短消息
            if len(msg["content"]) > min_content_length and not is_only_emoji_or_punctuation(msg["content"]):
                has_substantial_content = True
                break
        
        if not has_substantial_content:
            filter_reasons["no_substantial_content"] += 1
            continue
            
        # 3. 过滤无明确业务场景的对话
        if not has_business_context(dialog):
            filter_reasons["no_business_context"] += 1
            continue
            
        # 4. 计算对话质量分数
        quality_score = calculate_dialog_quality_score(dialog)
        if quality_score < min_dialog_quality_score:
            filter_reasons["low_quality_score"] += 1
            continue
            
        filtered_dialogs.append(dialog)
    
    # 打印过滤统计信息
    print(f"过滤完成，剩余对话数: {len(filtered_dialogs)}")
    print(f"过滤原因统计:")
    for reason, count in filter_reasons.items():
        print(f"  - {reason}: {count}")
    
    return filtered_dialogs

def is_only_emoji_or_punctuation(text):
    """
    判断文本是否只包含表情符号或标点符号
    
    参数:
    - text: 待检查的文本
    
    返回:
    - 是否只包含表情或标点
    """
    import re
    # 移除所有表情符号和标点符号
    text_without_emoji = remove_emojis(text)
    text_without_punctuation = re.sub(r'[^\w\s]', '', text_without_emoji)
    # 如果移除后为空，则原文本只包含表情或标点
    return len(text_without_punctuation.strip()) == 0

def remove_emojis(text):
    """
    移除文本中的表情符号
    
    参数:
    - text: 待处理的文本
    
    返回:
    - 移除表情符号后的文本
    """
    import re
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # 表情符号
                               u"\U0001F300-\U0001F5FF"  # 符号和象形文字
                               u"\U0001F680-\U0001F6FF"  # 交通和地图符号
                               u"\U0001F700-\U0001F77F"  # 警告符号
                               u"\U0001F780-\U0001F7FF"  # 几何形状
                               u"\U0001F800-\U0001F8FF"  # 补充箭头
                               u"\U0001F900-\U0001F9FF"  # 补充符号和象形文字
                               u"\U0001FA00-\U0001FA6F"  # 扩展符号和象形文字
                               u"\U0001FA70-\U0001FAFF"  # 符号和象形文字扩展-A
                               u"\U00002702-\U000027B0"  # 装饰符号
                               u"\U000024C2-\U0001F251" 
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def has_business_context(dialog):
    """
    判断对话是否包含业务上下文
    
    参数:
    - dialog: 对话数据
    
    返回:
    - 是否包含业务上下文
    """
    # 业务关键词列表
    business_keywords = [
        "订单", "物流", "快递", "发货", "收货", "退款", "价格", 
        "估价", "检测", "回收", "维修", "换新", "保修", "质量", 
        "售后", "支付", "付款", "取消", "修改", "投诉", "建议",
        "手机", "平板", "电脑", "笔记本", "相机", "耳机", "手表"
    ]
    
    # 检查对话中是否包含业务关键词
    for msg in dialog["messages"]:
        for keyword in business_keywords:
            if keyword in msg["content"]:
                return True
    
    # 检查对话元数据中是否包含业务信息
    if "metadata" in dialog:
        metadata_str = str(dialog["metadata"])
        for keyword in business_keywords:
            if keyword in metadata_str:
                return True
    
    return False

def calculate_dialog_quality_score(dialog):
    """
    计算对话质量分数
    
    参数:
    - dialog: 对话数据
    
    返回:
    - 质量分数 (0-1)
    """
    score = 0.0
    max_score = 5.0
    
    # 1. 对话长度得分 (最高1分)
    messages_count = len(dialog["messages"])
    if messages_count >= 10:
        score += 1.0
    elif messages_count >= 5:
        score += 0.5
    else:
        score += 0.2
    
    # 2. 用户参与度得分 (最高1分)
    user_messages = [msg for msg in dialog["messages"] if msg["sender_type"] == 1]
    user_participation = len(user_messages) / max(1, messages_count)
    score += min(1.0, user_participation * 2)
    
    # 3. 内容丰富度得分 (最高1分)
    total_content_length = sum(len(msg["content"]) for msg in dialog["messages"])
    avg_content_length = total_content_length / max(1, messages_count)
    if avg_content_length >= 15:
        score += 1.0
    elif avg_content_length >= 8:
        score += 0.5
    else:
        score += 0.2
    
    # 4. 业务相关度得分 (最高1分)
    business_relevance = calculate_business_relevance(dialog)
    score += business_relevance
    
    # 5. 对话完整性得分 (最高1分)
    has_greeting = any("您好" in msg["content"] or "你好" in msg["content"] for msg in dialog["messages"] if msg["sender_type"] == 2)
    has_closing = any("感谢" in msg["content"] or "谢谢" in msg["content"] or "再见" in msg["content"] for msg in dialog["messages"] if msg["sender_type"] == 2)
    
    if has_greeting and has_closing:
        score += 1.0
    elif has_greeting or has_closing:
        score += 0.5
    
    # 归一化分数到0-1范围
    normalized_score = score / max_score
    
    return normalized_score

def calculate_business_relevance(dialog):
    """
    计算对话的业务相关度
    
    参数:
    - dialog: 对话数据
    
    返回:
    - 业务相关度分数 (0-1)
    """
    # 业务关键词权重
    business_keywords = {
        "订单": 0.8, "物流": 0.7, "快递": 0.6, "发货": 0.7, "收货": 0.7, 
        "退款": 0.8, "价格": 0.6, "估价": 0.7, "检测": 0.7, "回收": 0.8, 
        "维修": 0.6, "换新": 0.6, "保修": 0.5, "质量": 0.5, "售后": 0.7, 
        "支付": 0.6, "付款": 0.6, "取消": 0.6, "修改": 0.5, "投诉": 0.7, 
        "建议": 0.4, "手机": 0.5, "平板": 0.5, "电脑": 0.5, "笔记本": 0.5, 
        "相机": 0.5, "耳机": 0.4, "手表": 0.4
    }
    
    # 计算业务关键词出现次数
    keyword_count = 0
    total_weight = 0
    
    for msg in dialog["messages"]:
        for keyword, weight in business_keywords.items():
            if keyword in msg["content"]:
                keyword_count += 1
                total_weight += weight
    
    # 计算业务相关度分数
    if keyword_count == 0:
        return 0.0
    
    # 归一化分数，最高1分
    relevance_score = min(1.0, total_weight / 5.0)
    
    return relevance_score

def enhanced_content_cleaning(content):
    """
    增强版消息内容清洗
    
    参数:
    - content: 原始消息内容
    
    返回:
    - 清洗后的内容
    """
    if not content or pd.isna(content):
        return ""
        
    # 1. 提取并保留关键业务信息
    preserved_info = extract_business_info(content)
    
    # 2. 移除无关信息
    cleaned_content = remove_system_prompts(content)
    cleaned_content = remove_format_marks(cleaned_content)
    
    # 3. 标准化处理
    cleaned_content = standardize_punctuation(cleaned_content)
    cleaned_content = standardize_expressions(cleaned_content)
    
    # 4. 恢复关键业务信息
    final_content = restore_business_info(cleaned_content, preserved_info)
    
    return final_content

def extract_business_info(content):
    """
    提取消息中的关键业务信息
    
    参数:
    - content: 原始消息内容
    
    返回:
    - 提取的业务信息字典
    """
    import re
    
    business_info = {
        "order_ids": [],
        "logistics_ids": [],
        "phone_numbers": [],
        "product_info": [],
        "price_info": []
    }
    
    # 1. 提取订单号 (通常为18位数字)
    order_pattern = r'\b\d{18}\b'
    order_matches = re.findall(order_pattern, content)
    business_info["order_ids"] = order_matches
    
    # 2. 提取物流单号 (通常为10-15位数字字母组合)
    logistics_pattern = r'\b[A-Za-z0-9]{10,15}\b'
    logistics_matches = re.findall(logistics_pattern, content)
    # 过滤掉订单号，避免重复
    logistics_matches = [m for m in logistics_matches if m not in order_matches]
    business_info["logistics_ids"] = logistics_matches
    
    # 3. 提取手机号 (11位数字，通常以1开头)
    phone_pattern = r'\b1[3-9]\d{9}\b'
    phone_matches = re.findall(phone_pattern, content)
    business_info["phone_numbers"] = phone_matches
    
    # 4. 提取产品信息 (包含型号的文本片段)
    product_patterns = [
        r'(iPhone\s*\d+\s*[A-Za-z]*\s*[\d]*\s*[A-Za-z]*)',
        r'(华为|荣耀|小米|OPPO|vivo|三星|魅族|一加)[\s\S]{0,10}?[\w\d]+',
        r'(\d+GB|\d+TB|\d+寸|\d+英寸)'
    ]
    
    for pattern in product_patterns:
        matches = re.findall(pattern, content)
        if matches:
            business_info["product_info"].extend(matches)
    
    # 5. 提取价格信息
    price_pattern = r'(\d+(?:\.\d+)?元|\d+(?:\.\d+)?块钱|\d+(?:\.\d+)?[元块]|\¥\s*\d+(?:\.\d+)?)'
    price_matches = re.findall(price_pattern, content)
    business_info["price_info"] = price_matches
    
    return business_info

def remove_system_prompts(content):
    """
    移除系统提示信息
    
    参数:
    - content: 消息内容
    
    返回:
    - 移除系统提示后的内容
    """
    import re
    
    # 常见的系统提示模式
    system_patterns = [
        r'\[系统提示\].*?\[\/系统提示\]',
        r'\[系统消息\].*?\[\/系统消息\]',
        r'\[自动回复\].*?\[\/自动回复\]',
        r'\[自动消息\].*?\[\/自动消息\]',
        r'【系统提示】.*?【\/系统提示】',
        r'【系统消息】.*?【\/系统消息】',
        r'【自动回复】.*?【\/自动回复】',
        r'【自动消息】.*?【\/自动消息】'
    ]
    
    # 移除系统提示
    cleaned_content = content
    for pattern in system_patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)
    
    return cleaned_content.strip()

def remove_format_marks(content):
    """
    移除格式标记
    
    参数:
    - content: 消息内容
    
    返回:
    - 移除格式标记后的内容
    """
    import re
    
    # 常见的格式标记
    format_patterns = [
        r'\*\*.*?\*\*',  # Markdown加粗
        r'\*.*?\*',      # Markdown斜体
        r'\~\~.*?\~\~',  # Markdown删除线
        r'\`.*?\`',      # Markdown代码
        r'\<.*?\>',      # HTML标签
        r'\[.*?\]\(.*?\)'  # Markdown链接
    ]
    
    # 移除格式标记，但保留内容
    cleaned_content = content
    for pattern in format_patterns:
        # 提取内容并替换标记
        matches = re.findall(pattern, cleaned_content)
        for match in matches:
            # 提取标记内的实际内容
            inner_content = re.sub(r'[\*\~\`\<\>\[\]\(\)]', '', match)
            cleaned_content = cleaned_content.replace(match, inner_content)
    
    return cleaned_content.strip()

def standardize_punctuation(content):
    """
    标准化标点符号
    
    参数:
    - content: 消息内容
    
    返回:
    - 标准化标点后的内容
    """
    import re
    
    # 1. 统一中英文标点
    punctuation_map = {
        '，': ',',
        '。': '.',
        '！': '!',
        '？': '?',
        '；': ';',
        '：': ':',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '（': '(',
        '）': ')',
        '【': '[',
        '】': ']',
        '《': '<',
        '》': '>',
        '—': '-'
    }
    
    standardized_content = content
    for ch_punct, en_punct in punctuation_map.items():
        standardized_content = standardized_content.replace(ch_punct, en_punct)
    
    # 2. 处理重复标点
    standardized_content = re.sub(r'\.{2,}', '...', standardized_content)  # 将多个点替换为省略号
    standardized_content = re.sub(r'([!?])\1+', r'\1', standardized_content)  # 减少重复的感叹号和问号
    
    # 3. 确保标点后有空格
    standardized_content = re.sub(r'([.,!?;:])([\u4e00-\u9fa5a-zA-Z0-9])', r'\1 \2', standardized_content)
    
    return standardized_content.strip()

def standardize_expressions(content):
    """
    标准化表达方式
    
    参数:
    - content: 消息内容
    
    返回:
    - 标准化表达后的内容
    """
    # 1. 标准化常见缩写和网络用语
    expression_map = {
        r'\b回收宝\b': '回收宝',
        r'\bhsb\b': '回收宝',
        r'\b咨询\b': '咨询',
        r'\b订单\b': '订单',
        r'\b物流\b': '物流',
        r'\b快递\b': '快递',
        r'\b发货\b': '发货',
        r'\b收货\b': '收货',
        r'\b退款\b': '退款',
        r'\b价格\b': '价格',
        r'\b估价\b': '估价',
        r'\b检测\b': '检测',
        r'\b回收\b': '回收',
        r'\b维修\b': '维修',
        r'\b换新\b': '换新',
        r'\b保修\b': '保修',
        r'\b质量\b': '质量',
        r'\b售后\b': '售后',
        r'\b支付\b': '支付',
        r'\b付款\b': '付款',
        r'\b取消\b': '取消',
        r'\b修改\b': '修改',
        r'\b投诉\b': '投诉',
        r'\b建议\b': '建议'
    }
    
    standardized_content = content
    for pattern, replacement in expression_map.items():
        standardized_content = re.sub(pattern, replacement, standardized_content, flags=re.IGNORECASE)
    
    return standardized_content.strip()

def restore_business_info(content, business_info):
    """
    恢复关键业务信息
    
    参数:
    - content: 清洗后的内容
    - business_info: 提取的业务信息
    
    返回:
    - 恢复业务信息后的内容
    """
    # 检查是否有需要恢复的业务信息
    has_business_info = False
    for key, value in business_info.items():
        if value:
            has_business_info = True
            break
    
    if not has_business_info:
        return content
    
    # 恢复业务信息
    restored_content = content
    
    # 检查业务信息是否已经存在于内容中
    for key, values in business_info.items():
        for value in values:
            # 如果业务信息已经存在于内容中，则不需要恢复
            if value in restored_content:
                continue
                
            # 根据业务信息类型，选择合适的恢复方式
            if key == "order_ids" and values:
                # 恢复订单号
                if "订单" in restored_content and "订单号" not in restored_content:
                    restored_content = restored_content.replace("订单", f"订单号{value} ")
                else:
                    restored_content += f" (订单号: {value})"
                    
            elif key == "logistics_ids" and values:
                # 恢复物流单号
                if "物流" in restored_content and "物流单号" not in restored_content:
                    restored_content = restored_content.replace("物流", f"物流单号{value} ")
                elif "快递" in restored_content and "快递单号" not in restored_content:
                    restored_content = restored_content.replace("快递", f"快递单号{value} ")
                else:
                    restored_content += f" (物流单号: {value})"
                    
            elif key == "product_info" and values:
                # 恢复产品信息
                if "手机" in restored_content and not any(v in restored_content for v in values):
                    restored_content = restored_content.replace("手机", f"{values[0]} ")
                else:
                    restored_content += f" (产品: {values[0]})"
                    
            elif key == "price_info" and values:
                # 恢复价格信息
                if "价格" in restored_content and not any(v in restored_content for v in values):
                    restored_content = restored_content.replace("价格", f"价格{values[0]} ")
                elif "多少钱" in restored_content and not any(v in restored_content for v in values):
                    restored_content = restored_content.replace("多少钱", f"{values[0]} ")
                else:
                    restored_content += f" (价格: {values[0]})"
    
    return restored_content.strip()

def preprocess_data(file_path, output_dir=None, filter_quality=True):
    """
    数据预处理主函数
    
    参数:
    - file_path: 原始数据文件路径
    - output_dir: 输出目录
    - filter_quality: 是否过滤低质量对话
    
    返回:
    - 预处理后的对话列表
    """
    print(f"开始预处理数据: {file_path}")
    
    # 1. 读取原始数据
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("不支持的文件格式，请提供.xlsx或.csv文件")
    
    # 打印原始列名，帮助理解数据结构
    print(f"原始数据列名: {df.columns.tolist()}")
    print(f"原始数据形状: {df.shape}")
    
    # 2. 数据清洗
    print("开始数据清洗...")
    df = clean_data(df)
    print(f"数据清洗后形状: {df.shape}")
    
    # 3. 识别发送者类型
    print("识别发送者类型...")
    df = identify_sender_type(df)
    
    # 4. 提取结构化信息
    print("提取结构化信息...")
    df = extract_structured_info(df)
    
    # 5. 增强对话结构
    print("增强对话结构...")
    df = enhance_dialog_structure(df)
    
    # 6. 组织对话
    print("组织对话...")
    dialogs = organize_dialogs(df)
    print(f"组织后的对话数量: {len(dialogs)}")
    
    # 7. 过滤低质量对话
    if filter_quality:
        print("过滤低质量对话...")
        dialogs = filter_low_quality_dialogs(dialogs)
    
    # 8. 增强消息内容清洗
    print("增强消息内容清洗...")
    for dialog in dialogs:
        for msg in dialog["messages"]:
            msg["enhanced_content"] = enhanced_content_cleaning(msg["content"])
    
    # 9. 保存预处理后的数据
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "preprocessed_dialogs.json")
        
        # 确保JSON序列化安全
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.integer, np.floating, np.bool_)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NumpyEncoder, self).default(obj)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dialogs, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        print(f"预处理数据已保存至: {output_file}")
    
    print("数据预处理完成!")
    return dialogs

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 数据预处理增强")
    print("=" * 50)
    
    # 1. 加载数据
    df = load_data(DATA_FILE)
    
    # 2. 数据预处理（包含多个步骤）
    dialogs = preprocess_data(df, output_dir=OUTPUT_DIR)
    
    print("=" * 50)
    print("数据预处理增强完成！")
    print("=" * 50)
    
    return dialogs

if __name__ == "__main__":
    main()

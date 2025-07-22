#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据探索脚本
功能：深入分析客服对话数据，生成数据质量报告
用法：python explore_data.py --source <excel_file_path> --output <report_dir> --sample 10000
"""

import argparse
import json
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='深入分析客服对话数据，生成数据质量报告')
    parser.add_argument('--source', required=True, help='源Excel文件路径')
    parser.add_argument('--output', required=True, help='输出报告目录')
    parser.add_argument('--sample', type=int, default=10000, help='样本数量')
    return parser.parse_args()


def load_data(file_path, sample_size=10000):
    """
    加载Excel数据
    
    参数:
        file_path: Excel文件路径
        sample_size: 样本数量
    
    返回:
        DataFrame: 加载的数据
    """
    print(f"正在加载数据: {file_path}")
    print(f"样本大小: {sample_size}")
    
    try:
        df = pd.read_excel(file_path, nrows=sample_size)
        print(f"成功加载 {len(df)} 行数据")
        return df
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None


def analyze_data_structure(df):
    """
    分析数据结构
    
    参数:
        df: DataFrame
    
    返回:
        dict: 数据结构分析结果
    """
    print("正在分析数据结构...")
    
    # 基本信息
    basic_info = {
        "行数": len(df),
        "列数": len(df.columns),
        "列名": df.columns.tolist(),
        "数据类型": {col: str(df[col].dtype) for col in df.columns}
    }
    
    # 缺失值分析
    missing_values = {
        "总缺失值": df.isnull().sum().sum(),
        "缺失值比例": df.isnull().sum().sum() / (df.shape[0] * df.shape[1]),
        "每列缺失值": df.isnull().sum().to_dict(),
        "每列缺失比例": (df.isnull().sum() / len(df)).to_dict()
    }
    
    # 唯一值分析
    unique_values = {
        "每列唯一值数量": {col: df[col].nunique() for col in df.columns},
        "每列唯一值比例": {col: df[col].nunique() / len(df) for col in df.columns}
    }
    
    return {
        "基本信息": basic_info,
        "缺失值分析": missing_values,
        "唯一值分析": unique_values
    }


def analyze_conversations(df):
    """
    分析对话特征
    
    参数:
        df: DataFrame
    
    返回:
        dict: 对话分析结果
    """
    print("正在分析对话特征...")
    
    # 对话数量
    conversation_count = df['touch_id'].nunique()
    
    # 每个对话的消息数量
    messages_per_conversation = df.groupby('touch_id').size()
    
    # 对话时长
    df['user_start_time'] = pd.to_datetime(df['user_start_time'], errors='coerce')
    df['user_end_time'] = pd.to_datetime(df['user_end_time'], errors='coerce')
    df['duration'] = (df['user_end_time'] - df['user_start_time']).dt.total_seconds() / 60
    
    # 发送者类型分布
    sender_distribution = df['sender_type'].value_counts().to_dict()
    
    # 业务分组分布
    business_distribution = df['group_name'].value_counts().to_dict()
    
    # 消息长度分析
    df['message_length'] = df['send_content'].astype(str).apply(len)
    
    return {
        "对话数量": conversation_count,
        "每对话消息数": {
            "平均值": messages_per_conversation.mean(),
            "中位数": messages_per_conversation.median(),
            "最小值": messages_per_conversation.min(),
            "最大值": messages_per_conversation.max(),
            "分布": messages_per_conversation.value_counts().to_dict()
        },
        "对话时长(分钟)": {
            "平均值": df['duration'].mean(),
            "中位数": df['duration'].median(),
            "最小值": df['duration'].min(),
            "最大值": df['duration'].max()
        },
        "发送者分布": sender_distribution,
        "业务分组": {k: v for k, v in sorted(business_distribution.items(), key=lambda item: item[1], reverse=True)},
        "消息长度": {
            "平均值": df['message_length'].mean(),
            "中位数": df['message_length'].median(),
            "最小值": df['message_length'].min(),
            "最大值": df['message_length'].max()
        }
    }


def analyze_message_content(df):
    """
    分析消息内容
    
    参数:
        df: DataFrame
    
    返回:
        dict: 内容分析结果
    """
    print("正在分析消息内容...")
    
    # 提取用户消息和客服消息
    user_messages = df[df['sender_type'] == 1.0]['send_content'].astype(str).tolist()
    service_messages = df[df['sender_type'] == 2.0]['send_content'].astype(str).tolist()
    
    # 分析用户问题类型
    question_patterns = {
        "订单查询": r'订单|查询|查看|进度|状态',
        "物流配送": r'物流|快递|发货|收货|邮寄|包裹|几天|什么时候到',
        "价格咨询": r'价格|多少钱|报价|估价|回收价|值多少',
        "回收流程": r'流程|步骤|怎么操作|如何|教程|怎么回收|怎么卖',
        "验货检测": r'检测|验机|验货|检查|成色|评估',
        "支付结算": r'支付|付款|打款|到账|微信|支付宝|银行卡',
        "账号问题": r'账号|登录|注册|密码|绑定',
        "售后服务": r'售后|退款|维修|换货|保修|投诉',
        "产品咨询": r'型号|配置|参数|规格|功能|版本'
    }
    
    question_types = {}
    for qtype, pattern in question_patterns.items():
        count = sum(1 for msg in user_messages if re.search(pattern, msg))
        question_types[qtype] = count
    
    # 分析消息情感特征
    sentiment_patterns = {
        "问候语": r'您好|你好|早上好|下午好|晚上好|欢迎',
        "感谢语": r'谢谢|感谢|多谢|非常感谢|辛苦了',
        "道歉语": r'抱歉|对不起|不好意思|很遗憾',
        "催促语": r'快点|赶紧|尽快|马上|立即|急',
        "不满语": r'不行|不可以|不满意|不好|差|垃圾|退款',
        "满意语": r'满意|好的|可以|不错|棒|优秀|好评'
    }
    
    user_sentiment = {}
    for stype, pattern in sentiment_patterns.items():
        count = sum(1 for msg in user_messages if re.search(pattern, msg))
        user_sentiment[stype] = count
    
    service_sentiment = {}
    for stype, pattern in sentiment_patterns.items():
        count = sum(1 for msg in service_messages if re.search(pattern, msg))
        service_sentiment[stype] = count
    
    # 提取一些典型的用户问题和客服回答示例
    user_question_examples = []
    for msg in user_messages:
        if len(msg) > 10 and len(msg) < 100 and ('?' in msg or '？' in msg):
            user_question_examples.append(msg)
            if len(user_question_examples) >= 20:
                break
    
    service_answer_examples = []
    for msg in service_messages:
        if len(msg) > 20 and len(msg) < 200:
            service_answer_examples.append(msg)
            if len(service_answer_examples) >= 20:
                break
    
    return {
        "用户问题类型": question_types,
        "用户情感特征": user_sentiment,
        "客服情感特征": service_sentiment,
        "用户问题示例": user_question_examples,
        "客服回答示例": service_answer_examples
    }


def analyze_data_quality(df):
    """
    分析数据质量
    
    参数:
        df: DataFrame
    
    返回:
        dict: 数据质量分析结果
    """
    print("正在分析数据质量...")
    
    # 检查重复行
    duplicate_rows = df.duplicated().sum()
    
    # 检查异常值
    # 这里简单定义异常值为消息长度为0或超长的消息
    df['message_length'] = df['send_content'].astype(str).apply(len)
    zero_length_messages = (df['message_length'] == 0).sum()
    very_long_messages = (df['message_length'] > 500).sum()
    
    # 检查时间异常
    df['user_start_time'] = pd.to_datetime(df['user_start_time'], errors='coerce')
    df['user_end_time'] = pd.to_datetime(df['user_end_time'], errors='coerce')
    df['send_time'] = pd.to_datetime(df['send_time'], errors='coerce')
    
    invalid_start_time = df['user_start_time'].isnull().sum()
    invalid_end_time = df['user_end_time'].isnull().sum()
    invalid_send_time = df['send_time'].isnull().sum()
    
    # 检查时间顺序异常
    time_order_issues = 0
    for touch_id, group in df.groupby('touch_id'):
        if len(group) > 1:
            sorted_times = group['send_time'].sort_values()
            if not sorted_times.equals(group['send_time']):
                time_order_issues += 1
    
    # 检查消息序号异常
    seq_issues = 0
    for touch_id, group in df.groupby('touch_id'):
        if len(group) > 1:
            seq_nums = group['seq_no'].sort_values()
            expected_seq = pd.Series(range(1, len(group) + 1))
            if not seq_nums.equals(expected_seq):
                seq_issues += 1
    
    return {
        "重复行数": duplicate_rows,
        "空消息数": zero_length_messages,
        "超长消息数": very_long_messages,
        "无效开始时间": invalid_start_time,
        "无效结束时间": invalid_end_time,
        "无效发送时间": invalid_send_time,
        "时间顺序异常对话数": time_order_issues,
        "消息序号异常对话数": seq_issues
    }


def generate_report(results, output_dir):
    """
    生成分析报告
    
    参数:
        results: 分析结果
        output_dir: 输出目录
    """
    print("正在生成分析报告...")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON结果
    with open(os.path.join(output_dir, 'data_exploration_results.json'), 'w', encoding='utf-8') as f:
        # 将NumPy类型转换为Python原生类型
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            else:
                return obj
        
        serializable_results = convert_to_serializable(results)
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    report = f"""# 客服对话数据探索报告

## 1. 数据概览

### 1.1 基本信息
- 样本大小: {results['数据结构']['基本信息']['行数']} 行
- 列数: {results['数据结构']['基本信息']['列数']} 列
- 唯一对话数: {results['对话特征']['对话数量']}

### 1.2 数据质量概况
- 缺失值比例: {results['数据结构']['缺失值分析']['缺失值比例']:.2%}
- 重复行数: {results['数据质量']['重复行数']}
- 数据异常情况: 
  - 空消息数: {results['数据质量']['空消息数']}
  - 超长消息数: {results['数据质量']['超长消息数']}
  - 时间顺序异常对话数: {results['数据质量']['时间顺序异常对话数']}

## 2. 对话特征分析

### 2.1 对话基本特征
- 平均每对话消息数: {results['对话特征']['每对话消息数']['平均值']:.2f}
- 中位数对话消息数: {results['对话特征']['每对话消息数']['中位数']}
- 平均对话时长: {results['对话特征']['对话时长(分钟)']['平均值']:.2f} 分钟

### 2.2 发送者分布
"""
    
    # 添加发送者分布
    for sender, count in results['对话特征']['发送者分布'].items():
        percentage = count / results['数据结构']['基本信息']['行数'] * 100
        report += f"- 发送者类型 {sender}: {count} ({percentage:.2f}%)\n"
    
    report += """
### 2.3 业务分组分布
"""
    
    # 添加业务分组分布（前10个）
    for i, (group, count) in enumerate(results['对话特征']['业务分组'].items()):
        if i >= 10:
            break
        percentage = count / results['数据结构']['基本信息']['行数'] * 100
        report += f"- {group}: {count} ({percentage:.2f}%)\n"
    
    report += """
## 3. 内容分析

### 3.1 用户问题类型分布
"""
    
    # 添加用户问题类型分布
    total_questions = sum(results['内容分析']['用户问题类型'].values())
    for qtype, count in sorted(results['内容分析']['用户问题类型'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / total_questions * 100 if total_questions > 0 else 0
        report += f"- {qtype}: {count} ({percentage:.2f}%)\n"
    
    report += """
### 3.2 情感特征分析

#### 用户情感特征
"""
    
    # 添加用户情感特征
    for stype, count in sorted(results['内容分析']['用户情感特征'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {stype}: {count}\n"
    
    report += """
#### 客服情感特征
"""
    
    # 添加客服情感特征
    for stype, count in sorted(results['内容分析']['客服情感特征'].items(), key=lambda x: x[1], reverse=True):
        report += f"- {stype}: {count}\n"
    
    report += """
### 3.3 用户问题示例
"""
    
    # 添加用户问题示例
    for i, example in enumerate(results['内容分析']['用户问题示例'][:10]):
        report += f"{i+1}. {example}\n"
    
    report += """
### 3.4 客服回答示例
"""
    
    # 添加客服回答示例
    for i, example in enumerate(results['内容分析']['客服回答示例'][:10]):
        report += f"{i+1}. {example}\n"
    
    report += """
## 4. 数据质量问题

### 4.1 缺失值问题
"""
    
    # 添加缺失值问题
    for col, missing in sorted(results['数据结构']['缺失值分析']['每列缺失值'].items(), key=lambda x: x[1], reverse=True):
        if missing > 0:
            percentage = missing / results['数据结构']['基本信息']['行数'] * 100
            report += f"- {col}: {missing} ({percentage:.2f}%)\n"
    
    report += """
### 4.2 时间异常问题
- 无效开始时间: {0}
- 无效结束时间: {1}
- 无效发送时间: {2}

## 5. 数据清洗建议

基于以上分析，建议采取以下数据清洗策略：

1. **处理缺失值**：
   - 对于关键字段（如touch_id, send_content等）的缺失值，考虑删除相应记录
   - 对于非关键字段的缺失值，可以根据具体情况选择填充或忽略

2. **处理重复数据**：
   - 识别并删除完全重复的记录
   - 对于部分重复（如同一对话中内容重复的消息），需要进一步分析和处理

3. **处理异常值**：
   - 删除或修正空消息
   - 检查并处理超长消息
   - 修正时间顺序异常的对话

4. **文本清洗**：
   - 去除HTML标签和特殊字符
   - 标准化文本格式（如空格、标点等）
   - 对敏感信息进行脱敏处理

5. **结构化处理**：
   - 按对话ID组织数据
   - 确保消息按时间顺序排列
   - 标准化发送者类型

## 6. 意图分析建议

基于内容分析，建议采取以下意图分析策略：

1. **分类体系构建**：
   - 采用两级分类体系，主分类包括订单查询、物流配送、价格咨询等
   - 每个主分类下设置2-3个子分类，细化问题类型

2. **意图识别方法**：
   - 对于高频明确的意图，使用关键词和规则匹配
   - 对于模糊或复杂的意图，使用语义相似度计算
   - 考虑上下文信息，提高意图识别准确性

3. **知识提取重点**：
   - 重点关注高频问题类型（如{3}、{4}、{5}）
   - 提取标准问题表述和变体
   - 识别典型的客服回答模式

4. **多轮对话处理**：
   - 识别需要多轮交互的复杂问题
   - 分析问题解决路径和转人工触发点
   - 设计多轮对话流程模板

## 7. 结论与建议

基于本次数据探索，我们对客服对话数据有了初步了解。数据质量总体{6}，但存在一些需要处理的问题。用户问题主要集中在{7}等方面，这些应作为知识库构建的重点。

建议采取分阶段的数据处理和意图分析策略，先处理数据质量问题，再进行基础意图识别，最后才是复杂的语义分析和知识提取。同时，应该保持人机协作的分析模式，确保自动提取的结果符合业务需求。
""".format(
        results['数据质量']['无效开始时间'],
        results['数据质量']['无效结束时间'],
        results['数据质量']['无效发送时间'],
        list(dict(sorted(results['内容分析']['用户问题类型'].items(), key=lambda x: x[1], reverse=True)[:3]).keys())[0],
        list(dict(sorted(results['内容分析']['用户问题类型'].items(), key=lambda x: x[1], reverse=True)[:3]).keys())[1],
        list(dict(sorted(results['内容分析']['用户问题类型'].items(), key=lambda x: x[1], reverse=True)[:3]).keys())[2],
        "良好" if results['数据结构']['缺失值分析']['缺失值比例'] < 0.1 else "一般",
        "、".join(list(dict(sorted(results['内容分析']['用户问题类型'].items(), key=lambda x: x[1], reverse=True)[:3]).keys()))
    )
    
    # 保存Markdown报告
    with open(os.path.join(output_dir, 'data_exploration_report.md'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"报告已保存到: {output_dir}")


def explore_data(file_path, output_dir, sample_size=10000):
    """
    探索数据
    
    参数:
        file_path: Excel文件路径
        output_dir: 输出目录路径
        sample_size: 样本数量
    
    返回:
        bool: 是否成功
    """
    try:
        # 加载数据
        df = load_data(file_path, sample_size)
        if df is None:
            return False
        
        # 分析数据结构
        structure_results = analyze_data_structure(df)
        
        # 分析对话特征
        conversation_results = analyze_conversations(df)
        
        # 分析消息内容
        content_results = analyze_message_content(df)
        
        # 分析数据质量
        quality_results = analyze_data_quality(df)
        
        # 整合结果
        results = {
            "数据结构": structure_results,
            "对话特征": conversation_results,
            "内容分析": content_results,
            "数据质量": quality_results
        }
        
        # 生成报告
        generate_report(results, output_dir)
        
        return True
    
    except Exception as e:
        print(f"数据探索过程中出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查源文件是否存在
    if not os.path.exists(args.source):
        print(f"错误: 源文件不存在: {args.source}")
        return
    
    # 执行数据探索
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    success = explore_data(args.source, args.output, args.sample)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据探索成功！")
    else:
        print("数据探索失败！")


if __name__ == "__main__":
    main()

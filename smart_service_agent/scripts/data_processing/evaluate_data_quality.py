#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据质量评估脚本
功能：对清洗后的客服对话数据进行质量评估
用法：python evaluate_data_quality.py --input <cleaned_json_path> --output <report_path> [--sample <sample_size>]
"""

import argparse
import json
import os
import random
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='对清洗后的客服对话数据进行质量评估')
    parser.add_argument('--input', required=True, help='输入清洗后的JSON文件路径')
    parser.add_argument('--output', required=True, help='质量评估报告输出路径')
    parser.add_argument('--sample', type=int, default=100, help='抽样检查的对话数量，默认100')
    parser.add_argument('--visualize', action='store_true', help='是否生成可视化图表')
    return parser.parse_args()


def load_data(input_path):
    """加载清洗后的数据"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None


def check_completeness(conversations):
    """
    检查数据完整性
    
    参数:
        conversations: 对话数据列表
    
    返回:
        dict: 完整性检查结果
    """
    total_conversations = len(conversations)
    total_messages = sum(len(conv.get('messages', [])) for conv in conversations)
    
    # 检查必要字段
    required_conversation_fields = ['touch_id', 'user_name', 'servicer_name', 'start_time', 'end_time', 'messages']
    required_message_fields = ['seq_no', 'send_time', 'sender_type', 'content']
    
    missing_fields = {field: 0 for field in required_conversation_fields}
    missing_message_fields = {field: 0 for field in required_message_fields}
    
    # 检查对话级别字段
    for conv in conversations:
        for field in required_conversation_fields:
            if field not in conv or conv[field] is None or conv[field] == "":
                missing_fields[field] += 1
    
    # 检查消息级别字段
    for conv in conversations:
        for msg in conv.get('messages', []):
            for field in required_message_fields:
                if field not in msg or msg[field] is None or msg[field] == "":
                    missing_message_fields[field] += 1
    
    # 计算完整性百分比
    conversation_completeness = {field: 100 - (count / total_conversations * 100) for field, count in missing_fields.items()}
    message_completeness = {field: 100 - (count / total_messages * 100) for field, count in missing_message_fields.items()}
    
    return {
        "对话级别完整性": conversation_completeness,
        "消息级别完整性": message_completeness,
        "总体完整性评分": (sum(conversation_completeness.values()) / len(conversation_completeness) + 
                     sum(message_completeness.values()) / len(message_completeness)) / 2
    }


def check_consistency(conversations):
    """
    检查数据一致性
    
    参数:
        conversations: 对话数据列表
    
    返回:
        dict: 一致性检查结果
    """
    total_conversations = len(conversations)
    
    # 时间顺序一致性
    time_sequence_issues = 0
    # 消息序号一致性
    seq_no_issues = 0
    # 发送者类型一致性
    sender_type_issues = 0
    
    for conv in conversations:
        messages = conv.get('messages', [])
        
        # 检查时间顺序
        if len(messages) >= 2:
            try:
                times = []
                for msg in messages:
                    if 'send_time' in msg and msg['send_time']:
                        times.append(datetime.strptime(msg['send_time'], '%Y-%m-%d %H:%M:%S'))
                
                # 检查是否有时间倒序
                is_sorted = all(times[i] <= times[i+1] for i in range(len(times)-1))
                if not is_sorted:
                    time_sequence_issues += 1
            except:
                # 时间格式异常也算作时间顺序异常
                time_sequence_issues += 1
        
        # 检查消息序号
        if len(messages) >= 2:
            seq_nos = [msg.get('seq_no') for msg in messages if 'seq_no' in msg and msg['seq_no'] is not None]
            if seq_nos:
                # 检查序号是否连续
                is_continuous = all(int(seq_nos[i+1]) - int(seq_nos[i]) == 1 for i in range(len(seq_nos)-1))
                if not is_continuous:
                    seq_no_issues += 1
        
        # 检查发送者类型
        sender_types = [msg.get('sender_type') for msg in messages if 'sender_type' in msg and msg['sender_type'] is not None]
        if sender_types:
            # 检查发送者类型是否合理交替（不应该连续多个相同类型）
            consecutive_same_type = 0
            for i in range(1, len(sender_types)):
                if sender_types[i] == sender_types[i-1]:
                    consecutive_same_type += 1
            
            # 如果连续相同类型超过总消息数的20%，认为可能有问题
            if consecutive_same_type > len(sender_types) * 0.2:
                sender_type_issues += 1
    
    # 计算一致性百分比
    time_consistency = 100 - (time_sequence_issues / total_conversations * 100)
    seq_no_consistency = 100 - (seq_no_issues / total_conversations * 100)
    sender_type_consistency = 100 - (sender_type_issues / total_conversations * 100)
    
    return {
        "时间顺序一致性": time_consistency,
        "消息序号一致性": seq_no_consistency,
        "发送者类型一致性": sender_type_consistency,
        "总体一致性评分": (time_consistency + seq_no_consistency + sender_type_consistency) / 3
    }


def check_text_quality(conversations, sample_size=100):
    """
    检查文本质量
    
    参数:
        conversations: 对话数据列表
        sample_size: 抽样检查的对话数量
    
    返回:
        dict: 文本质量检查结果
    """
    # 随机抽样
    if len(conversations) > sample_size:
        sampled_conversations = random.sample(conversations, sample_size)
    else:
        sampled_conversations = conversations
    
    # 文本质量问题统计
    html_tag_count = 0
    empty_message_count = 0
    too_short_message_count = 0
    too_long_message_count = 0
    sensitive_info_count = 0
    
    total_messages = 0
    
    # 敏感信息模式
    sensitive_patterns = {
        "手机号": r'1[3-9]\d{9}',
        "邮箱": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "身份证号": r'\b\d{17}[\dXx]\b',
        "银行卡号": r'\b\d{16,19}\b'
    }
    
    for conv in sampled_conversations:
        for msg in conv.get('messages', []):
            total_messages += 1
            content = msg.get('content', '')
            
            # 检查HTML标签
            if re.search(r'<[^>]+>', content):
                html_tag_count += 1
            
            # 检查空消息
            if not content:
                empty_message_count += 1
            
            # 检查消息长度
            if len(content) < 2 and content:  # 非空但过短
                too_short_message_count += 1
            elif len(content) > 500:  # 过长
                too_long_message_count += 1
            
            # 检查敏感信息
            for pattern in sensitive_patterns.values():
                if re.search(pattern, content):
                    sensitive_info_count += 1
                    break
    
    # 计算文本质量百分比
    html_free_rate = 100 - (html_tag_count / total_messages * 100)
    non_empty_rate = 100 - (empty_message_count / total_messages * 100)
    proper_length_rate = 100 - ((too_short_message_count + too_long_message_count) / total_messages * 100)
    privacy_protection_rate = 100 - (sensitive_info_count / total_messages * 100)
    
    return {
        "HTML标签清理率": html_free_rate,
        "非空消息率": non_empty_rate,
        "合适长度消息率": proper_length_rate,
        "隐私保护率": privacy_protection_rate,
        "总体文本质量评分": (html_free_rate + non_empty_rate + proper_length_rate + privacy_protection_rate) / 4
    }


def check_structural_quality(conversations):
    """
    检查结构质量
    
    参数:
        conversations: 对话数据列表
    
    返回:
        dict: 结构质量检查结果
    """
    total_conversations = len(conversations)
    
    # 对话结构问题统计
    missing_start_greeting = 0
    missing_end_greeting = 0
    unbalanced_dialog = 0
    too_short_dialog = 0
    too_long_dialog = 0
    
    for conv in conversations:
        messages = conv.get('messages', [])
        
        # 检查对话长度
        if len(messages) < 3:
            too_short_dialog += 1
        elif len(messages) > 50:
            too_long_dialog += 1
        
        # 检查开场问候
        if messages and 'content' in messages[0]:
            first_msg = messages[0]['content'].lower()
            if not any(greeting in first_msg for greeting in ['您好', '你好', '欢迎', 'hello', 'hi']):
                missing_start_greeting += 1
        
        # 检查结束语
        if messages and 'content' in messages[-1]:
            last_msg = messages[-1]['content'].lower()
            if not any(ending in last_msg for ending in ['谢谢', '感谢', '再见', '祝您', 'thank']):
                missing_end_greeting += 1
        
        # 检查对话平衡性
        user_messages = [msg for msg in messages if str(msg.get('sender_type')) == '1.0' or msg.get('sender_type') == 1.0]
        service_messages = [msg for msg in messages if str(msg.get('sender_type')) == '2.0' or msg.get('sender_type') == 2.0]
        
        # 如果用户消息或客服消息占比过高（超过80%），认为对话不平衡
        if len(messages) > 0:
            user_ratio = len(user_messages) / len(messages)
            service_ratio = len(service_messages) / len(messages)
            if user_ratio > 0.8 or service_ratio > 0.8:
                unbalanced_dialog += 1
    
    # 计算结构质量百分比
    greeting_rate = 100 - (missing_start_greeting / total_conversations * 100)
    ending_rate = 100 - (missing_end_greeting / total_conversations * 100)
    balanced_rate = 100 - (unbalanced_dialog / total_conversations * 100)
    proper_length_rate = 100 - ((too_short_dialog + too_long_dialog) / total_conversations * 100)
    
    return {
        "开场问候率": greeting_rate,
        "结束语率": ending_rate,
        "对话平衡率": balanced_rate,
        "合适长度对话率": proper_length_rate,
        "总体结构质量评分": (greeting_rate + ending_rate + balanced_rate + proper_length_rate) / 4
    }


def generate_visualizations(quality_results, output_dir):
    """
    生成可视化图表
    
    参数:
        quality_results: 质量评估结果
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 总体质量评分雷达图
    categories = ['完整性', '一致性', '文本质量', '结构质量']
    values = [
        quality_results['完整性检查']['总体完整性评分'],
        quality_results['一致性检查']['总体一致性评分'],
        quality_results['文本质量检查']['总体文本质量评分'],
        quality_results['结构质量检查']['总体结构质量评分']
    ]
    
    # 创建雷达图
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, polar=True)
    
    # 计算角度
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    values.append(values[0])
    angles.append(angles[0])
    categories.append(categories[0])
    
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
    ax.set_ylim(0, 100)
    ax.grid(True)
    plt.title('数据质量总体评分', size=15)
    
    # 保存雷达图
    plt.savefig(os.path.join(output_dir, 'overall_quality_radar.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 各维度详细评分条形图
    # 完整性详细评分
    completeness_fields = list(quality_results['完整性检查']['对话级别完整性'].keys())
    completeness_values = list(quality_results['完整性检查']['对话级别完整性'].values())
    
    plt.figure(figsize=(12, 6))
    plt.bar(completeness_fields, completeness_values, color='skyblue')
    plt.title('对话级别字段完整性评分')
    plt.ylabel('完整性评分 (%)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'conversation_completeness.png'), dpi=300)
    plt.close()
    
    # 一致性详细评分
    consistency_fields = list(quality_results['一致性检查'].keys())[:-1]  # 排除总体评分
    consistency_values = [quality_results['一致性检查'][field] for field in consistency_fields]
    
    plt.figure(figsize=(10, 6))
    plt.bar(consistency_fields, consistency_values, color='lightgreen')
    plt.title('数据一致性评分')
    plt.ylabel('一致性评分 (%)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'data_consistency.png'), dpi=300)
    plt.close()
    
    # 文本质量详细评分
    text_quality_fields = list(quality_results['文本质量检查'].keys())[:-1]  # 排除总体评分
    text_quality_values = [quality_results['文本质量检查'][field] for field in text_quality_fields]
    
    plt.figure(figsize=(10, 6))
    plt.bar(text_quality_fields, text_quality_values, color='salmon')
    plt.title('文本质量评分')
    plt.ylabel('质量评分 (%)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'text_quality.png'), dpi=300)
    plt.close()
    
    # 结构质量详细评分
    structure_quality_fields = list(quality_results['结构质量检查'].keys())[:-1]  # 排除总体评分
    structure_quality_values = [quality_results['结构质量检查'][field] for field in structure_quality_fields]
    
    plt.figure(figsize=(10, 6))
    plt.bar(structure_quality_fields, structure_quality_values, color='mediumpurple')
    plt.title('对话结构质量评分')
    plt.ylabel('质量评分 (%)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'structure_quality.png'), dpi=300)
    plt.close()


def evaluate_data_quality(input_path, output_path, sample_size=100, visualize=False):
    """
    评估数据质量
    
    参数:
        input_path: 输入JSON文件路径
        output_path: 输出报告路径
        sample_size: 抽样检查的对话数量
        visualize: 是否生成可视化图表
    
    返回:
        bool: 评估是否成功
    """
    try:
        # 加载数据
        print(f"开始加载数据: {input_path}")
        conversations = load_data(input_path)
        if not conversations:
            return False
        
        print(f"数据加载完成，共{len(conversations)}个对话")
        
        # 进行各项质量检查
        print("正在进行完整性检查...")
        completeness_results = check_completeness(conversations)
        
        print("正在进行一致性检查...")
        consistency_results = check_consistency(conversations)
        
        print("正在进行文本质量检查...")
        text_quality_results = check_text_quality(conversations, sample_size)
        
        print("正在进行结构质量检查...")
        structural_quality_results = check_structural_quality(conversations)
        
        # 汇总结果
        quality_results = {
            "完整性检查": completeness_results,
            "一致性检查": consistency_results,
            "文本质量检查": text_quality_results,
            "结构质量检查": structural_quality_results,
            "总体质量评分": (
                completeness_results["总体完整性评分"] +
                consistency_results["总体一致性评分"] +
                text_quality_results["总体文本质量评分"] +
                structural_quality_results["总体结构质量评分"]
            ) / 4
        }
        
        # 创建输出目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存JSON结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(quality_results, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown报告
        md_report = f"""# 数据质量评估报告

## 总体质量评分: {quality_results["总体质量评分"]:.2f}%

## 1. 完整性检查
- 总体完整性评分: {completeness_results["总体完整性评分"]:.2f}%
- 对话级别完整性:
  - touch_id: {completeness_results["对话级别完整性"]["touch_id"]:.2f}%
  - user_name: {completeness_results["对话级别完整性"]["user_name"]:.2f}%
  - servicer_name: {completeness_results["对话级别完整性"]["servicer_name"]:.2f}%
  - start_time: {completeness_results["对话级别完整性"]["start_time"]:.2f}%
  - end_time: {completeness_results["对话级别完整性"]["end_time"]:.2f}%
  - messages: {completeness_results["对话级别完整性"]["messages"]:.2f}%
- 消息级别完整性:
  - seq_no: {completeness_results["消息级别完整性"]["seq_no"]:.2f}%
  - send_time: {completeness_results["消息级别完整性"]["send_time"]:.2f}%
  - sender_type: {completeness_results["消息级别完整性"]["sender_type"]:.2f}%
  - content: {completeness_results["消息级别完整性"]["content"]:.2f}%

## 2. 一致性检查
- 总体一致性评分: {consistency_results["总体一致性评分"]:.2f}%
- 时间顺序一致性: {consistency_results["时间顺序一致性"]:.2f}%
- 消息序号一致性: {consistency_results["消息序号一致性"]:.2f}%
- 发送者类型一致性: {consistency_results["发送者类型一致性"]:.2f}%

## 3. 文本质量检查
- 总体文本质量评分: {text_quality_results["总体文本质量评分"]:.2f}%
- HTML标签清理率: {text_quality_results["HTML标签清理率"]:.2f}%
- 非空消息率: {text_quality_results["非空消息率"]:.2f}%
- 合适长度消息率: {text_quality_results["合适长度消息率"]:.2f}%
- 隐私保护率: {text_quality_results["隐私保护率"]:.2f}%

## 4. 结构质量检查
- 总体结构质量评分: {structural_quality_results["总体结构质量评分"]:.2f}%
- 开场问候率: {structural_quality_results["开场问候率"]:.2f}%
- 结束语率: {structural_quality_results["结束语率"]:.2f}%
- 对话平衡率: {structural_quality_results["对话平衡率"]:.2f}%
- 合适长度对话率: {structural_quality_results["合适长度对话率"]:.2f}%

## 5. 质量评估结论

### 优势
- {"完整性良好" if completeness_results["总体完整性评分"] > 90 else "完整性一般" if completeness_results["总体完整性评分"] > 70 else "完整性较差"}
- {"一致性良好" if consistency_results["总体一致性评分"] > 90 else "一致性一般" if consistency_results["总体一致性评分"] > 70 else "一致性较差"}
- {"文本质量良好" if text_quality_results["总体文本质量评分"] > 90 else "文本质量一般" if text_quality_results["总体文本质量评分"] > 70 else "文本质量较差"}
- {"结构质量良好" if structural_quality_results["总体结构质量评分"] > 90 else "结构质量一般" if structural_quality_results["总体结构质量评分"] > 70 else "结构质量较差"}

### 不足
{"- 完整性有待提高" if completeness_results["总体完整性评分"] < 90 else ""}
{"- 一致性有待提高" if consistency_results["总体一致性评分"] < 90 else ""}
{"- 文本质量有待提高" if text_quality_results["总体文本质量评分"] < 90 else ""}
{"- 结构质量有待提高" if structural_quality_results["总体结构质量评分"] < 90 else ""}

### 建议
- {"建议进一步完善数据清洗流程，提高数据完整性" if completeness_results["总体完整性评分"] < 90 else "数据完整性良好，可以继续保持"}
- {"建议优化时间顺序和消息序号处理，提高数据一致性" if consistency_results["总体一致性评分"] < 90 else "数据一致性良好，可以继续保持"}
- {"建议加强文本清洗和敏感信息处理，提高文本质量" if text_quality_results["总体文本质量评分"] < 90 else "文本质量良好，可以继续保持"}
- {"建议优化对话结构处理，提高结构质量" if structural_quality_results["总体结构质量评分"] < 90 else "对话结构质量良好，可以继续保持"}
"""
        
        with open(os.path.splitext(output_path)[0] + '.md', 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        # 生成可视化图表
        if visualize:
            print("正在生成可视化图表...")
            visualizations_dir = os.path.join(os.path.dirname(output_path), 'visualizations')
            generate_visualizations(quality_results, visualizations_dir)
            print(f"可视化图表已保存到: {visualizations_dir}")
        
        print(f"质量评估报告已保存到: {output_path}")
        return True
    
    except Exception as e:
        print(f"质量评估过程中出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 执行质量评估
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    success = evaluate_data_quality(args.input, args.output, args.sample, args.visualize)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据质量评估成功！")
    else:
        print("数据质量评估失败！")


if __name__ == "__main__":
    main()

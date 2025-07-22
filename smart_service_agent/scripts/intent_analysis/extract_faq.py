#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FAQ提取脚本
功能：从意图分析结果中提取常见问答对，构建知识库
用法：python extract_faq.py --input <input_path> --output <output_path> [--min_frequency <min_frequency>]
"""

import argparse
import json
import os
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='从意图分析结果中提取常见问答对，构建知识库')
    parser.add_argument('--input', required=True, help='意图分析结果JSON文件路径')
    parser.add_argument('--output', required=True, help='输出知识库文件路径')
    parser.add_argument('--min_frequency', type=int, default=2, help='最小出现频率，默认为2')
    parser.add_argument('--format', choices=['json', 'csv', 'excel', 'markdown'], default='json', help='输出格式，默认为json')
    parser.add_argument('--interactive', action='store_true', help='是否启用交互式模式')
    return parser.parse_args()


def load_analysis_results(input_path):
    """
    加载意图分析结果
    
    参数:
        input_path: 意图分析结果JSON文件路径
    
    返回:
        dict: 意图分析结果
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)
        
        print(f"成功加载意图分析结果")
        return analysis_results
    
    except Exception as e:
        print(f"加载意图分析结果时出错: {e}")
        return None


def organize_faq_by_intent(faq_items):
    """
    按意图组织FAQ
    
    参数:
        faq_items: FAQ列表
    
    返回:
        dict: 按意图组织的FAQ
    """
    organized_faq = defaultdict(list)
    
    for item in faq_items:
        intent_category = item.get('intent_category', '未知')
        intent_subcategory = item.get('intent_subcategory', '未知')
        
        # 使用意图类别和子类别作为键
        key = f"{intent_category} / {intent_subcategory}"
        organized_faq[key].append(item)
    
    # 转换为普通字典
    return dict(organized_faq)


def clean_answer(answer):
    """
    清理回答内容
    
    参数:
        answer: 原始回答
    
    返回:
        str: 清理后的回答
    """
    # 去除多余空格
    answer = re.sub(r'\s+', ' ', answer).strip()
    
    # 去除常见的无用前缀
    prefixes = [
        r'^亲[,，]?',
        r'^您好[,，]?',
        r'^你好[,，]?',
        r'^亲爱的[,，]?',
        r'^尊敬的[,，]?'
    ]
    for prefix in prefixes:
        answer = re.sub(prefix, '', answer)
    
    # 去除多余标点
    answer = re.sub(r'[!！]{2,}', '！', answer)
    answer = re.sub(r'[.。]{2,}', '。', answer)
    
    return answer.strip()


def enhance_faq(faq_items):
    """
    增强FAQ质量
    
    参数:
        faq_items: 原始FAQ列表
    
    返回:
        list: 增强后的FAQ列表
    """
    enhanced_faq = []
    
    for item in faq_items:
        # 清理回答
        cleaned_answer = clean_answer(item['answer'])
        
        # 增强FAQ项
        enhanced_item = {
            'question': item['question'],
            'answer': cleaned_answer,
            'intent_category': item['intent_category'],
            'intent_subcategory': item['intent_subcategory'],
            'frequency': item['frequency'],
            'similar_questions': item['similar_questions'],
            'tags': [],  # 添加标签字段
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加标签
        if item['intent_category'] != '未知':
            enhanced_item['tags'].append(item['intent_category'])
        
        if item['intent_subcategory'] != '未知':
            enhanced_item['tags'].append(item['intent_subcategory'])
        
        # 提取关键实体作为标签
        entities = extract_entities_from_text(item['question'])
        for entity_type, entity_value in entities:
            if entity_type not in ['未知']:
                enhanced_item['tags'].append(entity_type)
        
        # 去重标签
        enhanced_item['tags'] = list(set(enhanced_item['tags']))
        
        enhanced_faq.append(enhanced_item)
    
    return enhanced_faq


def extract_entities_from_text(text):
    """
    从文本中提取实体
    
    参数:
        text: 文本内容
    
    返回:
        list: 实体列表，每个实体是一个元组 (type, value)
    """
    entities = []
    
    # 提取订单号
    order_id_pattern = r'\b\d{16,19}\b'
    for match in re.finditer(order_id_pattern, text):
        entities.append(('订单号', match.group()))
    
    # 提取手机号
    phone_pattern = r'1[3-9]\d{9}'
    for match in re.finditer(phone_pattern, text):
        entities.append(('手机号', match.group()))
    
    # 提取日期
    date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'
    for match in re.finditer(date_pattern, text):
        entities.append(('日期', match.group()))
    
    # 提取金额
    money_pattern = r'\d+(\.\d+)?元|\d+(\.\d+)?块|\d+(\.\d+)?¥|\¥\d+(\.\d+)?'
    for match in re.finditer(money_pattern, text):
        entities.append(('金额', match.group()))
    
    return entities


def generate_knowledge_base(faq_items, min_frequency=2):
    """
    生成知识库
    
    参数:
        faq_items: FAQ列表
        min_frequency: 最小出现频率
    
    返回:
        dict: 知识库
    """
    # 过滤低频FAQ
    filtered_faq = [item for item in faq_items if item['frequency'] >= min_frequency]
    
    # 增强FAQ
    enhanced_faq = enhance_faq(filtered_faq)
    
    # 按意图组织FAQ
    organized_faq = organize_faq_by_intent(enhanced_faq)
    
    # 构建知识库
    knowledge_base = {
        'metadata': {
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_items': len(enhanced_faq),
            'intent_categories': len(organized_faq),
            'min_frequency': min_frequency
        },
        'faq_by_intent': organized_faq,
        'faq_items': enhanced_faq
    }
    
    return knowledge_base


def save_knowledge_base(knowledge_base, output_path, format='json'):
    """
    保存知识库
    
    参数:
        knowledge_base: 知识库
        output_path: 输出文件路径
        format: 输出格式
    
    返回:
        bool: 是否成功
    """
    try:
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == 'json':
            # 保存为JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            # 保存为CSV
            df = pd.DataFrame(knowledge_base['faq_items'])
            df.to_csv(output_path, index=False, encoding='utf-8')
        
        elif format == 'excel':
            # 保存为Excel
            df = pd.DataFrame(knowledge_base['faq_items'])
            df.to_excel(output_path, index=False)
        
        elif format == 'markdown':
            # 保存为Markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 回收宝客服知识库\n\n")
                f.write(f"生成时间: {knowledge_base['metadata']['created_at']}\n\n")
                f.write(f"总条目数: {knowledge_base['metadata']['total_items']}\n")
                f.write(f"意图类别数: {knowledge_base['metadata']['intent_categories']}\n")
                f.write(f"最小频率: {knowledge_base['metadata']['min_frequency']}\n\n")
                
                f.write("## 按意图分类的FAQ\n\n")
                for intent, items in knowledge_base['faq_by_intent'].items():
                    f.write(f"### {intent} ({len(items)}个问题)\n\n")
                    
                    for i, item in enumerate(items):
                        f.write(f"#### Q{i+1}: {item['question']}\n\n")
                        f.write(f"**回答**: {item['answer']}\n\n")
                        f.write(f"**频率**: {item['frequency']}\n\n")
                        
                        if item['similar_questions']:
                            f.write("**相似问题**:\n")
                            for j, q in enumerate(item['similar_questions'][:5]):
                                f.write(f"- {q}\n")
                            
                            if len(item['similar_questions']) > 5:
                                f.write(f"- ... 还有 {len(item['similar_questions']) - 5} 个相似问题\n")
                        
                        if item['tags']:
                            f.write(f"\n**标签**: {', '.join(item['tags'])}\n")
                        
                        f.write("\n---\n\n")
        
        print(f"知识库已保存到: {output_path}")
        return True
    
    except Exception as e:
        print(f"保存知识库时出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 执行提取
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    # 加载意图分析结果
    analysis_results = load_analysis_results(args.input)
    if not analysis_results:
        print("加载意图分析结果失败")
        return
    
    # 获取FAQ项
    faq_items = analysis_results.get('faq', [])
    if not faq_items:
        print("未找到FAQ项")
        return
    
    print(f"找到 {len(faq_items)} 个FAQ项")
    
    # 生成知识库
    knowledge_base = generate_knowledge_base(faq_items, args.min_frequency)
    
    # 保存知识库
    success = save_knowledge_base(knowledge_base, args.output, args.format)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("知识库生成成功！")
        
        # 交互式模式
        if args.interactive:
            print("\n是否查看知识库摘要？(y/n)")
            user_input = input()
            if user_input.lower() == 'y':
                # 显示知识库摘要
                print("\n知识库摘要:")
                print(f"总条目数: {knowledge_base['metadata']['total_items']}")
                print(f"意图类别数: {knowledge_base['metadata']['intent_categories']}")
                
                print("\n意图类别:")
                for i, intent in enumerate(knowledge_base['faq_by_intent'].keys()):
                    if i < 5:
                        print(f"- {intent}: {len(knowledge_base['faq_by_intent'][intent])}个问题")
                    else:
                        remaining = len(knowledge_base['faq_by_intent']) - 5
                        print(f"- ... 还有 {remaining} 个意图类别")
                        break
    else:
        print("知识库生成失败！")


if __name__ == "__main__":
    main()

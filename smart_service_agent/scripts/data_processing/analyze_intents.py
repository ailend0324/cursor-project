#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
意图分析脚本
功能：分析客服对话数据，提取用户意图和常见问题
用法：python analyze_intents.py --input <cleaned_data_path> --output <output_dir>
"""

import argparse
import json
import os
import re
import jieba
import jieba.analyse
import pandas as pd
from collections import Counter
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='分析客服对话数据，提取用户意图和常见问题')
    parser.add_argument('--input', required=True, help='清洗后的JSON数据文件路径')
    parser.add_argument('--output', required=True, help='输出目录路径')
    parser.add_argument('--top_n', type=int, default=100, help='提取的高频问题数量')
    return parser.parse_args()


def extract_user_questions(conversations):
    """
    提取用户问题
    
    参数:
        conversations: 对话数据列表
    
    返回:
        list: 用户问题列表
    """
    questions = []
    
    for conversation in conversations:
        # 获取用户消息
        user_messages = [msg for msg in conversation['messages'] 
                        if str(msg.get('sender_type')) == '1.0']
        
        # 提取可能的问题（通常是用户的第一条消息和包含问号的消息）
        for msg in user_messages:
            content = msg.get('content', '')
            
            # 跳过太短的消息
            if len(content) < 5:
                continue
            
            # 如果是第一条用户消息或包含问号，认为是问题
            is_first = msg == user_messages[0]
            has_question_mark = '?' in content or '？' in content
            
            if is_first or has_question_mark:
                questions.append({
                    'touch_id': conversation['touch_id'],
                    'content': content,
                    'send_time': msg.get('send_time', ''),
                    'is_first': is_first,
                    'has_question_mark': has_question_mark
                })
    
    return questions


def classify_questions(questions):
    """
    对问题进行分类
    
    参数:
        questions: 问题列表
    
    返回:
        dict: 分类结果
    """
    # 定义分类规则（正则表达式模式）
    patterns = {
        '订单查询': r'订单|查询|查看|进度|状态',
        '物流配送': r'物流|快递|发货|收货|邮寄|包裹|几天|什么时候到',
        '价格咨询': r'价格|多少钱|报价|估价|回收价|值多少',
        '回收流程': r'流程|步骤|怎么操作|如何|教程|怎么回收|怎么卖',
        '验货检测': r'检测|验机|验货|检查|成色|评估',
        '支付结算': r'支付|付款|打款|到账|微信|支付宝|银行卡',
        '账号问题': r'账号|登录|注册|密码|绑定',
        '售后服务': r'售后|退款|维修|换货|保修|投诉',
        '产品咨询': r'型号|配置|参数|规格|功能|版本',
        '其他问题': r'.*'  # 默认分类
    }
    
    # 分类结果
    classified = {category: [] for category in patterns.keys()}
    
    # 对每个问题进行分类
    for question in questions:
        content = question['content']
        assigned = False
        
        # 尝试匹配每个分类
        for category, pattern in patterns.items():
            if re.search(pattern, content):
                classified[category].append(question)
                assigned = True
                break
        
        # 如果没有匹配到任何分类，归为其他问题
        if not assigned:
            classified['其他问题'].append(question)
    
    return classified


def extract_keywords(questions, top_n=20):
    """
    提取问题中的关键词
    
    参数:
        questions: 问题列表
        top_n: 提取的关键词数量
    
    返回:
        list: 关键词列表
    """
    # 合并所有问题文本
    all_text = ' '.join([q['content'] for q in questions])
    
    # 使用TF-IDF提取关键词
    keywords = jieba.analyse.extract_tags(all_text, topK=top_n, withWeight=True)
    
    return keywords


def find_similar_questions(questions, threshold=0.7):
    """
    查找相似问题
    
    参数:
        questions: 问题列表
        threshold: 相似度阈值
    
    返回:
        list: 相似问题组列表
    """
    # 这里简化处理，仅基于关键词匹配
    # 实际项目中应使用更复杂的相似度算法（如余弦相似度、词向量等）
    
    # 提取每个问题的关键词
    for question in questions:
        keywords = jieba.analyse.extract_tags(question['content'], topK=5)
        question['keywords'] = keywords
    
    # 查找相似问题
    similar_groups = []
    processed = set()
    
    for i, q1 in enumerate(questions):
        if i in processed:
            continue
        
        group = [q1]
        processed.add(i)
        
        for j, q2 in enumerate(questions):
            if j in processed or i == j:
                continue
            
            # 计算关键词重叠度作为相似度
            common_keywords = set(q1['keywords']) & set(q2['keywords'])
            similarity = len(common_keywords) / max(len(q1['keywords']), len(q2['keywords']))
            
            if similarity >= threshold:
                group.append(q2)
                processed.add(j)
        
        if len(group) > 1:
            similar_groups.append(group)
    
    return similar_groups


def generate_faq_candidates(classified_questions, top_n=20):
    """
    生成FAQ候选项
    
    参数:
        classified_questions: 分类后的问题
        top_n: 每个分类提取的FAQ数量
    
    返回:
        dict: 分类FAQ候选项
    """
    faq_candidates = {}
    
    for category, questions in classified_questions.items():
        if not questions:
            continue
        
        # 提取该分类下的关键词
        keywords = extract_keywords(questions, top_n=10)
        
        # 查找相似问题组
        similar_groups = find_similar_questions(questions)
        
        # 选择最具代表性的问题作为FAQ候选
        candidates = []
        
        # 首先从相似问题组中选择
        for group in similar_groups:
            # 选择最长的问题作为代表
            representative = max(group, key=lambda q: len(q['content']))
            candidates.append({
                'question': representative['content'],
                'variants': [q['content'] for q in group if q != representative],
                'frequency': len(group)
            })
        
        # 如果候选数量不足，从剩余问题中选择
        if len(candidates) < top_n:
            # 按问题长度排序，选择更长的问题（通常更完整）
            remaining = [q for q in questions if not any(q in group for group in similar_groups)]
            remaining.sort(key=lambda q: len(q['content']), reverse=True)
            
            for question in remaining[:top_n - len(candidates)]:
                candidates.append({
                    'question': question['content'],
                    'variants': [],
                    'frequency': 1
                })
        
        # 限制数量
        faq_candidates[category] = candidates[:top_n]
    
    return faq_candidates


def save_results(results, output_dir):
    """
    保存分析结果
    
    参数:
        results: 分析结果
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存分类统计
    category_stats = {category: len(questions) for category, questions in results['classified_questions'].items()}
    with open(os.path.join(output_dir, 'category_stats.json'), 'w', encoding='utf-8') as f:
        json.dump(category_stats, f, ensure_ascii=False, indent=2)
    
    # 保存关键词统计
    with open(os.path.join(output_dir, 'keywords.json'), 'w', encoding='utf-8') as f:
        json.dump(results['keywords'], f, ensure_ascii=False, indent=2)
    
    # 保存FAQ候选项
    with open(os.path.join(output_dir, 'faq_candidates.json'), 'w', encoding='utf-8') as f:
        json.dump(results['faq_candidates'], f, ensure_ascii=False, indent=2)
    
    # 生成分析报告
    report = f"""# 客服对话数据分析报告

## 1. 基本统计

- 总对话数: {results['total_conversations']}
- 提取的用户问题数: {results['total_questions']}

## 2. 问题分类统计

| 分类 | 数量 | 占比 |
|------|------|------|
"""
    
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = count / results['total_questions'] * 100
        report += f"| {category} | {count} | {percentage:.2f}% |\n"
    
    report += """
## 3. 高频关键词

| 关键词 | 权重 |
|--------|------|
"""
    
    for keyword, weight in results['keywords']:
        report += f"| {keyword} | {weight:.4f} |\n"
    
    report += """
## 4. FAQ候选项

以下是各分类下的高频问题，可作为FAQ知识库的基础：

"""
    
    for category, candidates in results['faq_candidates'].items():
        if not candidates:
            continue
        
        report += f"### {category}\n\n"
        
        for i, candidate in enumerate(candidates):
            report += f"{i+1}. Q: {candidate['question']}\n"
            if candidate['variants']:
                report += f"   变体: {', '.join(candidate['variants'][:3])}\n"
            if i >= 9:  # 只显示前10个
                break
        
        report += "\n"
    
    # 保存报告
    with open(os.path.join(output_dir, 'analysis_report.md'), 'w', encoding='utf-8') as f:
        f.write(report)


def analyze_data(input_path, output_dir, top_n=100):
    """
    分析对话数据
    
    参数:
        input_path: 输入JSON文件路径
        output_dir: 输出目录路径
        top_n: 提取的高频问题数量
    
    返回:
        bool: 分析是否成功
    """
    try:
        print(f"开始读取JSON文件: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"读取完成，共{len(conversations)}个对话")
        
        # 提取用户问题
        questions = extract_user_questions(conversations)
        print(f"提取的用户问题数: {len(questions)}")
        
        # 对问题进行分类
        classified_questions = classify_questions(questions)
        print("问题分类完成")
        
        # 提取关键词
        keywords = extract_keywords(questions, top_n=30)
        print("关键词提取完成")
        
        # 生成FAQ候选项
        faq_candidates = generate_faq_candidates(classified_questions, top_n=top_n)
        print("FAQ候选项生成完成")
        
        # 整理结果
        results = {
            'total_conversations': len(conversations),
            'total_questions': len(questions),
            'classified_questions': classified_questions,
            'keywords': keywords,
            'faq_candidates': faq_candidates
        }
        
        # 保存结果
        save_results(results, output_dir)
        print(f"分析结果已保存到: {output_dir}")
        
        return True
    
    except Exception as e:
        print(f"分析过程中出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 执行分析
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    success = analyze_data(args.input, args.output, args.top_n)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据分析成功！")
    else:
        print("数据分析失败！")


if __name__ == "__main__":
    main()

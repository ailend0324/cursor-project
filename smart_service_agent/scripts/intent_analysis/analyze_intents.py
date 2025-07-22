#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
意图分析脚本
功能：分析优化结构的对话数据，提取常见用户问题和意图
用法：python analyze_intents.py --input <input_path> --output <output_dir> [--limit <limit>]
"""

import argparse
import json
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from datetime import datetime
import re


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='分析对话数据，提取常见用户问题和意图')
    parser.add_argument('--input', required=True, help='输入JSON文件路径')
    parser.add_argument('--output', required=True, help='输出目录路径')
    parser.add_argument('--limit', type=int, default=None, help='限制处理的对话数量，用于测试')
    parser.add_argument('--interactive', action='store_true', help='是否启用交互式模式')
    return parser.parse_args()


def load_data(input_path, limit=None):
    """
    加载优化结构的对话数据
    
    参数:
        input_path: 输入JSON文件路径
        limit: 限制处理的对话数量
    
    返回:
        list: 对话列表
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"成功加载 {len(conversations)} 个对话")
        
        if limit and limit < len(conversations):
            conversations = conversations[:limit]
            print(f"已限制处理前 {limit} 个对话")
        
        return conversations
    
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return []


def extract_user_questions(conversations):
    """
    从对话中提取用户问题
    
    参数:
        conversations: 对话列表
    
    返回:
        list: 用户问题列表，每个问题是一个字典
    """
    user_questions = []
    
    for conv in conversations:
        conv_id = conv.get('conversation_id', '')
        primary_intent = conv.get('primary_intent', {})
        
        for msg in conv.get('messages', []):
            if msg.get('sender_type') == 'user':
                content = msg.get('content', '')
                
                # 过滤掉太短的消息和无意义的消息
                if len(content) < 2 or re.match(r'^[0-9]+$', content):
                    continue
                
                # 提取问题信息
                question = {
                    'conversation_id': conv_id,
                    'message_id': msg.get('message_id', ''),
                    'content': content,
                    'send_time': msg.get('send_time', ''),
                    'intent': msg.get('intent', {}),
                    'entities': msg.get('entities', []),
                    'primary_intent': primary_intent
                }
                
                user_questions.append(question)
    
    print(f"成功提取 {len(user_questions)} 个用户问题")
    return user_questions


def extract_responses(conversations):
    """
    从对话中提取客服回复
    
    参数:
        conversations: 对话列表
    
    返回:
        list: 客服回复列表，每个回复是一个字典
    """
    responses = []
    
    for conv in conversations:
        conv_id = conv.get('conversation_id', '')
        
        # 按序号排序消息
        messages = sorted(conv.get('messages', []), key=lambda x: x.get('seq_no', 0))
        
        # 遍历消息，找出每个用户问题对应的客服回复
        for i, msg in enumerate(messages):
            if msg.get('sender_type') == 'user' and i + 1 < len(messages):
                user_msg = msg
                # 查找下一条客服消息
                for j in range(i + 1, len(messages)):
                    if messages[j].get('sender_type') == 'agent':
                        agent_msg = messages[j]
                        
                        # 构建问答对
                        qa_pair = {
                            'conversation_id': conv_id,
                            'user_message_id': user_msg.get('message_id', ''),
                            'agent_message_id': agent_msg.get('message_id', ''),
                            'question': user_msg.get('content', ''),
                            'answer': agent_msg.get('content', ''),
                            'user_intent': user_msg.get('intent', {}),
                            'agent_intent': agent_msg.get('intent', {}),
                            'user_entities': user_msg.get('entities', []),
                            'send_time': user_msg.get('send_time', '')
                        }
                        
                        responses.append(qa_pair)
                        break
    
    print(f"成功提取 {len(responses)} 个问答对")
    return responses


def analyze_intent_distribution(user_questions):
    """
    分析意图分布
    
    参数:
        user_questions: 用户问题列表
    
    返回:
        dict: 意图分布统计
    """
    # 统计主要意图类别
    intent_categories = Counter()
    intent_subcategories = Counter()
    intent_pairs = Counter()
    
    for question in user_questions:
        intent = question.get('intent', {})
        category = intent.get('category', '未知')
        subcategory = intent.get('subcategory', '未知')
        
        intent_categories[category] += 1
        intent_subcategories[subcategory] += 1
        intent_pairs[f"{category}-{subcategory}"] += 1
    
    # 计算百分比
    total = len(user_questions)
    intent_categories_percent = {k: v / total * 100 for k, v in intent_categories.items()}
    intent_subcategories_percent = {k: v / total * 100 for k, v in intent_subcategories.items()}
    intent_pairs_percent = {k: v / total * 100 for k, v in intent_pairs.items()}
    
    # 排序
    intent_categories_sorted = dict(sorted(intent_categories_percent.items(), key=lambda x: x[1], reverse=True))
    intent_subcategories_sorted = dict(sorted(intent_subcategories_percent.items(), key=lambda x: x[1], reverse=True))
    intent_pairs_sorted = dict(sorted(intent_pairs_percent.items(), key=lambda x: x[1], reverse=True))
    
    return {
        'categories': intent_categories_sorted,
        'subcategories': intent_subcategories_sorted,
        'pairs': intent_pairs_sorted,
        'total': total
    }


def extract_keywords(user_questions, top_n=20):
    """
    提取用户问题中的关键词
    
    参数:
        user_questions: 用户问题列表
        top_n: 返回的关键词数量
    
    返回:
        list: 关键词列表，每个关键词是一个元组 (word, weight)
    """
    # 合并所有用户问题
    all_content = ' '.join([q.get('content', '') for q in user_questions])
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(all_content, topK=top_n, withWeight=True)
    
    return keywords


def cluster_questions(user_questions, n_clusters=10):
    """
    聚类用户问题
    
    参数:
        user_questions: 用户问题列表
        n_clusters: 聚类数量
    
    返回:
        dict: 聚类结果
    """
    # 提取内容
    contents = [q.get('content', '') for q in user_questions]
    
    # 使用TF-IDF向量化
    vectorizer = TfidfVectorizer(max_features=1000, stop_words=['的', '了', '是', '我', '你', '吗', '在', '有', '和', '就', '不', '要', '这', '那', '啊', '呢', '吧'])
    X = vectorizer.fit_transform(contents)
    
    # KMeans聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    
    # 整理聚类结果
    cluster_results = defaultdict(list)
    for i, cluster_id in enumerate(clusters):
        cluster_results[int(cluster_id)].append(user_questions[i])
    
    # 提取每个聚类的关键词
    cluster_keywords = {}
    for cluster_id, questions in cluster_results.items():
        cluster_content = ' '.join([q.get('content', '') for q in questions])
        keywords = jieba.analyse.extract_tags(cluster_content, topK=5, withWeight=True)
        cluster_keywords[cluster_id] = keywords
    
    return {
        'clusters': dict(cluster_results),
        'keywords': cluster_keywords,
        'n_clusters': n_clusters
    }


def analyze_entity_types(user_questions):
    """
    分析实体类型分布
    
    参数:
        user_questions: 用户问题列表
    
    返回:
        dict: 实体类型分布
    """
    entity_types = Counter()
    
    for question in user_questions:
        entities = question.get('entities', [])
        for entity in entities:
            entity_type = entity.get('type', '未知')
            entity_types[entity_type] += 1
    
    # 计算百分比
    total = sum(entity_types.values())
    if total > 0:
        entity_types_percent = {k: v / total * 100 for k, v in entity_types.items()}
    else:
        entity_types_percent = {}
    
    # 排序
    entity_types_sorted = dict(sorted(entity_types_percent.items(), key=lambda x: x[1], reverse=True))
    
    return {
        'types': entity_types_sorted,
        'total': total
    }


def analyze_question_length(user_questions):
    """
    分析用户问题长度分布
    
    参数:
        user_questions: 用户问题列表
    
    返回:
        dict: 长度分布统计
    """
    lengths = [len(q.get('content', '')) for q in user_questions]
    
    return {
        'min': min(lengths) if lengths else 0,
        'max': max(lengths) if lengths else 0,
        'avg': sum(lengths) / len(lengths) if lengths else 0,
        'median': sorted(lengths)[len(lengths) // 2] if lengths else 0,
        'distribution': {
            '0-10': sum(1 for l in lengths if l <= 10),
            '11-20': sum(1 for l in lengths if 11 <= l <= 20),
            '21-50': sum(1 for l in lengths if 21 <= l <= 50),
            '51-100': sum(1 for l in lengths if 51 <= l <= 100),
            '>100': sum(1 for l in lengths if l > 100)
        }
    }


def find_similar_questions(user_questions, threshold=0.7):
    """
    查找相似问题
    
    参数:
        user_questions: 用户问题列表
        threshold: 相似度阈值
    
    返回:
        list: 相似问题组列表
    """
    # 使用TF-IDF向量化
    contents = [q.get('content', '') for q in user_questions]
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(contents)
    
    # 计算相似度矩阵
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(X)
    
    # 查找相似问题组
    similar_groups = []
    visited = set()
    
    for i in range(len(user_questions)):
        if i in visited:
            continue
        
        group = [i]
        visited.add(i)
        
        for j in range(i + 1, len(user_questions)):
            if j in visited:
                continue
            
            if similarity_matrix[i, j] >= threshold:
                group.append(j)
                visited.add(j)
        
        if len(group) > 1:
            similar_groups.append([user_questions[idx] for idx in group])
    
    return similar_groups


def extract_faq(responses, min_frequency=2):
    """
    提取常见问答对
    
    参数:
        responses: 问答对列表
        min_frequency: 最小出现频率
    
    返回:
        list: 常见问答对列表
    """
    # 使用TF-IDF向量化问题
    questions = [r.get('question', '') for r in responses]
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(questions)
    
    # 计算相似度矩阵
    from sklearn.metrics.pairwise import cosine_similarity
    similarity_matrix = cosine_similarity(X)
    
    # 聚类相似问题
    threshold = 0.7
    clusters = []
    visited = set()
    
    for i in range(len(questions)):
        if i in visited:
            continue
        
        cluster = [i]
        visited.add(i)
        
        for j in range(i + 1, len(questions)):
            if j in visited:
                continue
            
            if similarity_matrix[i, j] >= threshold:
                cluster.append(j)
                visited.add(j)
        
        if len(cluster) >= min_frequency:
            clusters.append(cluster)
    
    # 提取FAQ
    faq = []
    for cluster in clusters:
        # 选择最具代表性的问题（最短的非空问题）
        representative_q_idx = min(cluster, key=lambda i: len(questions[i]) if len(questions[i]) > 0 else float('inf'))
        representative_q = questions[representative_q_idx]
        
        # 选择最具代表性的回答（最长的非空回答）
        answers = [responses[i].get('answer', '') for i in cluster]
        representative_a_idx = max(range(len(answers)), key=lambda i: len(answers[i]) if len(answers[i]) > 0 else 0)
        representative_a = answers[representative_a_idx]
        
        # 获取意图信息
        intent = responses[representative_q_idx].get('user_intent', {})
        
        # 构建FAQ项
        faq_item = {
            'question': representative_q,
            'answer': representative_a,
            'intent_category': intent.get('category', '未知'),
            'intent_subcategory': intent.get('subcategory', '未知'),
            'frequency': len(cluster),
            'similar_questions': [questions[i] for i in cluster if i != representative_q_idx]
        }
        
        faq.append(faq_item)
    
    # 按频率排序
    faq.sort(key=lambda x: x['frequency'], reverse=True)
    
    return faq


def generate_visualizations(analysis_results, output_dir):
    """
    生成可视化图表
    
    参数:
        analysis_results: 分析结果
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 意图类别分布饼图
    plt.figure(figsize=(10, 8))
    categories = analysis_results['intent_distribution']['categories']
    labels = list(categories.keys())
    sizes = list(categories.values())
    
    # 只显示前7个类别，其余归为"其他"
    if len(labels) > 7:
        other_sum = sum(sizes[7:])
        labels = labels[:7] + ['其他']
        sizes = sizes[:7] + [other_sum]
    
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('用户意图类别分布')
    plt.savefig(os.path.join(output_dir, 'intent_category_distribution.png'))
    plt.close()
    
    # 意图子类别分布条形图
    plt.figure(figsize=(12, 8))
    subcategories = analysis_results['intent_distribution']['subcategories']
    labels = list(subcategories.keys())[:10]  # 只显示前10个子类别
    sizes = list(subcategories.values())[:10]
    
    plt.barh(range(len(labels)), sizes, align='center')
    plt.yticks(range(len(labels)), labels)
    plt.xlabel('百分比 (%)')
    plt.title('用户意图子类别分布 (前10)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'intent_subcategory_distribution.png'))
    plt.close()
    
    # 问题长度分布直方图
    plt.figure(figsize=(10, 6))
    distribution = analysis_results['question_length']['distribution']
    labels = list(distribution.keys())
    sizes = list(distribution.values())
    
    plt.bar(labels, sizes)
    plt.xlabel('问题长度')
    plt.ylabel('数量')
    plt.title('用户问题长度分布')
    plt.savefig(os.path.join(output_dir, 'question_length_distribution.png'))
    plt.close()
    
    # 实体类型分布饼图
    plt.figure(figsize=(10, 8))
    entity_types = analysis_results['entity_distribution']['types']
    if entity_types:
        labels = list(entity_types.keys())
        sizes = list(entity_types.values())
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('实体类型分布')
        plt.savefig(os.path.join(output_dir, 'entity_type_distribution.png'))
    plt.close()
    
    # 关键词词云
    try:
        from wordcloud import WordCloud
        
        keywords = analysis_results['keywords']
        wordcloud_data = {word: weight for word, weight in keywords}
        
        wordcloud = WordCloud(width=800, height=400, background_color='white')
        wordcloud.generate_from_frequencies(wordcloud_data)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'keywords_wordcloud.png'))
        plt.close()
    except Exception as e:
        print(f"生成词云图时出错: {e}")


def generate_reports(analysis_results, output_dir):
    """
    生成分析报告
    
    参数:
        analysis_results: 分析结果
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存JSON报告
    json_path = os.path.join(output_dir, 'intent_analysis_report.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    md_path = os.path.join(output_dir, 'intent_analysis_report.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 用户意图分析报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 基本统计信息
        f.write("## 1. 基本统计信息\n\n")
        f.write(f"- 分析对话数: {analysis_results['conversation_count']}\n")
        f.write(f"- 用户问题数: {analysis_results['question_count']}\n")
        f.write(f"- 问答对数: {analysis_results['response_count']}\n")
        f.write(f"- 提取的FAQ数: {len(analysis_results['faq'])}\n\n")
        
        # 意图分布
        f.write("## 2. 意图分布\n\n")
        f.write("### 2.1 意图类别分布\n\n")
        f.write("| 意图类别 | 百分比 |\n")
        f.write("|---------|-------|\n")
        for category, percent in analysis_results['intent_distribution']['categories'].items():
            f.write(f"| {category} | {percent:.2f}% |\n")
        
        f.write("\n### 2.2 意图子类别分布 (前10)\n\n")
        f.write("| 意图子类别 | 百分比 |\n")
        f.write("|-----------|-------|\n")
        subcategories = list(analysis_results['intent_distribution']['subcategories'].items())[:10]
        for subcategory, percent in subcategories:
            f.write(f"| {subcategory} | {percent:.2f}% |\n")
        
        # 问题长度分析
        f.write("\n## 3. 问题长度分析\n\n")
        length_info = analysis_results['question_length']
        f.write(f"- 最短问题长度: {length_info['min']}\n")
        f.write(f"- 最长问题长度: {length_info['max']}\n")
        f.write(f"- 平均问题长度: {length_info['avg']:.2f}\n")
        f.write(f"- 中位数问题长度: {length_info['median']}\n\n")
        
        f.write("问题长度分布:\n\n")
        f.write("| 长度范围 | 数量 |\n")
        f.write("|---------|-----|\n")
        for length_range, count in length_info['distribution'].items():
            f.write(f"| {length_range} | {count} |\n")
        
        # 实体分布
        f.write("\n## 4. 实体分布\n\n")
        f.write("| 实体类型 | 百分比 |\n")
        f.write("|---------|-------|\n")
        for entity_type, percent in analysis_results['entity_distribution']['types'].items():
            f.write(f"| {entity_type} | {percent:.2f}% |\n")
        
        # 关键词
        f.write("\n## 5. 关键词 (前20)\n\n")
        f.write("| 关键词 | 权重 |\n")
        f.write("|-------|-----|\n")
        for word, weight in analysis_results['keywords']:
            f.write(f"| {word} | {weight:.4f} |\n")
        
        # 聚类结果
        f.write("\n## 6. 问题聚类\n\n")
        clusters_data = analysis_results['clusters']
        if 'keywords' in clusters_data and 'clusters' in clusters_data:
            for cluster_id, keywords in clusters_data['keywords'].items():
                cluster_key = str(cluster_id)
                if cluster_key in clusters_data['clusters']:
                    keyword_str = ', '.join([word for word, _ in keywords])
                    question_count = len(clusters_data['clusters'][cluster_key])
                    f.write(f"### 聚类 {cluster_id}: {keyword_str} ({question_count}个问题)\n\n")
                    
                    # 显示每个聚类的前5个问题
                    questions = clusters_data['clusters'][cluster_key][:5]
                    for i, q in enumerate(questions):
                        f.write(f"{i+1}. {q['content']}\n")
                    
                    if question_count > 5:
                        f.write(f"... 还有 {question_count - 5} 个问题\n")
                    
                    f.write("\n")
        
        # FAQ
        f.write("\n## 7. 常见问答对 (前20)\n\n")
        for i, faq in enumerate(analysis_results['faq'][:20]):
            f.write(f"### 7.{i+1} {faq['question']} (频率: {faq['frequency']})\n\n")
            f.write(f"**回答**: {faq['answer']}\n\n")
            f.write(f"**意图**: {faq['intent_category']} / {faq['intent_subcategory']}\n\n")
            
            if faq['similar_questions']:
                f.write("**相似问题**:\n")
                for j, q in enumerate(faq['similar_questions'][:3]):
                    f.write(f"- {q}\n")
                
                if len(faq['similar_questions']) > 3:
                    f.write(f"- ... 还有 {len(faq['similar_questions']) - 3} 个相似问题\n")
            
            f.write("\n")
    
    print(f"分析报告已保存到: {output_dir}")


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 执行分析
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    # 加载数据
    conversations = load_data(args.input, args.limit)
    if not conversations:
        print("加载数据失败")
        return
    
    # 提取用户问题和客服回复
    user_questions = extract_user_questions(conversations)
    responses = extract_responses(conversations)
    
    # 分析意图分布
    intent_distribution = analyze_intent_distribution(user_questions)
    
    # 提取关键词
    keywords = extract_keywords(user_questions)
    
    # 聚类用户问题
    clusters = cluster_questions(user_questions)
    
    # 分析实体类型
    entity_distribution = analyze_entity_types(user_questions)
    
    # 分析问题长度
    question_length = analyze_question_length(user_questions)
    
    # 查找相似问题
    similar_questions = find_similar_questions(user_questions)
    
    # 提取FAQ
    faq = extract_faq(responses)
    
    # 整合分析结果
    analysis_results = {
        'conversation_count': len(conversations),
        'question_count': len(user_questions),
        'response_count': len(responses),
        'intent_distribution': intent_distribution,
        'keywords': keywords,
        'clusters': clusters,
        'entity_distribution': entity_distribution,
        'question_length': question_length,
        'similar_questions': [
            [q['content'] for q in group] for group in similar_questions
        ],
        'faq': faq
    }
    
    # 生成可视化图表
    visualizations_dir = os.path.join(args.output, 'visualizations')
    generate_visualizations(analysis_results, visualizations_dir)
    
    # 生成报告
    generate_reports(analysis_results, args.output)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    print("意图分析完成！")
    
    # 交互式模式
    if args.interactive:
        print("\n是否查看分析结果摘要？(y/n)")
        user_input = input()
        if user_input.lower() == 'y':
            # 显示意图分布摘要
            print("\n意图类别分布:")
            for category, percent in list(intent_distribution['categories'].items())[:5]:
                print(f"- {category}: {percent:.2f}%")
            
            print("\n常见问答对(前3个):")
            for i, faq_item in enumerate(faq[:3]):
                print(f"{i+1}. Q: {faq_item['question']}")
                print(f"   A: {faq_item['answer'][:100]}..." if len(faq_item['answer']) > 100 else f"   A: {faq_item['answer']}")
                print()


if __name__ == "__main__":
    main()

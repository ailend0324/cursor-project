#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Knowledge Base Builder Script for AI Customer Service

This script processes quality training data to extract common questions and answers,
builds a structured knowledge base in JSON format, and saves it to the specified
output directory.
"""

import os
import json
import re
import pandas as pd
from collections import Counter, defaultdict
import jieba
import jieba.posseg as pseg
from datetime import datetime

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "knowledge_base")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Constants
MIN_QUESTION_FREQUENCY = 1  # Minimum frequency for a question to be included (lowered for testing)
MIN_SOLUTION_QUALITY = 0.7  # Minimum quality score for solutions


def load_training_data(file_path):
    """Load training data from the specified JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading training data: {e}")
        return []


def extract_keywords_from_text(text):
    """Extract keywords from text using jieba."""
    if not text or not isinstance(text, str):
        return []
    
    # Cut the text using jieba for better keyword extraction
    words = pseg.cut(text)
    
    # Keep only nouns, verbs, and adjectives as keywords
    keywords = []
    for word, flag in words:
        if len(word) > 1 and flag[0] in ['n', 'v', 'a']:  # noun, verb, or adjective
            keywords.append(word)
    
    return keywords


def normalize_text(text):
    """Normalize text by removing punctuation and extra spaces."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove punctuation and normalize spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def is_question(text):
    """Determine if a text is likely a question."""
    if not text or not isinstance(text, str):
        return False
    
    # Check for question marks
    if '?' in text or '？' in text:
        return True
    
    # Check for question keywords
    question_words = ['什么', '如何', '怎么', '为什么', '哪里', '谁', '何时', 
                      '多少', '是否', '能否', '可以', '请问']
    for word in question_words:
        if word in text:
            return True
    
    return False


def extract_questions_and_answers(conversations):
    """Extract question-answer pairs from conversations."""
    qa_pairs = []
    
    for conversation in conversations:
        messages = conversation.get('messages', [])
        solution_templates = conversation.get('solution_templates', [])
        quality_score = conversation.get('quality_score', 0)
        
        if quality_score < MIN_SOLUTION_QUALITY:
            continue
        
        # Extract user questions
        user_questions = []
        for i, msg in enumerate(messages):
            if msg.get('role') == 'user' and is_question(msg.get('content', '')):
                user_questions.append({
                    'text': msg.get('content', ''),
                    'index': i
                })
        
        # Extract agent answers
        for question in user_questions:
            q_index = question['index']
            # Look for agent responses after this question
            for i in range(q_index + 1, len(messages)):
                if messages[i].get('role') == 'agent':
                    qa_pairs.append({
                        'question': question['text'],
                        'answer': messages[i].get('content', ''),
                        'solution_templates': solution_templates,
                        'quality_score': quality_score,
                        'keywords': conversation.get('keywords', [])
                    })
                    break
    
    return qa_pairs


def group_similar_questions(qa_pairs):
    """Group similar questions together."""
    # Normalize questions for better grouping
    for pair in qa_pairs:
        pair['normalized_question'] = normalize_text(pair['question'])
    
    # Count question frequencies
    question_counter = Counter([pair['normalized_question'] for pair in qa_pairs])
    
    # Group by normalized question
    question_groups = defaultdict(list)
    for pair in qa_pairs:
        norm_q = pair['normalized_question']
        if question_counter[norm_q] >= MIN_QUESTION_FREQUENCY:
            question_groups[norm_q].append(pair)
    
    return question_groups


def create_faq_entry(question_group, q_id):
    """Create a FAQ entry from a group of similar questions."""
    # Use the most common question as the standard question
    standard_question = question_group[0]['question']
    
    # Collect all unique answers
    answers = [pair['answer'] for pair in question_group]
    answer_counter = Counter(answers)
    standard_answer = answer_counter.most_common(1)[0][0]
    
    # Extract keywords from questions and answers
    all_keywords = []
    for pair in question_group:
        all_keywords.extend(pair['keywords'])
        all_keywords.extend(extract_keywords_from_text(pair['question']))
        all_keywords.extend(extract_keywords_from_text(pair['answer']))
    
    # Count keyword frequencies and select top keywords
    keyword_counter = Counter(all_keywords)
    top_keywords = [kw for kw, count in keyword_counter.most_common(10)]
    
    # Create variants of the question
    variants = list(set([pair['question'] for pair in question_group]))
    variants = [q for q in variants if q != standard_question][:5]  # Limit to 5 variants
    
    # Determine the category
    category = determine_category(question_group, top_keywords)
    
    # Create the FAQ entry
    faq = {
        "id": f"FAQ_{q_id:03d}",
        "category": category,
        "question": {
            "standard": standard_question,
            "variants": variants
        },
        "answer": {
            "standard": standard_answer,
            "keywords": top_keywords
        },
        "related_faqs": [],  # To be filled later
        "update_time": datetime.now().strftime("%Y-%m-%d")
    }
    
    return faq


def determine_category(question_group, keywords):
    """Determine the category of a question based on keywords."""
    # Category keywords mapping
    category_keywords = {
        "产品咨询类/产品功能": ["功能", "使用", "操作", "特点", "支持"],
        "产品咨询类/产品价格": ["价格", "多少钱", "估价", "报价", "预估"],
        "产品咨询类/产品使用": ["如何使用", "操作方法", "步骤", "指南"],
        "产品咨询类/产品比较": ["对比", "区别", "差异", "比较", "哪个好"],
        "服务支持类/账号问题": ["账号", "登录", "注册", "密码", "绑定"],
        "服务支持类/支付问题": ["支付", "付款", "充值", "提现", "余额"],
        "服务支持类/退款问题": ["退款", "退回", "取消", "申请退", "不想要了"],
        "服务支持类/物流问题": ["快递", "物流", "顺丰", "发货", "收货", "运费", "邮费"],
        "技术问题类/系统故障": ["故障", "错误", "问题", "异常", "失败", "打不开"],
        "技术问题类/操作指导": ["怎么操作", "如何", "步骤", "教程", "指导"],
        "技术问题类/兼容性问题": ["兼容", "支持", "版本", "适配", "系统要求"],
        "技术问题类/检测问题": ["检测", "质检", "评估", "测试", "成色", "验机"],
        "业务咨询类/合作咨询": ["合作", "加盟", "代理", "招商", "渠道"],
        "业务咨询类/商务合作": ["商务", "企业", "批量", "大客户", "定制"],
        "其他类/投诉建议": ["投诉", "意见", "建议", "不满", "差评"],
        "其他类/人工服务": ["人工", "客服", "转人工", "专员", "电话"]
    }
    
    # Score each category
    category_scores = {cat: 0 for cat in category_keywords}
    
    # Check keywords
    for kw in keywords:
        for cat, cat_keywords in category_keywords.items():
            if any(ck in kw for ck in cat_keywords) or any(kw in ck for ck in cat_keywords):
                category_scores[cat] += 1
    
    # Check question content
    for pair in question_group:
        question = pair['question']
        for cat, cat_keywords in category_keywords.items():
            if any(ck in question for ck in cat_keywords):
                category_scores[cat] += 2
    
    # Find the category with the highest score
    if max(category_scores.values()) > 0:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    
    return "其他类/其他问题"  # Default category


def find_related_faqs(faqs, num_related=3):
    """Find related FAQs based on keyword similarity."""
    for faq in faqs:
        faq_keywords = set(faq['answer']['keywords'])
        
        # Calculate similarity scores
        similarity_scores = []
        for other_faq in faqs:
            if other_faq['id'] == faq['id']:
                continue
            
            other_keywords = set(other_faq['answer']['keywords'])
            # Jaccard similarity: intersection over union
            intersection = len(faq_keywords.intersection(other_keywords))
            union = len(faq_keywords.union(other_keywords))
            
            if union > 0:
                similarity = intersection / union
            else:
                similarity = 0
                
            similarity_scores.append((other_faq['id'], similarity))
        
        # Sort by similarity and get top related FAQs
        related_faqs = [id for id, score in sorted(similarity_scores, key=lambda x: x[1], reverse=True)[:num_related]]
        faq['related_faqs'] = related_faqs
    
    return faqs


def create_template_entry(content, template_id):
    """Create a template entry from content."""
    # Determine template category and scenario
    category = "通用/其他"
    scenario = "一般回复"
    
    if "您已经进入人工服务" in content:
        category = "通用/开场白"
        scenario = "首次回复"
    elif "马上为您查询" in content:
        category = "服务支持/查询"
        scenario = "订单查询等待"
    elif "点一下【很满意】" in content or "给客服一个【很满意】的赞" in content:
        category = "通用/结束语"
        scenario = "服务结束满意度收集"
    elif "运费" in content or "邮费" in content:
        category = "服务支持/物流"
        scenario = "运费政策说明"
    elif "抱歉" in content and ("退回" in content or "退货" in content):
        category = "服务支持/退回"
        scenario = "设备退回道歉"
    
    template = {
        "id": f"TEMP_{template_id:03d}",
        "category": category,
        "scenario": scenario,
        "content": content,
        "variables": [],
        "usage_tips": f"用于{scenario}场景的标准回复",
        "update_time": datetime.now().strftime("%Y-%m-%d")
    }
    
    return template


def extract_solution_templates(qa_pairs):
    """Extract common solution templates from QA pairs."""
    all_templates = []
    for pair in qa_pairs:
        if 'solution_templates' in pair:
            all_templates.extend(pair['solution_templates'])
    
    # Count template frequencies
    template_counter = Counter(all_templates)
    
    # Select common templates
    common_templates = []
    for i, (template, count) in enumerate(template_counter.most_common(50)):
        if count >= MIN_QUESTION_FREQUENCY and len(template) > 10:
            common_templates.append(create_template_entry(template, i+1))
    
    return common_templates


def save_knowledge_base(faqs, templates):
    """Save the knowledge base to JSON files."""
    # Save FAQs
    faq_path = os.path.join(OUTPUT_DIR, "faqs.json")
    with open(faq_path, 'w', encoding='utf-8') as f:
        json.dump(faqs, f, ensure_ascii=False, indent=2)
    
    # Save templates
    template_path = os.path.join(OUTPUT_DIR, "templates.json")
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)
    
    print(f"Knowledge base saved to {OUTPUT_DIR}")
    print(f"- {len(faqs)} FAQs saved to {faq_path}")
    print(f"- {len(templates)} templates saved to {template_path}")


def main():
    """Main function to build the knowledge base."""
    print("Building knowledge base...")
    
    # Load training data
    # For testing, use the sample file instead of the full one
    training_data_path = os.path.join(DATA_DIR, "raw", "quality_training_data_sample.json")
    if not os.path.exists(training_data_path):
        print(f"Error: Training data file not found at {training_data_path}")
        return
    
    training_data = load_training_data(training_data_path)
    print(f"Loaded {len(training_data)} conversations from training data")
    
    # Extract question-answer pairs
    qa_pairs = extract_questions_and_answers(training_data)
    print(f"Extracted {len(qa_pairs)} question-answer pairs")
    
    # Group similar questions
    question_groups = group_similar_questions(qa_pairs)
    print(f"Grouped into {len(question_groups)} unique questions")
    
    # Create FAQ entries
    faqs = []
    for i, (norm_q, group) in enumerate(question_groups.items()):
        faq = create_faq_entry(group, i+1)
        faqs.append(faq)
    
    # Find related FAQs
    faqs = find_related_faqs(faqs)
    
    # Extract templates
    templates = extract_solution_templates(qa_pairs)
    print(f"Extracted {len(templates)} common templates")
    
    # Save knowledge base
    save_knowledge_base(faqs, templates)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Knowledge Base Query Script for AI Customer Service

This script provides functions to query the knowledge base and find appropriate
answers for customer questions. It uses keyword matching and text similarity to find
the most relevant FAQ entries or templates.
"""

import os
import json
import re
import jieba
import difflib
from collections import Counter

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_BASE_DIR = os.path.join(PROJECT_ROOT, "knowledge_base")

# Constants
SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score for a match (lowered for testing)
TOP_N_RESULTS = 3  # Number of top results to return


def load_knowledge_base():
    """Load the knowledge base from JSON files."""
    faqs = []
    templates = []
    
    try:
        # Load FAQs
        faq_path = os.path.join(KNOWLEDGE_BASE_DIR, "faqs.json")
        if os.path.exists(faq_path):
            with open(faq_path, 'r', encoding='utf-8') as f:
                faqs = json.load(f)
        
        # Load templates
        template_path = os.path.join(KNOWLEDGE_BASE_DIR, "templates.json")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        
        print(f"Loaded {len(faqs)} FAQs and {len(templates)} templates")
        return faqs, templates
    
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        return [], []


def preprocess_text(text):
    """Preprocess text for better matching."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove punctuation and normalize spaces
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def extract_keywords(text):
    """Extract keywords from text."""
    if not text or not isinstance(text, str):
        return []
    
    # Cut the text using jieba for better keyword extraction
    words = jieba.cut(text)
    
    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 1]
    return keywords


def calculate_keyword_similarity(query_keywords, target_keywords):
    """Calculate similarity based on keyword overlap."""
    if not query_keywords or not target_keywords:
        return 0
    
    query_set = set(query_keywords)
    target_set = set(target_keywords)
    
    # Calculate Jaccard similarity (intersection over union)
    intersection = len(query_set.intersection(target_set))
    union = len(query_set.union(target_set))
    
    if union > 0:
        return intersection / union
    return 0


def calculate_text_similarity(text1, text2):
    """Calculate text similarity using difflib."""
    if not text1 or not text2:
        return 0
    
    # Use difflib's SequenceMatcher to calculate similarity
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def find_matching_faqs(query, faqs):
    """Find FAQs matching the query."""
    if not query or not faqs:
        return []
    
    # Preprocess query
    processed_query = preprocess_text(query)
    query_keywords = extract_keywords(processed_query)
    
    # Calculate similarity scores for each FAQ
    scores = []
    for faq in faqs:
        # Get standard question and variants
        standard_question = faq['question']['standard']
        variants = faq['question'].get('variants', [])
        keywords = faq['answer'].get('keywords', [])
        
        # Calculate similarity with standard question
        standard_sim = calculate_text_similarity(processed_query, preprocess_text(standard_question))
        
        # Calculate similarity with variants
        variant_sims = [calculate_text_similarity(processed_query, preprocess_text(var)) for var in variants]
        best_variant_sim = max(variant_sims) if variant_sims else 0
        
        # Calculate keyword similarity
        keyword_sim = calculate_keyword_similarity(query_keywords, keywords)
        
        # Check for partial keyword matches (improves recall)
        partial_keyword_match = 0
        for q_kw in query_keywords:
            for kw in keywords:
                if q_kw in kw or kw in q_kw:
                    partial_keyword_match = max(partial_keyword_match, 0.5)
        
        # Check for keyword presence in question/answer
        keyword_in_qa = 0
        for q_kw in query_keywords:
            if q_kw in standard_question.lower() or any(q_kw in var.lower() for var in variants):
                keyword_in_qa = max(keyword_in_qa, 0.6)
        
        # Combine scores (weighted average)
        combined_score = 0.3 * max(standard_sim, best_variant_sim) + \
                         0.3 * keyword_sim + \
                         0.2 * partial_keyword_match + \
                         0.2 * keyword_in_qa
        
        # Boost score for exact keyword matches
        for q_kw in query_keywords:
            if q_kw in keywords:
                combined_score += 0.1
                break
        
        scores.append((faq, combined_score))
    
    # Sort by score and filter by threshold
    sorted_results = sorted(scores, key=lambda x: x[1], reverse=True)
    filtered_results = [(faq, score) for faq, score in sorted_results if score >= SIMILARITY_THRESHOLD]
    
    # Return top N results
    return filtered_results[:TOP_N_RESULTS]


def find_related_templates(category, templates):
    """Find templates related to a specific category."""
    if not category or not templates:
        return []
    
    # Find templates in the same category
    matching_templates = []
    
    # Extract main category (before the slash)
    main_category = category.split('/')[0] if '/' in category else category
    
    for template in templates:
        template_category = template.get('category', '')
        
        # Check if the template belongs to the same main category
        if main_category in template_category:
            matching_templates.append(template)
    
    return matching_templates


def suggest_answer(query):
    """Suggest an answer for the given query."""
    # Load knowledge base
    faqs, templates = load_knowledge_base()
    
    if not faqs:
        return {
            "success": False,
            "message": "Knowledge base is empty or could not be loaded",
            "results": []
        }
    
    # Find matching FAQs
    matching_faqs = find_matching_faqs(query, faqs)
    
    if not matching_faqs:
        return {
            "success": True,
            "message": "No matching FAQs found",
            "results": []
        }
    
    # Prepare results
    results = []
    for faq, score in matching_faqs:
        # Find related templates for the FAQ category
        related_templates = find_related_templates(faq.get('category', ''), templates)
        
        result = {
            "faq": faq,
            "confidence": round(score, 4),
            "related_templates": related_templates[:2]  # Limit to 2 related templates
        }
        results.append(result)
    
    return {
        "success": True,
        "message": f"Found {len(results)} matching FAQs",
        "results": results
    }


def format_answer(result):
    """Format the answer result for display."""
    if not result or not result.get('success', False):
        return "抱歉，我无法找到相关的回答。请提供更多信息或联系人工客服。"
    
    if not result.get('results', []):
        return "抱歉，我没有找到与您问题匹配的答案。请尝试用不同的方式描述您的问题，或联系人工客服获取帮助。"
    
    # Get the best match
    best_match = result['results'][0]
    faq = best_match['faq']
    confidence = best_match['confidence']
    
    # Format the answer
    answer = faq['answer']['standard']
    
    # Reformat the answer for "how to" questions when confidence is low
    if confidence < 0.5:
        question = faq['question']['standard']
        if "如何" in question or "怎么" in question or "申请" in question:
            answer = f"如果您想{question.replace('如何', '').replace('？', '')}，{answer}"
    
    # If confidence is low, add a disclaimer
    if confidence < 0.75:
        answer += "\n\n(注：以上回答可能不完全符合您的问题，如有疑问，请联系人工客服)"
    
    # Add related questions if available
    if len(result['results']) > 1:
        related_questions = [res['faq']['question']['standard'] for res in result['results'][1:]]
        if related_questions:
            answer += "\n\n您可能还想了解：\n"
            for i, question in enumerate(related_questions, 1):
                answer += f"{i}. {question}\n"
    
    return answer


def interactive_mode():
    """Run the script in interactive mode."""
    print("欢迎使用回收宝AI客服知识库查询系统")
    print("输入您的问题，系统将为您提供回答。输入'退出'或'exit'结束对话。")
    print("-" * 50)
    
    # Load knowledge base
    faqs, templates = load_knowledge_base()
    
    if not faqs:
        print("错误：知识库为空或无法加载")
        return
    
    while True:
        # Get user input
        user_input = input("\n请输入您的问题: ")
        
        # Check for exit command
        if user_input.lower() in ['退出', 'exit', 'quit', 'q']:
            print("谢谢使用，再见！")
            break
        
        # Get answer suggestion
        result = suggest_answer(user_input)
        
        # Format and display the answer
        formatted_answer = format_answer(result)
        print("\n回答:", formatted_answer)
        print("-" * 50)


if __name__ == "__main__":
    interactive_mode()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识提取脚本
功能：从分析结果中提取和构建FAQ知识库
用法：python extract_knowledge.py --input <analysis_dir> --output <faq_output_path>
"""

import argparse
import json
import os
import re
import uuid
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='从分析结果中提取和构建FAQ知识库')
    parser.add_argument('--input', required=True, help='分析结果目录路径')
    parser.add_argument('--output', required=True, help='FAQ知识库输出路径')
    return parser.parse_args()


def generate_faq_id(category):
    """
    生成FAQ ID
    
    参数:
        category: 问题分类
    
    返回:
        str: FAQ ID
    """
    # 提取分类的首字母
    category_code = ''.join([word[0].upper() for word in re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', category)])
    # 生成唯一ID
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"FAQ_{category_code}_{unique_id}"


def extract_keywords_from_question(question):
    """
    从问题中提取关键词
    
    参数:
        question: 问题文本
    
    返回:
        list: 关键词列表
    """
    # 简单实现，实际项目中可使用更复杂的算法
    # 移除标点符号
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', question)
    # 分词并去重
    words = cleaned.split()
    # 过滤掉停用词和过短的词
    keywords = [word for word in words if len(word) > 1]
    # 取最多5个关键词
    return list(set(keywords))[:5]


def build_faq_item(question, variants, category):
    """
    构建FAQ条目
    
    参数:
        question: 标准问题
        variants: 问题变体
        category: 问题分类
    
    返回:
        dict: FAQ条目
    """
    # 生成FAQ ID
    faq_id = generate_faq_id(category)
    
    # 提取关键词
    keywords = extract_keywords_from_question(question)
    
    # 构建FAQ条目
    faq_item = {
        "id": faq_id,
        "category": category,
        "question": {
            "standard": question,
            "variants": variants[:5]  # 最多保留5个变体
        },
        "answer": {
            "standard": "",  # 暂时留空，需要人工填写
            "keywords": keywords
        },
        "related_faqs": [],  # 暂时留空，需要后续处理
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.now().strftime("%Y-%m-%d")
    }
    
    return faq_item


def build_knowledge_base(analysis_dir, output_path):
    """
    构建知识库
    
    参数:
        analysis_dir: 分析结果目录
        output_path: 输出文件路径
    
    返回:
        bool: 是否成功
    """
    try:
        # 读取FAQ候选项
        faq_candidates_path = os.path.join(analysis_dir, 'faq_candidates.json')
        if not os.path.exists(faq_candidates_path):
            print(f"错误: FAQ候选项文件不存在: {faq_candidates_path}")
            return False
        
        with open(faq_candidates_path, 'r', encoding='utf-8') as f:
            faq_candidates = json.load(f)
        
        # 构建知识库
        knowledge_base = []
        
        # 处理每个分类
        for category, candidates in faq_candidates.items():
            # 细分类别
            if '/' not in category:
                # 为主分类添加子分类
                subcategories = {
                    '订单查询': ['订单查询/订单状态', '订单查询/订单详情', '订单查询/订单历史'],
                    '物流配送': ['物流配送/配送进度', '物流配送/配送方式', '物流配送/包装要求'],
                    '价格咨询': ['价格咨询/估价查询', '价格咨询/价格波动', '价格咨询/加价服务'],
                    '回收流程': ['回收流程/邮寄回收', '回收流程/上门回收', '回收流程/到店回收'],
                    '验货检测': ['验货检测/检测流程', '验货检测/检测标准', '验货检测/检测结果'],
                    '支付结算': ['支付结算/支付方式', '支付结算/打款时间', '支付结算/账户问题'],
                    '账号问题': ['账号问题/注册登录', '账号问题/账户安全', '账号问题/个人信息'],
                    '售后服务': ['售后服务/退货政策', '售后服务/争议处理', '售后服务/投诉建议'],
                    '产品咨询': ['产品咨询/产品功能', '产品咨询/产品规格', '产品咨询/产品比较'],
                    '其他问题': ['其他问题/系统故障', '其他问题/活动咨询', '其他问题/其他']
                }
                
                if category in subcategories:
                    # 为每个候选项分配子分类
                    for i, candidate in enumerate(candidates):
                        # 轮流分配子分类
                        subcategory = subcategories[category][i % len(subcategories[category])]
                        faq_item = build_faq_item(
                            candidate['question'],
                            candidate.get('variants', []),
                            subcategory
                        )
                        knowledge_base.append(faq_item)
                else:
                    # 使用主分类
                    for candidate in candidates:
                        faq_item = build_faq_item(
                            candidate['question'],
                            candidate.get('variants', []),
                            category
                        )
                        knowledge_base.append(faq_item)
            else:
                # 已有子分类
                for candidate in candidates:
                    faq_item = build_faq_item(
                        candidate['question'],
                        candidate.get('variants', []),
                        category
                    )
                    knowledge_base.append(faq_item)
        
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存知识库
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
        print(f"知识库构建完成，共{len(knowledge_base)}个FAQ条目，已保存到: {output_path}")
        return True
    
    except Exception as e:
        print(f"知识库构建过程中出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入目录不存在: {args.input}")
        return
    
    # 执行知识提取
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    success = build_knowledge_base(args.input, args.output)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("知识库构建成功！")
        print("注意: FAQ答案部分需要人工填写或进一步处理。")
    else:
        print("知识库构建失败！")


if __name__ == "__main__":
    main()

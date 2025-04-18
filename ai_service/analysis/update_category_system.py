#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新问题分类系统
根据聚类分析结果，更新问题分类系统中的关键词和分类
"""

import os
import pandas as pd
import re
import json
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_clustered_data():
    """加载聚类后的问题数据"""
    file_path = os.path.join(PROJECT_ROOT, 'analysis', 'clustered_questions.xlsx')
    try:
        df = pd.read_excel(file_path)
        print(f"成功加载聚类数据，共{len(df)}条记录")
        return df
    except Exception as e:
        print(f"无法加载聚类数据: {e}")
        return None

def load_current_categories():
    """加载当前的问题分类系统"""
    # 从analyze_chat_data.py中提取当前的分类关键词
    analyze_script_path = os.path.join(PROJECT_ROOT, 'analysis', 'analyze_chat_data.py')
    try:
        with open(analyze_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
            
        # 使用正则表达式提取CATEGORY_KEYWORDS字典
        pattern = r"CATEGORY_KEYWORDS\s*=\s*\{([\s\S]*?)\}"
        match = re.search(pattern, script_content)
        
        if not match:
            print("无法找到CATEGORY_KEYWORDS定义，将创建新的分类系统")
            return {}
        
        # 解析提取的字典内容
        dict_content = match.group(1)
        
        # 将提取的字符串转换为Python代码，然后执行
        dict_code = "{" + dict_content + "}"
        try:
            # 这里使用eval，仅用于开发目的，生产环境中应避免
            categories = eval(dict_code)
            print(f"成功加载当前分类系统，包含{len(categories)}个分类")
            return categories
        except Exception as e:
            print(f"解析分类关键词失败: {e}")
            return {}
            
    except Exception as e:
        print(f"读取analyze_chat_data.py时出错: {e}")
        return {}

def analyze_clusters(df):
    """分析聚类，为每个聚类提取关键信息"""
    clusters = df['cluster'].unique()
    cluster_info = {}
    
    for cluster_id in clusters:
        cluster_data = df[df['cluster'] == cluster_id]
        
        # 提取该聚类中最常见的词
        # 这里简化处理，实际中可以使用更复杂的TF-IDF或词频分析
        all_words = []
        for text in cluster_data['processed_text']:
            if isinstance(text, str):
                all_words.extend(text.split())
                
        word_counts = {}
        for word in all_words:
            if len(word) > 1:  # 忽略单个字符
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        top_words = [word for word, _ in sorted_words[:10]]
        
        # 获取代表性问题示例
        examples = cluster_data['send_content'].sample(min(5, len(cluster_data))).tolist()
        
        cluster_info[cluster_id] = {
            'size': len(cluster_data),
            'top_words': top_words,
            'examples': examples
        }
    
    return cluster_info

def suggest_category_names(cluster_info):
    """根据聚类信息建议分类名称"""
    predefined_categories = {
        '咨询类': ['什么', '如何', '可以', '能', '多少', '怎么'],
        '投诉类': ['不好', '问题', '差', '退', '赔', '投诉'],
        '反馈类': ['建议', '希望', '反馈', '评价', '感觉', '觉得'],
        '感谢类': ['谢谢', '感谢', '好的', '非常好', '满意', '赞'],
        '疑问类': ['为什么', '是否', '可不可以', '能不能', '吗', '呢'],
        '预约类': ['预约', '什么时候', '约', '时间', '几点', '安排'],
        '操作指导类': ['怎么操作', '步骤', '流程', '指导', '教程', '使用方法']
    }
    
    suggested_names = {}
    
    for cluster_id, info in cluster_info.items():
        best_match = None
        best_score = 0
        
        for category, keywords in predefined_categories.items():
            score = 0
            for word in info['top_words']:
                if word in keywords:
                    score += 1
            
            # 检查示例问题中是否包含关键词
            for example in info['examples']:
                if isinstance(example, str):
                    for keyword in keywords:
                        if keyword in example:
                            score += 0.5
            
            if score > best_score:
                best_score = score
                best_match = category
        
        # 如果没有良好匹配，使用通用名称
        if best_score < 1:
            best_match = f"未识别类型{cluster_id}"
        
        suggested_names[cluster_id] = best_match
    
    return suggested_names

def generate_updated_categories(current_categories, cluster_info, suggested_names):
    """生成更新后的分类系统"""
    updated_categories = current_categories.copy()
    
    # 为每个有建议名称的聚类创建或更新分类
    for cluster_id, category_name in suggested_names.items():
        # 如果是现有分类，合并关键词
        if category_name in updated_categories:
            current_keywords = set(updated_categories[category_name])
            new_keywords = set(cluster_info[cluster_id]['top_words'][:5])  # 取前5个词
            merged_keywords = list(current_keywords.union(new_keywords))
            updated_categories[category_name] = merged_keywords
        else:
            # 创建新分类
            updated_categories[category_name] = cluster_info[cluster_id]['top_words'][:5]  # 取前5个词
    
    return updated_categories

def update_analysis_script(updated_categories):
    """更新分析脚本中的分类系统"""
    analyze_script_path = os.path.join(PROJECT_ROOT, 'analysis', 'analyze_chat_data.py')
    
    try:
        with open(analyze_script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # 格式化更新后的分类字典为字符串
        categories_str = "CATEGORY_KEYWORDS = {\n"
        for category, keywords in updated_categories.items():
            keywords_str = "', '".join(keywords)
            categories_str += f"    '{category}': ['{keywords_str}'],\n"
        categories_str += "}\n"
        
        # 替换原始分类字典
        updated_content = re.sub(
            r"CATEGORY_KEYWORDS\s*=\s*\{[\s\S]*?\}", 
            categories_str, 
            script_content
        )
        
        # 写回文件
        with open(analyze_script_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"成功更新分析脚本中的分类系统，现在包含{len(updated_categories)}个分类")
        return True
    except Exception as e:
        print(f"更新分析脚本时出错: {e}")
        return False

def save_category_documentation(updated_categories, suggested_names, cluster_info):
    """更新问题分类文档"""
    doc_path = os.path.join(PROJECT_ROOT, 'analysis', 'question_categories.md')
    
    try:
        # 读取现有文档
        if os.path.exists(doc_path):
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
        else:
            doc_content = "# 问题分类体系\n\n## 分类框架\n\n"
        
        # 添加更新日志
        update_section = f"\n## 分类更新记录\n\n"
        update_section += f"### {pd.Timestamp.now().strftime('%Y-%m-%d')} 更新\n\n"
        
        # 添加聚类发现的新分类
        new_categories = {}
        updated_old_categories = {}
        
        for cluster_id, category_name in suggested_names.items():
            if category_name in set(current_categories.keys()):
                updated_old_categories[category_name] = {
                    'new_words': set(cluster_info[cluster_id]['top_words'][:5]),
                    'examples': cluster_info[cluster_id]['examples'][:2]
                }
            else:
                new_categories[category_name] = {
                    'keywords': cluster_info[cluster_id]['top_words'][:5],
                    'examples': cluster_info[cluster_id]['examples'][:2]
                }
        
        # 记录新增分类
        if new_categories:
            update_section += "#### 新增分类\n\n"
            for category, info in new_categories.items():
                update_section += f"- **{category}**\n"
                update_section += f"  - 关键词: {', '.join(info['keywords'])}\n"
                update_section += f"  - 示例问题:\n"
                for example in info['examples']:
                    if isinstance(example, str):
                        update_section += f"    - {example}\n"
                update_section += "\n"
        
        # 记录更新的分类
        if updated_old_categories:
            update_section += "#### 更新分类\n\n"
            for category, info in updated_old_categories.items():
                update_section += f"- **{category}**\n"
                update_section += f"  - 新增关键词: {', '.join(info['new_words'])}\n"
                update_section += "\n"
        
        # 更新当前分类体系部分
        categories_section = "\n## 当前分类体系\n\n"
        categories_section += "| 分类名称 | 关键词 | 示例问题 |\n"
        categories_section += "|---------|--------|----------|\n"
        
        for category, keywords in updated_categories.items():
            # 获取示例问题
            examples = []
            for cluster_id, name in suggested_names.items():
                if name == category and cluster_id in cluster_info:
                    examples = cluster_info[cluster_id]['examples'][:1]
                    break
            
            example_str = " " if not examples else examples[0] if isinstance(examples[0], str) else ""
            keywords_str = ", ".join(keywords[:5])  # 限制显示的关键词数量
            categories_section += f"| {category} | {keywords_str} | {example_str} |\n"
        
        # 组合文档
        # 检查是否已有"当前分类体系"部分
        if "## 当前分类体系" in doc_content:
            # 替换现有的分类体系部分
            doc_content = re.sub(
                r"## 当前分类体系[\s\S]*?(?=##|$)", 
                categories_section, 
                doc_content
            )
        else:
            # 添加到文档末尾
            doc_content += categories_section
        
        # 添加更新记录
        if "## 分类更新记录" in doc_content:
            # 在现有更新记录之后添加新记录
            pattern = r"(## 分类更新记录\n\n)"
            doc_content = re.sub(pattern, r"\1" + update_section.replace("## 分类更新记录\n\n", ""), doc_content)
        else:
            # 在文档末尾添加更新记录
            doc_content += "\n" + update_section
        
        # 写回文件
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        print(f"成功更新问题分类文档: {doc_path}")
        return True
    except Exception as e:
        print(f"更新问题分类文档时出错: {e}")
        return False

def export_to_json(updated_categories):
    """将更新后的分类系统导出为JSON文件"""
    json_path = os.path.join(PROJECT_ROOT, 'analysis', 'category_keywords.json')
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_categories, f, ensure_ascii=False, indent=2)
        print(f"成功导出分类系统到JSON文件: {json_path}")
        return True
    except Exception as e:
        print(f"导出JSON文件时出错: {e}")
        return False

def main():
    print("开始更新问题分类系统...")
    
    # 1. 加载聚类数据
    clustered_df = load_clustered_data()
    if clustered_df is None or len(clustered_df) == 0:
        print("没有可用的聚类数据，请先运行聚类分析")
        return
    
    # 2. 加载当前分类系统
    global current_categories
    current_categories = load_current_categories()
    
    # 3. 分析聚类
    cluster_info = analyze_clusters(clustered_df)
    print(f"分析了{len(cluster_info)}个聚类")
    
    # 4. 为聚类建议分类名称
    suggested_names = suggest_category_names(cluster_info)
    print("已为聚类生成建议分类名称:")
    for cluster_id, name in suggested_names.items():
        print(f"聚类 {cluster_id} -> {name}")
    
    # 5. 生成更新后的分类系统
    updated_categories = generate_updated_categories(current_categories, cluster_info, suggested_names)
    print(f"更新后的分类系统包含{len(updated_categories)}个分类")
    
    # 6. 更新分析脚本
    update_analysis_script(updated_categories)
    
    # 7. 更新分类文档
    save_category_documentation(updated_categories, suggested_names, cluster_info)
    
    # 8. 导出为JSON
    export_to_json(updated_categories)
    
    print("问题分类系统更新完成！")

if __name__ == "__main__":
    main() 
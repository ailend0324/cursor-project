import json
import pandas as pd
from collections import Counter
import jieba
import re

def load_processed_data():
    """加载处理后的对话数据"""
    with open('customer_service_data/data/processed/conversations.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(text):
    """提取关键词"""
    # 使用结巴分词
    words = jieba.cut(text)
    # 过滤停用词和特殊字符
    words = [w for w in words if len(w) > 1 and not re.match(r'[^\w\s]', w)]
    return words

def analyze_conversations(conversations):
    """分析对话内容"""
    # 统计数据
    stats = {
        'total_conversations': len(conversations),
        'avg_messages_per_conv': [],
        'common_topics': Counter(),
        'response_patterns': [],
        'group_distribution': Counter()
    }
    
    # 分析每个对话
    for conv_id, conv in conversations.items():
        # 统计每个对话的消息数
        stats['avg_messages_per_conv'].append(len(conv['dialogue']))
        
        # 统计分组分布
        stats['group_distribution'][conv['group_name']] += 1
        
        # 分析对话内容
        user_messages = []
        service_messages = []
        
        for msg in conv['dialogue']:
            if msg['sender_type'] == 'user':
                user_messages.append(msg['content'])
            else:
                service_messages.append(msg['content'])
        
        # 提取用户问题关键词
        for msg in user_messages:
            if msg:
                keywords = extract_keywords(str(msg))
                stats['common_topics'].update(keywords)
    
    # 计算平均值
    stats['avg_messages_per_conv'] = sum(stats['avg_messages_per_conv']) / len(stats['avg_messages_per_conv'])
    
    return stats

def print_analysis(stats):
    """打印分析结果"""
    print("\n=== 对话数据分析 ===")
    print(f"总对话数: {stats['total_conversations']}")
    print(f"平均每个对话消息数: {stats['avg_messages_per_conv']:.2f}")
    
    print("\n最常见的话题关键词 (top 20):")
    for word, count in stats['common_topics'].most_common(20):
        print(f"  {word}: {count}")
    
    print("\n分组分布:")
    for group, count in stats['group_distribution'].most_common():
        print(f"  {group}: {count}")

def main():
    # 加载数据
    conversations = load_processed_data()
    
    # 分析数据
    stats = analyze_conversations(conversations)
    
    # 打印分析结果
    print_analysis(stats)
    
    # 保存分析结果
    with open('customer_service_data/data/processed/analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

if __name__ == "__main__":
    main() 
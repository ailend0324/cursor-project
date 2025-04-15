import json
import re
from collections import defaultdict
from datetime import datetime

# 定义分类关键词
KEYWORDS = {
    'business_type': {
        '邮寄回收': ['邮寄', '快递', '包装', '寄件', '收件', '顺丰', '物流', '包邮'],
        '验货服务': ['验机', '检测', '评估', '质检', '验货', '实际情况', '验机报告'],
        '上门到店': ['上门', '到店', '预约', '地址', '时间', '专员'],
        '帮卖服务': ['帮卖', '鱼市', '转卖', '寄卖', '卖出价格'],
        '黄金回收': ['黄金', '金饰', '金条', '金币']
    },
    'intent': {
        '价格咨询': ['多少钱', '报价', '价格', '价值', '估价', '预估价', '心理价', '抬价'],
        '进度查询': ['进度', '到哪', '收到', '查询', '状态', '核实', '催促'],
        '预约服务': ['预约', '约时间', '什么时候', '可以来', '等待专员'],
        '投诉处理': ['投诉', '不满意', '问题', '差评', '退款', '差别', '不合理'],
        '售后服务': ['售后', '保修', '维修', '换货', '退货', '退回', '原路退回']
    }
}

def extract_keywords(text):
    """提取文本中的关键词"""
    keywords = []
    text = str(text).lower()
    for category in KEYWORDS.values():
        for label, words in category.items():
            for word in words:
                if word in text:
                    keywords.append(word)
    return keywords

def classify_message(text, category):
    """根据关键词对消息进行分类"""
    text = str(text).lower()
    scores = defaultdict(int)
    
    for label, keywords in KEYWORDS[category].items():
        for keyword in keywords:
            if keyword in text:
                scores[label] += 1
    
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    return '其他'

def analyze_conversation_flow(messages):
    """分析对话流程和结果"""
    # 简单的结果判断逻辑
    last_messages = messages[-3:] if len(messages) >= 3 else messages
    text = ' '.join(str(msg['content']) for msg in last_messages)
    
    if any(word in text for word in ['谢谢', '感谢', '再见', '好的', '辛苦了']):
        return '已解决'
    elif any(word in text for word in ['转接', '转给', '专员会']):
        return '转介绍'
    elif any(word in text for word in ['等待', '稍后', '回复', '催促']):
        return '待处理'
    else:
        return '未解决'

def classify_conversations(conversations):
    """对对话进行分类和标注"""
    classified_data = []
    
    for conv_id, conv in conversations.items():
        # 合并所有消息
        all_messages = ' '.join(
            str(msg['content']) 
            for msg in conv['dialogue']
        )
        
        # 计算持续时间
        try:
            start_time = datetime.fromisoformat(conv['start_time'].replace('Z', '+00:00')) if 'start_time' in conv else None
            end_time = datetime.fromisoformat(conv['end_time'].replace('Z', '+00:00')) if 'end_time' in conv else None
            duration = (end_time - start_time).total_seconds() if start_time and end_time else None
        except (ValueError, TypeError):
            duration = None
        
        # 提取关键词
        keywords = extract_keywords(all_messages)
        
        # 分类
        classification = {
            'conversation_id': conv_id,
            'business_type': classify_message(all_messages, 'business_type'),
            'primary_intent': classify_message(all_messages, 'intent'),
            'status': analyze_conversation_flow(conv['dialogue']),
            'group_name': conv['group_name'],
            'duration': duration,
            'message_count': len(conv['dialogue']),
            'keywords': keywords
        }
        
        classified_data.append(classification)
    
    return classified_data

def main():
    # 加载处理后的对话数据
    with open('customer_service_data/data/processed/conversations.json', 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    # 对对话进行分类
    classified_data = classify_conversations(conversations)
    
    # 保存分类结果
    with open('customer_service_data/data/processed/classified_conversations.json', 'w', encoding='utf-8') as f:
        json.dump(classified_data, f, ensure_ascii=False, indent=2, default=str)
    
    # 打印分类统计
    stats = defaultdict(lambda: defaultdict(int))
    for conv in classified_data:
        stats['business_type'][conv['business_type']] += 1
        stats['intent'][conv['primary_intent']] += 1
        stats['status'][conv['status']] += 1
    
    print("\n=== 分类统计 ===")
    for category, counts in stats.items():
        print(f"\n{category}分布:")
        total = sum(counts.values())
        for label, count in counts.items():
            percentage = (count / total) * 100
            print(f"  {label}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    main() 
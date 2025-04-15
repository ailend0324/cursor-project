import json
import random

def analyze_sample_conversations(conversations, sample_size=5):
    """分析样本对话内容"""
    # 随机选择样本对话
    sample_ids = random.sample(list(conversations.keys()), sample_size)
    
    for conv_id in sample_ids:
        conv = conversations[conv_id]
        print(f"\n=== 对话 ID: {conv_id} ===")
        print(f"分组: {conv['group_name']}")
        print("对话内容:")
        
        for msg in conv['dialogue']:
            sender = "用户" if msg['sender_type'] == 'user' else "客服"
            content = str(msg['content']).replace('\n', ' ')
            print(f"{sender}: {content}")
        
        print("-" * 80)

def main():
    # 加载处理后的对话数据
    with open('customer_service_data/data/processed/conversations.json', 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    # 分析样本对话
    analyze_sample_conversations(conversations, sample_size=5)

if __name__ == "__main__":
    main() 
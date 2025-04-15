import json
from datetime import datetime
import re

def clean_message_content(content):
    """清理消息内容，移除HTML标签和特殊字符"""
    # 移除HTML标签
    content = re.sub(r'<[^>]+>', '', str(content))
    # 移除图片链接
    content = re.sub(r'https?://\S+', '', content)
    # 移除多余空白
    content = re.sub(r'\s+', ' ', content).strip()
    return content

def extract_solution_template(messages):
    """提取解决方案模板"""
    templates = []
    for msg in messages:
        if msg['sender_type'] != 'user':
            content = clean_message_content(msg['content'])
            if len(content) > 10 and not content.startswith('亲亲') and not content.startswith('订单号'):
                templates.append(content)
    return templates

def format_conversation(conv_id, conv, classification):
    """格式化对话数据"""
    messages = []
    for msg in conv['dialogue']:
        content = clean_message_content(msg['content'])
        if content:  # 只保留非空消息
            messages.append({
                "role": "user" if msg['sender_type'] == 'user' else "agent",
                "content": content,
                "timestamp": msg['send_time']
            })
    
    # 提取解决方案模板
    solution_templates = extract_solution_template(conv['dialogue'])
    
    return {
        "id": conv_id,
        "metadata": {
            "business_type": classification['business_type'],
            "primary_intent": classification['primary_intent'],
            "status": classification['status'],
            "duration": classification['duration'],
            "message_count": classification['message_count'],
            "group_name": classification['group_name']
        },
        "messages": messages,
        "keywords": classification['keywords'],
        "solution_templates": solution_templates
    }

def main():
    # 加载分类数据
    with open('customer_service_data/data/processed/classified_conversations.json', 'r', encoding='utf-8') as f:
        classified_data = json.load(f)
    
    # 加载原始对话数据
    with open('customer_service_data/data/processed/conversations.json', 'r', encoding='utf-8') as f:
        conversations = json.load(f)
    
    # 生成训练数据
    training_data = {
        "metadata": {
            "total_conversations": len(classified_data),
            "generated_at": datetime.now().isoformat(),
            "version": "1.0"
        },
        "conversations": []
    }
    
    # 格式化每个对话
    for conv in classified_data:
        conv_id = conv['conversation_id']
        if conv_id in conversations:
            formatted_conv = format_conversation(conv_id, conversations[conv_id], conv)
            training_data['conversations'].append(formatted_conv)
    
    # 保存训练数据
    with open('customer_service_data/data/final/training_data.json', 'w', encoding='utf-8') as f:
        json.dump(training_data, f, ensure_ascii=False, indent=2)
    
    print(f"生成了 {len(training_data['conversations'])} 个训练样本")
    
    # 输出一个样本示例
    if training_data['conversations']:
        print("\n=== 样本示例 ===")
        sample = training_data['conversations'][0]
        print(f"ID: {sample['id']}")
        print(f"业务类型: {sample['metadata']['business_type']}")
        print(f"主要意图: {sample['metadata']['primary_intent']}")
        print(f"状态: {sample['metadata']['status']}")
        print("\n前3条消息:")
        for msg in sample['messages'][:3]:
            print(f"{msg['role']}: {msg['content']}")

if __name__ == "__main__":
    main() 
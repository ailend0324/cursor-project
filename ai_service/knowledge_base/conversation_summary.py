import os
import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import jieba.analyse
from collections import Counter

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_data(excel_path):
    """加载Excel数据文件"""
    try:
        print(f"正在加载数据: {excel_path}")
        df = pd.read_excel(excel_path)
        print(f"成功加载 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def load_faq_data():
    """加载FAQ数据"""
    faq_path = os.path.join(PROJECT_ROOT, 'knowledge_base', 'faq.json')
    try:
        with open(faq_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载FAQ数据失败: {e}")
        return []

def preprocess_text(text):
    """预处理文本"""
    if not isinstance(text, str):
        return ""
    
    # 去除URL
    text = re.sub(r'http\S+', '', text)
    # 去除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, top_n=5):
    """提取文本关键词"""
    if not text or len(text) < 5:
        return []
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_n)
    return keywords

def group_messages_by_conversation(df):
    """按对话分组消息"""
    conversations = {}
    
    # 确保数据按对话ID和时间戳排序
    df = df.sort_values(['touch_id', 'timestamp'])
    
    # 按对话ID分组
    for touch_id, group in df.groupby('touch_id'):
        messages = []
        
        for _, row in group.iterrows():
            sender_type = row.get('sender_type')
            content = row.get('content', '')
            
            if sender_type == 1.0:  # 用户消息
                sender = "用户"
            elif sender_type == 2.0:  # 机器人消息
                sender = "机器人"
            else:
                sender = "系统"
                
            messages.append({
                'sender': sender,
                'content': content,
                'timestamp': row.get('timestamp')
            })
        
        # 提取对话开始和结束时间
        start_time = group['timestamp'].min() if not group.empty else None
        end_time = group['timestamp'].max() if not group.empty else None
        
        # 计算对话持续时间（分钟）
        duration = None
        if start_time is not None and end_time is not None:
            duration = (end_time - start_time).total_seconds() / 60
        
        # 存储对话信息
        conversations[touch_id] = {
            'messages': messages,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'message_count': len(messages)
        }
    
    return conversations

def analyze_conversation_intent(messages, faq_data):
    """分析对话意图"""
    # 提取用户消息
    user_messages = [msg['content'] for msg in messages if msg['sender'] == "用户"]
    
    if not user_messages:
        return {
            'primary_intent': "未知",
            'keywords': [],
            'faq_matches': []
        }
    
    # 合并用户消息并提取关键词
    all_user_content = " ".join(user_messages)
    keywords = extract_keywords(all_user_content, top_n=8)
    
    # 匹配FAQ
    faq_matches = []
    
    if faq_data and keywords:
        # 为每个FAQ创建关键词集合
        faq_keywords = {}
        for faq in faq_data:
            faq_id = faq.get('id')
            question = faq.get('question', '')
            faq_keys = set(extract_keywords(question, top_n=10))
            faq_keywords[faq_id] = faq_keys
        
        # 计算用户关键词与FAQ关键词的匹配度
        user_key_set = set(keywords)
        for faq_id, faq_keys in faq_keywords.items():
            if faq_keys:
                # 计算交集大小除以并集大小
                intersection = len(user_key_set.intersection(faq_keys))
                union = len(user_key_set.union(faq_keys))
                
                if union > 0:
                    similarity = intersection / union
                    
                    if similarity > 0.1:  # 设置一个阈值
                        # 找到对应的FAQ
                        faq_item = next((faq for faq in faq_data if faq.get('id') == faq_id), None)
                        if faq_item:
                            faq_matches.append({
                                'id': faq_id,
                                'question': faq_item.get('question', ''),
                                'category': faq_item.get('category', ''),
                                'similarity': similarity
                            })
    
    # 根据匹配度排序
    faq_matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 确定主要意图
    primary_intent = "其他"
    if faq_matches:
        primary_intent = faq_matches[0]['category']
    
    return {
        'primary_intent': primary_intent,
        'keywords': keywords,
        'faq_matches': faq_matches[:3]  # 只返回前3个匹配
    }

def analyze_conversation_satisfaction(messages):
    """分析用户满意度"""
    # 简单的规则基础分析
    
    # 查找转人工请求
    transfer_requested = False
    for msg in messages:
        if msg['sender'] == "用户" and any(keyword in msg['content'] for keyword in ["转人工", "人工客服", "真人", "转接", "需要帮助"]):
            transfer_requested = True
            break
    
    # 查找明显的情绪表达
    positive_words = ["谢谢", "感谢", "不错", "好的", "满意", "解决了", "明白了"]
    negative_words = ["不满意", "没用", "无用", "没有解决", "解决不了", "不行", "不能", "不会", "差评"]
    
    sentiment_score = 0
    last_user_messages = []
    
    # 收集最后3条用户消息
    for msg in reversed(messages):
        if msg['sender'] == "用户":
            last_user_messages.append(msg['content'])
            if len(last_user_messages) >= 3:
                break
    
    # 简单情感分析
    for msg in last_user_messages:
        # 计算正面词汇出现次数
        for word in positive_words:
            if word in msg:
                sentiment_score += 1
        
        # 计算负面词汇出现次数
        for word in negative_words:
            if word in msg:
                sentiment_score -= 2  # 负面情绪权重更高
    
    # 确定满意度级别
    if transfer_requested:
        satisfaction = "可能不满意 - 请求转人工"
    elif sentiment_score > 0:
        satisfaction = "可能满意"
    elif sentiment_score < 0:
        satisfaction = "可能不满意"
    else:
        satisfaction = "未确定"
    
    return {
        'satisfaction': satisfaction,
        'transfer_requested': transfer_requested,
        'sentiment_score': sentiment_score
    }

def generate_conversation_summary(conversation):
    """生成对话摘要"""
    messages = conversation.get('messages', [])
    
    if not messages:
        return "空对话"
    
    # 提取对话信息
    user_messages = [msg['content'] for msg in messages if msg['sender'] == "用户"]
    bot_messages = [msg['content'] for msg in messages if msg['sender'] == "机器人"]
    
    # 计算一些基本统计信息
    message_count = len(messages)
    user_message_count = len(user_messages)
    bot_message_count = len(bot_messages)
    
    # 提取第一条用户消息作为初始问题
    initial_question = user_messages[0] if user_messages else "未知"
    
    # 提取最后一条机器人消息作为最终回复
    final_response = bot_messages[-1] if bot_messages else "未知"
    
    # 提取对话关键词（从所有用户消息中）
    all_user_content = " ".join(user_messages)
    keywords = extract_keywords(all_user_content, top_n=5)
    
    # 生成对话摘要文本
    summary = (
        f"用户初始问题: {initial_question[:100]}{'...' if len(initial_question) > 100 else ''}\n\n"
        f"对话轮次: {message_count} (用户:{user_message_count}, 机器人:{bot_message_count})\n\n"
        f"关键词: {', '.join(keywords)}\n\n"
        f"最终回复: {final_response[:100]}{'...' if len(final_response) > 100 else ''}"
    )
    
    return summary

def analyze_common_paths(conversations, limit=100):
    """分析常见对话路径"""
    # 简化对话路径为发送者序列
    paths = []
    
    # 限制分析的对话数量
    conv_sample = list(conversations.values())[:limit]
    
    for conv in conv_sample:
        path = "".join(["U" if msg['sender'] == "用户" else "B" for msg in conv.get('messages', [])])
        paths.append(path)
    
    # 计算路径频率
    path_counter = Counter(paths)
    common_paths = path_counter.most_common(5)
    
    # 格式化结果
    result = []
    for path, count in common_paths:
        result.append({
            'pattern': path,
            'count': count,
            'percentage': (count / len(paths)) * 100
        })
    
    return result

def generate_conversation_summaries(excel_path, output_path=None):
    """生成所有对话的摘要"""
    # 加载数据
    df = load_data(excel_path)
    if df is None:
        return False
    
    # 加载FAQ数据
    faq_data = load_faq_data()
    
    # 按对话分组
    conversations = group_messages_by_conversation(df)
    print(f"共找到 {len(conversations)} 个对话")
    
    # 如果对话数量过多，只分析一部分
    max_conversations = 1000
    if len(conversations) > max_conversations:
        print(f"对话数量过多，将只分析前 {max_conversations} 个对话")
        
        # 获取对话ID列表并排序
        conversation_ids = sorted(conversations.keys())
        selected_ids = conversation_ids[:max_conversations]
        
        # 创建新的字典
        selected_conversations = {conv_id: conversations[conv_id] for conv_id in selected_ids}
        conversations = selected_conversations
    
    # 分析常见路径
    common_paths = analyze_common_paths(conversations)
    
    # 生成每个对话的摘要
    summaries = []
    for touch_id, conversation in conversations.items():
        # 基本摘要
        summary = generate_conversation_summary(conversation)
        
        # 意图分析
        intent_analysis = analyze_conversation_intent(conversation['messages'], faq_data)
        
        # 满意度分析
        satisfaction_analysis = analyze_conversation_satisfaction(conversation['messages'])
        
        # 汇总信息
        summary_data = {
            'touch_id': touch_id,
            'summary': summary,
            'message_count': conversation['message_count'],
            'duration': conversation['duration'],
            'start_time': conversation['start_time'].strftime('%Y-%m-%d %H:%M:%S') if conversation['start_time'] else None,
            'end_time': conversation['end_time'].strftime('%Y-%m-%d %H:%M:%S') if conversation['end_time'] else None,
            'intent': intent_analysis,
            'satisfaction': satisfaction_analysis
        }
        
        summaries.append(summary_data)
    
    # 保存结果
    if output_path is None:
        # 默认保存到知识库目录
        output_dir = os.path.join(PROJECT_ROOT, 'knowledge_base', 'summaries')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f'conversation_summaries_{timestamp}.json')
    
    try:
        # 创建总结报告
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_conversations': len(conversations),
            'common_paths': common_paths,
            'summaries': summaries
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"对话摘要已保存至: {output_path}")
        return True
    except Exception as e:
        print(f"保存摘要失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        # 默认数据路径
        excel_path = os.path.join(PROJECT_ROOT, 'data', 'merged_chat_records.xlsx')
    
    generate_conversation_summaries(excel_path) 
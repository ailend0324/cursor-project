import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import re
import jieba
import jieba.analyse
from collections import Counter, defaultdict

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
            faq_data = json.load(f)
        print(f"成功加载 {len(faq_data)} 个FAQ条目")
        return faq_data
    except Exception as e:
        print(f"加载FAQ数据失败: {e}")
        return []

def preprocess_text(text):
    """预处理文本"""
    if not isinstance(text, str):
        return ""
    
    # 移除URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    
    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text, top_n=5):
    """提取文本中的关键词"""
    text = preprocess_text(text)
    if not text:
        return []
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_n)
    return keywords

def group_messages_by_conversation(df):
    """按对话ID分组消息并计算时长"""
    conversations = []
    
    for touch_id, group in df.groupby('touch_id'):
        # 按时间排序 - 使用user_start_time而不是timestamp
        if 'user_start_time' in group.columns:
            group = group.sort_values('user_start_time')
        
        # 计算对话时长
        if 'user_start_time' in group.columns and 'user_end_time' in group.columns:
            start_time = group['user_start_time'].min()
            end_time = group['user_end_time'].max()
            
            if pd.notna(start_time) and pd.notna(end_time):
                duration_minutes = (end_time - start_time).total_seconds() / 60
            else:
                duration_minutes = None
        else:
            duration_minutes = None
        
        # 创建对话字典
        conversation = {
            'touch_id': touch_id,
            'messages': group.to_dict('records'),
            'message_count': len(group),
            'start_time': start_time if 'start_time' in locals() else None,
            'end_time': end_time if 'end_time' in locals() else None,
            'duration_minutes': duration_minutes
        }
        
        conversations.append(conversation)
    
    print(f"已分组 {len(conversations)} 个对话")
    return conversations

def analyze_conversation_intent(messages, faq_data):
    """分析对话意图"""
    # 提取用户消息
    user_messages = [msg for msg in messages if msg.get('sender_type') == 1.0]
    
    if not user_messages:
        return {
            'primary_intent': '未知',
            'matched_faqs': [],
            'confidence': 0
        }
    
    # 获取初始用户消息
    initial_user_messages = user_messages[:min(3, len(user_messages))]
    initial_text = " ".join([str(msg.get('content', '')) for msg in initial_user_messages])
    
    # 提取关键词
    keywords = extract_keywords(initial_text, top_n=8)
    
    # 匹配FAQ
    matched_faqs = []
    
    for faq in faq_data:
        # 计算关键词匹配度
        faq_keywords = faq.get('keywords', [])
        matched_keywords = [kw for kw in keywords if kw in faq.get('question', '') or kw in faq_keywords]
        
        if matched_keywords:
            similarity = len(matched_keywords) / len(keywords) if keywords else 0
            
            if similarity > 0.1:  # 设置阈值
                matched_faqs.append({
                    'id': faq.get('id'),
                    'category': faq.get('category', '未分类'),
                    'question': faq.get('question', ''),
                    'similarity': similarity,
                    'matched_keywords': matched_keywords
                })
    
    # 排序匹配结果
    matched_faqs = sorted(matched_faqs, key=lambda x: x['similarity'], reverse=True)
    
    # 确定主要意图
    primary_intent = matched_faqs[0]['category'] if matched_faqs else '其他'
    confidence = matched_faqs[0]['similarity'] if matched_faqs else 0
    
    return {
        'primary_intent': primary_intent,
        'matched_faqs': matched_faqs[:3],  # 只返回前3个匹配
        'confidence': confidence
    }

def analyze_conversation_satisfaction(messages):
    """评估用户满意度"""
    # 提取用户消息
    user_messages = [msg for msg in messages if msg.get('sender_type') == 1.0]
    
    if not user_messages:
        return {
            'satisfaction': '未知',
            'confidence': 0,
            'indicators': []
        }
    
    # 最后几条用户消息
    last_user_messages = user_messages[-min(3, len(user_messages)):]
    last_text = " ".join([str(msg.get('content', '')) for msg in last_user_messages])
    
    # 定义指标词汇
    satisfaction_indicators = {
        '满意': ['谢谢', '感谢', '好的', '明白了', '解决了', '懂了', '非常好', '很好', '太好了', '👍'],
        '不满意': ['不行', '没用', '没解决', '不对', '错误', '烦人', '转人工', '人工', '差评', '不明白', '听不懂', '转接'],
        '中性': ['哦', '嗯', '知道了', '再见', '拜拜']
    }
    
    # 计数匹配的指标
    matched_indicators = {category: [] for category in satisfaction_indicators}
    
    for category, indicators in satisfaction_indicators.items():
        for indicator in indicators:
            if indicator in last_text:
                matched_indicators[category].append(indicator)
    
    # 计算满意度分数
    satisfaction_score = len(matched_indicators['满意']) - len(matched_indicators['不满意'])
    
    # 确定最终满意度
    if satisfaction_score > 0:
        satisfaction = '满意'
        confidence = min(1.0, satisfaction_score / 3)
    elif satisfaction_score < 0:
        satisfaction = '不满意'
        confidence = min(1.0, abs(satisfaction_score) / 3)
    else:
        # 如果有中性指标但没有其他指标
        if matched_indicators['中性'] and not (matched_indicators['满意'] or matched_indicators['不满意']):
            satisfaction = '中性'
            confidence = min(1.0, len(matched_indicators['中性']) / 3)
        else:
            satisfaction = '未知'
            confidence = 0
    
    # 收集所有匹配的指标
    all_indicators = []
    for category, indicators in matched_indicators.items():
        all_indicators.extend(indicators)
    
    return {
        'satisfaction': satisfaction,
        'confidence': confidence,
        'indicators': all_indicators
    }

def generate_conversation_summary(conversation):
    """生成对话摘要"""
    messages = conversation.get('messages', [])
    
    if not messages:
        return {
            'summary': '空对话',
            'keywords': [],
            'details': {}
        }
    
    # 计算基本统计数据
    user_messages = [msg for msg in messages if msg.get('sender_type') == 1.0]
    bot_messages = [msg for msg in messages if msg.get('sender_type') == 2.0]
    
    user_message_count = len(user_messages)
    bot_message_count = len(bot_messages)
    
    # 提取用户第一条消息
    initial_question = user_messages[0].get('content', '') if user_messages else '无初始问题'
    
    # 提取对话关键词
    all_user_content = " ".join([str(msg.get('content', '')) for msg in user_messages])
    keywords = extract_keywords(all_user_content, top_n=8)
    
    # 获取最后一条机器人回复
    final_response = bot_messages[-1].get('content', '') if bot_messages else '无最终回复'
    
    # 检查是否有人工转接
    transfer_request = False
    transfer_keywords = ["转人工", "人工客服", "真人", "转接"]
    
    for msg in user_messages:
        content = str(msg.get('content', ''))
        if any(keyword in content for keyword in transfer_keywords):
            transfer_request = True
            break
    
    # 创建摘要对象
    summary = {
        'touch_id': conversation.get('touch_id'),
        'start_time': conversation.get('start_time'),
        'end_time': conversation.get('end_time'),
        'duration_minutes': conversation.get('duration_minutes'),
        'message_count': conversation.get('message_count'),
        'user_message_count': user_message_count,
        'bot_message_count': bot_message_count,
        'initial_question': initial_question,
        'keywords': keywords,
        'final_response': final_response,
        'transfer_request': transfer_request
    }
    
    return summary

def analyze_common_paths(conversations, limit=100):
    """分析共同对话路径及其频率"""
    # 仅分析限定数量的对话
    sample_conversations = conversations[:limit]
    
    # 统计初始问题
    initial_questions = []
    
    for conv in sample_conversations:
        messages = conv.get('messages', [])
        user_messages = [msg for msg in messages if msg.get('sender_type') == 1.0]
        
        if user_messages:
            initial_question = user_messages[0].get('content', '')
            keywords = extract_keywords(initial_question, top_n=3)
            initial_questions.append(" ".join(keywords))
    
    # 计算频率
    question_counter = Counter(initial_questions)
    
    # 返回最常见的初始问题
    common_questions = question_counter.most_common(10)
    
    return common_questions

def generate_conversation_summaries(excel_path=None, output_path=None):
    """生成所有对话摘要"""
    # 设置默认路径
    if excel_path is None:
        excel_path = os.path.join(PROJECT_ROOT, 'data', 'merged_chat_records.xlsx')
    
    if output_path is None:
        output_dir = os.path.join(PROJECT_ROOT, 'knowledge_base', 'summaries')
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f'conversation_summaries_{timestamp}.json')
    
    # 加载数据
    df = load_data(excel_path)
    if df is None:
        return False
    
    # 加载FAQ数据
    faq_data = load_faq_data()
    
    # 分组对话
    conversations = group_messages_by_conversation(df)
    
    # 生成摘要
    print("正在生成对话摘要...")
    summaries = []
    
    for i, conversation in enumerate(conversations):
        if i % 100 == 0:
            print(f"已处理 {i}/{len(conversations)} 个对话")
        
        # 基本摘要
        summary = generate_conversation_summary(conversation)
        
        # 意图分析
        intent_analysis = analyze_conversation_intent(conversation.get('messages', []), faq_data)
        summary['intent'] = intent_analysis
        
        # 满意度分析
        satisfaction_analysis = analyze_conversation_satisfaction(conversation.get('messages', []))
        summary['satisfaction'] = satisfaction_analysis
        
        summaries.append(summary)
    
    # 分析共同路径
    common_paths = analyze_common_paths(conversations)
    
    # 创建完整结果
    result = {
        'summaries': summaries,
        'common_paths': common_paths,
        'metadata': {
            'total_conversations': len(conversations),
            'generated_at': datetime.now().isoformat()
        }
    }
    
    # 保存结果
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"摘要已保存至: {output_path}")
        return True
    except Exception as e:
        print(f"保存摘要失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    excel_path = None
    output_path = None
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    generate_conversation_summaries(excel_path, output_path) 
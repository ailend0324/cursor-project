import os
import sys
import pandas as pd
import json
import numpy as np
import re
from collections import Counter, defaultdict
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
import jieba
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap

# Define project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Add the knowledge_base directory to the path to import conversation_summary
KNOWLEDGE_BASE_DIR = os.path.join(PROJECT_ROOT, 'knowledge_base')
sys.path.insert(0, KNOWLEDGE_BASE_DIR)

# 问题分类关键词
CATEGORY_KEYWORDS = {
    '产品咨询类': {
        'keywords': ['功能', '价格', '使用', '怎么用', '区别', '特点', '优势', '版本'],
        'subcategories': ['产品功能', '产品价格', '产品使用', '产品比较']
    },
    '服务支持类': {
        'keywords': ['账号', '登录', '注册', '支付', '退款', '售后', '服务', '客服'],
        'subcategories': ['账号问题', '支付问题', '退款问题', '售后服务']
    },
    '技术问题类': {
        'keywords': ['报错', '故障', '操作', '指导', '兼容', '设备', '性能', '卡顿'],
        'subcategories': ['系统故障', '操作指导', '兼容性问题', '性能问题']
    },
    '业务咨询类': {
        'keywords': ['合作', '商务', '企业', '定制', 'API', '接口', '开发', '方案'],
        'subcategories': ['合作咨询', '商务合作', '企业服务', '定制需求']
    },
    '其他类': {
        'keywords': ['投诉', '建议', '人工', '转人工', '其他'],
        'subcategories': ['投诉建议', '人工服务', '其他问题']
    }
}

def load_data(file_path):
    """Load data from Excel file."""
    print(f"Loading data from file: {file_path}")
    try:
        df = pd.read_excel(file_path)
        print(f"Successfully loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def preprocess_text(text):
    """Clean and prepare text for analysis."""
    if not isinstance(text, str):
        return ""
    # Convert to lowercase and remove punctuation
    text = str(text).lower().strip()
    return text

def categorize_question(question):
    # 定义关键词列表
    product_keywords = ['价格', '多少钱', '型号', '什么型号', '产品', '功能', '参数', '配置', 
                        '支持', '兼容', '新品', '上市', '什么时候']
    
    service_keywords = ['如何使用', '怎么用', '使用方法', '操作步骤', '流程', '服务', '维修', 
                       '售后', '保修', '质保', '退货', '换货', '物流', '快递', '运费', 
                       '上门', '预约', '安装', '人工', '客服']
    
    technical_keywords = ['不能开机', '黑屏', '无法充电', '没反应', '蓝屏', '死机', '卡顿', 
                         '闪退', '无信号', '连不上', '无法连接', '升级', '更新', '系统', 
                         '软件', '应用', '程序', '设置', '清除', '格式化', '重置']
    
    business_keywords = ['合作', '招商', '加盟', '代理', '批发', '采购', '企业', '公司', 
                        '资质', '执照', '证书', '认证']
    
    # 检查关键词匹配
    question = preprocess_text(question)
    
    if any(keyword in question for keyword in product_keywords):
        return "产品咨询类"
    elif any(keyword in question for keyword in service_keywords):
        return "服务支持类"
    elif any(keyword in question for keyword in technical_keywords):
        return "技术问题类"
    elif any(keyword in question for keyword in business_keywords):
        return "业务咨询类"
    else:
        return "其他类"

def basic_analysis(df):
    """进行基础数据分析"""
    print("\n=== 基础数据分析 ===")
    
    # 1. 数据基本信息
    print("\n1. 数据基本信息:")
    print(df.info())
    
    # 2. 统计对话数量
    print("\n2. 对话数量统计:")
    print(f"总对话数: {len(df)}")
    
    # 3. 时间范围分析
    if 'create_time' in df.columns:
        df['create_time'] = pd.to_datetime(df['create_time'])
        print("\n3. 时间范围:")
        print(f"最早对话: {df['create_time'].min()}")
        print(f"最新对话: {df['create_time'].max()}")
        print(f"时间跨度: {df['create_time'].max() - df['create_time'].min()}")
    
    # 4. 用户和客服消息统计
    if 'sender_type' in df.columns:
        print("\n4. 消息发送者统计:")
        print(df['sender_type'].value_counts())
    
    return df

def analyze_questions(df):
    """分析问题类型和模式"""
    results = []
    results.append("=== 问题分析 ===")
    
    # Filter for user messages only
    user_df = df[df['sender_type'] == 1.0]
    
    if 'send_content' not in user_df.columns:
        results.append("Column 'send_content' not found in the DataFrame.")
        return results
    
    # Count the frequency of each question
    question_counts = Counter(user_df['send_content'].dropna())
    
    # Get the top 10 most common questions
    top_questions = question_counts.most_common(10)
    results.append("\nTop 10 User Questions:")
    for i, (question, count) in enumerate(top_questions, 1):
        results.append(f"{i}. \"{question}\" - {count} occurrences")
    
    # Categorize each question
    categories = user_df['send_content'].dropna().apply(categorize_question)
    category_counts = Counter(categories)
    
    # Display category distribution
    total = sum(category_counts.values())
    results.append("\nQuestion Categories:")
    for category, count in category_counts.most_common():
        percentage = (count / total) * 100
        results.append(f"{category}: {count} ({percentage:.2f}%)")
    
    # Generate word cloud visualization
    try:
        output_dir = os.path.join(PROJECT_ROOT, "analysis", "visualizations")
        os.makedirs(output_dir, exist_ok=True)
        
        # Filter stopwords and generate word cloud
        all_text = " ".join(user_df['send_content'].dropna())
        words = jieba.cut(all_text)
        stopwords = {'了', '的', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                    '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会'}
        
        filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]
        word_counts = Counter(filtered_words)
        
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/PingFang.ttc',
            width=800, 
            height=400,
            background_color='white',
            max_words=100
        ).generate_from_frequencies(word_counts)
        
        # Save the word cloud
        wordcloud_path = os.path.join(output_dir, "user_questions_wordcloud.png")
        wordcloud.to_file(wordcloud_path)
        results.append(f"\nUser questions word cloud saved to {wordcloud_path}")
    except Exception as e:
        results.append(f"Error generating word cloud: {e}")
    
    return results

def analyze_conversation_patterns(df):
    """分析对话模式"""
    results = []
    results.append("=== 对话模式分析 ===")
    
    # Group by conversation ID (touch_id)
    if 'touch_id' not in df.columns:
        results.append("Column 'touch_id' not found in the DataFrame.")
        return results
    
    conversation_groups = df.groupby('touch_id')
    
    # Calculate the number of dialogue turns per conversation
    dialogue_turns = conversation_groups.size()
    
    # Calculate statistics on dialogue turns
    avg_turns = dialogue_turns.mean()
    max_turns = dialogue_turns.max()
    min_turns = dialogue_turns.min()
    
    results.append(f"Average dialogue turns per conversation: {avg_turns:.2f}")
    results.append(f"Longest conversation: {max_turns} turns")
    results.append(f"Shortest conversation: {min_turns} turns")
    
    # Generate a histogram of conversation turns
    try:
        output_dir = os.path.join(PROJECT_ROOT, "analysis", "visualizations")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create turn bins
        bins = [0, 5, 10, 20, 30, 50, 100, dialogue_turns.max() + 1]
        labels = ['1-5', '6-10', '11-20', '21-30', '31-50', '51-100', '100+']
        turn_categories = pd.cut(dialogue_turns, bins=bins, labels=labels)
        
        # Count conversations in each bin
        turn_counts = turn_categories.value_counts().sort_index()
        
        # Plot histogram
        plt.figure(figsize=(10, 6))
        plt.bar(turn_counts.index, turn_counts.values)
        plt.title('Distribution of Conversation Lengths')
        plt.xlabel('Number of Turns')
        plt.ylabel('Number of Conversations')
        plt.tight_layout()
        
        # Save the plot
        chart_path = os.path.join(output_dir, "conversation_turns_distribution.png")
        plt.savefig(chart_path)
        plt.close()
        
        results.append(f"\nConversation turns distribution chart saved to {chart_path}")
    except Exception as e:
        results.append(f"Error generating conversation turns chart: {e}")
    
    return results

def analyze_conversation_duration(df):
    """分析对话时长"""
    results = []
    results.append("=== 对话时长分析 ===")
    
    # Check for required columns
    if 'user_start_time' not in df.columns or 'user_end_time' not in df.columns:
        results.append("Required columns not found: user_start_time or user_end_time")
        return results
    
    # Create a copy of the dataframe
    df_copy = df.copy()
    df_copy['user_start_time'] = pd.to_datetime(df_copy['user_start_time'], errors='coerce')
    df_copy['user_end_time'] = pd.to_datetime(df_copy['user_end_time'], errors='coerce')
    
    # Create a new DataFrame with valid timestamps
    valid_df = df_copy.dropna(subset=['user_start_time', 'user_end_time']).copy()
    results.append(f"Successfully processed {len(valid_df)} conversations with valid timestamps.")
    
    # Calculate duration in minutes
    duration_minutes = (valid_df['user_end_time'] - valid_df['user_start_time']).dt.total_seconds() / 60
    valid_df = valid_df.assign(duration_minutes=duration_minutes)
    
    # Filter valid durations
    valid_duration_df = valid_df[(valid_df['duration_minutes'] >= 0) & (valid_df['duration_minutes'] <= 120)].copy()
    
    # Report filtering results
    filtered_count = len(valid_df) - len(valid_duration_df)
    filter_percentage = (filtered_count / len(valid_df)) * 100 if len(valid_df) > 0 else 0
    results.append(f"Filtered out {filtered_count} conversations ({filter_percentage:.2f}%) with invalid durations.")
    
    # Calculate statistics
    avg_duration = valid_duration_df['duration_minutes'].mean()
    max_duration = valid_duration_df['duration_minutes'].max()
    min_duration = valid_duration_df['duration_minutes'].min()
    
    results.append(f"Average conversation duration: {avg_duration:.2f} minutes")
    results.append(f"Longest conversation: {max_duration:.2f} minutes")
    results.append(f"Shortest conversation: {min_duration:.2f} minutes")
    
    # Categorize durations
    duration_bins = [0, 1, 3, 5, 10, 15, 30, 60, 120]
    duration_labels = ['<1min', '1-3min', '3-5min', '5-10min', '10-15min', '15-30min', '30-60min', '1-2hrs']
    duration_category = pd.cut(valid_duration_df['duration_minutes'], bins=duration_bins, labels=duration_labels)
    valid_duration_df = valid_duration_df.assign(duration_category=duration_category)
    
    # Count conversations in each category
    duration_counts = valid_duration_df['duration_category'].value_counts().sort_index()
    
    results.append("\nConversation Duration Distribution:")
    for category, count in duration_counts.items():
        percentage = (count / len(valid_duration_df)) * 100
        results.append(f"{category}: {count} ({percentage:.2f}%)")
    
    # Generate duration distribution chart
    try:
        output_dir = os.path.join(PROJECT_ROOT, "analysis", "visualizations")
        os.makedirs(output_dir, exist_ok=True)
        
        plt.figure(figsize=(10, 6))
        plt.bar(duration_counts.index, duration_counts.values)
        plt.title('Conversation Duration Distribution')
        plt.xlabel('Duration')
        plt.ylabel('Number of Conversations')
        plt.tight_layout()
        
        chart_path = os.path.join(output_dir, "conversation_duration_distribution.png")
        plt.savefig(chart_path)
        plt.close()
        
        results.append(f"\nConversation duration distribution chart saved to {chart_path}")
    except Exception as e:
        results.append(f"Error generating duration chart: {e}")
    
    # Analyze correlation between duration and turns
    if 'touch_id' in df.columns:
        # Group by touch_id and count turns
        turns_df = df.groupby('touch_id').size().reset_index(name='turns')
        
        # Merge with duration data
        merged_df = pd.merge(
            valid_duration_df[['touch_id', 'duration_minutes']].drop_duplicates(),
            turns_df,
            on='touch_id'
        )
        
        # Calculate correlation
        correlation = merged_df['duration_minutes'].corr(merged_df['turns'])
        results.append(f"\nCorrelation between conversation duration and dialogue turns: {correlation:.2f}")
    
    return results

def analyze_human_transfer(df):
    """分析转人工场景"""
    results = []
    results.append("=== 转人工场景分析 ===")
    
    # Create a copy of the dataframe
    df_copy = df.copy()
    user_df = df_copy[df_copy['sender_type'] == 1.0].copy()
    
    if 'send_content' not in user_df.columns:
        results.append("Column 'send_content' not found in the DataFrame.")
        return results
    
    # Define keywords for human transfer requests
    transfer_keywords = ["人工", "转人工", "真人", "客服", "人工服务", "转接", "转接人工", "请转人工"]
    
    # Create a function to detect transfer requests
    def is_transfer_request(text):
        if not isinstance(text, str):
            return False
        text = preprocess_text(text)
        return any(keyword in text for keyword in transfer_keywords)
    
    # Apply the function to detect transfer requests
    is_transfer = user_df['send_content'].apply(is_transfer_request)
    user_df = user_df.assign(is_transfer_request=is_transfer)
    
    # Count transfer requests
    transfer_count = user_df['is_transfer_request'].sum()
    transfer_percentage = (transfer_count / len(user_df)) * 100
    
    results.append(f"Total human transfer requests: {transfer_count} ({transfer_percentage:.2f}% of user messages)")
    
    # Analyze transfer requests by conversation
    if 'touch_id' in user_df.columns and 'seq_no' in user_df.columns:
        # Group by conversation ID
        transfer_by_conv = user_df.groupby('touch_id')['is_transfer_request'].any()
        conv_with_transfer = transfer_by_conv.sum()
        conv_percentage = (conv_with_transfer / len(transfer_by_conv)) * 100
        
        results.append(f"Conversations with transfer requests: {conv_with_transfer} ({conv_percentage:.2f}% of all conversations)")
        
        # Analyze at which turn users request transfer
        transfer_df = user_df[user_df['is_transfer_request']].copy()
        if len(transfer_df) > 0:
            # Get the first transfer request in each conversation
            transfer_df = transfer_df.sort_values(['touch_id', 'seq_no'])
            first_transfers = transfer_df.drop_duplicates('touch_id').copy()
            
            # Calculate average turn when transfer is requested
            avg_turn = first_transfers['seq_no'].mean()
            results.append(f"Average turn when transfer is requested: {avg_turn:.2f}")
            
            # Categorize turns
            turn_bins = [0, 1, 2, 3, 5, 10, 20, 100]
            turn_labels = ['First msg', 'Turn 2', 'Turn 3', 'Turns 4-5', 'Turns 6-10', 'Turns 11-20', '20+ turns']
            turn_category = pd.cut(first_transfers['seq_no'], bins=turn_bins, labels=turn_labels)
            first_transfers = first_transfers.assign(turn_category=turn_category)
            
            # Count transfers by turn category
            turn_counts = first_transfers['turn_category'].value_counts().sort_index()
            
            results.append("\nTransfer Request Distribution by Turn:")
            for category, count in turn_counts.items():
                percentage = (count / len(first_transfers)) * 100
                results.append(f"{category}: {count} ({percentage:.2f}%)")
            
            # Generate transfer distribution chart
            try:
                output_dir = os.path.join(PROJECT_ROOT, "analysis", "visualizations")
                os.makedirs(output_dir, exist_ok=True)
                
                plt.figure(figsize=(10, 6))
                plt.bar(turn_counts.index, turn_counts.values)
                plt.title('Transfer Request Distribution by Turn')
                plt.xlabel('Conversation Turn')
                plt.ylabel('Number of Transfer Requests')
                plt.tight_layout()
                
                chart_path = os.path.join(output_dir, "transfer_request_distribution.png")
                plt.savefig(chart_path)
                plt.close()
                
                results.append(f"\nTransfer request distribution chart saved to {chart_path}")
            except Exception as e:
                results.append(f"Error generating transfer chart: {e}")
    
    return results

def analyze_conversation_intent_by_touch_id(df):
    """以对话(touch_id)为单位分析对话意图"""
    print("\n=== 对话级别意图分析 ===")
    
    # 检查必要的列是否存在
    if 'touch_id' not in df.columns or 'sender_type' not in df.columns or 'send_content' not in df.columns:
        print("缺少必要的列：touch_id, sender_type 或 send_content")
        return None
    
    # 创建副本以避免修改原始数据
    df_copy = df.copy()
    
    # 获取所有唯一的对话ID
    conversation_ids = df_copy['touch_id'].unique()
    print(f"总共找到 {len(conversation_ids)} 个唯一对话")
    
    # 创建存储对话意图的字典
    conversation_intents = {}
    intent_distribution = Counter()
    
    # 为每个对话分析意图
    for touch_id in conversation_ids:
        # 获取该对话的所有消息
        conv_df = df_copy[df_copy['touch_id'] == touch_id].sort_values('seq_no')
        
        # 提取用户消息
        user_messages = conv_df[conv_df['sender_type'] == 1.0]['send_content'].dropna().tolist()
        
        if not user_messages:
            # 如果没有用户消息，跳过此对话
            continue
        
        # 获取首条用户消息和前三条用户消息
        first_message = user_messages[0] if user_messages else ""
        initial_messages = " ".join(user_messages[:min(3, len(user_messages))])
        
        # 判断是否是问候语开始
        is_greeting = any(greeting in first_message for greeting in ["你好", "您好", "早上好", "下午好", "晚上好", "在吗"])
        
        # 确定主要意图
        if is_greeting and len(user_messages) > 1:
            # 如果以问候语开始，则看后续消息
            intent = categorize_question(initial_messages)
            
            # 如果依然无法分类，检查整个对话中的关键词
            if intent == "其他类" and len(user_messages) > 2:
                all_user_content = " ".join(user_messages)
                intent = categorize_question(all_user_content)
                
                # 检查是否有转人工请求
                if any("人工" in msg for msg in user_messages):
                    intent = "人工服务需求"
        else:
            # 直接分析初始消息
            intent = categorize_question(first_message)
            
            # 如果无法分类初始消息，尝试分析前三条消息
            if intent == "其他类" and len(user_messages) > 1:
                intent = categorize_question(initial_messages)
                
                # 如果前三条仍无法分类，尝试整个对话
                if intent == "其他类" and len(user_messages) > 3:
                    all_user_content = " ".join(user_messages)
                    intent = categorize_question(all_user_content)
        
        # 检查确认和拒绝回复模式
        if intent == "其他类":
            confirmation_keywords = ["好的", "可以", "确认", "同意", "明白", "知道了", "收到", "嗯", "好"]
            rejection_keywords = ["不行", "不可以", "不同意", "不要", "拒绝", "算了", "不好"]
            
            # 检查是否为确认回复
            if any(keyword in first_message for keyword in confirmation_keywords):
                intent = "确认回复"
            # 检查是否为拒绝回复
            elif any(keyword in first_message for keyword in rejection_keywords):
                intent = "拒绝回复"
        
        # 存储结果
        conversation_intents[touch_id] = intent
        intent_distribution[intent] += 1
    
    # 打印意图分布
    total_convs = len(conversation_intents)
    print(f"\n对话级别意图分布 (总计: {total_convs} 对话):")
    for intent, count in intent_distribution.most_common():
        percentage = (count / total_convs) * 100
        print(f"{intent}: {count} ({percentage:.2f}%)")
    
    # 计算整体分类率
    other_count = intent_distribution.get("其他类", 0)
    classified_rate = 100 - (other_count / total_convs * 100) if total_convs > 0 else 0
    print(f"\n对话级别意图分类率: {classified_rate:.2f}%")
    
    return conversation_intents

def analyze_template_usage(df):
    """Analyze the usage of predefined response templates by the bot"""
    results = []
    results.append("=== Template Usage Analysis ===")
    
    # Filter for bot messages only
    bot_df = df[df['sender_type'] == 2.0]
    
    if len(bot_df) == 0:
        results.append("No bot messages found in the data.")
        return results
    
    # Load template data
    template_file = os.path.join(PROJECT_ROOT, 'knowledge_base', 'answer_templates.json')
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)
        
        # Check for templates in the nested structure
        if 'templates' in templates_data:
            templates = templates_data['templates']
            results.append(f"Successfully loaded {len(templates)} templates from {template_file}")
        else:
            results.append(f"No 'templates' key found in {template_file}")
            return results
    except Exception as e:
        results.append(f"Error loading templates: {e}")
        return results
    
    # Extract template texts and categories
    template_texts = []
    template_categories = {}
    
    for template in templates:
        if 'template' in template and 'category' in template:
            template_texts.append(template['template'])
            template_categories[template['template']] = template['category']
    
    if not template_texts:
        results.append("No valid templates found in the template file.")
        return results
    
    # Count the occurrences of each template
    template_counts = defaultdict(int)
    total_bot_messages = len(bot_df)
    
    # Check each bot message for exact matches with templates
    for message in bot_df['send_content'].dropna():
        for template in template_texts:
            if message == template:
                template_counts[template] += 1
    
    # Calculate template usage rate
    total_template_uses = sum(template_counts.values())
    template_usage_rate = (total_template_uses / total_bot_messages) * 100 if total_bot_messages > 0 else 0
    
    results.append(f"\nTemplate usage rate: {template_usage_rate:.2f}% ({total_template_uses} of {total_bot_messages} bot messages)")
    
    # Report most used templates
    if template_counts:
        results.append("\nMost used response templates:")
        for i, (template, count) in enumerate(sorted(template_counts.items(), key=lambda x: x[1], reverse=True)[:5], 1):
            category = template_categories.get(template, "Unknown")
            usage_rate = (count / total_bot_messages) * 100
            results.append(f"{i}. Category: {category}, Count: {count} ({usage_rate:.2f}%)")
            results.append(f"   Text: \"{template[:100]}{'...' if len(template) > 100 else ''}\"")
    else:
        results.append("No template matches found in bot messages.")
    
    # Count templates by category
    category_counts = defaultdict(int)
    for template, count in template_counts.items():
        category = template_categories.get(template, "Unknown")
        category_counts[category] += count
    
    if category_counts:
        results.append("\nTemplate usage by category:")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            category_rate = (count / total_template_uses) * 100 if total_template_uses > 0 else 0
            results.append(f"{category}: {count} ({category_rate:.2f}%)")
    
    return results

def analyze_faq_topics(df):
    """Analyze user messages against FAQ database to identify common topics"""
    results = []
    results.append("=== FAQ Topic Analysis ===")
    
    # Filter for user messages only
    user_df = df[df['sender_type'] == 1.0]
    
    if 'send_content' not in user_df.columns:
        results.append("Column 'send_content' not found in the DataFrame.")
        return results
    
    # Load FAQ data
    faq_file = os.path.join(PROJECT_ROOT, 'knowledge_base', 'faq.json')
    try:
        with open(faq_file, 'r', encoding='utf-8') as f:
            faq_data = json.load(f)
        
        # Check for FAQs in the nested structure
        if 'faqs' in faq_data:
            faqs = faq_data['faqs']
            results.append(f"Successfully loaded {len(faqs)} FAQs from {faq_file}")
        else:
            results.append(f"No 'faqs' key found in {faq_file}")
            return results
    except Exception as e:
        results.append(f"Error loading FAQ data: {e}")
        return results
    
    # Create indexes by category and keywords
    faq_categories = defaultdict(list)
    faq_keywords = defaultdict(list)
    
    for faq in faqs:
        if 'category' in faq and 'question' in faq and 'keywords' in faq:
            faq_categories[faq['category']].append(faq)
            
            for keyword in faq['keywords']:
                faq_keywords[keyword].append(faq)
    
    if not faq_keywords:
        results.append("No valid FAQ data with keywords found.")
        return results
    
    # Process user messages for matches
    match_counts = defaultdict(int)
    matched_messages = 0
    total_messages = len(user_df['send_content'].dropna())
    
    for message in user_df['send_content'].dropna():
        message = preprocess_text(message)
        
        # Skip very short messages
        if len(message) < 3:
            continue
        
        matched = False
        
        # Check for keyword matches
        for keyword, faqs in faq_keywords.items():
            if keyword in message:
                matched = True
                for faq in faqs:
                    match_counts[faq['category']] += 1
        
        if matched:
            matched_messages += 1
    
    # Calculate matching rate
    matching_rate = (matched_messages / total_messages) * 100 if total_messages > 0 else 0
    results.append(f"FAQ matching rate: {matching_rate:.2f}% ({matched_messages} of {total_messages} user messages)")
    
    # Identify common FAQ categories
    if match_counts:
        results.append("\nCommon FAQ categories in user questions:")
        total_matches = sum(match_counts.values())
        
        for i, (category, count) in enumerate(sorted(match_counts.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            category_percentage = (count / total_matches) * 100
            results.append(f"{i}. {category}: {count} matches ({category_percentage:.2f}%)")
        
        # Create a dictionary for visualization
        faq_matches = {
            'category_counts': match_counts,
            'total_matches': total_matches,
            'matched_messages': matched_messages
        }
        
        # Generate word cloud for FAQ categories
        try:
            # Prepare for visualization
            visualize_faq_categories(faq_matches)
            
            # Add info about visualization to results
            wordcloud_path = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations', 'faq_categories_wordcloud.png')
            results.append(f"\nFAQ category word cloud saved to {wordcloud_path}")
        except Exception as e:
            results.append(f"Error generating FAQ category word cloud: {e}")
    else:
        results.append("No FAQ matches found in user messages.")
    
    return results

def analyze_word_frequency(df):
    """分析用户消息中的词频并生成词云"""
    print("\n=== 词频分析与词云可视化 ===")
    
    # 筛选用户消息
    user_df = df[df['sender_type'] == 1.0]
    
    if 'send_content' not in user_df.columns:
        print("Column 'send_content' not found in the DataFrame.")
        return
    
    # 合并所有用户消息
    all_messages = " ".join(user_df['send_content'].dropna().astype(str))
    
    # 使用jieba进行中文分词
    words = jieba.cut(all_messages)
    
    # 过滤停用词
    stopwords = {'了', '的', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', 
                '我们', '为', '啊', '吗', '吧', '呢', '但', '还', '好', '这', '那'}
    
    filtered_words = [word for word in words if len(word) > 1 and word not in stopwords]
    
    # 统计词频
    word_counts = Counter(filtered_words)
    
    # 打印最常见的词
    print("\nTop 20 Most Frequent Words:")
    for word, count in word_counts.most_common(20):
        print(f"{word}: {count}")
    
    # 生成词云
    try:
        wordcloud = WordCloud(
            font_path='/System/Library/Fonts/PingFang.ttc',  # 中文字体路径
            width=800, 
            height=400, 
            background_color='white'
        ).generate_from_frequencies(word_counts)
        
        # 保存词云图像
        output_dir = os.path.join(PROJECT_ROOT, "analysis", "visualizations")
        os.makedirs(output_dir, exist_ok=True)
        wordcloud_path = os.path.join(output_dir, "wordcloud.png")
        wordcloud.to_file(wordcloud_path)
        print(f"\nWordcloud saved to {wordcloud_path}")
        
        # 可选：显示词云
        # plt.figure(figsize=(10, 5))
        # plt.imshow(wordcloud, interpolation='bilinear')
        # plt.axis('off')
        # plt.tight_layout()
        # plt.savefig(os.path.join(output_dir, "wordcloud.png"))
        
    except Exception as e:
        print(f"Error generating wordcloud: {e}")
    
    return word_counts

def generate_word_cloud(df, output_dir):
    """Generate word clouds from user questions."""
    print("\nGenerating word clouds from user questions...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter for user messages
    user_df = df[df['sender_type'] == 1.0]
    
    if user_df.empty:
        print("No user messages found for word cloud generation.")
        return
    
    # Combine all user messages
    all_text = ' '.join(user_df['send_content'].fillna('').astype(str))
    
    # Use jieba for word segmentation
    seg_list = jieba.cut(all_text)
    seg_text = ' '.join(seg_list)
    
    # Find a suitable Chinese font
    font_path = None
    # Try some common Chinese fonts on different platforms
    possible_fonts = [
        '/System/Library/Fonts/PingFang.ttc',  # macOS
        '/Library/Fonts/Arial Unicode.ttf',    # macOS
        '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
        'C:\\Windows\\Fonts\\simhei.ttf',      # Windows
        'C:\\Windows\\Fonts\\msyh.ttf',        # Windows
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'  # Linux
    ]
    
    for font in possible_fonts:
        if os.path.exists(font):
            font_path = font
            print(f"Using font: {font}")
            break
    
    if not font_path:
        print("Warning: Could not find a suitable Chinese font. Word cloud may not display Chinese characters correctly.")
        # Fall back to default font
        font_path = None
    
    # Generate and save word cloud
    try:
        wordcloud = WordCloud(
            font_path=font_path,
            width=800, 
            height=400, 
            background_color='white',
            max_words=100,
            collocations=False  # Avoid duplicate word pairs
        ).generate(seg_text)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout()
        
        # Save the word cloud
        wordcloud_path = os.path.join(output_dir, 'user_questions_wordcloud.png')
        plt.savefig(wordcloud_path)
        plt.close()  # Close the figure to free memory
        print(f"Word cloud saved to {wordcloud_path}")
        
        # Generate word clouds by question category
        if 'question_category' in df.columns:
            categories = df['question_category'].dropna().unique()
            for category in categories:
                if pd.isna(category) or category == '':
                    continue
                    
                category_df = df[(df['sender_type'] == 1.0) & (df['question_category'] == category)]
                if category_df.empty or len(category_df) < 5:  # Skip if too few samples
                    continue
                    
                cat_text = ' '.join(category_df['send_content'].fillna('').astype(str))
                cat_seg_list = jieba.cut(cat_text)
                cat_seg_text = ' '.join(cat_seg_list)
                
                if len(cat_seg_text.strip()) < 10:  # Skip if text is too short
                    continue
                    
                try:
                    cat_wordcloud = WordCloud(
                        font_path=font_path,
                        width=800, 
                        height=400, 
                        background_color='white',
                        max_words=50,
                        collocations=False
                    ).generate(cat_seg_text)
                    
                    plt.figure(figsize=(10, 5))
                    plt.imshow(cat_wordcloud, interpolation='bilinear')
                    plt.title(f'Category: {category}')
                    plt.axis('off')
                    plt.tight_layout()
                    
                    # Save category word cloud
                    # Convert category to a filename-friendly string
                    safe_category = ''.join(c if c.isalnum() else '_' for c in str(category))
                    cat_path = os.path.join(output_dir, f'wordcloud_{safe_category}.png')
                    plt.savefig(cat_path)
                    plt.close()  # Close the figure to free memory
                    print(f"Word cloud for category '{category}' saved to {cat_path}")
                except Exception as e:
                    print(f"Error generating word cloud for category '{category}': {e}")
    except Exception as e:
        print(f"Error generating word cloud: {e}")
    
    plt.close('all')  # Close all remaining figures

def generate_wordcloud(text_data, title, output_path):
    """
    Generate and save a word cloud from the given text data.
    
    Args:
        text_data (str): Text to generate word cloud from
        title (str): Title for the word cloud image
        output_path (str): Path to save the word cloud image
    """
    print(f"\nGenerating word cloud for {title}...")
    
    # Ensure text data is a string
    if isinstance(text_data, list):
        text_data = ' '.join(text_data)
    
    # Check if text data is empty
    if not text_data or len(text_data.strip()) == 0:
        print(f"No text data available for {title} word cloud.")
        return
    
    # Use jieba for Chinese word segmentation
    words = ' '.join(jieba.cut(text_data))
    
    # Find a suitable Chinese font
    font_path = None
    # Try some common Chinese fonts on different platforms
    possible_fonts = [
        '/System/Library/Fonts/PingFang.ttc',  # macOS
        '/Library/Fonts/Arial Unicode.ttf',    # macOS
        '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
        'C:\\Windows\\Fonts\\simhei.ttf',      # Windows
        'C:\\Windows\\Fonts\\msyh.ttf',        # Windows
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'  # Linux
    ]
    
    for font in possible_fonts:
        if os.path.exists(font):
            font_path = font
            break
    
    try:
        # Create the WordCloud object
        wordcloud = WordCloud(
            font_path=font_path,  # Font for Chinese characters
            width=800,
            height=400,
            background_color='white',
            max_words=200,
            collocations=False  # Avoid duplicate word pairs
        ).generate(words)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create the figure
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(title)
        plt.tight_layout()
        
        # Save the figure
        plt.savefig(output_path, dpi=300)
        plt.close()  # Close the figure to free memory
        
        print(f"Word cloud saved to {output_path}")
    except Exception as e:
        print(f"Error generating word cloud: {e}")
        print(f"Text length: {len(words)} characters")

def visualize_user_questions(df):
    """
    Generate a word cloud visualization for user questions.
    
    Args:
        df (DataFrame): DataFrame containing user messages
        
    Returns:
        str: Path to the generated word cloud image
    """
    print("\nVisualizing user questions...")
    
    # Filter for user messages only
    user_messages = df[df['sender_type'] == 1.0]
    
    if user_messages.empty:
        print("No user messages found for visualization.")
        return None
    
    # Check column name - could be 'send_content' or 'message_content'
    message_col = 'send_content' if 'send_content' in user_messages.columns else 'message_content'
    
    if message_col not in user_messages.columns:
        print(f"Column '{message_col}' not found in DataFrame.")
        return None
    
    # Combine all user messages
    all_questions = ' '.join(user_messages[message_col].dropna().astype(str).tolist())
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(PROJECT_ROOT, 'analysis', 'visualizations'), exist_ok=True)
    
    # Generate and save the word cloud
    output_path = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations', 'user_questions_wordcloud.png')
    generate_wordcloud(all_questions, 'User Questions Word Cloud', output_path)
    
    return output_path

def visualize_faq_categories(faq_matches):
    """
    Generate a word cloud visualization for FAQ categories.
    
    Args:
        faq_matches (dict): Dictionary with FAQ category counts
        
    Returns:
        str: Path to the generated word cloud image
    """
    print("\nVisualizing FAQ categories...")
    
    if not faq_matches or not isinstance(faq_matches, dict) or 'category_counts' not in faq_matches:
        print("No FAQ category data available for visualization.")
        return None
    
    # Create text for word cloud with repeated categories based on their counts
    category_text = []
    for category, count in faq_matches['category_counts'].items():
        category_text.extend([category] * count)
    
    category_text = ' '.join(category_text)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(PROJECT_ROOT, 'analysis', 'visualizations'), exist_ok=True)
    
    # Generate and save the word cloud
    output_path = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations', 'faq_categories_wordcloud.png')
    generate_wordcloud(category_text, 'FAQ Categories Word Cloud', output_path)
    
    return output_path

def main():
    """Main function to run all analysis."""
    # Set file paths using PROJECT_ROOT
    data_file = os.path.join(PROJECT_ROOT, 'data', 'merged_chat_records.xlsx')
    output_file = os.path.join(PROJECT_ROOT, 'analysis', 'analysis_results.txt')
    
    # Create visualizations directory
    visualizations_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    os.makedirs(visualizations_dir, exist_ok=True)
    
    # Load data
    df = load_data(data_file)
    
    # Open file for writing results
    with open(output_file, 'w', encoding='utf-8') as f:
        # Basic data information
        f.write("=== Basic Data Information ===\n")
        f.write(f"Data shape: {df.shape[0]} rows, {df.shape[1]} columns\n")
        f.write(f"Columns: {', '.join(df.columns)}\n")
        f.write("Non-null counts:\n")
        for col in df.columns:
            f.write(f"  - {col}: {df[col].count()}\n")
        f.write("\n")
        
        # Total conversation count
        f.write("=== Conversation Statistics ===\n")
        unique_conversations = df['touch_id'].nunique()
        f.write(f"Total conversation count: {unique_conversations}\n")
        
        # Time range of conversations
        # Convert timestamps to datetime with error handling
        df['user_start_time'] = pd.to_datetime(df['user_start_time'], errors='coerce')
        df['user_end_time'] = pd.to_datetime(df['user_end_time'], errors='coerce')
        
        # Only use valid timestamps for min/max calculations
        valid_start_times = df['user_start_time'].dropna()
        valid_end_times = df['user_end_time'].dropna()
        
        if not valid_start_times.empty and not valid_end_times.empty:
            min_time = valid_start_times.min()
            max_time = valid_end_times.max()
            time_diff = max_time - min_time
            days = time_diff.days
            hours = time_diff.seconds // 3600
            f.write(f"Earliest conversation: {min_time}\n")
            f.write(f"Latest conversation: {max_time}\n")
            f.write(f"Time span: {days} days and {hours} hours\n\n")
        else:
            f.write("Could not determine time range: insufficient valid timestamp data\n\n")
        
        # Sender type statistics
        f.write("=== Sender Type Statistics ===\n")
        sender_counts = df['sender_type'].value_counts()
        for sender_type, count in sender_counts.items():
            f.write(f"Sender type {sender_type}: {count} messages\n")
        f.write("\n")
        
        # Analyze user questions
        f.write("=== User Questions Analysis ===\n")
        question_results = analyze_questions(df)
        for line in question_results:
            f.write(f"{line}\n")
        f.write("\n")
        
        # Analyze conversation patterns
        f.write("=== Conversation Pattern Analysis ===\n")
        pattern_results = analyze_conversation_patterns(df)
        for line in pattern_results:
            f.write(f"{line}\n")
        f.write("\n")
        
        # Analyze conversation duration
        f.write("=== Conversation Duration Analysis ===\n")
        duration_results = analyze_conversation_duration(df)
        for line in duration_results:
            f.write(f"{line}\n")
        f.write("\n")
        
        # Analyze human transfer
        f.write("=== Human Transfer Analysis ===\n")
        transfer_results = analyze_human_transfer(df)
        for line in transfer_results:
            f.write(f"{line}\n")
        f.write("\n")
        
        # Analyze template usage
        f.write("=== Template Usage Analysis ===\n")
        template_results = analyze_template_usage(df)
        for line in template_results:
            f.write(f"{line}\n")
        f.write("\n")
        
        # Analyze FAQ topics
        f.write("=== FAQ Topic Analysis ===\n")
        faq_results = analyze_faq_topics(df)
        for line in faq_results:
            f.write(f"{line}\n")
        f.write("\n")
    
    # Generate word clouds from user messages
    try:
        generate_word_cloud(df, visualizations_dir)
        visualize_user_questions(df)
    except Exception as e:
        print(f"Error generating visualizations: {e}")
    
    print(f"Analysis results saved to {output_file}")
    print(f"Visualizations saved to {visualizations_dir}")

if __name__ == "__main__":
    main() 
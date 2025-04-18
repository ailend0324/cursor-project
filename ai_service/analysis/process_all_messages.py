import pandas as pd
import numpy as np
from collections import Counter
import jieba
import jieba.analyse
import os
import re
import json
import time
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置jieba分词的停用词
STOP_WORDS = set(['的', '了', '是', '我', '你', '他', '她', '它', '这', '那', '啊', '呢', '吗', '吧', '，', '。', '？', '！', '：', '；', '、'])

def load_data(file_path):
    """加载Excel文件数据"""
    try:
        print(f"Loading data from {file_path}...")
        start_time = time.time()
        df = pd.read_excel(file_path)
        elapsed_time = time.time() - start_time
        print(f"Successfully loaded {len(df)} records in {elapsed_time:.2f} seconds.")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def preprocess_text(text):
    """文本预处理，去除特殊字符并分词"""
    if pd.isna(text):
        return ""
    
    # 转换为字符串并去除空白
    text = str(text).strip()
    
    # 去除URL
    text = re.sub(r'https?://\S+', '', text)
    
    # 去除特殊字符，但保留中文、数字、字母和一些基本标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff。，？！：；]', '', text)
    
    # 分词并去除停用词
    words = [word for word in jieba.cut(text) if word not in STOP_WORDS and len(word) > 1]
    
    return " ".join(words)

def extract_keywords_batch(texts, top_n=50, batch_size=1000):
    """分批提取关键词以节省内存"""
    all_keywords = Counter()
    
    # 分批处理
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_text = " ".join([text for text in batch_texts if isinstance(text, str) and text.strip()])
        
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(batch_text, topK=top_n)
        for keyword in keywords:
            all_keywords[keyword] += 1
    
    # 返回最终的关键词列表
    return [keyword for keyword, _ in all_keywords.most_common(top_n)]

def analyze_all_user_messages(df):
    """分析所有用户消息"""
    print("Starting analysis of all user messages...")
    start_time = time.time()
    
    # 筛选用户消息
    user_df = df[df['sender_type'] == 1.0].copy()
    print(f"Found {len(user_df)} user messages.")
    
    # 预处理用户消息文本
    print("Preprocessing user messages (this may take a while)...")
    user_df['processed_text'] = user_df['send_content'].progress_apply(preprocess_text)
    
    # 过滤掉空消息和极短消息(少于2个字符)
    user_df = user_df[user_df['processed_text'].str.len() > 1]
    print(f"After filtering, {len(user_df)} valid user messages remain.")
    
    # 统计最常见的用户消息
    print("Counting most common user messages...")
    common_messages = Counter(user_df['send_content'].dropna())
    top_messages = common_messages.most_common(100)
    
    # 分析问题类型和意图
    print("Analyzing question types and intents...")
    
    # 各种业务相关关键词
    keyword_groups = {
        "价格咨询": ["价格", "多少钱", "报价", "估价", "值多少", "收多少", "钱", "价", "便宜", "贵"],
        "回收流程": ["流程", "步骤", "怎么卖", "如何卖", "卖出", "怎么回收", "回收流程", "邮寄", "怎么操作"],
        "设备型号": ["型号", "配置", "几代", "多大内存", "多大存储", "参数", "规格", "几寸", "多少存储"],
        "设备状况": ["几成新", "有划痕", "磕碰", "外观", "电池", "电池健康", "屏幕", "破损", "维修过"],
        "数据安全": ["数据", "删除", "清除", "格式化", "隐私", "个人信息", "账号", "恢复出厂", "重置"],
        "订单状态": ["订单", "物流", "快递", "几天", "到货", "发货", "收货", "验货", "顺丰"],
        "退回取消": ["退回", "不卖了", "取消", "撤销", "反悔", "不想卖", "退货", "拒收"],
        "质量争议": ["有问题", "异议", "不认可", "不接受", "不满意", "申诉", "复检", "重新检查"],
        "人工服务": ["人工", "客服", "转人工", "真人", "电话", "联系", "工作人员"],
        "投诉问题": ["投诉", "举报", "差评", "不满", "态度", "服务差", "欺骗", "虚假"],
        "确认回复": ["好的", "可以", "确认", "同意", "明白", "知道了", "收到", "嗯", "好"],
        "拒绝回复": ["不行", "不可以", "不同意", "不要", "拒绝", "算了", "不好"],
        "问候语": ["你好", "早上好", "下午好", "晚上好", "您好", "在吗", "在不在"]
    }
    
    # 使用关键词进行分类
    print("Classifying user messages by keywords...")
    
    def categorize_by_keywords(text):
        if not isinstance(text, str):
            return "其他"
        text = str(text).lower()
        for category, keywords in keyword_groups.items():
            if any(keyword in text for keyword in keywords):
                return category
        return "其他"
    
    user_df['intent_category'] = user_df['send_content'].apply(categorize_by_keywords)
    intent_counts = user_df['intent_category'].value_counts()
    
    # 为每个类别提取示例
    intent_examples = {}
    for category in keyword_groups.keys():
        category_df = user_df[user_df['intent_category'] == category]
        if len(category_df) > 0:
            example_counts = category_df['send_content'].value_counts().head(20)
            intent_examples[category] = {
                "count": len(category_df),
                "percentage": (len(category_df) / len(user_df)) * 100,
                "examples": example_counts.to_dict()
            }
    
    # 执行小批量聚类分析
    print("Performing mini-batch clustering for large-scale intent analysis...")
    try:
        # 使用TF-IDF向量化文本
        print("Vectorizing text...")
        vectorizer = TfidfVectorizer(max_features=500)
        
        # 分批处理以避免内存溢出
        batch_size = 50000
        n_clusters = 25  # 增加聚类数量以捕获更多意图
        
        # 初始化聚类器
        kmeans = MiniBatchKMeans(n_clusters=n_clusters, 
                               batch_size=batch_size,
                               random_state=42)
        
        # 分批拟合
        for i in tqdm(range(0, len(user_df), batch_size), desc="Clustering"):
            batch = user_df.iloc[i:i+batch_size]
            batch_vectors = vectorizer.fit_transform(batch['processed_text'])
            if i == 0:
                kmeans = kmeans.partial_fit(batch_vectors)
            else:
                kmeans = kmeans.partial_fit(batch_vectors)
        
        # 将所有数据都向量化一次（这可能需要大量内存）
        all_vectors = vectorizer.transform(user_df['processed_text'])
        user_df['cluster'] = kmeans.predict(all_vectors)
        
        # 分析每个聚类的关键词
        cluster_keywords = {}
        cluster_examples = {}
        cluster_sizes = {}
        
        for cluster_id in range(n_clusters):
            cluster_mask = user_df['cluster'] == cluster_id
            cluster_texts = user_df.loc[cluster_mask, 'send_content'].tolist()
            cluster_sizes[cluster_id] = len(cluster_texts)
            
            if cluster_texts:
                # 提取关键词
                keywords = extract_keywords_batch(cluster_texts, top_n=15, batch_size=5000)
                cluster_keywords[cluster_id] = keywords
                
                # 获取每个聚类的典型示例
                example_counts = Counter(cluster_texts).most_common(10)
                cluster_examples[cluster_id] = [text for text, _ in example_counts]
        
        # 将聚类结果输出
        clustering_results = {
            "cluster_keywords": cluster_keywords,
            "cluster_examples": cluster_examples,
            "cluster_sizes": cluster_sizes
        }
        
    except Exception as e:
        print(f"Error in clustering: {e}")
        clustering_results = {"error": str(e)}
    
    # 统计每种意图的频率
    intent_data = {
        "top_messages": top_messages,
        "intent_categories": intent_counts.to_dict(),
        "intent_examples": intent_examples,
        "clustering_results": clustering_results
    }
    
    elapsed_time = time.time() - start_time
    print(f"User message analysis completed in {elapsed_time:.2f} seconds.")
    
    return intent_data

def generate_extended_faq(intent_data):
    """根据意图分析生成扩展的FAQ"""
    print("Generating extended FAQ based on intent analysis...")
    
    # 当前的FAQ类别和问题
    current_faq_categories = [
        "价格咨询", "回收流程", "设备状况", "数据安全", "订单跟踪", 
        "退回/取消", "质量争议", "人工服务", "投诉处理", "第三方平台"
    ]
    
    # 基于意图分析提取待添加的FAQ
    new_faqs = []
    faq_id_counter = 16  # 从16开始，假设已有15个FAQ
    
    # 从聚类结果中提取FAQ
    clusters = intent_data.get("clustering_results", {}).get("cluster_keywords", {})
    examples = intent_data.get("clustering_results", {}).get("cluster_examples", {})
    
    for cluster_id, keywords in clusters.items():
        if not keywords:
            continue
            
        # 尝试确定此聚类的主题
        keyword_str = " ".join(keywords)
        cluster_examples = examples.get(cluster_id, [])
        if not cluster_examples:
            continue
            
        # 确定FAQ类别
        category = "其他"
        for cat in current_faq_categories:
            cat_keywords = cat.split("/")[0].lower()
            if cat_keywords in keyword_str.lower():
                category = cat
                break
                
        # 根据关键词和示例生成问题和答案
        # 这里仅简单示例，实际应用中可能需要更复杂的逻辑或人工审核
        
        # 生成问题
        common_question = cluster_examples[0]
        # 如果问题太短或太通用，尝试组合关键词生成问题
        if len(common_question) < 5 or common_question in ["你好", "好的", "谢谢", "人工"]:
            if "价格" in keyword_str:
                question = f"{keywords[0]}的{keywords[1]}价格是如何评估的？"
            elif "流程" in keyword_str:
                question = f"{keywords[0]}的{keywords[1]}流程是怎样的？"
            elif "订单" in keyword_str or "物流" in keyword_str:
                question = f"如何查询{keywords[0]}{keywords[1]}的状态？"
            elif "退回" in keyword_str or "取消" in keyword_str:
                question = f"如何{keywords[0]}{keywords[1]}？"
            else:
                question = f"关于{keywords[0]}和{keywords[1]}的常见问题"
        else:
            # 如果是问句，直接使用
            if "？" in common_question or "?" in common_question:
                question = common_question
            else:
                # 否则尝试转换为问句
                question = f"{common_question}是怎么回事？"
                
        # 生成简单的答案框架
        answer = f"这是关于{keywords[0]}、{keywords[1]}和{keywords[2]}的问题。根据我们的分析，多数用户关心的是{keywords[:3]}。建议详细说明相关流程和注意事项。"
        
        # 创建新FAQ条目
        new_faq = {
            "id": faq_id_counter,
            "category": category,
            "question": question,
            "answer": answer,
            "keywords": keywords[:5],
            "examples": cluster_examples[:3],
            "cluster_id": cluster_id
        }
        
        new_faqs.append(new_faq)
        faq_id_counter += 1
    
    print(f"Generated {len(new_faqs)} potential new FAQ items from cluster analysis.")
    return new_faqs

def analyze_conversation_flows(df):
    """分析完整对话流程"""
    print("Analyzing conversation flows...")
    
    # 按对话ID和序列号排序
    df_sorted = df.sort_values(['touch_id', 'seq_no'])
    
    # 提取所有对话ID
    conversation_ids = df_sorted['touch_id'].unique()
    print(f"Found {len(conversation_ids)} unique conversations.")
    
    # 分析每个对话的开始、结束和关键节点
    conversation_flows = []
    
    # 限制分析的对话数量以避免处理时间过长
    sample_size = min(10000, len(conversation_ids))
    print(f"Analyzing a sample of {sample_size} conversations...")
    
    for conv_id in tqdm(conversation_ids[:sample_size], desc="Analyzing conversations"):
        conv_df = df_sorted[df_sorted['touch_id'] == conv_id]
        
        # 跳过过短的对话
        if len(conv_df) < 3:
            continue
            
        # 提取对话的开始和结束消息
        first_msg = conv_df.iloc[0]['send_content'] if not pd.isna(conv_df.iloc[0]['send_content']) else ""
        last_msg = conv_df.iloc[-1]['send_content'] if not pd.isna(conv_df.iloc[-1]['send_content']) else ""
        
        # 检查是否包含转人工请求
        has_transfer = any("人工" in str(msg) for msg in conv_df[conv_df['sender_type'] == 1.0]['send_content'] if isinstance(msg, str))
        
        # 检查对话中的关键词
        keywords_in_conv = []
        for keyword_group, keywords in {
            "价格": ["价格", "多少钱", "报价"],
            "流程": ["流程", "步骤", "如何"],
            "状态": ["订单", "物流", "到货"],
            "问题": ["问题", "故障", "坏了"],
            "数据": ["数据", "删除", "隐私"]
        }.items():
            if any(any(kw in str(msg) for kw in keywords) 
                   for msg in conv_df[conv_df['sender_type'] == 1.0]['send_content'] 
                   if isinstance(msg, str)):
                keywords_in_conv.append(keyword_group)
        
        # 对话时长
        if 'user_start_time' in conv_df.columns and 'user_end_time' in conv_df.columns:
            try:
                start_time = pd.to_datetime(conv_df['user_start_time'].iloc[0])
                end_time = pd.to_datetime(conv_df['user_end_time'].iloc[-1])
                duration_minutes = (end_time - start_time).total_seconds() / 60
            except:
                duration_minutes = None
        else:
            duration_minutes = None
            
        # 收集对话信息
        conversation_info = {
            "conversation_id": conv_id,
            "message_count": len(conv_df),
            "user_message_count": len(conv_df[conv_df['sender_type'] == 1.0]),
            "bot_message_count": len(conv_df[conv_df['sender_type'] == 2.0]),
            "first_message": first_msg[:100] if len(first_msg) > 100 else first_msg,
            "last_message": last_msg[:100] if len(last_msg) > 100 else last_msg,
            "has_transfer_request": has_transfer,
            "keywords": keywords_in_conv,
            "duration_minutes": duration_minutes
        }
        
        conversation_flows.append(conversation_info)
    
    print(f"Collected flow information for {len(conversation_flows)} conversations.")
    return conversation_flows

def main():
    # 文件路径
    file_path = os.path.join(PROJECT_ROOT, "data", "merged_chat_records.xlsx")
    
    # 加载数据
    df = load_data(file_path)
    if df is None:
        return
    
    # 开启tqdm进度条
    tqdm.pandas(desc="Processing")
    
    # 分析所有用户消息
    intent_data = analyze_all_user_messages(df)
    
    # 生成扩展的FAQ
    new_faqs = generate_extended_faq(intent_data)
    
    # 分析对话流程
    conversation_flows = analyze_conversation_flows(df)
    
    # 保存结果
    output_dir = os.path.join(PROJECT_ROOT, "analysis", "complete_analysis")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存意图分析结果
    intent_path = os.path.join(output_dir, "complete_intent_analysis.json")
    with open(intent_path, 'w', encoding='utf-8') as f:
        # 过滤掉不可序列化的数据
        serializable_data = {}
        for key, value in intent_data.items():
            if key == "top_messages":
                serializable_data[key] = [[str(k), int(v)] for k, v in value]
            elif key == "intent_categories":
                serializable_data[key] = {k: int(v) for k, v in value.items()}
            elif key == "clustering_results":
                clustering_results = {}
                for subkey, subvalue in value.items():
                    if subkey == "cluster_keywords":
                        clustering_results[subkey] = {str(k): v for k, v in subvalue.items()}
                    elif subkey == "cluster_examples":
                        clustering_results[subkey] = {str(k): v for k, v in subvalue.items()}
                    elif subkey == "cluster_sizes":
                        clustering_results[subkey] = {str(k): int(v) for k, v in subvalue.items()}
                    else:
                        clustering_results[subkey] = subvalue
                serializable_data[key] = clustering_results
            else:
                serializable_data[key] = value
        
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)
    
    # 保存扩展FAQ建议
    faq_path = os.path.join(output_dir, "extended_faq_suggestions.json")
    with open(faq_path, 'w', encoding='utf-8') as f:
        json.dump(new_faqs, f, ensure_ascii=False, indent=2)
    
    # 保存对话流程分析
    flow_path = os.path.join(output_dir, "conversation_flow_analysis.json")
    with open(flow_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_flows, f, ensure_ascii=False, indent=2)
    
    print(f"Analysis results saved to {output_dir}")
    print(f"Intent analysis: {intent_path}")
    print(f"FAQ suggestions: {faq_path}")
    print(f"Conversation flows: {flow_path}")

if __name__ == "__main__":
    main() 
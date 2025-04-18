import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import jieba
import jieba.analyse
import os
import re
import json
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 设置jieba分词的停用词
STOP_WORDS = set(['的', '了', '是', '我', '你', '他', '她', '它', '这', '那', '啊', '呢', '吗', '吧', '，', '。', '？', '！', '：', '；', '、'])

def load_data(file_path):
    """加载Excel文件数据"""
    try:
        print(f"Loading data from {file_path}...")
        df = pd.read_excel(file_path)
        print(f"Successfully loaded {len(df)} records.")
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

def extract_keywords(texts, top_n=50):
    """提取关键词"""
    # 合并所有文本
    all_text = " ".join([text for text in texts if isinstance(text, str) and text.strip()])
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(all_text, topK=top_n)
    
    return keywords

def _intents(df, n_clusters=10):
    """对用户意图进行聚类"""
    # 筛选用户消息
    user_df = df[df['sender_type'] == 1.0].copy()
    
    # 预处理用户消息文本
    print("Preprocessing user messages...")
    user_df['processed_text'] = user_df['send_content'].apply(preprocess_text)
    
    # 过滤掉空消息
    user_df = user_df[user_df['processed_text'].str.strip() != ""]
    
    # 提取前5000条消息用于聚类分析（提高计算效率）
    sample_df = user_df.sample(min(5000, len(user_df)), random_state=42)
    
    # 使用TF-IDF向量化文本
    print("Vectorizing text...")
    vectorizer = TfidfVectorizer(max_features=100)
    X = vectorizer.fit_transform(sample_df['processed_text'])
    
    # 使用K-means聚类
    print(f"Clustering into {n_clusters} groups...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    sample_df['cluster'] = kmeans.fit_predict(X)
    
    # 降维用于可视化
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X.toarray())
    sample_df['x'] = X_pca[:, 0]
    sample_df['y'] = X_pca[:, 1]
    
    # 分析每个聚类的关键词
    cluster_keywords = {}
    cluster_examples = {}
    
    for cluster_id in range(n_clusters):
        cluster_texts = sample_df[sample_df['cluster'] == cluster_id]['send_content'].tolist()
        if cluster_texts:
            # 提取关键词
            keywords = extract_keywords(cluster_texts, top_n=10)
            cluster_keywords[cluster_id] = keywords
            
            # 获取每个聚类的典型示例（最靠近中心的5个样本）
            cluster_df = sample_df[sample_df['cluster'] == cluster_id]
            cluster_center = kmeans.cluster_centers_[cluster_id]
            
            # 计算每个样本到聚类中心的距离
            distances = np.sqrt(((X_pca[sample_df['cluster'] == cluster_id] - cluster_center[:2]) ** 2).sum(axis=1))
            
            # 获取距离中心最近的5个样本
            closest_indices = distances.argsort()[:5]
            examples = cluster_df.iloc[closest_indices]['send_content'].tolist()
            cluster_examples[cluster_id] = examples
    
    # 可视化聚类结果
    plt.figure(figsize=(12, 10))
    scatter = plt.scatter(sample_df['x'], sample_df['y'], c=sample_df['cluster'], cmap='viridis', alpha=0.6)
    plt.colorbar(scatter, label='Cluster')
    plt.title('User Intent Clusters')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.tight_layout()
    
    # 保存可视化结果
    vis_path = os.path.join(PROJECT_ROOT, "analysis", "user_intent_clusters.png")
    plt.savefig(vis_path)
    plt.close()
    
    return {
        'sample_df': sample_df,
        'cluster_keywords': cluster_keywords,
        'cluster_examples': cluster_examples,
        'vis_path': vis_path
    }

def extract_common_patterns(df):
    """提取常见对话模式"""
    # 筛选用户消息
    user_df = df[df['sender_type'] == 1.0].copy()
    
    # 统计最常见的用户消息
    common_messages = Counter(user_df['send_content'].dropna())
    top_messages = common_messages.most_common(30)
    
    # 分析转人工请求
    transfer_keywords = ["人工", "转人工", "真人", "客服", "人工服务", "转接", "转接人工", "请转人工"]
    
    def is_transfer_request(text):
        if not isinstance(text, str):
            return False
        text = str(text).lower()
        return any(keyword in text for keyword in transfer_keywords)
    
    user_df['is_transfer'] = user_df['send_content'].apply(is_transfer_request)
    transfer_examples = user_df[user_df['is_transfer']]['send_content'].value_counts().head(20).to_dict()
    
    # 分析问题类型（根据关键词）
    pricing_keywords = ["价格", "多少钱", "报价", "估价", "值多少", "收多少"]
    process_keywords = ["流程", "步骤", "怎么卖", "如何卖", "卖出", "怎么回收", "回收流程"]
    model_keywords = ["型号", "配置", "几代", "多大内存", "多大存储", "参数", "规格"]
    condition_keywords = ["几成新", "有划痕", "磕碰", "外观", "电池", "电池健康", "屏幕"]
    data_keywords = ["数据", "删除", "清除", "格式化", "隐私", "个人信息", "账号"]
    
    def categorize_by_keywords(text, keyword_dict):
        if not isinstance(text, str):
            return "其他"
        text = str(text).lower()
        for category, keywords in keyword_dict.items():
            if any(keyword in text for keyword in keywords):
                return category
        return "其他"
    
    keyword_dict = {
        "价格咨询": pricing_keywords,
        "回收流程": process_keywords,
        "设备型号": model_keywords,
        "设备状况": condition_keywords,
        "数据安全": data_keywords
    }
    
    user_df['category'] = user_df['send_content'].apply(lambda x: categorize_by_keywords(x, keyword_dict))
    category_counts = user_df['category'].value_counts().to_dict()
    
    # 常见问题示例
    category_examples = {}
    for category in keyword_dict.keys():
        examples = user_df[user_df['category'] == category]['send_content'].value_counts().head(5).to_dict()
        category_examples[category] = examples
    
    return {
        'top_messages': top_messages,
        'transfer_examples': transfer_examples,
        'category_counts': category_counts,
        'category_examples': category_examples
    }

def analyze_conversation_patterns(df):
    """分析对话的序列模式"""
    # 按对话ID和序列号排序
    df = df.sort_values(['touch_id', 'seq_no'])
    
    # 分析用户的第一条消息
    first_messages = df.groupby('touch_id').first()
    first_user_messages = first_messages[first_messages['sender_type'] == 1.0]['send_content']
    
    # 统计最常见的第一条消息
    common_first = Counter(first_user_messages.dropna()).most_common(20)
    
    # 分析常见的对话流程
    # 简化版：获取每个对话的前3个回合
    conversation_starts = {}
    
    for touch_id, group in df.groupby('touch_id'):
        if len(group) >= 3:
            start_sequence = []
            for i, (_, row) in enumerate(group.iloc[:6].iterrows()):
                if pd.notna(row['send_content']):
                    sender = '用户' if row['sender_type'] == 1.0 else '客服'
                    content = str(row['send_content'])
                    if len(content) > 30:
                        content = content[:30] + "..."
                    start_sequence.append(f"{sender}: {content}")
            
            if len(start_sequence) >= 3:
                seq_key = " -> ".join(start_sequence[:3])
                conversation_starts[seq_key] = conversation_starts.get(seq_key, 0) + 1
    
    # 获取前20个最常见的对话开始序列
    common_starts = sorted(conversation_starts.items(), key=lambda x: x[1], reverse=True)[:20]
    
    return {
        'common_first_messages': common_first,
        'common_conversation_starts': common_starts
    }

def infer_intent_taxonomy(cluster_results, pattern_results):
    """根据聚类和模式分析结果推断意图分类体系"""
    # 综合分析结果创建意图分类
    intents = []
    
    # 从聚类结果中提取意图
    for cluster_id, keywords in cluster_results['cluster_keywords'].items():
        examples = cluster_results['cluster_examples'].get(cluster_id, [])
        
        # 基于关键词和示例推断意图类别
        intent_name = "未定义意图"
        
        # 检查关键词组合来确定类别
        keyword_str = " ".join(keywords)
        
        # 价格相关
        if any(word in keyword_str for word in ["价格", "多少钱", "报价", "估价"]):
            intent_name = "价格咨询"
            intent_type = "查询类"
            
        # 流程相关
        elif any(word in keyword_str for word in ["流程", "步骤", "怎么", "如何"]):
            intent_name = "流程咨询"
            intent_type = "查询类"
            
        # 设备相关
        elif any(word in keyword_str for word in ["型号", "配置", "参数", "规格"]):
            intent_name = "设备信息"
            intent_type = "查询类"
            
        # 订单相关
        elif any(word in keyword_str for word in ["订单", "物流", "发货", "收货"]):
            intent_name = "订单跟踪"
            intent_type = "查询类"
            
        # 问题相关
        elif any(word in keyword_str for word in ["问题", "故障", "坏了", "不能用"]):
            intent_name = "故障咨询"
            intent_type = "问题类"
            
        # 数据相关
        elif any(word in keyword_str for word in ["数据", "删除", "清除", "隐私"]):
            intent_name = "数据安全"
            intent_type = "查询类"
            
        # 人工服务
        elif any(word in keyword_str for word in ["人工", "客服", "转接"]):
            intent_name = "人工服务"
            intent_type = "服务类"
            
        # 同意/确认
        elif any(word in keyword_str for word in ["好的", "可以", "行", "同意"]):
            intent_name = "用户确认"
            intent_type = "交互类"
            
        # 拒绝/否定
        elif any(word in keyword_str for word in ["不行", "不可以", "不同意", "不要"]):
            intent_name = "用户拒绝"
            intent_type = "交互类"
            
        # 问候
        elif any(word in keyword_str for word in ["你好", "早上好", "下午好", "晚上好"]):
            intent_name = "用户问候"
            intent_type = "交互类"
        
        # 如果未能识别意图，尝试从示例推断
        if intent_name == "未定义意图" and examples:
            example_text = " ".join(examples)
            
            # 简单示例推断
            if "价格" in example_text or "多少钱" in example_text:
                intent_name = "价格咨询"
                intent_type = "查询类"
            elif "人工" in example_text:
                intent_name = "人工服务"
                intent_type = "服务类"
            elif "你好" in example_text:
                intent_name = "用户问候"
                intent_type = "交互类"
            else:
                intent_name = f"聚类{cluster_id}"
                intent_type = "其他类"
                
        # 构建意图对象
        intent = {
            "intent_id": f"intent_{cluster_id}",
            "intent_name": intent_name,
            "keywords": keywords,
            "examples": examples[:3],  # 最多3个示例
            "type": intent_type
        }
        
        intents.append(intent)
    
    # 添加从常见模式中发现的其他意图
    # 分析常见消息
    common_msgs = [msg for msg, _ in pattern_results['top_messages']]
    common_text = " ".join(common_msgs)
    
    # 添加确认类意图
    if not any(intent["intent_name"] == "用户确认" for intent in intents):
        if any(msg in ["好的", "可以", "行", "好", "嗯", "是的", "对"] for msg, _ in pattern_results['top_messages'][:10]):
            intents.append({
                "intent_id": "intent_confirm",
                "intent_name": "用户确认",
                "keywords": ["好的", "可以", "确认", "同意"],
                "examples": [msg for msg, _ in pattern_results['top_messages'] if msg in ["好的", "可以", "行", "好", "嗯", "是的", "对"]][:3],
                "type": "交互类"
            })
    
    # 整理意图分类体系
    taxonomy = {
        "业务场景": {
            "回收业务": [intent for intent in intents if intent["intent_name"] in ["价格咨询", "流程咨询", "设备信息", "数据安全"]],
            "售后服务": [intent for intent in intents if intent["intent_name"] in ["订单跟踪", "故障咨询"]],
            "客户服务": [intent for intent in intents if intent["intent_name"] in ["人工服务"]]
        },
        "交互意图": {
            "问候类": [intent for intent in intents if intent["intent_name"] in ["用户问候"]],
            "确认类": [intent for intent in intents if intent["intent_name"] in ["用户确认", "用户拒绝"]],
            "其他交互": [intent for intent in intents if intent["type"] == "交互类" and intent["intent_name"] not in ["用户问候", "用户确认", "用户拒绝"]]
        },
        "其他意图": [intent for intent in intents if intent["type"] not in ["查询类", "问题类", "服务类", "交互类"]]
    }
    
    return taxonomy

def generate_intent_markdown(taxonomy):
    """生成意图分类的Markdown文档"""
    markdown = "# 回收宝用户意图分类体系（基于数据分析）\n\n"
    markdown += f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    markdown += "## 意图分类总览\n\n"
    
    # 添加总览部分
    business_intents = taxonomy["业务场景"]["回收业务"] + taxonomy["业务场景"]["售后服务"] + taxonomy["业务场景"]["客户服务"]
    interaction_intents = taxonomy["交互意图"]["问候类"] + taxonomy["交互意图"]["确认类"] + taxonomy["交互意图"]["其他交互"]
    other_intents = taxonomy["其他意图"]
    
    markdown += f"- 业务场景意图: {len(business_intents)} 个\n"
    markdown += f"- 交互类意图: {len(interaction_intents)} 个\n"
    markdown += f"- 其他意图: {len(other_intents)} 个\n\n"
    
    # 添加业务场景部分
    markdown += "## 1. 业务场景意图\n\n"
    
    markdown += "### 1.1 回收业务\n\n"
    for intent in taxonomy["业务场景"]["回收业务"]:
        markdown += f"#### {intent['intent_name']}\n"
        markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
        markdown += "- **示例**:\n"
        for example in intent['examples']:
            markdown += f"  - \"{example}\"\n"
        markdown += "\n"
    
    markdown += "### 1.2 售后服务\n\n"
    for intent in taxonomy["业务场景"]["售后服务"]:
        markdown += f"#### {intent['intent_name']}\n"
        markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
        markdown += "- **示例**:\n"
        for example in intent['examples']:
            markdown += f"  - \"{example}\"\n"
        markdown += "\n"
    
    markdown += "### 1.3 客户服务\n\n"
    for intent in taxonomy["业务场景"]["客户服务"]:
        markdown += f"#### {intent['intent_name']}\n"
        markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
        markdown += "- **示例**:\n"
        for example in intent['examples']:
            markdown += f"  - \"{example}\"\n"
        markdown += "\n"
    
    # 添加交互意图部分
    markdown += "## 2. 交互类意图\n\n"
    
    markdown += "### 2.1 问候类\n\n"
    for intent in taxonomy["交互意图"]["问候类"]:
        markdown += f"#### {intent['intent_name']}\n"
        markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
        markdown += "- **示例**:\n"
        for example in intent['examples']:
            markdown += f"  - \"{example}\"\n"
        markdown += "\n"
    
    markdown += "### 2.2 确认类\n\n"
    for intent in taxonomy["交互意图"]["确认类"]:
        markdown += f"#### {intent['intent_name']}\n"
        markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
        markdown += "- **示例**:\n"
        for example in intent['examples']:
            markdown += f"  - \"{example}\"\n"
        markdown += "\n"
    
    # 添加其他意图
    if taxonomy["其他意图"]:
        markdown += "## 3. 其他意图\n\n"
        for intent in taxonomy["其他意图"]:
            markdown += f"#### {intent['intent_name']}\n"
            markdown += f"- **关键词**: {', '.join(intent['keywords'][:5])}\n"
            markdown += "- **示例**:\n"
            for example in intent['examples']:
                markdown += f"  - \"{example}\"\n"
            markdown += "\n"
    
    # 添加应用指导
    markdown += "## 应用指导\n\n"
    markdown += "### 知识库构建\n"
    markdown += "基于以上意图分类，建议按以下方向构建知识库：\n\n"
    markdown += "1. **价格咨询**: 建立不同设备型号的价格查询系统\n"
    markdown += "2. **流程咨询**: 详细说明回收流程、步骤和所需材料\n"
    markdown += "3. **设备信息**: 创建设备型号库，包含各型号详细规格\n"
    markdown += "4. **数据安全**: 提供数据删除指南和隐私保护措施\n"
    markdown += "5. **订单跟踪**: 设计订单状态查询接口和自动通知系统\n\n"
    
    markdown += "### 机器人设计\n"
    markdown += "在对话机器人设计中建议重点关注：\n\n"
    markdown += "1. 优化**交互类意图**处理，确保基础对话流畅\n"
    markdown += "2. 针对**价格咨询**和**流程咨询**这两个高频业务场景进行深度优化\n"
    markdown += "3. 对**人工服务**请求设置智能识别和转接规则\n"
    markdown += "4. 设计兜底策略，处理未能识别的意图\n"
    
    return markdown

def main():
    # 文件路径
    file_path = os.path.join(PROJECT_ROOT, "data", "merged_chat_records.xlsx")
    
    # 加载数据
    df = load_data(file_path)
    if df is None:
        return
    
    # 聚类分析用户意图
    cluster_results = _intents(df, n_clusters=15)
    
    # 提取常见对话模式
    pattern_results = extract_common_patterns(df)
    
    # 分析对话序列模式
    conversation_patterns = analyze_conversation_patterns(df)
    
    # 推断意图分类体系
    intent_taxonomy = infer_intent_taxonomy(cluster_results, pattern_results)
    
    # 生成意图分类Markdown文档
    intent_markdown = generate_intent_markdown(intent_taxonomy)
    
    # 保存结果
    output_path = os.path.join(PROJECT_ROOT, "analysis", "user_intent_taxonomy.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(intent_markdown)
    
    # 保存详细分析数据
    detailed_results = {
        'cluster_keywords': cluster_results['cluster_keywords'],
        'common_messages': pattern_results['top_messages'],
        'category_counts': pattern_results['category_counts'],
        'common_conversation_starts': conversation_patterns['common_conversation_starts']
    }
    
    json_path = os.path.join(PROJECT_ROOT, "analysis", "intent_analysis_details.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        # 转换为可序列化的格式
        serializable_results = {}
        for key, value in detailed_results.items():
            if key == 'cluster_keywords':
                serializable_results[key] = {str(k): v for k, v in value.items()}
            elif key == 'common_messages':
                serializable_results[key] = [[k, int(v)] for k, v in value]
            elif key == 'category_counts':
                serializable_results[key] = {k: int(v) for k, v in value.items()}
            elif key == 'common_conversation_starts':
                serializable_results[key] = [[k, int(v)] for k, v in value]
            else:
                serializable_results[key] = value
        
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"Intent taxonomy saved to {output_path}")
    print(f"Visualization saved to {cluster_results['vis_path']}")
    print(f"Detailed analysis saved to {json_path}")

if __name__ == "__main__":
    main() 
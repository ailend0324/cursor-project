#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import jieba
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import matplotlib.font_manager as fm

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体为黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决保存图像时负号'-'显示为方块的问题

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 停用词集合
STOPWORDS = set(['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', 
                '着', '没有', '看', '好', '自己', '这', '么', '什么', '吗', '呢', '啊',
                '吧', '把', '那', '这样', '这个', '那个', '怎么', '为什么'])

# 定义类别关键词字典
CATEGORY_KEYWORDS = {
    '产品咨询类': ['功能', '价格', '使用', '产品', '什么', '怎么样', '多少钱', '有什么', '如何', '可以'],
    '服务支持类': ['账号', '登录', '支付', '订单', '充值', '注册', '找回', '密码', '绑定', '购买'],
    '技术问题类': ['报错', '故障', '操作', '问题', '无法', '失败', '错误', '打不开', '闪退', '卡顿'],
    '业务咨询类': ['合作', '商务', '企业', '代理', '加盟', '渠道', '开发', '对接', '招商', '推广'],
    '人工转接类': ['人工', '客服', '转人工', '真人', '转接', '转客服', '接人', '人工客服', '找人工'],
}

def load_data():
    """加载Excel数据"""
    try:
        file_path = os.path.join(PROJECT_ROOT, "data", "merged_chat_records.xlsx")
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def preprocess_text(text):
    """文本预处理与分词"""
    if not isinstance(text, str):
        return ""
    
    # 清理文本
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    
    # 中文分词
    words = jieba.cut(text)
    
    # 过滤停用词
    words = [word for word in words if word not in STOPWORDS and len(word.strip()) > 0]
    
    return " ".join(words)

def categorize_question(text):
    """对问题进行分类"""
    if not isinstance(text, str):
        return "其他类"
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return "其他类"

def extract_unclassified_questions(df):
    """提取未分类的问题（其他类）"""
    # 筛选用户发送的消息
    if 'sender_type' in df.columns:
        user_messages = df[df['sender_type'] == 1.0]
    else:
        # 如果没有sender_type列，则根据其他规则筛选
        user_messages = df
    
    # 预处理文本并分类
    user_messages['processed_text'] = user_messages['send_content'].apply(preprocess_text)
    user_messages['category'] = user_messages['send_content'].apply(categorize_question)
    
    # 提取其他类问题
    unclassified = user_messages[user_messages['category'] == '其他类']
    
    # 排除空内容
    unclassified = unclassified[unclassified['processed_text'].str.len() > 0]
    
    print(f"总共找到 {len(unclassified)} 条未分类问题")
    return unclassified

def vectorize_text(df):
    """将文本转换为TF-IDF向量"""
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.9
    )
    
    X = vectorizer.fit_transform(df['processed_text'])
    feature_names = vectorizer.get_feature_names_out()
    
    print(f"向量化完成，特征维度: {X.shape}")
    return X, vectorizer, feature_names

def determine_optimal_k(X):
    """使用肘部法则确定最优K值"""
    max_k = min(15, X.shape[0] - 1)  # 防止K值过大
    if max_k < 2:
        return 2  # 数据太少，至少分为2类
    
    distortions = []
    silhouette_scores = []
    K_range = range(2, max_k + 1)
    
    for k in K_range:
        print(f"测试聚类数量: {k}")
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        distortions.append(kmeans.inertia_)
        
        if X.shape[0] > k:  # 确保样本数量大于聚类数
            score = silhouette_score(X, kmeans.labels_)
            silhouette_scores.append(score)
            print(f"轮廓系数: {score:.4f}")
        else:
            silhouette_scores.append(0)
    
    # 保存肘部法则图
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(K_range, distortions, 'bx-')
    plt.xlabel('K值（聚类数量）')
    plt.ylabel('畸变度')
    plt.title('畸变度随聚类数量变化（肘部法则）')
    
    plt.subplot(1, 2, 2)
    plt.plot(K_range, silhouette_scores, 'rx-')
    plt.xlabel('K值（聚类数量）')
    plt.ylabel('轮廓系数')
    plt.title('轮廓系数随聚类数量变化')
    
    plt.tight_layout()
    plt.savefig(os.path.join(PROJECT_ROOT, 'analysis', 'elbow_method.png'), dpi=300)
    
    # 根据轮廓系数选择最优K值
    if len(silhouette_scores) > 0:
        best_k = K_range[silhouette_scores.index(max(silhouette_scores))]
    else:
        best_k = 3  # 默认值
    
    print(f"最优聚类数量: {best_k}")
    return best_k

def perform_clustering(X, n_clusters, df):
    """执行K-Means聚类"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(X)
    
    # 添加聚类标签到DataFrame
    df_clustered = df.copy()
    df_clustered['cluster'] = kmeans.labels_
    
    # 统计每个聚类的样本数量
    cluster_counts = df_clustered['cluster'].value_counts().sort_index()
    print("\n聚类分布情况:")
    for cluster, count in cluster_counts.items():
        print(f"聚类 {cluster}: {count} 条数据 ({count/len(df_clustered)*100:.2f}%)")
    
    return df_clustered, kmeans

def visualize_clusters(X, df_clustered):
    """可视化聚类结果"""
    # 使用PCA降维到2D进行可视化
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X.toarray())
    
    # 创建可视化图
    plt.figure(figsize=(10, 8))
    
    # 每个聚类使用不同颜色
    clusters = df_clustered['cluster'].unique()
    for cluster in clusters:
        plt.scatter(
            X_pca[df_clustered['cluster'] == cluster, 0],
            X_pca[df_clustered['cluster'] == cluster, 1],
            label=f'聚类 {cluster}',
            alpha=0.7
        )
    
    plt.title('问题聚类结果可视化 (PCA降维)')
    plt.xlabel('主成分1')
    plt.ylabel('主成分2')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 保存图像
    plt.tight_layout()
    plt.savefig(os.path.join(PROJECT_ROOT, 'analysis', 'cluster_visualization.png'), dpi=300)

def extract_cluster_keywords(df_clustered, kmeans, feature_names):
    """提取每个聚类的关键词"""
    # 提取每个聚类中心的前N个关键词
    n_keywords = 10
    cluster_keywords = {}
    
    for i in range(len(kmeans.cluster_centers_)):
        # 获取聚类中心
        center = kmeans.cluster_centers_[i]
        # 获取最重要的特征索引
        top_indices = center.argsort()[-n_keywords:][::-1]
        # 获取这些索引对应的特征名称
        keywords = [feature_names[idx] for idx in top_indices]
        
        # 获取聚类的样本
        cluster_samples = df_clustered[df_clustered['cluster'] == i]
        
        # 从样本中选择一些代表性的问题
        example_questions = []
        if len(cluster_samples) > 0:
            # 选择距离聚类中心最近的5个样本作为代表
            # 这里简化处理，仅随机选择样本
            sample_size = min(5, len(cluster_samples))
            examples = cluster_samples.sample(sample_size)
            example_questions = examples['send_content'].tolist()
        
        cluster_keywords[i] = {
            'keywords': keywords,
            'sample_size': len(cluster_samples),
            'examples': example_questions
        }
    
    return cluster_keywords

def save_results(df_clustered, cluster_keywords, best_k):
    """保存聚类结果"""
    # 保存带有聚类标签的数据
    output_path = os.path.join(PROJECT_ROOT, 'analysis', 'clustered_questions.xlsx')
    df_clustered.to_excel(output_path, index=False)
    print(f"聚类结果已保存至: {output_path}")
    
    # 生成Markdown分析报告
    md_path = os.path.join(PROJECT_ROOT, 'analysis', 'unclassified_cluster_analysis.md')
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 未分类问题聚类分析报告\n\n")
        f.write(f"## 概述\n\n")
        f.write(f"- 总共分析了 {len(df_clustered)} 条未分类问题\n")
        f.write(f"- 使用K-Means算法将这些问题分为 {best_k} 个聚类\n")
        f.write(f"- 分析日期: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
        
        f.write("## 聚类分布\n\n")
        f.write("| 聚类ID | 数量 | 占比 |\n")
        f.write("|--------|------|------|\n")
        
        for cluster in sorted(df_clustered['cluster'].unique()):
            count = len(df_clustered[df_clustered['cluster'] == cluster])
            percentage = count / len(df_clustered) * 100
            f.write(f"| 聚类 {cluster} | {count} | {percentage:.2f}% |\n")
        
        f.write("\n## 聚类详情\n\n")
        
        for cluster, data in cluster_keywords.items():
            f.write(f"### 聚类 {cluster}（{data['sample_size']}条问题）\n\n")
            
            f.write("**关键词**：\n\n")
            f.write(", ".join(data['keywords']) + "\n\n")
            
            f.write("**代表性问题示例**：\n\n")
            for i, example in enumerate(data['examples'], 1):
                f.write(f"{i}. {example}\n")
            
            f.write("\n**建议分类**：[请根据关键词和示例为这个聚类指定一个合适的分类名称]\n\n")
            f.write("---\n\n")
        
        f.write("## 聚类可视化\n\n")
        f.write("![聚类可视化](cluster_visualization.png)\n\n")
        f.write("![最优K值确定](elbow_method.png)\n\n")
        
        f.write("## 建议行动\n\n")
        f.write("1. 根据聚类结果，为每个聚类指定一个有意义的分类名称\n")
        f.write("2. 更新问题分类系统，将这些新分类添加到关键词识别中\n")
        f.write("3. 针对高频问题类别，完善客服回复模板\n")
    
    print(f"分析报告已保存至: {md_path}")

def main():
    """主函数"""
    print("开始未分类问题聚类分析...")
    
    # 加载数据
    df = load_data()
    if df is None:
        return
    
    # 提取未分类问题
    unclassified = extract_unclassified_questions(df)
    if len(unclassified) < 10:
        print("未分类问题数量过少，无法进行有效聚类")
        return
    
    # 向量化文本
    X, vectorizer, feature_names = vectorize_text(unclassified)
    
    # 确定最优K值
    best_k = determine_optimal_k(X)
    
    # 执行聚类
    df_clustered, kmeans = perform_clustering(X, best_k, unclassified)
    
    # 可视化聚类结果
    visualize_clusters(X, df_clustered)
    
    # 提取聚类关键词
    cluster_keywords = extract_cluster_keywords(df_clustered, kmeans, feature_names)
    
    # 保存结果
    save_results(df_clustered, cluster_keywords, best_k)
    
    print("聚类分析完成！")

if __name__ == "__main__":
    main() 
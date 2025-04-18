#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
实现用户意图与诉求分析的第一步：增强现有数据分析功能
基于已有的analyze_chat_data.py，扩展对用户意图和诉求的深度分析
"""

import os
import sys
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
from collections import Counter, defaultdict
from datetime import datetime
import json
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from snownlp import SnowNLP

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 添加现有分析脚本路径
ANALYSIS_DIR = os.path.join(PROJECT_ROOT, 'analysis')
sys.path.insert(0, ANALYSIS_DIR)

# 尝试导入现有分析函数
try:
    from analyze_chat_data import load_data, preprocess_text, categorize_question
except ImportError:
    print("警告: 无法导入现有分析函数，将使用简化版本")
    
    def load_data(file_path):
        """加载Excel数据文件"""
        print(f"加载数据文件: {file_path}")
        try:
            df = pd.read_excel(file_path)
            print(f"成功加载 {len(df)} 条记录")
            return df
        except Exception as e:
            print(f"加载数据错误: {e}")
            sys.exit(1)
    
    def preprocess_text(text):
        """清洗和准备文本数据"""
        if not isinstance(text, str):
            return ""
        return str(text).lower().strip()
    
    def categorize_question(question):
        """基本问题分类"""
        return "未分类"

# 定义意图分类的增强关键词
INTENT_KEYWORDS = {
    "订单查询": ["订单", "查询", "状态", "物流", "到哪了", "几天", "什么时候", "快递"],
    "价格咨询": ["价格", "多少钱", "报价", "估价", "值多少", "便宜", "贵"],
    "回收流程": ["流程", "步骤", "怎么卖", "如何卖", "怎么回收", "验机", "检测"],
    "退货退款": ["退货", "退款", "取消", "不卖了", "反悔", "取回", "寄回"],
    "物流相关": ["运费", "包邮", "快递", "顺丰", "邮费", "收件", "取件"],
    "设备检测": ["检测", "验机", "擦除", "格式化", "数据", "照片", "隐私"],
    "买卖纠纷": ["纠纷", "投诉", "不满", "差评", "骗", "欺诈", "举报"],
    "人工服务": ["人工", "客服", "转人工", "电话", "联系", "等不及"],
}

# 定义诉求分类框架
DEMAND_TYPES = {
    "信息透明": ["告诉我", "说明", "解释", "说清楚", "明白", "详细"],
    "流程简化": ["简单", "麻烦", "复杂", "操作", "步骤", "方便"],
    "效率提升": ["快点", "加急", "尽快", "着急", "等不及", "赶时间"],
    "信任保障": ["保证", "承诺", "担保", "担心", "不放心", "怕"],
    "服务改进": ["态度", "服务", "不满", "建议", "改进", "提升"]
}

def process_conversation_groups(df):
    """按对话ID分组处理对话"""
    # 检查必要的列是否存在
    required_columns = ['touch_id', 'seq_no', 'sender_type', 'send_content']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"错误: 数据中缺少必要的列: {', '.join(missing_columns)}")
        return None
    
    print("按对话ID分组处理...")
    conversations = defaultdict(list)
    
    # 按touch_id分组
    for touch_id, group in df.groupby('touch_id'):
        # 按seq_no排序，确保对话顺序正确
        sorted_msgs = group.sort_values('seq_no')
        conversations[touch_id] = sorted_msgs.to_dict('records')
    
    print(f"共处理 {len(conversations)} 个对话")
    return conversations

def extract_keywords_tfidf(text, top_n=5):
    """使用TF-IDF提取关键词"""
    if not text or len(text.strip()) < 5:
        return []
    
    try:
        # 使用jieba的TF-IDF实现
        keywords = jieba.analyse.extract_tags(text, topK=top_n)
        return keywords
    except Exception as e:
        print(f"提取关键词错误: {e}")
        return []

def analyze_intent(message, context=None):
    """分析用户意图"""
    if not message or not isinstance(message, str):
        return "未知意图"
    
    # 预处理文本
    text = preprocess_text(message)
    if len(text) < 2:  # 跳过过短的消息
        return "简短回复"
    
    # 关键词匹配法确定意图
    intent_scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            intent_scores[intent] = score
    
    # 如果有明确的意图匹配
    if intent_scores:
        # 返回得分最高的意图
        return max(intent_scores.items(), key=lambda x: x[1])[0]
    
    # 如果是问候语
    greetings = ["你好", "您好", "早上好", "下午好", "晚上好", "在吗"]
    if any(greeting in text for greeting in greetings) and len(text) < 10:
        return "问候语"
    
    # 如果是简单确认
    confirmations = ["好的", "可以", "行", "嗯", "对", "是的", "好"]
    if any(confirm in text for confirm in confirmations) and len(text) < 5:
        return "确认回复"
    
    # 考虑上下文（如果提供）
    if context and isinstance(context, list) and len(context) > 0:
        # 获取前面的意图并考虑延续性
        prev_intents = [msg.get('intent') for msg in context if msg.get('intent') != "未知意图"]
        if prev_intents:
            return prev_intents[-1]  # 返回最近的有效意图
    
    # 默认分类
    return "其他咨询"

def analyze_sentiment(text):
    """分析文本情感倾向"""
    if not text or len(text.strip()) < 5:
        return 0.5  # 中性
    
    try:
        return SnowNLP(text).sentiments
    except:
        return 0.5  # 出错时返回中性

def extract_user_demand(message, intent, sentiment=None):
    """基于意图和情感分析提取用户诉求"""
    if not message or not intent:
        return "未知诉求"
    
    text = preprocess_text(message)
    
    # 基于情感和关键词判断诉求类型
    demand_scores = {}
    for demand_type, keywords in DEMAND_TYPES.items():
        score = sum(1 for keyword in keywords if keyword in text)
        demand_scores[demand_type] = score
    
    # 如果有明确的诉求匹配
    if any(score > 0 for score in demand_scores.values()):
        primary_demand = max(demand_scores.items(), key=lambda x: x[1])[0]
    else:
        # 基于意图的默认诉求
        intent_demand_mapping = {
            "订单查询": "信息透明",
            "价格咨询": "信息透明",
            "回收流程": "流程简化",
            "退货退款": "效率提升",
            "物流相关": "效率提升",
            "设备检测": "信任保障",
            "买卖纠纷": "信任保障",
            "人工服务": "服务改进"
        }
        primary_demand = intent_demand_mapping.get(intent, "未知诉求")
    
    # 考虑情感因素
    if sentiment is not None:
        if sentiment < 0.3:  # 负面情感
            # 对于负面情感，优先考虑效率和服务
            if primary_demand not in ["效率提升", "服务改进"]:
                if "快" in text or "急" in text:
                    primary_demand = "效率提升"
                elif "态度" in text or "服务" in text:
                    primary_demand = "服务改进"
    
    return primary_demand

def analyze_conversations(conversations):
    """深度分析对话，提取意图和诉求"""
    intent_stats = Counter()
    demand_stats = Counter()
    intent_demand_matrix = defaultdict(Counter)
    
    conversation_analysis = {}
    
    for touch_id, messages in conversations.items():
        # 初始化对话分析
        conversation_analysis[touch_id] = {
            "messages": [],
            "intents": Counter(),
            "demands": Counter(),
            "primary_intent": None,
            "primary_demand": None,
            "message_count": len(messages),
            "user_message_count": sum(1 for m in messages if m['sender_type'] == 1.0),
            "transfer_requested": any("人工" in str(m.get('send_content', '')) for m in messages if m['sender_type'] == 1.0)
        }
        
        # 处理每条消息
        conversation_context = []
        
        for msg in messages:
            if msg['sender_type'] != 1.0:  # 只处理用户消息
                continue
                
            content = msg.get('send_content', '')
            if not content or not isinstance(content, str):
                continue
            
            # 提取意图和诉求
            msg_intent = analyze_intent(content, conversation_context)
            sentiment = analyze_sentiment(content)
            msg_demand = extract_user_demand(content, msg_intent, sentiment)
            
            # 更新消息分析
            msg_analysis = {
                "seq_no": msg.get('seq_no'),
                "content": content,
                "keywords": extract_keywords_tfidf(content),
                "intent": msg_intent,
                "sentiment": sentiment,
                "demand": msg_demand
            }
            
            conversation_context.append(msg_analysis)
            conversation_analysis[touch_id]["messages"].append(msg_analysis)
            
            # 更新统计
            conversation_analysis[touch_id]["intents"][msg_intent] += 1
            conversation_analysis[touch_id]["demands"][msg_demand] += 1
            
            intent_stats[msg_intent] += 1
            demand_stats[msg_demand] += 1
            intent_demand_matrix[msg_intent][msg_demand] += 1
        
        # 确定主要意图和诉求
        if conversation_analysis[touch_id]["intents"]:
            conversation_analysis[touch_id]["primary_intent"] = conversation_analysis[touch_id]["intents"].most_common(1)[0][0]
        
        if conversation_analysis[touch_id]["demands"]:
            conversation_analysis[touch_id]["primary_demand"] = conversation_analysis[touch_id]["demands"].most_common(1)[0][0]
    
    # 汇总分析结果
    summary = {
        "total_conversations": len(conversations),
        "intent_distribution": {intent: count for intent, count in intent_stats.most_common()},
        "demand_distribution": {demand: count for demand, count in demand_stats.most_common()},
        "intent_demand_matrix": {intent: dict(demands) for intent, demands in intent_demand_matrix.items()},
        "transfer_requested_count": sum(1 for data in conversation_analysis.values() if data["transfer_requested"])
    }
    
    return conversation_analysis, summary

def generate_visualization(summary, output_dir):
    """生成分析可视化图表"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 意图分布饼图
    plt.figure(figsize=(12, 8))
    intents = summary["intent_distribution"]
    labels = list(intents.keys())
    sizes = list(intents.values())
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('用户意图分布')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'intent_distribution_pie.png'))
    plt.close()
    
    # 2. 诉求分布条形图
    plt.figure(figsize=(12, 8))
    demands = summary["demand_distribution"]
    plt.bar(demands.keys(), demands.values())
    plt.title('用户诉求分布')
    plt.xlabel('诉求类型')
    plt.ylabel('频次')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'demand_distribution_bar.png'))
    plt.close()
    
    # 3. 意图-诉求热力图
    intent_demand = summary["intent_demand_matrix"]
    # 转换为DataFrame便于绘图
    intents = list(intent_demand.keys())
    demands = set()
    for demand_dict in intent_demand.values():
        demands.update(demand_dict.keys())
    demands = list(demands)
    
    # 创建矩阵数据
    matrix_data = []
    for intent in intents:
        row = []
        for demand in demands:
            row.append(intent_demand[intent].get(demand, 0))
        matrix_data.append(row)
    
    if matrix_data:  # 确保有数据再绘图
        matrix_df = pd.DataFrame(matrix_data, index=intents, columns=demands)
        
        plt.figure(figsize=(14, 10))
        sns = plt.cm.Blues  # 使用蓝色渐变色
        plt.imshow(matrix_df.values, cmap=sns)
        
        # 设置坐标轴
        plt.xticks(np.arange(len(demands)), demands, rotation=45)
        plt.yticks(np.arange(len(intents)), intents)
        
        # 添加颜色条和标题
        plt.colorbar(label='频次')
        plt.title('意图-诉求关联热力图')
        
        # 在单元格中添加数值
        for i in range(len(intents)):
            for j in range(len(demands)):
                text = plt.text(j, i, matrix_df.iloc[i, j],
                              ha="center", va="center", color="w" if matrix_df.iloc[i, j] > 10 else "black")
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'intent_demand_heatmap.png'))
        plt.close()
    
    print(f"可视化图表已保存至: {output_dir}")

def save_analysis_results(conversation_analysis, summary, output_dir):
    """保存分析结果到文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存统计汇总
    with open(os.path.join(output_dir, 'analysis_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # 保存详细分析结果 (可能很大，考虑分批保存)
    batch_size = 1000
    conversation_ids = list(conversation_analysis.keys())
    
    for i in range(0, len(conversation_ids), batch_size):
        batch_ids = conversation_ids[i:i+batch_size]
        batch_data = {conv_id: conversation_analysis[conv_id] for conv_id in batch_ids}
        
        batch_filename = f'conversation_analysis_batch_{i//batch_size+1}.json'
        with open(os.path.join(output_dir, batch_filename), 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
    
    print(f"分析结果已保存至: {output_dir}")

def generate_faq_suggestions(summary, output_dir):
    """基于分析生成FAQ建议"""
    # 提取高频意图
    top_intents = list(summary["intent_distribution"].keys())[:10]
    
    faq_suggestions = []
    
    # 为每个高频意图生成FAQ条目
    for intent in top_intents:
        # 获取该意图的主要诉求
        if intent in summary["intent_demand_matrix"]:
            demands = summary["intent_demand_matrix"][intent]
            primary_demand = max(demands.items(), key=lambda x: x[1])[0] if demands else "未知诉求"
            
            # 根据意图创建FAQ条目
            if intent == "订单查询":
                faq_suggestions.append({
                    "question": "如何查询我的订单状态？",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": "您可以通过以下方式查询订单状态：1.打开APP，在\"我的订单\"中查看；2.登录官网，在个人中心查询；3.提供订单号，我们可以为您实时查询当前状态。",
                    "scenarios": ["所有"]
                })
            elif intent == "价格咨询":
                faq_suggestions.append({
                    "question": "回收价格是如何评估的？",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": "回收价格根据设备型号、配置、使用状况、市场行情等因素综合评估。我们会通过专业检测设备的外观和功能，最终给出合理报价。",
                    "scenarios": ["所有"]
                })
            elif intent == "回收流程":
                faq_suggestions.append({
                    "question": "回收流程是怎样的？",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": "回收流程包括：1.提交设备信息获取预估价；2.确认回收并选择回收方式(快递寄送/上门取件)；3.设备到达后进行专业检测；4.确认最终回收价格；5.双方确认后支付回收款项。整个流程通常需要3-7个工作日。",
                    "scenarios": ["所有"]
                })
            elif intent == "退货退款":
                faq_suggestions.append({
                    "question": "我不想卖了，可以退货吗？",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": "完全理解！请提供订单号、退货地址和联系方式，我们会通过顺丰到付寄回，24小时内发送物流单号。您也可通过APP/官网的退货申请链接自助申请。",
                    "scenarios": ["上门&到店回收", "邮寄回收"]
                })
            elif intent == "人工服务":
                faq_suggestions.append({
                    "question": "如何联系人工客服？",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": "您可以通过以下方式联系人工客服：1.在对话中直接输入"人工客服"或"转人工"；2.拨打客服热线400-888-9999（工作时间9:00-21:00）；3.在APP或官网的"联系我们"中提交客服工单。",
                    "scenarios": ["所有"]
                })
            else:
                # 为其他意图生成通用FAQ条目
                faq_suggestions.append({
                    "question": f"关于{intent}的常见问题",
                    "intent": intent,
                    "demand": primary_demand,
                    "answer": f"这是关于{intent}的标准回答，需要根据具体情况进一步完善。",
                    "scenarios": ["所有"]
                })
    
    # 保存FAQ建议
    with open(os.path.join(output_dir, 'faq_suggestions.json'), 'w', encoding='utf-8') as f:
        json.dump(faq_suggestions, f, ensure_ascii=False, indent=2)
    
    print(f"FAQ建议已保存至: {output_dir}/faq_suggestions.json")

def main():
    """主函数"""
    # 设置输入和输出路径
    data_file = os.path.join(PROJECT_ROOT, 'data', 'merged_chat_records.xlsx')
    output_dir = os.path.join(PROJECT_ROOT, 'analysis', 'intent_analysis_results')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 加载数据
    print("开始加载数据...")
    df = load_data(data_file)
    
    # 2. 按对话分组处理
    print("开始按对话分组...")
    conversations = process_conversation_groups(df)
    if not conversations:
        print("处理对话失败，退出。")
        return
    
    # 3. 分析对话意图和诉求
    print("开始深度分析对话...")
    conversation_analysis, summary = analyze_conversations(conversations)
    
    # 4. 保存分析结果
    print("保存分析结果...")
    save_analysis_results(conversation_analysis, summary, output_dir)
    
    # 5. 生成可视化
    print("生成可视化图表...")
    try:
        import matplotlib.pyplot as plt
        generate_visualization(summary, os.path.join(output_dir, 'visualizations'))
    except ImportError:
        print("警告: 缺少matplotlib库，无法生成可视化图表")
    
    # 6. 生成FAQ建议
    print("生成FAQ建议...")
    generate_faq_suggestions(summary, output_dir)
    
    print("分析完成！结果已保存到:", output_dir)

if __name__ == "__main__":
    main()
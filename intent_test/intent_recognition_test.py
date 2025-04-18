#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 意图识别测试脚本
该脚本实现了多维度混合识别框架的核心功能，用于测试小数据集上的效果
"""

import pandas as pd
import re
import json
import jieba
import jieba.analyse
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime

# 文件路径
DATA_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
OUTPUT_DIR = '/Users/boxie/cursor/intent_test'

# ================ 1. 数据预处理增强 ================

def load_data(file_path):
    """加载Excel数据文件"""
    print(f"正在加载数据: {file_path}")
    df = pd.read_excel(file_path)
    print(f"数据加载完成，共 {len(df)} 行")
    return df

def preprocess_data(df):
    """数据预处理：清洗、结构化和发送者识别"""
    # 复制数据，避免修改原始数据
    processed_df = df.copy()
    
    # 处理缺失值
    processed_df = processed_df.dropna(subset=['send_content'])
    
    # 统一时间格式
    if 'send_time' in processed_df.columns:
        processed_df['send_time'] = pd.to_datetime(processed_df['send_time'], errors='coerce')
    
    # 按对话ID和序号排序
    if 'touch_id' in processed_df.columns and 'seq_no' in processed_df.columns:
        processed_df = processed_df.sort_values(['touch_id', 'seq_no'])
    
    # 提取结构化信息
    processed_df['order_number'] = processed_df['send_content'].apply(extract_order_number)
    processed_df['logistics_number'] = processed_df['send_content'].apply(extract_logistics_number)
    
    # 清理文本内容
    processed_df['clean_content'] = processed_df['send_content'].apply(clean_text)
    
    # 识别发送者类型（如果没有sender_type字段）
    if 'sender_type' not in processed_df.columns:
        processed_df = identify_sender_types(processed_df)
    
    print(f"数据预处理完成，处理后 {len(processed_df)} 行")
    return processed_df

def extract_order_number(text):
    """提取订单号"""
    if not isinstance(text, str):
        return None
    
    # 常见订单号模式
    patterns = [
        r'订单号[:：]?\s*(\d{20,25})',  # 匹配"订单号:1234567890123456789"格式
        r'订单\s*[号#]?\s*[为是]?\s*(\d{20,25})',  # 匹配"订单号是1234567890123456789"格式
        r'(\d{20,25})'  # 匹配独立的长数字（可能是订单号）
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def extract_logistics_number(text):
    """提取物流单号"""
    if not isinstance(text, str):
        return None
    
    # 常见物流单号模式
    patterns = [
        r'快递单号[:：]?\s*([A-Za-z0-9]{10,15})',  # 匹配"快递单号:SF1234567890"格式
        r'物流单号[:：]?\s*([A-Za-z0-9]{10,15})',  # 匹配"物流单号:SF1234567890"格式
        r'运单号[:：]?\s*([A-Za-z0-9]{10,15})',    # 匹配"运单号:SF1234567890"格式
        r'SF(\d{10,12})',                        # 匹配顺丰单号格式
        r'YT(\d{10,12})',                        # 匹配圆通单号格式
        r'ZTO(\d{10,12})'                        # 匹配中通单号格式
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def clean_text(text):
    """清理文本内容，保留语义信息"""
    if not isinstance(text, str):
        return ""
    
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 处理表情符号，保留语义
    text = re.sub(r'\[ww:天使\]', '[微笑]', text)
    text = re.sub(r'\[ww:飞吻\]', '[亲吻]', text)
    text = re.sub(r'\[ww:.*?\]', '', text)
    
    # 处理图片链接
    text = re.sub(r'<img\s+src="[^"]*"[^>]*>', '[图片]', text)
    
    # 敏感信息脱敏
    text = re.sub(r'1[3-9]\d{9}', '[手机号]', text)
    text = re.sub(r'\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', '[邮箱]', text)
    
    return text.strip()

def identify_sender_types(df):
    """识别发送者类型"""
    # 客服特征词
    service_keywords = ['您好', '感谢', '请问', '祝您', '很高兴为您服务', '请稍等', 
                        '亲', '已经进入人工服务', '回收宝', '小宝', '客服', 
                        '有什么可以帮到您', '请问有什么可以帮到您']
    
    # 用户特征词
    user_keywords = ['怎么', '什么时候', '多久', '多少钱', '谢谢', '我的', 
                     '订单号', '快递', '物流', '取消', '退款']
    
    # 添加发送者类型列
    if 'sender_type' not in df.columns:
        df['sender_type'] = None
    
    # 按对话分组处理
    for touch_id, group in df.groupby('touch_id'):
        prev_type = None
        
        for idx, row in group.iterrows():
            content = str(row['clean_content'])
            
            # 根据内容特征判断发送者类型
            service_score = sum([1 for word in service_keywords if word in content])
            user_score = sum([1 for word in user_keywords if word in content])
            
            # 初步判断
            if service_score > user_score:
                current_type = 2  # 客服
            elif user_score > service_score:
                current_type = 1  # 用户
            else:
                # 如果无法通过关键词判断，则考虑交替规则
                if prev_type == 1:
                    current_type = 2
                elif prev_type == 2:
                    current_type = 1
                else:
                    # 默认第一条是客服消息
                    current_type = 2
            
            df.at[idx, 'sender_type'] = current_type
            prev_type = current_type
    
    return df

def organize_dialogs(df):
    """将扁平数据组织为对话结构"""
    dialogs = []
    
    for touch_id, group in df.groupby('touch_id'):
        # 按seq_no排序
        group = group.sort_values('seq_no')
        
        # 提取用户消息
        user_messages = group[group['sender_type'] == 1]
        
        # 创建对话结构
        dialog = {
            "conversation_id": touch_id,
            "metadata": {
                "group_name": group['group_name'].iloc[0] if 'group_name' in group.columns else "",
                "start_time": group['send_time'].min().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
                "end_time": group['send_time'].max().strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in group.columns else "",
            },
            "statistics": {
                "message_count": len(group),
                "user_message_count": len(user_messages),
                "service_message_count": len(group) - len(user_messages),
            },
            "messages": [],
            "user_messages": [],
            "structured_info": {
                "order_numbers": list(filter(None, group['order_number'].unique())),
                "logistics_numbers": list(filter(None, group['logistics_number'].unique())),
            }
        }
        
        # 添加消息
        for _, row in group.iterrows():
            message = {
                "seq_no": row['seq_no'],
                "sender_type": row['sender_type'],
                "content": row['send_content'],
                "clean_content": row['clean_content'],
                "send_time": row['send_time'].strftime('%Y-%m-%d %H:%M:%S') if 'send_time' in row else "",
            }
            dialog["messages"].append(message)
            
            # 收集用户消息
            if row['sender_type'] == 1:
                dialog["user_messages"].append(message)
        
        dialogs.append(dialog)
    
    print(f"对话组织完成，共 {len(dialogs)} 个对话")
    return dialogs

# ================ 2. 多层次意图识别 ================

def extract_keywords(text, topK=5):
    """提取文本关键词"""
    if not isinstance(text, str) or not text.strip():
        return []
    
    # 使用jieba提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=topK)
    return keywords

def classify_business_scenario(dialog):
    """第一层：业务场景分类"""
    # 业务场景关键词映射
    scenario_keywords = {
        "回收估价": ["回收", "估价", "价格", "多少钱", "收购", "卖", "值多少"],
        "邮寄流程": ["邮寄", "快递", "物流", "顺丰", "运费", "包装", "寄", "发货"],
        "验货问题": ["验货", "检测", "质量", "评估", "验机", "检查", "测试"],
        "订单管理": ["订单", "下单", "取消", "修改", "查询", "进度", "状态"],
        "售后服务": ["退款", "投诉", "不满意", "问题", "售后", "赔偿", "退货"]
    }
    
    # 合并所有用户消息
    all_user_content = " ".join([msg["clean_content"] for msg in dialog["user_messages"]])
    
    # 提取关键词
    keywords = extract_keywords(all_user_content, topK=10)
    
    # 计算各场景得分
    scenario_scores = {}
    for scenario, scenario_kws in scenario_keywords.items():
        score = sum([1 for kw in keywords if kw in scenario_kws])
        # 检查结构化信息
        if scenario == "订单管理" and dialog["structured_info"]["order_numbers"]:
            score += 3  # 有订单号加分
        if scenario == "邮寄流程" and dialog["structured_info"]["logistics_numbers"]:
            score += 3  # 有物流单号加分
        scenario_scores[scenario] = score
    
    # 如果所有场景得分为0，返回"其他"
    if sum(scenario_scores.values()) == 0:
        return "其他"
    
    # 返回得分最高的场景
    return max(scenario_scores.items(), key=lambda x: x[1])[0]

def recognize_intent_in_scenario(dialog, business_scenario):
    """第二层：场景内意图识别"""
    # 各业务场景下的意图关键词映射
    intent_keywords = {
        "回收估价": {
            "价格咨询": ["多少钱", "价格", "报价", "估价", "值多少"],
            "回收条件": ["回收条件", "能回收吗", "收不收", "要求", "标准"],
            "加价服务": ["加价", "提价", "价格高", "多给钱"]
        },
        "邮寄流程": {
            "发货查询": ["发货", "发出", "寄出", "快递", "物流", "单号"],
            "收货确认": ["收到", "签收", "到货", "收货"],
            "物流问题": ["延迟", "丢失", "损坏", "没收到", "问题"]
        },
        "验货问题": {
            "检测结果查询": ["检测结果", "验货结果", "检测完了吗", "结果"],
            "检测标准咨询": ["检测标准", "怎么检测", "验机标准", "标准"],
            "检测异议": ["不同意", "有异议", "不认可", "不对", "错误"]
        },
        "订单管理": {
            "订单查询": ["查询", "查订单", "订单状态", "进度", "怎么样了"],
            "订单取消": ["取消", "不卖了", "不要了", "撤销", "关闭"],
            "订单修改": ["修改", "变更", "改", "更新", "更改"]
        },
        "售后服务": {
            "退款查询": ["退款", "钱", "到账", "退", "返还"],
            "投诉处理": ["投诉", "不满", "差评", "态度", "服务差"],
            "建议反馈": ["建议", "意见", "反馈", "改进"]
        },
        "其他": {
            "问候": ["你好", "您好", "早上好", "下午好", "晚上好"],
            "感谢": ["谢谢", "感谢", "多谢", "谢了"],
            "告别": ["再见", "拜拜", "goodbye", "88"],
            "其他查询": ["怎么", "如何", "是什么", "能不能", "可以吗"]
        }
    }
    
    # 如果业务场景不在预定义场景中，默认为"其他"
    if business_scenario not in intent_keywords:
        business_scenario = "其他"
    
    # 合并所有用户消息
    all_user_content = " ".join([msg["clean_content"] for msg in dialog["user_messages"]])
    
    # 提取关键词
    keywords = extract_keywords(all_user_content, topK=15)
    
    # 计算各意图得分
    intent_scores = {}
    for intent, intent_kws in intent_keywords[business_scenario].items():
        score = sum([1 for kw in keywords if kw in intent_kws])
        
        # 特殊规则增强
        if intent == "订单查询" and dialog["structured_info"]["order_numbers"]:
            score += 2  # 有订单号加分
        if intent == "发货查询" and dialog["structured_info"]["logistics_numbers"]:
            score += 2  # 有物流单号加分
        if intent == "订单取消" and any(["取消" in msg["clean_content"] or "不要了" in msg["clean_content"] for msg in dialog["user_messages"]]):
            score += 3  # 明确表达取消意图加分
            
        intent_scores[intent] = score
    
    # 如果所有意图得分为0，返回"其他查询"
    if sum(intent_scores.values()) == 0:
        return "其他查询"
    
    # 返回得分最高的意图
    return max(intent_scores.items(), key=lambda x: x[1])[0]

def refine_intent_with_entities(dialog, business_scenario, intent):
    """第三层：实体关联分析"""
    # 特定实体与意图的强关联规则
    if dialog["structured_info"]["order_numbers"]:
        if "取消" in " ".join([msg["clean_content"] for msg in dialog["user_messages"]]):
            return "订单取消", 0.9  # 有订单号+取消关键词，高置信度判定为订单取消
        elif "查" in " ".join([msg["clean_content"] for msg in dialog["user_messages"]]):
            return "订单查询", 0.9  # 有订单号+查询关键词，高置信度判定为订单查询
    
    if dialog["structured_info"]["logistics_numbers"]:
        if any(["到" in msg["clean_content"] or "收" in msg["clean_content"] for msg in dialog["user_messages"]]):
            return "收货确认", 0.85  # 有物流单号+收货关键词，较高置信度判定为收货确认
        else:
            return "发货查询", 0.85  # 有物流单号，较高置信度判定为发货查询
    
    # 计算置信度
    confidence = 0.7  # 默认置信度
    
    # 根据业务场景和意图调整置信度
    if business_scenario == "其他" or intent == "其他查询":
        confidence = 0.5  # 其他类别置信度较低
    
    return intent, confidence

def analyze_dialog_intent(dialog):
    """对单个对话进行多层次意图分析"""
    # 第一层：业务场景分类
    business_scenario = classify_business_scenario(dialog)
    
    # 第二层：场景内意图识别
    intent = recognize_intent_in_scenario(dialog, business_scenario)
    
    # 第三层：实体关联分析
    refined_intent, confidence = refine_intent_with_entities(dialog, business_scenario, intent)
    
    # 返回分析结果
    return {
        "conversation_id": dialog["conversation_id"],
        "business_scenario": business_scenario,
        "intent": refined_intent,
        "confidence": confidence,
        "user_message_count": dialog["statistics"]["user_message_count"],
        "total_message_count": dialog["statistics"]["message_count"]
    }

# ================ 主函数 ================

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 意图识别测试")
    print("=" * 50)
    
    # 1. 加载数据
    df = load_data(DATA_FILE)
    
    # 2. 数据预处理
    processed_df = preprocess_data(df)
    
    # 3. 组织对话结构
    dialogs = organize_dialogs(processed_df)
    
    # 4. 意图分析
    intent_results = []
    for dialog in dialogs:
        intent_result = analyze_dialog_intent(dialog)
        intent_results.append(intent_result)
    
    # 5. 生成分析报告
    generate_report(intent_results)
    
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)

def generate_report(intent_results):
    """生成意图分析报告"""
    # 保存详细结果
    with open(f"{OUTPUT_DIR}/intent_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(intent_results, f, ensure_ascii=False, indent=2)
    
    # 统计业务场景分布
    scenario_counts = Counter([result["business_scenario"] for result in intent_results])
    total_dialogs = len(intent_results)
    
    # 统计意图分布
    intent_counts = Counter([result["intent"] for result in intent_results])
    
    # 统计置信度分布
    confidence_levels = {
        "高 (>0.8)": len([r for r in intent_results if r["confidence"] > 0.8]),
        "中 (0.6-0.8)": len([r for r in intent_results if 0.6 <= r["confidence"] <= 0.8]),
        "低 (<0.6)": len([r for r in intent_results if r["confidence"] < 0.6])
    }
    
    # 生成报告
    report = {
        "总对话数": total_dialogs,
        "业务场景分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in scenario_counts.items()},
        "意图分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in intent_counts.items()},
        "置信度分布": {k: {"数量": v, "占比": f"{v/total_dialogs*100:.2f}%"} for k, v in confidence_levels.items()},
        "其他类别占比": f"{intent_counts.get('其他查询', 0)/total_dialogs*100:.2f}%",
        "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 保存报告
    with open(f"{OUTPUT_DIR}/intent_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 打印报告摘要
    print("\n" + "=" * 50)
    print("意图分析报告摘要")
    print("=" * 50)
    print(f"总对话数: {total_dialogs}")
    print("\n业务场景分布:")
    for scenario, count in scenario_counts.most_common():
        print(f"  - {scenario}: {count} ({count/total_dialogs*100:.2f}%)")
    
    print("\n意图分布:")
    for intent, count in intent_counts.most_common():
        print(f"  - {intent}: {count} ({count/total_dialogs*100:.2f}%)")
    
    print(f"\n'其他'类别占比: {intent_counts.get('其他查询', 0)/total_dialogs*100:.2f}%")
    print("=" * 50)

if __name__ == "__main__":
    main()

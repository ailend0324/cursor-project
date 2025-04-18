#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 意图识别方法C：上下文增强识别法
重点关注对话历史和上下文，考虑客服问题和用户回答的对应关系
"""

import sys
from intent_recognition_common import *

# ================ 方法C：上下文增强识别法 ================

def method_c_analyze_intent(dialog):
    """
    方法C：上下文增强识别法
    重点关注对话历史和上下文，考虑客服问题和用户回答的对应关系
    """
    # 意图关键词映射（与方法A相同）
    intent_keywords = {
        "订单查询": ["订单", "查询", "查", "订单号", "进度", "状态", "怎么样了"],
        "订单取消": ["取消", "不卖了", "不要了", "撤销", "关闭"],
        "订单修改": ["修改", "变更", "改", "更新", "更改"],
        "发货查询": ["发货", "发出", "寄出", "快递", "物流", "单号", "什么时候发"],
        "收货确认": ["收到", "签收", "到货", "收货"],
        "物流问题": ["延迟", "丢失", "损坏", "没收到", "问题"],
        "价格咨询": ["多少钱", "价格", "报价", "估价", "值多少", "价钱"],
        "回收条件": ["回收条件", "能回收吗", "收不收", "要求", "标准"],
        "加价服务": ["加价", "提价", "价格高", "多给钱"],
        "检测结果查询": ["检测结果", "验货结果", "检测完了吗", "结果"],
        "检测标准咨询": ["检测标准", "怎么检测", "验机标准", "标准"],
        "检测异议": ["不同意", "有异议", "不认可", "不对", "错误"],
        "退款查询": ["退款", "钱", "到账", "退", "返还"],
        "投诉处理": ["投诉", "不满", "差评", "态度", "服务差"],
        "建议反馈": ["建议", "意见", "反馈", "改进"],
        "问候": ["你好", "您好", "早上好", "下午好", "晚上好"],
        "感谢": ["谢谢", "感谢", "多谢", "谢了"],
        "告别": ["再见", "拜拜", "goodbye", "88"]
    }
    
    # 业务场景映射
    scenario_mapping = {
        "订单查询": "订单管理",
        "订单取消": "订单管理",
        "订单修改": "订单管理",
        "发货查询": "邮寄流程",
        "收货确认": "邮寄流程",
        "物流问题": "邮寄流程",
        "价格咨询": "回收估价",
        "回收条件": "回收估价",
        "加价服务": "回收估价",
        "检测结果查询": "验货问题",
        "检测标准咨询": "验货问题",
        "检测异议": "验货问题",
        "退款查询": "售后服务",
        "投诉处理": "售后服务",
        "建议反馈": "售后服务",
        "问候": "其他",
        "感谢": "其他",
        "告别": "其他"
    }
    
    # 客服问题模式及对应意图
    service_question_patterns = {
        "有什么可以帮到您": None,  # 开放性问题，需要根据用户回答判断
        "请问有什么能帮到您": None,  # 开放性问题，需要根据用户回答判断
        "请问是要查询订单": "订单查询",
        "请问是要取消订单": "订单取消",
        "请问是要查询物流": "发货查询",
        "请问是关于价格的咨询": "价格咨询",
        "请问是关于检测的问题": "检测结果查询",
        "请问是要退款": "退款查询"
    }
    
    # 意图转换标志词
    intent_transition_words = ["另外", "还有", "对了", "顺便问一下", "再问一下", "还想问"]
    
    # 提取所有消息（按顺序）
    messages = dialog["messages"]
    
    # 初始化意图列表（可能有多个意图）
    detected_intents = []
    
    # 分析对话流
    for i in range(len(messages)):
        msg = messages[i]
        
        # 只分析用户消息
        if msg["sender_type"] != 1:
            continue
        
        # 获取当前用户消息
        user_content = msg["clean_content"]
        
        # 查找前一条客服消息（如果存在）
        prev_service_msg = None
        for j in range(i-1, -1, -1):
            if messages[j]["sender_type"] == 2:
                prev_service_msg = messages[j]["clean_content"]
                break
        
        # 基于客服问题判断意图
        if prev_service_msg:
            for pattern, intent in service_question_patterns.items():
                if pattern in prev_service_msg:
                    if intent:  # 如果是特定意图的问题
                        detected_intents.append((intent, 0.8))  # 较高置信度
                    break
        
        # 检查意图转换标志词
        has_transition = any(word in user_content for word in intent_transition_words)
        
        # 基于关键词匹配判断意图
        intent_scores = {}
        for intent, keywords in intent_keywords.items():
            score = sum([1 for keyword in keywords if keyword in user_content])
            if score > 0:
                intent_scores[intent] = score
        
        # 如果有意图转换标志词，且找到了新意图，添加到列表
        if has_transition and intent_scores:
            new_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            max_score = intent_scores[new_intent]
            total_score = sum(intent_scores.values())
            confidence = min(0.4 + (max_score / total_score) * 0.4, 0.9)  # 置信度范围：0.4-0.9
            detected_intents.append((new_intent, confidence))
        # 如果是对话开始的第一条用户消息，且找到了意图，添加到列表
        elif i <= 3 and intent_scores:  # 假设前3条消息中的用户消息是开场白
            new_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
            max_score = intent_scores[new_intent]
            total_score = sum(intent_scores.values())
            confidence = min(0.5 + (max_score / total_score) * 0.4, 0.9)  # 置信度范围：0.5-0.9
            detected_intents.append((new_intent, confidence))
    
    # 特殊规则增强
    if dialog["structured_info"]["order_numbers"]:
        # 检查是否有取消关键词
        all_user_content = " ".join([msg["clean_content"] for msg in dialog["user_messages"]])
        if "取消" in all_user_content or "不要了" in all_user_content:
            detected_intents.append(("订单取消", 0.9))
        else:
            detected_intents.append(("订单查询", 0.85))
    
    if dialog["structured_info"]["logistics_numbers"]:
        all_user_content = " ".join([msg["clean_content"] for msg in dialog["user_messages"]])
        if "收到" in all_user_content or "签收" in all_user_content:
            detected_intents.append(("收货确认", 0.9))
        else:
            detected_intents.append(("发货查询", 0.85))
    
    # 如果没有检测到任何意图，返回"其他查询"
    if not detected_intents:
        intent = "其他查询"
        confidence = 0.3
        business_scenario = "其他"
    else:
        # 选择置信度最高的意图
        detected_intents.sort(key=lambda x: x[1], reverse=True)
        intent, confidence = detected_intents[0]
        business_scenario = scenario_mapping.get(intent, "其他")
    
    # 返回分析结果
    return {
        "conversation_id": dialog["conversation_id"],
        "business_scenario": business_scenario,
        "intent": intent,
        "confidence": confidence,
        "user_message_count": dialog["statistics"]["user_message_count"],
        "total_message_count": dialog["statistics"]["message_count"]
    }

def method_c_analyze_all_dialogs(dialogs):
    """使用方法C分析所有对话"""
    intent_results = []
    for dialog in dialogs:
        intent_result = method_c_analyze_intent(dialog)
        intent_results.append(intent_result)
    return intent_results

# ================ 主函数 ================

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 意图识别方法C：上下文增强识别法")
    print("=" * 50)
    
    # 1. 加载数据
    df = load_data(DATA_FILE)
    
    # 2. 数据预处理
    processed_df = preprocess_data(df)
    
    # 3. 组织对话结构
    dialogs = organize_dialogs(processed_df)
    
    # 4. 使用方法C进行意图分析
    intent_results = method_c_analyze_all_dialogs(dialogs)
    
    # 5. 生成分析报告
    generate_report(intent_results, "方法C_上下文增强识别法")
    
    print("=" * 50)
    print("方法C测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回收宝智能客服系统 - 意图识别方法A：基础规则匹配法
使用关键词匹配和简单规则识别用户意图
"""

import sys
from intent_recognition_common import *

# ================ 方法A：基础规则匹配法 ================

def method_a_analyze_intent(dialog):
    """
    方法A：基础规则匹配法
    使用关键词匹配和简单规则识别用户意图
    """
    # 意图关键词映射
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
    
    # 合并所有用户消息
    all_user_content = " ".join([msg["clean_content"] for msg in dialog["user_messages"]])
    
    # 计算各意图得分
    intent_scores = {}
    for intent, keywords in intent_keywords.items():
        score = sum([1 for keyword in keywords if keyword in all_user_content])
        intent_scores[intent] = score
    
    # 特殊规则增强
    if dialog["structured_info"]["order_numbers"]:
        intent_scores["订单查询"] += 2
    if dialog["structured_info"]["logistics_numbers"]:
        intent_scores["发货查询"] += 2
    
    # 如果所有意图得分为0，返回"其他查询"
    if sum(intent_scores.values()) == 0:
        intent = "其他查询"
        confidence = 0.3
        business_scenario = "其他"
    else:
        # 返回得分最高的意图
        intent = max(intent_scores.items(), key=lambda x: x[1])[0]
        # 计算置信度（简单实现）
        max_score = intent_scores[intent]
        total_score = sum(intent_scores.values())
        confidence = min(0.3 + (max_score / total_score) * 0.5, 0.9)  # 置信度范围：0.3-0.9
        # 获取对应的业务场景
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

def method_a_analyze_all_dialogs(dialogs):
    """使用方法A分析所有对话"""
    intent_results = []
    for dialog in dialogs:
        intent_result = method_a_analyze_intent(dialog)
        intent_results.append(intent_result)
    return intent_results

# ================ 主函数 ================

def main():
    """主函数"""
    print("=" * 50)
    print("回收宝智能客服系统 - 意图识别方法A：基础规则匹配法")
    print("=" * 50)
    
    # 1. 加载数据
    df = load_data(DATA_FILE)
    
    # 2. 数据预处理
    processed_df = preprocess_data(df)
    
    # 3. 组织对话结构
    dialogs = organize_dialogs(processed_df)
    
    # 4. 使用方法A进行意图分析
    intent_results = method_a_analyze_all_dialogs(dialogs)
    
    # 5. 生成分析报告
    generate_report(intent_results, "方法A_基础规则匹配法")
    
    print("=" * 50)
    print("方法A测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()

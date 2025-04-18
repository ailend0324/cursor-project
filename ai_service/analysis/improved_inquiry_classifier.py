#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 分类体系定义
CLASSIFICATION_SYSTEM = {
    "订单与物流类": {
        "keywords": ["订单", "物流", "快递", "发货", "收货", "寄", "派送", "签收"],
        "subcategories": {
            "订单查询": ["查询", "订单号", "下单", "查单", "查订单", "订单状态"],
            "物流追踪": ["物流", "快递", "发货", "到货", "收货", "派送", "追踪", "跟踪", "签收"],
            "订单修改": ["修改", "更改", "地址", "电话", "改", "改地址", "改电话", "修改地址"],
            "订单取消": ["取消", "撤销", "不要了", "不买了", "取消订单"],
            "订单确认": ["确认", "收到", "签收", "确认收货", "已收到", "已签收"]
        }
    },
    "产品咨询类": {
        "keywords": ["产品", "功能", "价格", "多少钱", "怎么用", "区别", "参数", "配置", "真假"],
        "subcategories": {
            "产品功能": ["功能", "特点", "作用", "怎么用", "使用", "操作", "指南"],
            "产品价格": ["价格", "多少钱", "报价", "折扣", "便宜", "贵", "优惠"],
            "产品对比": ["对比", "区别", "差异", "推荐", "哪个好", "比较", "更好"],
            "产品配置": ["规格", "配置", "型号", "参数", "尺寸", "大小", "颜色"],
            "产品真伪": ["真假", "鉴定", "真品", "仿制", "假货", "正品", "辨别", "官方"]
        }
    },
    "售后服务类": {
        "keywords": ["退款", "退货", "换货", "维修", "保修", "质量问题", "坏了", "不满意"],
        "subcategories": {
            "退款处理": ["退款", "退钱", "返款", "钱退", "退我", "退给我", "退回我"],
            "退货处理": ["退货", "寄回", "退回", "不要了", "退掉", "退产品"],
            "换货处理": ["换货", "更换", "调换", "换一个", "换新", "换产品"],
            "维修服务": ["维修", "修理", "保修", "坏了", "故障", "问题", "不好用", "不能用"],
            "投诉建议": ["投诉", "不满", "建议", "意见", "差评", "不好", "糟糕", "服务差"]
        }
    },
    "账户管理类": {
        "keywords": ["账号", "账户", "登录", "注册", "密码", "会员", "积分", "支付"],
        "subcategories": {
            "注册问题": ["注册", "创建账号", "注册账号", "新账号", "建账号"],
            "登录问题": ["登录", "密码", "无法登录", "登不上", "进不去", "账号登录"],
            "账户安全": ["安全", "修改密码", "隐私", "账号安全", "改密码", "忘记密码"],
            "会员权益": ["会员", "积分", "等级", "权益", "特权", "会员等级", "积分兑换"],
            "支付问题": ["支付", "付款", "支付宝", "微信支付", "付不了", "支付失败", "银行卡"]
        }
    },
    "服务咨询类": {
        "keywords": ["流程", "政策", "规则", "活动", "优惠", "人工", "客服", "时间"],
        "subcategories": {
            "业务咨询": ["流程", "方式", "步骤", "合作", "怎么操作", "如何办理", "申请流程"],
            "政策咨询": ["政策", "规则", "条款", "协议", "条件", "要求", "资格"],
            "活动咨询": ["活动", "促销", "优惠", "折扣", "打折", "降价", "满减", "特价"],
            "人工服务": ["人工", "客服", "转人工", "真人", "人工客服", "找客服", "需要人工"],
            "运营时间": ["时间", "几点", "营业", "工作时间", "营业时间", "服务时间", "几点关门"]
        }
    },
    "问候语": {
        "keywords": ["你好", "您好", "早上好", "下午好", "晚上好", "喂", "在吗", "有人吗"],
        "subcategories": {}
    },
    "其他": {
        "keywords": [],
        "subcategories": {}
    }
}

def preprocess_text(text):
    """文本预处理"""
    if not isinstance(text, str) or pd.isna(text):
        return ""
    # 去除标点符号但保留中文标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff，。？！、：；""''【】《》]', '', text)
    # 转换为小写
    text = text.lower()
    return text

def categorize_query(text, classification_system=CLASSIFICATION_SYSTEM):
    """对用户问题进行多层次分类"""
    text = preprocess_text(text)
    if not text:
        return "其他", "未分类"
    
    # 检查问候语
    if any(greeting in text for greeting in classification_system["问候语"]["keywords"]):
        if len(text) < 10 and not any(keyword in text for category in ["订单与物流类", "产品咨询类", "售后服务类", "账户管理类", "服务咨询类"] 
                               for keyword in classification_system[category]["keywords"]):
            return "问候语", "问候语"
    
    # 一级分类匹配
    for category, info in classification_system.items():
        if category in ["问候语", "其他"]:
            continue
            
        for keyword in info["keywords"]:
            if keyword in text:
                # 进行二级分类匹配
                for subcategory, subkeywords in info["subcategories"].items():
                    for subkeyword in subkeywords:
                        if subkeyword in text:
                            return category, subcategory
                
                # 若未匹配到二级分类，返回默认二级分类
                return category, f"{category}-其他"
    
    # 未匹配到任何分类
    return "其他", "未分类"

def analyze_conversation_context(df):
    """通过对话上下文改进分类"""
    # 按touchId分组处理对话
    touch_ids = df['touch_id'].unique()
    improved_categories = {}
    
    for touch_id in touch_ids:
        conversation = df[df['touch_id'] == touch_id].sort_values('seq_no')
        user_msgs = conversation[conversation['sender_type'] == 1]['send_content'].astype(str).tolist()
        
        if not user_msgs:
            continue
            
        # 处理首条消息是问候语的情况
        first_msg = user_msgs[0]
        first_category, first_subcategory = categorize_query(first_msg)
        
        if first_category == "问候语" and len(user_msgs) > 1:
            # 寻找问候语后的第一个实质性问题
            for msg in user_msgs[1:]:
                category, subcategory = categorize_query(msg)
                if category != "问候语" and category != "其他":
                    improved_categories[touch_id] = (category, subcategory)
                    break
            else:
                improved_categories[touch_id] = (first_category, first_subcategory)
        else:
            improved_categories[touch_id] = (first_category, first_subcategory)
    
    return improved_categories

def create_classification_report(df, improved_categories):
    """创建分类报告"""
    # 一级分类统计
    category_counts = Counter([cat for cat, _ in improved_categories.values()])
    total = sum(category_counts.values())
    
    print("===== 一级分类统计 =====")
    for category, count in category_counts.most_common():
        print(f"{category}: {count} ({count/total*100:.2f}%)")
    
    # 二级分类统计
    subcategory_counts = Counter([subcat for _, subcat in improved_categories.values()])
    
    print("\n===== 二级分类TOP20 =====")
    for subcategory, count in subcategory_counts.most_common(20):
        print(f"{subcategory}: {count} ({count/total*100:.2f}%)")
    
    # 按业务场景分类统计
    business_categories = defaultdict(Counter)
    for touch_id, (category, subcategory) in improved_categories.items():
        group_name = df[df['touch_id'] == touch_id]['group_name'].iloc[0] if not df[df['touch_id'] == touch_id].empty else "Unknown"
        business_categories[group_name][category] += 1
    
    print("\n===== 业务场景分类统计 =====")
    for business, categories in business_categories.items():
        total_business = sum(categories.values())
        print(f"\n{business} (总计: {total_business})")
        for category, count in categories.most_common():
            print(f"  {category}: {count} ({count/total_business*100:.2f}%)")
    
    # 生成结果DataFrame
    results = []
    for touch_id, (category, subcategory) in improved_categories.items():
        first_row = df[df['touch_id'] == touch_id].iloc[0] if not df[df['touch_id'] == touch_id].empty else None
        if first_row is not None:
            results.append({
                'touch_id': touch_id,
                'first_msg': df[(df['touch_id'] == touch_id) & (df['sender_type'] == 1)].iloc[0]['send_content'] if not df[(df['touch_id'] == touch_id) & (df['sender_type'] == 1)].empty else "",
                'group_name': first_row['group_name'],
                'category': category,
                'subcategory': subcategory
            })
    
    results_df = pd.DataFrame(results)
    
    # 保存分类结果
    output_file = os.path.join(PROJECT_ROOT, "analysis", "inquiry_classification_results.csv")
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n分类结果已保存至 {output_file}")
    
    return results_df

def visualize_classification(results_df):
    """可视化分类结果"""
    # 设置图表样式
    plt.style.use('ggplot')
    plt.figure(figsize=(12, 8))
    
    # 一级分类饼图
    plt.subplot(1, 2, 1)
    category_counts = results_df['category'].value_counts()
    plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('用户诉求一级分类分布')
    plt.axis('equal')
    
    # 二级分类前10名柱状图
    plt.subplot(1, 2, 2)
    subcategory_counts = results_df['subcategory'].value_counts().head(10)
    sns.barplot(x=subcategory_counts.values, y=subcategory_counts.index)
    plt.title('用户诉求二级分类TOP10')
    plt.xlabel('数量')
    
    # 保存图表
    output_file = os.path.join(PROJECT_ROOT, "analysis", "inquiry_classification_chart.png")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"分类可视化结果已保存至 {output_file}")

def main():
    """主函数"""
    # 加载数据
    file_path = os.path.join(PROJECT_ROOT, "data", "merged_chat_records.xlsx")
    print(f"正在加载数据文件: {file_path}")
    
    try:
        # 设置较大的样本量
        sample_size = 100000
        df = pd.read_excel(file_path, nrows=sample_size)
        print(f"成功加载数据，共 {len(df)} 行")
        
        # 分析对话上下文，改进分类
        print("正在进行用户诉求分类...")
        improved_categories = analyze_conversation_context(df)
        print(f"完成分类，共处理 {len(improved_categories)} 个对话")
        
        # 创建分类报告
        results_df = create_classification_report(df, improved_categories)
        
        # 可视化分类结果
        print("正在生成可视化结果...")
        visualize_classification(results_df)
        
    except Exception as e:
        print(f"处理数据时出错: {e}")
        
if __name__ == "__main__":
    main() 
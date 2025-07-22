#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据结构转换脚本
功能：将Excel格式或扁平JSON格式的客服对话数据转换为优化的嵌套JSON结构
用法：python convert_to_optimized_structure.py --source <source_path> --output <output_path> [--format <excel|json>]
"""

import argparse
import json
import os
import pandas as pd
import uuid
import re
from datetime import datetime
from collections import defaultdict


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='将客服对话数据转换为优化的嵌套JSON结构')
    parser.add_argument('--source', required=True, help='源数据文件路径（Excel或JSON）')
    parser.add_argument('--output', required=True, help='输出JSON文件路径')
    parser.add_argument('--format', choices=['excel', 'json'], default='excel', help='源数据格式，默认为excel')
    parser.add_argument('--limit', type=int, default=None, help='限制处理的对话数量，用于测试')
    parser.add_argument('--interactive', action='store_true', help='是否启用交互式模式，每处理100个对话暂停一次')
    return parser.parse_args()


def load_data(source_path, format_type='excel', limit=None):
    """
    加载源数据
    
    参数:
        source_path: 源数据文件路径
        format_type: 数据格式，'excel'或'json'
        limit: 限制处理的对话数量
    
    返回:
        list or dict: 加载的数据
    """
    try:
        if format_type == 'excel':
            # 读取Excel文件
            if limit:
                df = pd.read_excel(source_path, nrows=limit)
                print(f"已限制读取前{limit}行数据")
            else:
                df = pd.read_excel(source_path)
            
            # 转换为字典列表
            records = df.to_dict(orient='records')
            return records
        
        elif format_type == 'json':
            # 读取JSON文件
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果有限制，只取前N个对话
            if limit and isinstance(data, list):
                data = data[:limit]
            
            return data
        
        else:
            raise ValueError(f"不支持的数据格式: {format_type}")
    
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None


def extract_entities(content):
    """
    从消息内容中提取实体
    
    参数:
        content: 消息内容
    
    返回:
        list: 提取的实体列表
    """
    entities = []
    
    # 提取订单号
    order_id_pattern = r'\b\d{16,19}\b'
    for match in re.finditer(order_id_pattern, content):
        entities.append({
            "type": "order_id",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # 提取手机号
    phone_pattern = r'1[3-9]\d{9}'
    for match in re.finditer(phone_pattern, content):
        entities.append({
            "type": "phone_number",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # 提取日期
    date_pattern = r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?'
    for match in re.finditer(date_pattern, content):
        entities.append({
            "type": "date",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    # 提取金额
    money_pattern = r'\d+(\.\d+)?元|\d+(\.\d+)?块|\d+(\.\d+)?¥|\¥\d+(\.\d+)?'
    for match in re.finditer(money_pattern, content):
        entities.append({
            "type": "money",
            "value": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    return entities


def detect_intent(content, sender_type):
    """
    检测消息的意图
    
    参数:
        content: 消息内容
        sender_type: 发送者类型
    
    返回:
        dict: 意图信息
    """
    # 用户意图模式
    user_intent_patterns = {
        "订单查询": {
            "订单状态查询": [r'订单.*状态', r'订单.*进度', r'什么时候.*发货', r'发货了吗'],
            "订单详情查询": [r'订单.*详情', r'订单.*信息', r'查.*订单'],
            "订单修改": [r'修改.*订单', r'订单.*修改', r'能不能改']
        },
        "物流配送": {
            "物流状态查询": [r'物流.*状态', r'快递.*到哪', r'发货.*了吗', r'什么时候.*到'],
            "物流信息修改": [r'修改.*地址', r'地址.*修改', r'换.*地方'],
            "物流问题反馈": [r'快递.*问题', r'物流.*慢', r'没.*收到']
        },
        "价格咨询": {
            "价格查询": [r'多少钱', r'价格.*是', r'报价', r'费用'],
            "价格异议": [r'价格.*高', r'能便宜', r'优惠', r'降价'],
            "价格说明": [r'为什么.*这么贵', r'价格.*包含', r'价格.*区别']
        },
        "验货检测": {
            "检测流程": [r'怎么检测', r'检测.*流程', r'验货.*步骤'],
            "检测结果": [r'检测.*结果', r'验货.*情况', r'检测.*出来'],
            "检测标准": [r'检测.*标准', r'怎么判断', r'验货.*依据']
        },
        "支付结算": {
            "支付方式": [r'怎么付款', r'支付方式', r'付款.*方式'],
            "支付问题": [r'付款.*失败', r'支付.*问题', r'没.*扣款'],
            "退款咨询": [r'退款', r'钱.*退', r'返.*钱']
        },
        "账号问题": {
            "登录问题": [r'登录.*不了', r'账号.*登录', r'密码.*忘'],
            "注册问题": [r'怎么注册', r'注册.*不了', r'账号.*注册'],
            "账号安全": [r'账号.*安全', r'修改.*密码', r'账号.*异常']
        },
        "信息提供": {
            "订单号提供": [r'\d{16,19}'],
            "联系方式提供": [r'1[3-9]\d{9}'],
            "地址提供": [r'省.*市.*区.*路']
        },
        "问候": {
            "开场问候": [r'^你好', r'^您好', r'^hi', r'^hello'],
            "结束感谢": [r'谢谢', r'感谢', r'多谢', r'thank']
        }
    }
    
    # 客服意图模式
    agent_intent_patterns = {
        "信息获取": {
            "订单号获取": [r'订单号.*是', r'请.*提供.*订单'],
            "联系方式获取": [r'电话.*是', r'请.*提供.*联系方式'],
            "地址获取": [r'地址.*是', r'请.*提供.*地址']
        },
        "信息确认": {
            "订单确认": [r'确认.*订单', r'这个订单', r'订单.*是'],
            "信息核对": [r'核对.*信息', r'确认.*信息', r'信息.*正确']
        },
        "问题解答": {
            "状态说明": [r'订单.*状态.*是', r'物流.*状态.*是'],
            "流程解释": [r'流程.*是', r'步骤.*是', r'需要.*操作'],
            "政策说明": [r'政策.*是', r'规定.*是', r'要求.*是']
        },
        "服务提供": {
            "帮助提供": [r'帮您.*查', r'为您.*处理', r'给您.*解决'],
            "建议提供": [r'建议您', r'可以.*尝试', r'推荐您']
        },
        "情感回应": {
            "道歉": [r'抱歉', r'对不起', r'很遗憾'],
            "安抚": [r'理解.*您', r'请.*不要着急', r'请.*放心'],
            "感谢": [r'感谢.*您', r'谢谢.*您', r'非常感谢']
        },
        "问候": {
            "开场问候": [r'^您好', r'^你好', r'^亲', r'^欢迎'],
            "结束问候": [r'祝.*愉快', r'感谢.*咨询', r'还有.*问题']
        }
    }
    
    # 根据发送者类型选择意图模式
    if sender_type == "user" or sender_type == 1.0 or sender_type == "1.0":
        intent_patterns = user_intent_patterns
    else:
        intent_patterns = agent_intent_patterns
    
    # 检测意图
    for category, subcategories in intent_patterns.items():
        for subcategory, patterns in subcategories.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return {
                        "category": category,
                        "subcategory": subcategory,
                        "confidence": 0.85  # 简单起见，使用固定置信度
                    }
    
    # 默认意图
    return {
        "category": "其他",
        "subcategory": "未分类",
        "confidence": 0.5
    }


def detect_sentiment(content):
    """
    检测消息的情感倾向
    
    参数:
        content: 消息内容
    
    返回:
        str: 情感倾向
    """
    # 正面情感词
    positive_words = ['谢谢', '感谢', '满意', '好的', '可以', '不错', '优秀', '棒', '赞', '喜欢', '开心', '期待', '希望']
    
    # 负面情感词
    negative_words = ['不满', '投诉', '差', '慢', '贵', '问题', '退款', '取消', '失败', '错误', '不行', '垃圾', '坏']
    
    # 计算情感得分
    positive_score = sum(1 for word in positive_words if word in content)
    negative_score = sum(1 for word in negative_words if word in content)
    
    # 判断情感倾向
    if positive_score > negative_score:
        return "positive"
    elif negative_score > positive_score:
        return "negative"
    else:
        return "neutral"


def convert_to_optimized_structure(records, interactive=False):
    """
    将扁平结构转换为优化的嵌套JSON结构
    
    参数:
        records: 扁平结构的记录列表
        interactive: 是否启用交互式模式
    
    返回:
        list: 优化结构的对话列表
    """
    # 按对话ID分组
    conversations_dict = defaultdict(list)
    for record in records:
        touch_id = record.get('touch_id')
        if touch_id:
            conversations_dict[touch_id].append(record)
    
    print(f"共找到{len(conversations_dict)}个对话")
    
    # 转换为优化结构
    optimized_conversations = []
    processed_count = 0
    
    for touch_id, messages in conversations_dict.items():
        # 排序消息
        messages.sort(key=lambda x: x.get('seq_no', 0))
        
        # 构建对话元数据
        first_message = messages[0] if messages else {}
        last_message = messages[-1] if messages else {}
        
        # 计算对话时长
        start_time = first_message.get('send_time') or first_message.get('user_start_time')
        end_time = last_message.get('send_time') or first_message.get('user_end_time')
        
        try:
            if start_time and end_time:
                start_dt = pd.to_datetime(start_time)
                end_dt = pd.to_datetime(end_time)
                duration_minutes = (end_dt - start_dt).total_seconds() / 60
            else:
                duration_minutes = 0
        except:
            duration_minutes = 0
        
        # 构建消息列表
        optimized_messages = []
        for i, msg in enumerate(messages):
            content = msg.get('send_content', '') or msg.get('content', '')
            sender_type_raw = msg.get('sender_type')
            
            # 转换发送者类型
            if sender_type_raw == 1.0 or sender_type_raw == '1.0':
                sender_type = "user"
            elif sender_type_raw == 2.0 or sender_type_raw == '2.0':
                sender_type = "agent"
            else:
                sender_type = "system"
            
            # 检测意图
            intent = detect_intent(content, sender_type)
            
            # 提取实体
            entities = extract_entities(content)
            
            # 检测情感
            sentiment = detect_sentiment(content)
            
            # 构建消息
            message = {
                "message_id": f"m{i+1:03d}",
                "seq_no": msg.get('seq_no', i+1),
                "sender_type": sender_type,
                "sender_id": msg.get('user_name') if sender_type == "user" else msg.get('servicer_name'),
                "content": content,
                "send_time": msg.get('send_time', ''),
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment
            }
            
            optimized_messages.append(message)
        
        # 确定主要意图
        user_messages = [msg for msg in optimized_messages if msg['sender_type'] == 'user']
        if user_messages:
            # 使用第一条用户消息的意图作为主要意图
            primary_intent = user_messages[0]['intent']
        else:
            primary_intent = {
                "category": "未知",
                "subcategory": "未知",
                "confidence": 0.5
            }
        
        # 构建优化结构的对话
        optimized_conversation = {
            "conversation_id": str(touch_id),
            "metadata": {
                "user_name": first_message.get('user_name', ''),
                "user_id": first_message.get('user_name', ''),  # 使用用户名作为ID
                "servicer_name": first_message.get('servicer_name', ''),
                "servicer_id": first_message.get('servicer_name', ''),  # 使用客服名作为ID
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": duration_minutes,
                "channel": "在线客服",
                "group_name": first_message.get('group_name', ''),
                "feedback_rating": None,
                "feedback_comment": first_message.get('new_feedback_name', '')
            },
            "statistics": {
                "message_count": len(messages),
                "user_message_count": len([msg for msg in optimized_messages if msg['sender_type'] == 'user']),
                "service_message_count": len([msg for msg in optimized_messages if msg['sender_type'] == 'agent']),
                "avg_response_time_seconds": None  # 需要计算平均响应时间
            },
            "primary_intent": primary_intent,
            "messages": optimized_messages,
            "resolution": {
                "status": "resolved",  # 假设所有对话都已解决
                "resolution_type": "information_provided",
                "satisfaction_level": "unknown"
            }
        }
        
        optimized_conversations.append(optimized_conversation)
        
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"已处理 {processed_count}/{len(conversations_dict)} 个对话")
            
            # 交互式模式下，每处理100个对话暂停一次
            if interactive and processed_count < len(conversations_dict):
                user_input = input("按Enter键继续，输入'q'退出：")
                if user_input.lower() == 'q':
                    break
    
    return optimized_conversations


def save_optimized_data(optimized_conversations, output_path):
    """
    保存优化结构的数据
    
    参数:
        optimized_conversations: 优化结构的对话列表
        output_path: 输出文件路径
    
    返回:
        bool: 是否成功
    """
    try:
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(optimized_conversations, f, ensure_ascii=False, indent=2)
        
        print(f"优化结构的数据已保存到: {output_path}")
        return True
    
    except Exception as e:
        print(f"保存数据时出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查源文件是否存在
    if not os.path.exists(args.source):
        print(f"错误: 源文件不存在: {args.source}")
        return
    
    # 执行转换
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    # 加载数据
    records = load_data(args.source, args.format, args.limit)
    if not records:
        print("加载数据失败")
        return
    
    # 转换为优化结构
    optimized_conversations = convert_to_optimized_structure(records, args.interactive)
    
    # 保存优化结构的数据
    success = save_optimized_data(optimized_conversations, args.output)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据结构转换成功！")
    else:
        print("数据结构转换失败！")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据清洗脚本
功能：对导入的客服对话数据进行清洗和预处理
用法：python clean_data.py --input <input_json_path> --output <output_json_path> [--report <report_path>]
"""

import argparse
import json
import os
import re
import pandas as pd
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='对客服对话数据进行清洗和预处理')
    parser.add_argument('--input', required=True, help='输入JSON文件路径')
    parser.add_argument('--output', required=True, help='输出JSON文件路径')
    parser.add_argument('--report', help='清洗报告输出路径')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    return parser.parse_args()


def clean_text(text):
    """
    清洗文本内容
    
    参数:
        text: 原始文本
    
    返回:
        str: 清洗后的文本
    """
    if not isinstance(text, str):
        return ""
    
    # 移除HTML标签（增强版）
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除图片标签
    text = re.sub(r'<img\s+[^>]*src=[\'"]([^\'"]+)[\'"][^>]*>', '[图片]', text)
    
    # 移除URL
    text = re.sub(r'https?://\S+', '[URL]', text)
    
    # 移除多余空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 移除特殊控制字符
    text = re.sub(r'[\x00-\x1F\x7F]', '', text)
    
    # 处理常见HTML实体
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&nbsp;', ' ')
    
    return text


def anonymize_sensitive_info(text):
    """
    对敏感信息进行脱敏
    
    参数:
        text: 原始文本
    
    返回:
        str: 脱敏后的文本
    """
    if not isinstance(text, str):
        return ""
    
    # 手机号脱敏
    text = re.sub(r'1[3-9]\d{9}', '[手机号]', text)
    
    # 邮箱脱敏
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[邮箱]', text)
    
    # 身份证号脱敏
    text = re.sub(r'\b\d{17}[\dXx]\b', '[身份证号]', text)
    
    # 银行卡号脱敏
    text = re.sub(r'\b\d{16,19}\b', '[银行卡号]', text)
    
    # 订单号脱敏（保留前4位）
    text = re.sub(r'\b(\d{4})\d{12,16}\b', r'\1[订单号]', text)
    
    # 地址脱敏
    text = re.sub(r'[省市区县].*?[路街道].*?号', '[地址]', text)
    
    return text


def is_valid_conversation(conversation):
    """
    判断对话是否有效
    
    参数:
        conversation: 对话数据
    
    返回:
        bool: 是否为有效对话
    """
    # 检查对话是否包含消息
    if not conversation.get('messages'):
        return False
    
    # 检查对话是否包含用户消息
    user_messages = [msg for msg in conversation['messages'] if msg.get('sender_type') == 1.0 or msg.get('sender_type') == '1.0']
    if not user_messages:
        return False
    
    # 检查对话是否包含客服消息
    service_messages = [msg for msg in conversation['messages'] if msg.get('sender_type') == 2.0 or msg.get('sender_type') == '2.0']
    if not service_messages:
        return False
    
    # 检查对话长度（至少2条消息）
    if len(conversation['messages']) < 2:
        return False
    
    return True


def fix_missing_values(conversation):
    """
    处理缺失值
    
    参数:
        conversation: 对话数据
    
    返回:
        dict: 处理后的对话数据
    """
    # 复制对话数据
    fixed = conversation.copy()
    
    # 处理消息中的缺失值
    for i, message in enumerate(fixed['messages']):
        # 处理缺失的sender_type
        if 'sender_type' not in message or message['sender_type'] is None:
            # 尝试根据上下文推断发送者类型
            if i > 0 and 'sender_type' in fixed['messages'][i-1]:
                # 如果上一条是用户，这一条可能是客服
                if fixed['messages'][i-1]['sender_type'] == 1.0 or fixed['messages'][i-1]['sender_type'] == '1.0':
                    fixed['messages'][i]['sender_type'] = 2.0
                else:
                    # 否则可能是用户
                    fixed['messages'][i]['sender_type'] = 1.0
            else:
                # 默认设为客服
                fixed['messages'][i]['sender_type'] = 2.0
        
        # 处理缺失的content
        if 'content' not in message or message['content'] is None:
            fixed['messages'][i]['content'] = ""
        
        # 处理缺失的send_time
        if 'send_time' not in message or message['send_time'] is None:
            # 尝试使用上一条消息的时间加1分钟
            if i > 0 and 'send_time' in fixed['messages'][i-1] and fixed['messages'][i-1]['send_time']:
                try:
                    prev_time = datetime.strptime(fixed['messages'][i-1]['send_time'], '%Y-%m-%d %H:%M:%S')
                    fixed['messages'][i]['send_time'] = (prev_time.replace(second=0) + pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    # 使用对话开始时间
                    fixed['messages'][i]['send_time'] = fixed.get('user_start_time', '2025-01-01 00:00:00')
            else:
                # 使用对话开始时间
                fixed['messages'][i]['send_time'] = fixed.get('user_start_time', '2025-01-01 00:00:00')
        
        # 处理缺失的seq_no
        if 'seq_no' not in message or message['seq_no'] is None:
            fixed['messages'][i]['seq_no'] = float(i + 1)
    
    # 处理对话元数据中的缺失值
    if 'new_feedback_name' not in fixed or fixed['new_feedback_name'] is None:
        fixed['new_feedback_name'] = "未知反馈"
    
    if 'servicer_name' not in fixed or fixed['servicer_name'] is None:
        # 尝试从消息中找到客服名称
        service_messages = [msg for msg in fixed['messages'] if msg.get('sender_type') == 2.0 or msg.get('sender_type') == '2.0']
        if service_messages and 'servicer_name' in service_messages[0] and service_messages[0]['servicer_name']:
            fixed['servicer_name'] = service_messages[0]['servicer_name']
        else:
            fixed['servicer_name'] = "未知客服"
    
    return fixed


def fix_time_sequence(conversation):
    """
    修复时间顺序异常
    
    参数:
        conversation: 对话数据
    
    返回:
        dict: 修复后的对话数据
    """
    # 复制对话数据
    fixed = conversation.copy()
    
    # 按send_time排序
    try:
        # 转换时间字符串为datetime对象
        for i, message in enumerate(fixed['messages']):
            if 'send_time' in message and message['send_time']:
                try:
                    message['_send_time_obj'] = datetime.strptime(message['send_time'], '%Y-%m-%d %H:%M:%S')
                except:
                    # 如果时间格式不正确，使用当前时间
                    message['_send_time_obj'] = datetime.now()
                    message['send_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 如果没有发送时间，使用当前时间
                message['_send_time_obj'] = datetime.now()
                message['send_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 按时间排序
        fixed['messages'] = sorted(fixed['messages'], key=lambda x: x['_send_time_obj'])
        
        # 移除临时字段
        for message in fixed['messages']:
            if '_send_time_obj' in message:
                del message['_send_time_obj']
        
        # 更新seq_no
        for i, message in enumerate(fixed['messages']):
            message['seq_no'] = float(i + 1)
    
    except Exception as e:
        print(f"修复时间顺序时出错: {e}")
    
    return fixed


def fix_sender_types(conversation):
    """
    优化发送者类型，确保用户和客服消息交替出现
    
    参数:
        conversation: 对话数据
    
    返回:
        dict: 修复后的对话数据
    """
    # 复制对话数据
    fixed = conversation.copy()
    messages = fixed['messages']
    
    if not messages:
        return fixed
    
    # 1. 基于内容特征识别发送者类型
    for i, message in enumerate(messages):
        content = message.get('content', '').lower()
        
        # 客服特征词
        service_keywords = [
            '亲亲', '小宝人工客服', '有什么可以帮到您', '请问是咨询这个订单吗', 
            '感谢您的支持', '请您点击', '稍等一下', '小小去给您查', '您可以提供下',
            '非常抱歉', '工程师', '客服这边', '您好，请您', '谢谢您的反馈'
        ]
        
        # 用户特征词
        user_keywords = [
            '怎么查', '为什么', '什么时候', '能不能', '可以吗', '多久', 
            '怎么办', '帮我', '谢谢你', '谢谢', '我的订单', '我想问', '我要'
        ]
        
        # 检查是否包含客服特征词
        is_service = any(keyword in content for keyword in service_keywords)
        
        # 检查是否包含用户特征词
        is_user = any(keyword in content for keyword in user_keywords)
        
        # 如果同时包含或都不包含，保持原有类型
        if is_service and not is_user:
            message['sender_type'] = 2.0
        elif is_user and not is_service:
            message['sender_type'] = 1.0
    
    # 2. 确保对话的第一条消息是用户发送的，最后一条是客服回复的
    if len(messages) >= 2:
        # 如果第一条不是用户消息，且内容没有明显的客服特征，将其设为用户消息
        first_msg = messages[0]
        if (first_msg.get('sender_type') != 1.0 and first_msg.get('sender_type') != '1.0' and
            not any(keyword in first_msg.get('content', '').lower() for keyword in service_keywords)):
            first_msg['sender_type'] = 1.0
        
        # 如果最后一条不是客服消息，且内容没有明显的用户特征，将其设为客服消息
        last_msg = messages[-1]
        if (last_msg.get('sender_type') != 2.0 and last_msg.get('sender_type') != '2.0' and
            not any(keyword in last_msg.get('content', '').lower() for keyword in user_keywords)):
            last_msg['sender_type'] = 2.0
    
    # 3. 修复连续相同发送者类型的问题
    for i in range(1, len(messages)):
        curr_type = messages[i].get('sender_type')
        prev_type = messages[i-1].get('sender_type')
        
        # 如果当前消息和前一条消息的发送者类型相同
        if curr_type == prev_type:
            # 检查消息内容特征
            content = messages[i].get('content', '').lower()
            
            # 如果有明显的客服或用户特征，保持原有类型
            if (curr_type == 2.0 or curr_type == '2.0') and any(keyword in content for keyword in service_keywords):
                continue
            elif (curr_type == 1.0 or curr_type == '1.0') and any(keyword in content for keyword in user_keywords):
                continue
            
            # 否则，交替设置发送者类型
            if prev_type == 1.0 or prev_type == '1.0':
                messages[i]['sender_type'] = 2.0
            else:
                messages[i]['sender_type'] = 1.0
    
    return fixed


def enhance_dialog_structure(conversation):
    """
    增强对话结构，添加开场白和结束语
    
    参数:
        conversation: 对话数据
    
    返回:
        dict: 增强后的对话数据
    """
    # 复制对话数据
    enhanced = conversation.copy()
    messages = enhanced['messages']
    
    if not messages:
        return enhanced
    
    # 检查是否已有开场白
    first_msg = messages[0]
    first_content = first_msg.get('content', '').lower()
    has_greeting = any(greeting in first_content for greeting in ['您好', '你好', '欢迎', 'hello', 'hi'])
    
    # 检查是否已有结束语
    last_msg = messages[-1]
    last_content = last_msg.get('content', '').lower()
    has_ending = any(ending in last_content for ending in ['谢谢', '感谢', '再见', '祝您', 'thank'])
    
    # 如果第一条是客服消息但没有开场白，添加开场白
    if (first_msg.get('sender_type') == 2.0 or first_msg.get('sender_type') == '2.0') and not has_greeting:
        first_msg['content'] = f"您好，欢迎咨询回收宝客服。{first_msg.get('content', '')}"
    
    # 如果最后一条是客服消息但没有结束语，添加结束语
    if (last_msg.get('sender_type') == 2.0 or last_msg.get('sender_type') == '2.0') and not has_ending:
        last_msg['content'] = f"{last_msg.get('content', '')} 感谢您的咨询，祝您生活愉快！"
    
    return enhanced


def clean_conversation(conversation):
    """
    清洗单个对话数据
    
    参数:
        conversation: 原始对话数据
    
    返回:
        dict: 清洗后的对话数据
    """
    # 复制对话数据
    cleaned = conversation.copy()
    
    # 处理缺失值
    cleaned = fix_missing_values(cleaned)
    
    # 修复时间顺序
    cleaned = fix_time_sequence(cleaned)
    
    # 优化发送者类型
    cleaned = fix_sender_types(cleaned)
    
    # 增强对话结构
    cleaned = enhance_dialog_structure(cleaned)
    
    # 清洗消息内容
    for i, message in enumerate(cleaned['messages']):
        if 'content' in message and message['content']:
            # 清洗文本
            cleaned_content = clean_text(message['content'])
            # 脱敏处理
            anonymized_content = anonymize_sensitive_info(cleaned_content)
            cleaned['messages'][i]['content'] = anonymized_content
    
    # 添加对话元数据
    cleaned['message_count'] = len(cleaned['messages'])
    cleaned['user_message_count'] = len([msg for msg in cleaned['messages'] if str(msg.get('sender_type')) == '1.0' or msg.get('sender_type') == 1.0])
    cleaned['service_message_count'] = len([msg for msg in cleaned['messages'] if str(msg.get('sender_type')) == '2.0' or msg.get('sender_type') == 2.0])
    
    # 计算对话时长（分钟）
    try:
        start_time = datetime.strptime(cleaned['messages'][0]['send_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(cleaned['messages'][-1]['send_time'], '%Y-%m-%d %H:%M:%S')
        duration = (end_time - start_time).total_seconds() / 60
        cleaned['duration_minutes'] = duration
    except:
        cleaned['duration_minutes'] = 0
    
    return cleaned


def generate_cleaning_report(original_conversations, cleaned_conversations, report_path):
    """
    生成数据清洗报告
    
    参数:
        original_conversations: 原始对话数据
        cleaned_conversations: 清洗后的对话数据
        report_path: 报告输出路径
    """
    report = {
        "清洗前对话数": len(original_conversations),
        "清洗后对话数": len(cleaned_conversations),
        "无效对话数": len(original_conversations) - len(cleaned_conversations),
        "处理的问题": {
            "缺失值": {
                "sender_type": 0,
                "send_time": 0,
                "content": 0,
                "seq_no": 0,
                "new_feedback_name": 0,
                "servicer_name": 0
            },
            "时间顺序异常": 0,
            "消息序号异常": 0
        },
        "清洗前后对比": {
            "平均消息数": {
                "清洗前": sum(len(conv.get('messages', [])) for conv in original_conversations) / len(original_conversations) if original_conversations else 0,
                "清洗后": sum(len(conv.get('messages', [])) for conv in cleaned_conversations) / len(cleaned_conversations) if cleaned_conversations else 0
            },
            "用户消息占比": {
                "清洗前": sum(len([msg for msg in conv.get('messages', []) if str(msg.get('sender_type')) == '1.0' or msg.get('sender_type') == 1.0]) for conv in original_conversations) / sum(len(conv.get('messages', [])) for conv in original_conversations) if original_conversations else 0,
                "清洗后": sum(len([msg for msg in conv.get('messages', []) if str(msg.get('sender_type')) == '1.0' or msg.get('sender_type') == 1.0]) for conv in cleaned_conversations) / sum(len(conv.get('messages', [])) for conv in cleaned_conversations) if cleaned_conversations else 0
            }
        }
    }
    
    # 统计处理的问题
    for conv in original_conversations:
        for msg in conv.get('messages', []):
            if 'sender_type' not in msg or msg['sender_type'] is None:
                report["处理的问题"]["缺失值"]["sender_type"] += 1
            if 'send_time' not in msg or msg['send_time'] is None:
                report["处理的问题"]["缺失值"]["send_time"] += 1
            if 'content' not in msg or msg['content'] is None:
                report["处理的问题"]["缺失值"]["content"] += 1
            if 'seq_no' not in msg or msg['seq_no'] is None:
                report["处理的问题"]["缺失值"]["seq_no"] += 1
        
        if 'new_feedback_name' not in conv or conv['new_feedback_name'] is None:
            report["处理的问题"]["缺失值"]["new_feedback_name"] += 1
        if 'servicer_name' not in conv or conv['servicer_name'] is None:
            report["处理的问题"]["缺失值"]["servicer_name"] += 1
    
    # 统计时间顺序异常
    for conv in original_conversations:
        messages = conv.get('messages', [])
        if len(messages) >= 2:
            try:
                times = []
                for msg in messages:
                    if 'send_time' in msg and msg['send_time']:
                        times.append(datetime.strptime(msg['send_time'], '%Y-%m-%d %H:%M:%S'))
                
                # 检查是否有时间倒序
                is_sorted = all(times[i] <= times[i+1] for i in range(len(times)-1))
                if not is_sorted:
                    report["处理的问题"]["时间顺序异常"] += 1
            except:
                # 时间格式异常也算作时间顺序异常
                report["处理的问题"]["时间顺序异常"] += 1
    
    # 统计消息序号异常
    for conv in original_conversations:
        messages = conv.get('messages', [])
        if len(messages) >= 2:
            seq_nos = [msg.get('seq_no') for msg in messages if 'seq_no' in msg and msg['seq_no'] is not None]
            if seq_nos:
                # 检查序号是否连续
                is_continuous = all(int(seq_nos[i+1]) - int(seq_nos[i]) == 1 for i in range(len(seq_nos)-1))
                if not is_continuous:
                    report["处理的问题"]["消息序号异常"] += 1
    
    # 写入报告
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成Markdown报告
    md_report = f"""# 数据清洗报告

## 基本信息
- 清洗前对话数: {report["清洗前对话数"]}
- 清洗后对话数: {report["清洗后对话数"]}
- 无效对话数: {report["无效对话数"]}

## 处理的问题
### 缺失值
- sender_type: {report["处理的问题"]["缺失值"]["sender_type"]}
- send_time: {report["处理的问题"]["缺失值"]["send_time"]}
- content: {report["处理的问题"]["缺失值"]["content"]}
- seq_no: {report["处理的问题"]["缺失值"]["seq_no"]}
- new_feedback_name: {report["处理的问题"]["缺失值"]["new_feedback_name"]}
- servicer_name: {report["处理的问题"]["缺失值"]["servicer_name"]}

### 其他问题
- 时间顺序异常: {report["处理的问题"]["时间顺序异常"]}
- 消息序号异常: {report["处理的问题"]["消息序号异常"]}

## 清洗前后对比
- 平均消息数:
  - 清洗前: {report["清洗前后对比"]["平均消息数"]["清洗前"]:.2f}
  - 清洗后: {report["清洗前后对比"]["平均消息数"]["清洗后"]:.2f}
- 用户消息占比:
  - 清洗前: {report["清洗前后对比"]["用户消息占比"]["清洗前"]*100:.2f}%
  - 清洗后: {report["清洗前后对比"]["用户消息占比"]["清洗后"]*100:.2f}%
"""
    
    with open(os.path.splitext(report_path)[0] + '.md', 'w', encoding='utf-8') as f:
        f.write(md_report)


def clean_data(input_path, output_path, report_path=None, verbose=False):
    """
    清洗对话数据
    
    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        report_path: 清洗报告输出路径
        verbose: 是否显示详细日志
    
    返回:
        bool: 清洗是否成功
    """
    try:
        print(f"开始读取JSON文件: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        print(f"读取完成，共{len(conversations)}个对话")
        
        # 保存原始对话数据（用于生成报告）
        original_conversations = conversations.copy()
        
        # 过滤有效对话
        valid_conversations = [conv for conv in conversations if is_valid_conversation(conv)]
        print(f"有效对话数: {len(valid_conversations)}")
        
        # 清洗对话数据
        cleaned_conversations = []
        for i, conv in enumerate(valid_conversations):
            if verbose and i % 100 == 0:
                print(f"正在处理第{i+1}/{len(valid_conversations)}个对话...")
            
            cleaned = clean_conversation(conv)
            cleaned_conversations.append(cleaned)
        
        print(f"清洗完成，共处理{len(cleaned_conversations)}个对话")
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_conversations, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {output_path}")
        
        # 生成清洗报告
        if report_path:
            print(f"正在生成清洗报告...")
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            generate_cleaning_report(original_conversations, cleaned_conversations, report_path)
            print(f"清洗报告已保存到: {report_path}")
        
        return True
    
    except Exception as e:
        print(f"清洗过程中出错: {e}")
        return False


def main():
    """主函数"""
    args = parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 执行清洗
    start_time = datetime.now()
    print(f"开始时间: {start_time}")
    
    success = clean_data(args.input, args.output, args.report, args.verbose)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据清洗成功！")
    else:
        print("数据清洗失败！")


if __name__ == "__main__":
    main()

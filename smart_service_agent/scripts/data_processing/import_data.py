#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据导入脚本
功能：将Excel格式的客服对话数据导入并转换为JSON格式
用法：python import_data.py --source <excel_file_path> --target <json_file_path>
"""

import argparse
import json
import os
import pandas as pd
from datetime import datetime


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='导入Excel格式的客服对话数据并转换为JSON格式')
    parser.add_argument('--source', required=True, help='源Excel文件路径')
    parser.add_argument('--target', required=True, help='目标JSON文件路径')
    parser.add_argument('--limit', type=int, default=None, help='限制导入的行数，默认全部导入')
    return parser.parse_args()


def excel_to_json(excel_path, json_path, limit=None):
    """
    将Excel文件转换为JSON格式
    
    参数:
        excel_path (str): Excel文件路径
        json_path (str): 输出JSON文件路径
        limit (int, optional): 限制读取的行数，用于测试
    
    返回:
        bool: 转换是否成功
    """
    try:
        print(f"开始读取Excel文件: {excel_path}")
        # 读取Excel文件
        if limit:
            df = pd.read_excel(excel_path, nrows=limit)
            print(f"已限制读取前{limit}行数据")
        else:
            df = pd.read_excel(excel_path)
        
        # 检查数据基本情况
        total_rows = len(df)
        unique_conversations = df['touch_id'].nunique()
        print(f"总行数: {total_rows}")
        print(f"唯一对话数: {unique_conversations}")
        
        # 检查并处理日期时间列
        date_columns = ['user_start_time', 'user_end_time', 'create_time', 'send_time']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).astype(str)
        
        # 将DataFrame转换为字典列表
        records = df.to_dict(orient='records')
        
        # 按对话ID组织数据
        conversations = {}
        for record in records:
            touch_id = record['touch_id']
            if touch_id not in conversations:
                conversations[touch_id] = {
                    'touch_id': touch_id,
                    'user_name': record.get('user_name', ''),
                    'servicer_name': record.get('servicer_name', ''),
                    'group_name': record.get('group_name', ''),
                    'start_time': record.get('user_start_time', ''),
                    'end_time': record.get('user_end_time', ''),
                    'create_time': record.get('create_time', ''),
                    'messages': []
                }
            
            # 添加消息
            message = {
                'seq_no': record.get('seq_no', 0),
                'send_time': record.get('send_time', ''),
                'sender_type': record.get('sender_type', ''),
                'content': record.get('send_content', '')
            }
            conversations[touch_id]['messages'].append(message)
        
        # 将对话按照消息序号排序
        for touch_id, conversation in conversations.items():
            conversation['messages'].sort(key=lambda x: x['seq_no'])
        
        # 创建目标目录（如果不存在）
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        # 写入JSON文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(list(conversations.values()), f, ensure_ascii=False, indent=2)
        
        print(f"转换完成，共处理{unique_conversations}个对话，已保存到: {json_path}")
        return True
    
    except Exception as e:
        print(f"转换过程中出错: {e}")
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
    
    success = excel_to_json(args.source, args.target, args.limit)
    
    end_time = datetime.now()
    print(f"结束时间: {end_time}")
    print(f"耗时: {end_time - start_time}")
    
    if success:
        print("数据导入成功！")
    else:
        print("数据导入失败！")


if __name__ == "__main__":
    main()

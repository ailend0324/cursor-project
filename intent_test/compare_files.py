#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
比较源文件和处理后的文件，找出并解决问题
"""

import pandas as pd
import numpy as np
import json
import os

# 文件路径
SOURCE_FILE = '/Users/boxie/cursor/ai_service/data/raw/250407.xlsx'
PROCESSED_FILE_1 = '/Users/boxie/cursor/intent_test/优化后真实预处理数据样本.csv'
PROCESSED_FILE_2 = '/Users/boxie/cursor/intent_test/完整维度预处理数据样本.csv'
JSON_FILE = '/Users/boxie/cursor/intent_test/complete_preprocessing_20250418_122817/preprocessed_dialogs.json'

def compare_files():
    """比较源文件和处理后的文件"""
    print("=" * 50)
    print("源文件和处理后文件比较")
    print("=" * 50)
    
    # 1. 读取源文件
    print("\n读取源文件...")
    source_df = pd.read_excel(SOURCE_FILE)
    print(f"源文件列名: {source_df.columns.tolist()}")
    print(f"源文件形状: {source_df.shape}")
    
    # 2. 读取处理后的文件1
    print("\n读取优化后真实预处理数据样本...")
    try:
        processed_df1 = pd.read_csv(PROCESSED_FILE_1)
        print(f"处理后文件1列名: {processed_df1.columns.tolist()}")
        print(f"处理后文件1形状: {processed_df1.shape}")
    except Exception as e:
        print(f"读取处理后文件1出错: {e}")
    
    # 3. 读取处理后的文件2
    print("\n读取完整维度预处理数据样本...")
    try:
        processed_df2 = pd.read_csv(PROCESSED_FILE_2)
        print(f"处理后文件2列名: {processed_df2.columns.tolist()}")
        print(f"处理后文件2形状: {processed_df2.shape}")
    except Exception as e:
        print(f"读取处理后文件2出错: {e}")
    
    # 4. 读取JSON文件
    print("\n读取JSON文件...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"JSON文件对话数: {len(json_data)}")
        if len(json_data) > 0:
            print(f"第一个对话的元数据字段: {list(json_data[0]['metadata'].keys())}")
            print(f"第一个对话的消息数: {len(json_data[0]['messages'])}")
            if len(json_data[0]['messages']) > 0:
                print(f"第一条消息的字段: {list(json_data[0]['messages'][0].keys())}")
    except Exception as e:
        print(f"读取JSON文件出错: {e}")
    
    # 5. 比较源文件和处理后文件的列
    print("\n比较列名...")
    source_columns = set(source_df.columns)
    
    if 'processed_df1' in locals():
        processed_columns1 = set(processed_df1.columns)
        missing_columns1 = source_columns - processed_columns1
        extra_columns1 = processed_columns1 - source_columns
        print(f"处理后文件1缺少的列: {missing_columns1}")
        print(f"处理后文件1额外的列: {extra_columns1}")
    
    if 'processed_df2' in locals():
        processed_columns2 = set(processed_df2.columns)
        missing_columns2 = source_columns - processed_columns2
        extra_columns2 = processed_columns2 - source_columns
        print(f"处理后文件2缺少的列: {missing_columns2}")
        print(f"处理后文件2额外的列: {extra_columns2}")
    
    # 6. 检查JSON文件中的字段
    print("\n检查JSON文件中的字段...")
    if 'json_data' in locals() and len(json_data) > 0:
        metadata_fields = set(json_data[0]['metadata'].keys())
        source_columns_set = set([col.lower() for col in source_columns])
        metadata_missing = [field for field in source_columns_set if field.lower() not in [f.lower() for f in metadata_fields]]
        print(f"JSON元数据中缺少的源文件字段: {metadata_missing}")
        
        if len(json_data[0]['messages']) > 0:
            message_fields = set(json_data[0]['messages'][0].keys())
            print(f"消息字段: {message_fields}")
    
    # 7. 检查数据内容
    print("\n检查数据内容样本...")
    if 'source_df' in locals():
        print("\n源文件数据样本:")
        print(source_df.head(1).to_string())
    
    if 'processed_df1' in locals():
        print("\n处理后文件1数据样本:")
        print(processed_df1.head(1).to_string())
    
    if 'processed_df2' in locals():
        print("\n处理后文件2数据样本:")
        print(processed_df2.head(1).to_string())
    
    # 8. 检查new_feedback_name字段
    print("\n检查new_feedback_name字段...")
    if 'source_df' in locals():
        print(f"源文件中new_feedback_name的唯一值数量: {source_df['new_feedback_name'].nunique()}")
        print(f"源文件中new_feedback_name的前5个唯一值: {source_df['new_feedback_name'].unique()[:5]}")
    
    if 'json_data' in locals() and len(json_data) > 0:
        feedback_values = []
        for dialog in json_data[:100]:  # 只检查前100个对话
            if 'new_feedback_name' in dialog['metadata']:
                feedback_values.append(dialog['metadata']['new_feedback_name'])
        print(f"JSON文件中new_feedback_name的唯一值数量: {len(set(feedback_values))}")
        print(f"JSON文件中new_feedback_name的前5个唯一值: {list(set(feedback_values))[:5]}")
    
    print("=" * 50)

def identify_problems():
    """识别问题并提出解决方案"""
    print("\n识别的问题和解决方案:")
    
    # 读取源文件和处理后的文件
    source_df = pd.read_excel(SOURCE_FILE)
    
    try:
        processed_df1 = pd.read_csv(PROCESSED_FILE_1)
    except:
        processed_df1 = None
    
    try:
        processed_df2 = pd.read_csv(PROCESSED_FILE_2)
    except:
        processed_df2 = None
    
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except:
        json_data = None
    
    # 1. 检查缺失的列
    source_columns = set(source_df.columns)
    
    if processed_df1 is not None:
        processed_columns1 = set(processed_df1.columns)
        missing_columns1 = source_columns - processed_columns1
        if missing_columns1:
            print(f"问题1: 优化后真实预处理数据样本缺少以下列: {missing_columns1}")
            print("解决方案: 修改数据预处理代码，确保保留这些列")
    
    if processed_df2 is not None:
        processed_columns2 = set(processed_df2.columns)
        missing_columns2 = source_columns - processed_columns2
        if missing_columns2:
            print(f"问题2: 完整维度预处理数据样本缺少以下列: {missing_columns2}")
            print("解决方案: 修改数据预处理代码，确保保留这些列")
    
    # 2. 检查new_feedback_name字段
    if json_data is not None:
        feedback_in_json = False
        for dialog in json_data[:10]:
            if 'new_feedback_name' in dialog['metadata'] and dialog['metadata']['new_feedback_name']:
                feedback_in_json = True
                break
        
        if not feedback_in_json:
            print("问题3: JSON文件中new_feedback_name字段可能缺失或为空")
            print("解决方案: 确保正确提取和保存new_feedback_name字段")
    
    # 3. 检查结构化信息
    if json_data is not None:
        has_structured_info = False
        for dialog in json_data[:10]:
            for msg in dialog['messages'][:5]:
                if 'structured_info' in msg:
                    has_structured_info = True
                    break
            if has_structured_info:
                break
        
        if not has_structured_info:
            print("问题4: 消息中可能缺少结构化信息字段")
            print("解决方案: 确保提取并保存结构化信息")
    
    # 4. 检查数据类型转换问题
    if json_data is not None:
        for dialog in json_data[:10]:
            for msg in dialog['messages'][:5]:
                for key, value in msg.items():
                    if isinstance(value, (dict, list)):
                        print(f"问题5: 字段'{key}'的值是复杂类型，可能导致JSON序列化问题")
                        print("解决方案: 确保所有值都是简单类型，或者实现自定义JSON序列化")
    
    print("\n建议的改进:")
    print("1. 确保所有原始数据维度都被保留")
    print("2. 正确处理new_feedback_name等可能包含特殊值的字段")
    print("3. 增强结构化信息提取，确保关键业务数据被正确识别")
    print("4. 优化JSON序列化处理，避免类型转换问题")
    print("5. 添加数据质量验证步骤，确保处理后的数据符合预期")

if __name__ == "__main__":
    compare_files()
    identify_problems()

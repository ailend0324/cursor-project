import pandas as pd
import os
import sys

def analyze_excel_structure(file_path):
    """分析Excel文件的结构并显示摘要信息"""
    try:
        # 读取Excel文件
        print(f"正在读取文件: {file_path}")
        df = pd.read_excel(file_path)
        
        # 显示基本信息
        print(f"\n文件大小: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")
        print(f"数据行数: {df.shape[0]}")
        print(f"数据列数: {df.shape[1]}")
        
        # 显示列名和数据类型
        print("\n列名和数据类型:")
        for col in df.columns:
            print(f"- {col} ({df[col].dtype})")
        
        # 显示前5行数据
        print("\n前5行数据预览:")
        print(df.head(5).to_string())
        
        # 检查空值
        null_counts = df.isnull().sum()
        print("\n每列空值数:")
        for col in df.columns:
            print(f"- {col}: {null_counts[col]} ({(null_counts[col] / len(df)) * 100:.2f}%)")
        
        # 如果是对话数据，统计对话数量
        if 'session_id' in df.columns or 'conversation_id' in df.columns:
            id_column = 'session_id' if 'session_id' in df.columns else 'conversation_id'
            unique_conversations = df[id_column].nunique()
            print(f"\n唯一对话数量: {unique_conversations}")
            
        return df
    except Exception as e:
        print(f"错误: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "/Users/boxie/cursor/ai_service/data/merged_chat_records.xlsx"
    
    df = analyze_excel_structure(file_path) 
import pandas as pd

def verify_merged_file():
    print("开始验证合并后的文件...")
    
    # 读取合并后的文件
    print("读取合并后的文件: merged_chat_records.xlsx")
    merged_df = pd.read_excel('merged_chat_records.xlsx')
    
    # 显示基本信息
    print("\n基本信息:")
    print(f"总行数: {len(merged_df)}")
    print(f"总列数: {len(merged_df.columns)}")
    print("\n列名:")
    for col in merged_df.columns:
        print(f"- {col}")
    
    # 显示前5行数据预览
    print("\n数据预览 (前5行):")
    print(merged_df.head())
    
    # 检查是否有重复行
    duplicates = merged_df.duplicated().sum()
    print(f"\n重复行数: {duplicates}")
    
    # 检查是否有空值
    null_counts = merged_df.isnull().sum()
    print("\n每列空值统计:")
    for col, count in null_counts.items():
        if count > 0:
            print(f"- {col}: {count} 个空值")

if __name__ == "__main__":
    verify_merged_file() 
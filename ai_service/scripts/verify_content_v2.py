import pandas as pd
import glob
import numpy as np

def verify_content():
    print("开始验证文件内容完整性...")
    
    # 读取合并后的文件
    print("\n读取合并后的文件: merged_chat_records.xlsx")
    merged_df = pd.read_excel('merged_chat_records.xlsx')
    print(f"合并文件总行数: {len(merged_df)}")
    
    # 获取所有原始xlsx文件
    original_files = glob.glob('*.xlsx')
    original_files.remove('merged_chat_records.xlsx')
    
    total_original_rows = 0
    verification_results = []
    
    # 对每个原始文件进行验证
    for file in original_files:
        print(f"\n验证文件: {file}")
        original_df = pd.read_excel(file)
        total_original_rows += len(original_df)
        
        # 使用关键列创建唯一标识
        key_columns = ['touch_id', 'user_name', 'send_content', 'seq_no']
        
        # 创建用于比较的键
        def create_key(df):
            return df[key_columns].fillna('').astype(str).agg('|'.join, axis=1)
        
        original_keys = create_key(original_df)
        merged_keys = create_key(merged_df)
        
        # 检查原始文件中的行在合并文件中的存在情况
        found_rows = original_keys.isin(merged_keys).sum()
        missing_rows = len(original_df) - found_rows
        
        verification_results.append({
            'file': file,
            'original_rows': len(original_df),
            'found_in_merged': found_rows,
            'missing_rows': missing_rows
        })
        
        # 如果有缺失的行，显示一些示例
        if missing_rows > 0:
            print(f"警告：发现 {missing_rows} 行数据缺失！")
            missing_mask = ~original_keys.isin(merged_keys)
            missing_df = original_df[missing_mask]
            print("\n缺失数据示例（最多显示3行）：")
            print(missing_df[key_columns].head(3))
            
            # 显示一些统计信息
            print("\n数据分布检查：")
            print("原始文件中的一些 touch_id：")
            print(original_df['touch_id'].value_counts().head(3))
            print("\n合并文件中对应的 touch_id：")
            print(merged_df['touch_id'].value_counts().head(3))
    
    # 打印验证结果摘要
    print("\n=== 验证结果摘要 ===")
    print(f"原始文件总行数: {total_original_rows}")
    print(f"合并文件总行数: {len(merged_df)}")
    print(f"差异: {len(merged_df) - total_original_rows} 行")
    
    print("\n各文件详细统计：")
    for result in verification_results:
        print(f"\n文件: {result['file']}")
        print(f"- 原始行数: {result['original_rows']}")
        print(f"- 在合并文件中找到: {result['found_in_merged']}")
        print(f"- 缺失行数: {result['missing_rows']}")

if __name__ == "__main__":
    verify_content() 
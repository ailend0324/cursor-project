import pandas as pd
import os
import glob

def merge_excel_files():
    # 获取目录下所有的xlsx文件
    excel_files = glob.glob('*.xlsx')
    
    # 创建一个空的DataFrame列表
    dfs = []
    
    # 读取每个Excel文件并添加到列表中
    for file in excel_files:
        print(f"正在读取文件: {file}")
        try:
            # 读取Excel文件
            df = pd.read_excel(file)
            dfs.append(df)
            print(f"成功读取文件: {file}, 行数: {len(df)}")
        except Exception as e:
            print(f"读取文件 {file} 时出错: {str(e)}")
    
    if not dfs:
        print("没有成功读取任何文件！")
        return
    
    # 合并所有DataFrame
    print("正在合并所有文件...")
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"合并完成，总行数: {len(combined_df)}")
    
    # 保存合并后的文件
    output_file = 'merged_chat_records.xlsx'
    print(f"正在保存合并后的文件到: {output_file}")
    combined_df.to_excel(output_file, index=False)
    print("合并完成！")

if __name__ == "__main__":
    merge_excel_files() 
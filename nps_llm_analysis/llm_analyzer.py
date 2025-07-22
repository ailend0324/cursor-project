import pandas as pd
import os
import json
import time
import google.generativeai as genai
from tqdm import tqdm

def get_gemini_analysis(model, row):
    """
    调用Google Gemini API，结合上下文对单条记录进行深度分析。
    """
    # 1. 提取上下文信息
    user_identity = row['用户身份']
    trade_result = row['交易结果']
    comment = row['用户留言']
    nps_score = row['NPS评分']
    nps_category = row['NPS']

    # 2. 构建给Gemini的"指令包"（Prompt）
    prompt = (
        "你是一位顶级的电商平台产品分析专家，专门分析用户反馈。"
        "你的任务是深入理解用户留言背后的真实、具体的核心诉求，并结合其上下文进行分析。"
        "请将你的分析结果以一个JSON对象返回，该对象必须包含两个键："
        "'core_demand' (一个精炼的短语，如'验货标准太低'或'费用规则不公') 和 "
        "'analysis_text' (一段详细的、包含上下文的综合分析)。\n\n"
        "--- 用户数据 ---\n"
        f"用户身份：{user_identity}\n"
        f"交易结果：{trade_result}\n"
        f"NPS评分：{nps_score} ({nps_category})\n"
        f"用户留言：'{comment}'\n"
        "--- 分析结果 (JSON) ---"
    )

    try:
        # 3. 调用Gemini API
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # 4. 解析返回的JSON结果
        analysis_result = json.loads(response.text)
        # 增加礼貌性停顿，避免API速率限制
        time.sleep(1) 
        return analysis_result.get('core_demand', '分析失败'), analysis_result.get('analysis_text', '分析失败')

    except Exception as e:
        print(f"调用Gemini API时发生错误: {e}")
        return "API调用失败", f"处理留言 '{comment[:20]}...' 时出错。"

def run_gemini_analysis(output_path):
    """
    执行完整的、由Gemini驱动的上下文分析流程。
    """
    # --- 安全设置 ---
    try:
        api_key = os.environ["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except KeyError:
        print("错误：未找到GOOGLE_API_KEY环境变量。")
        print("请先设置API Key: export GOOGLE_API_KEY='Your-Gemini-API-Key'")
        return
    
    model = genai.GenerativeModel('gemini-2.0-flash')

    # --- 数据准备 ---
    file_path = 'nps_llm_analysis/processed_data.xlsx'
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"错误：找不到数据文件 -> {file_path}")
        return

    # 清洗和筛选数据
    detractors_df = df[df['NPS'] == '贬损者'].copy()
    detractors_df.dropna(subset=['用户留言'], inplace=True)
    detractors_df = detractors_df[~detractors_df['用户留言'].isin(['无留言', '好评'])]
    detractors_df = detractors_df[detractors_df['用户留言'].str.strip().astype(bool)]

    if detractors_df.empty:
        print('没有找到有效的"贬损者"留言进行分析。')
        return
    
    # --- 全量LLM分析 ---
    # 报告总数并准备进度条
    total_comments = len(detractors_df)
    print(f"已找到 {total_comments} 条有效留言，准备开始全量分析...")
    tqdm.pandas(desc="Gemini正在分析")
    
    # 将 .apply 替换为 .progress_apply 来启用进度条
    analysis_results = detractors_df.progress_apply(lambda row: get_gemini_analysis(model, row), axis=1)

    detractors_df['核心诉求 (Gemini)'] = [result[0] for result in analysis_results]
    detractors_df['LLM综合分析 (Gemini)'] = [result[1] for result in analysis_results]
    
    # --- 保存成果 ---
    try:
        output_columns = ['用户身份', '交易结果', 'NPS评分', '用户留言', '核心诉求 (Gemini)', 'LLM综合分析 (Gemini)']
        detractors_df[output_columns].to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n分析完成！由Gemini生成的全量报告已保存到: {output_path}")
    except Exception as e:
        print(f"保存Excel文件时出错: {e}")

if __name__ == '__main__':
    output_file = 'nps_llm_analysis/nps_GEMINI_analysis_report_FULL.xlsx'
    run_gemini_analysis(output_file) 
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from collections import Counter
import matplotlib.font_manager as fm
import re
import jieba
import jieba.analyse
from wordcloud import WordCloud

# 设置中文字体支持
# 尝试设置中文字体
chinese_fonts = [f for f in fm.findSystemFonts() if 'chinese' in f.lower() or 'cjk' in f.lower() or 'yahei' in f.lower() or 'simhei' in f.lower()]
if chinese_fonts:
    plt.rcParams['font.family'] = fm.FontProperties(fname=chinese_fonts[0]).get_name()
else:
    # 备选字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'WenQuanYi Micro Hei']
    plt.rcParams['axes.unicode_minus'] = False

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_data(excel_path):
    """加载Excel数据文件"""
    try:
        print(f"正在加载数据: {excel_path}")
        df = pd.read_excel(excel_path)
        print(f"成功加载 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def preprocess_data(df):
    """预处理数据"""
    print("预处理数据...")
    
    # 确保时间列为datetime类型
    for col in ['timestamp', 'user_start_time', 'user_end_time']:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except:
                print(f"转换{col}列为日期时间类型失败")
    
    # 创建日期列
    if 'timestamp' in df.columns:
        df['date'] = df['timestamp'].dt.date
    
    # 创建小时列
    if 'timestamp' in df.columns:
        df['hour'] = df['timestamp'].dt.hour
    
    # 标识用户和机器人消息
    if 'sender_type' in df.columns:
        df['is_user'] = df['sender_type'] == 1.0
        df['is_bot'] = df['sender_type'] == 2.0
    
    return df

def plot_conversation_volume_over_time(df, output_dir):
    """绘制一段时间内的对话量"""
    print("绘制对话量时间趋势...")
    
    if 'touch_id' not in df.columns or 'date' not in df.columns:
        print("缺少必要的列：touch_id 或 date")
        return
    
    # 按日期计算对话数量
    daily_conversations = df.groupby('date')['touch_id'].nunique()
    
    # 确保日期是连续的
    date_range = pd.date_range(start=daily_conversations.index.min(), end=daily_conversations.index.max())
    daily_conversations = daily_conversations.reindex(date_range, fill_value=0)
    
    # 绘制日对话量
    plt.figure(figsize=(12, 6))
    plt.plot(daily_conversations.index, daily_conversations.values, marker='o', linestyle='-')
    plt.title('每日对话数量')
    plt.xlabel('日期')
    plt.ylabel('对话数量')
    plt.grid(True, alpha=0.3)
    
    # 格式化x轴日期
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))  # 每7天显示一个刻度
    
    # 自动旋转日期标签
    plt.gcf().autofmt_xdate()
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'daily_conversation_volume.png'), dpi=300)
    plt.close()
    
    # 按小时计算对话数量
    if 'hour' in df.columns:
        hourly_conversations = df.groupby('hour')['touch_id'].nunique()
        
        plt.figure(figsize=(12, 6))
        plt.bar(hourly_conversations.index, hourly_conversations.values, color='skyblue')
        plt.title('各小时对话数量')
        plt.xlabel('小时')
        plt.ylabel('对话数量')
        plt.xticks(range(0, 24, 2))  # 每2小时显示一个刻度
        plt.grid(True, alpha=0.3, axis='y')
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'hourly_conversation_volume.png'), dpi=300)
        plt.close()

def plot_conversation_duration_distribution(df, output_dir):
    """绘制对话持续时间分布"""
    print("绘制对话持续时间分布...")
    
    if 'user_start_time' not in df.columns or 'user_end_time' not in df.columns:
        print("缺少必要的列：user_start_time 或 user_end_time")
        return
    
    # 按对话ID分组
    conv_duration = df.groupby('touch_id').agg({
        'user_start_time': 'min',
        'user_end_time': 'max'
    }).dropna()
    
    # 计算持续时间（分钟）
    conv_duration['duration_minutes'] = (conv_duration['user_end_time'] - conv_duration['user_start_time']).dt.total_seconds() / 60
    
    # 过滤掉异常值
    conv_duration = conv_duration[(conv_duration['duration_minutes'] >= 0) & (conv_duration['duration_minutes'] <= 120)]
    
    # 绘制持续时间分布
    plt.figure(figsize=(12, 6))
    
    # 使用更适合的bin大小
    bins = [0, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120]
    
    plt.hist(conv_duration['duration_minutes'], bins=bins, color='skyblue', alpha=0.7, edgecolor='black')
    plt.title('对话持续时间分布')
    plt.xlabel('持续时间（分钟）')
    plt.ylabel('对话数量')
    plt.grid(True, alpha=0.3)
    
    # 添加平均线
    mean_duration = conv_duration['duration_minutes'].mean()
    plt.axvline(mean_duration, color='red', linestyle='dashed', linewidth=1)
    plt.text(mean_duration + 1, plt.ylim()[1] * 0.9, f'平均: {mean_duration:.2f}分钟', color='red')
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'conversation_duration_distribution.png'), dpi=300)
    plt.close()
    
    # 绘制箱线图
    plt.figure(figsize=(10, 6))
    sns.boxplot(y=conv_duration['duration_minutes'])
    plt.title('对话持续时间箱线图')
    plt.ylabel('持续时间（分钟）')
    plt.grid(True, alpha=0.3, axis='y')
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'conversation_duration_boxplot.png'), dpi=300)
    plt.close()

def plot_conversation_turns_distribution(df, output_dir):
    """绘制对话轮次分布"""
    print("绘制对话轮次分布...")
    
    if 'touch_id' not in df.columns:
        print("缺少必要的列：touch_id")
        return
    
    # 计算每个对话的消息数量
    conv_turns = df.groupby('touch_id').size()
    
    # 绘制轮次分布
    plt.figure(figsize=(12, 6))
    
    # 使用更适合的bin大小
    bins = [0, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
    
    plt.hist(conv_turns.values, bins=bins, color='lightgreen', alpha=0.7, edgecolor='black')
    plt.title('对话轮次分布')
    plt.xlabel('轮次数量')
    plt.ylabel('对话数量')
    plt.grid(True, alpha=0.3)
    
    # 添加平均线
    mean_turns = conv_turns.mean()
    plt.axvline(mean_turns, color='red', linestyle='dashed', linewidth=1)
    plt.text(mean_turns + 1, plt.ylim()[1] * 0.9, f'平均: {mean_turns:.2f}轮', color='red')
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'conversation_turns_distribution.png'), dpi=300)
    plt.close()

def extract_keywords_from_messages(df, output_dir):
    """从用户消息中提取关键词并生成词云"""
    print("提取用户消息关键词并生成词云...")
    
    if 'content' not in df.columns or 'is_user' not in df.columns:
        print("缺少必要的列：content 或 is_user")
        return
    
    # 提取用户消息
    user_messages = df[df['is_user']]['content'].dropna().astype(str)
    
    if user_messages.empty:
        print("没有用户消息可用于分析")
        return
    
    # 合并所有用户消息
    all_user_content = " ".join(user_messages)
    
    # 提取关键词
    keywords = jieba.analyse.extract_tags(all_user_content, topK=100, withWeight=True)
    
    # 创建词频字典
    keyword_freq = {word: freq for word, freq in keywords}
    
    # 绘制前20个关键词的条形图
    top_keywords = dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20])
    
    plt.figure(figsize=(12, 8))
    plt.barh(list(reversed(list(top_keywords.keys()))), list(reversed(list(top_keywords.values()))), color='skyblue')
    plt.title('用户消息中的Top20关键词')
    plt.xlabel('权重')
    plt.ylabel('关键词')
    plt.grid(True, alpha=0.3, axis='x')
    
    # 保存图表
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'top_keywords.png'), dpi=300)
    plt.close()
    
    # 生成词云
    try:
        font_path = None
        if chinese_fonts:
            font_path = chinese_fonts[0]
        
        wordcloud = WordCloud(
            width=1200, 
            height=800,
            font_path=font_path,
            background_color='white',
            max_words=100,
            max_font_size=150,
            random_state=42
        ).generate_from_frequencies(keyword_freq)
        
        plt.figure(figsize=(16, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(os.path.join(output_dir, 'user_messages_wordcloud.png'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"生成词云时出错: {e}")

def plot_human_transfer_analysis(df, output_dir):
    """分析转人工请求"""
    print("分析转人工请求...")
    
    if 'content' not in df.columns or 'is_user' not in df.columns:
        print("缺少必要的列：content 或 is_user")
        return
    
    # 查找包含转人工请求的用户消息
    transfer_keywords = ["转人工", "人工客服", "真人", "转接", "人工"]
    
    # 创建标记转人工请求的列
    df['is_transfer_request'] = df.apply(
        lambda row: row['is_user'] and any(keyword in str(row['content']) for keyword in transfer_keywords) 
        if isinstance(row['content'], str) else False, axis=1
    )
    
    # 统计包含转人工请求的对话数量
    transfer_count = df[df['is_transfer_request']]['touch_id'].nunique()
    total_conv_count = df['touch_id'].nunique()
    
    transfer_percentage = (transfer_count / total_conv_count) * 100 if total_conv_count > 0 else 0
    
    # 创建饼图
    plt.figure(figsize=(10, 8))
    labels = ['有转人工请求', '无转人工请求']
    sizes = [transfer_count, total_conv_count - transfer_count]
    colors = ['#ff9999', '#66b3ff']
    explode = (0.1, 0)  # 突出显示第一个扇形
    
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.axis('equal')  # 确保饼图是圆的
    plt.title('转人工请求比例')
    
    # 保存图表
    plt.savefig(os.path.join(output_dir, 'human_transfer_percentage.png'), dpi=300)
    plt.close()
    
    # 分析请求转人工的对话轮次
    if 'touch_id' in df.columns and 'is_transfer_request' in df.columns:
        # 对于每个对话，找到第一次转人工请求的位置
        transfer_positions = []
        
        for touch_id, group in df.groupby('touch_id'):
            # 重置索引以便计算轮次
            group = group.reset_index(drop=True)
            
            # 查找第一次转人工请求的位置
            transfer_rows = group[group['is_transfer_request']]
            
            if not transfer_rows.empty:
                # 第一次转人工请求的位置（从1开始计数）
                position = transfer_rows.index[0] + 1
                transfer_positions.append(position)
        
        if transfer_positions:
            # 绘制转人工请求轮次分布
            plt.figure(figsize=(12, 6))
            bins = list(range(1, 26, 2)) + [30, 40, 50]  # 自定义bin
            plt.hist(transfer_positions, bins=bins, color='salmon', alpha=0.7, edgecolor='black')
            plt.title('转人工请求在对话中的轮次分布')
            plt.xlabel('对话轮次')
            plt.ylabel('请求次数')
            plt.grid(True, alpha=0.3)
            
            # 添加平均值线
            mean_position = np.mean(transfer_positions)
            plt.axvline(mean_position, color='red', linestyle='dashed', linewidth=1)
            plt.text(mean_position + 1, plt.ylim()[1] * 0.9, f'平均: {mean_position:.2f}轮', color='red')
            
            # 保存图表
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'transfer_request_position.png'), dpi=300)
            plt.close()

def generate_conversation_visualizations(excel_path=None, output_dir=None):
    """生成所有对话可视化"""
    # 设置默认路径
    if excel_path is None:
        excel_path = os.path.join(PROJECT_ROOT, 'data', 'merged_chat_records.xlsx')
    
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载数据
    df = load_data(excel_path)
    if df is None:
        return False
    
    # 预处理数据
    df = preprocess_data(df)
    
    # 生成各种可视化
    plot_conversation_volume_over_time(df, output_dir)
    plot_conversation_duration_distribution(df, output_dir)
    plot_conversation_turns_distribution(df, output_dir)
    extract_keywords_from_messages(df, output_dir)
    plot_human_transfer_analysis(df, output_dir)
    
    print(f"所有可视化图表已保存至: {output_dir}")
    return True

if __name__ == "__main__":
    import sys
    
    excel_path = None
    output_dir = None
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    generate_conversation_visualizations(excel_path, output_dir) 
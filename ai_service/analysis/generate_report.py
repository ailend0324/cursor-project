import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
import seaborn as sns
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class PDF(FPDF):
    def header(self):
        # 设置页眉
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '智能客服系统对话数据分析报告', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        # 设置页脚
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')

def load_data(file_path):
    """加载 JSON 数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def load_analysis_results():
    """加载分析结果"""
    analysis_results_path = os.path.join(PROJECT_ROOT, 'analysis', 'analysis_results.txt')
    results = {}
    
    try:
        with open(analysis_results_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # 提取基本信息
            if "基本数据信息" in content:
                results['basic_info'] = content.split("基本数据信息")[1].split("===")[0].strip()
            
            # 提取对话统计
            if "对话统计" in content:
                conversation_stats = content.split("对话统计")[1].split("===")[0].strip()
                results['conversation_stats'] = conversation_stats
            
            # 提取发送者类型分布
            if "发送者类型分布" in content:
                sender_distribution = content.split("发送者类型分布")[1].split("===")[0].strip()
                results['sender_distribution'] = sender_distribution
            
            # 提取问题分析
            if "问题分析" in content:
                question_analysis = content.split("问题分析")[1].split("===")[0].strip()
                results['question_analysis'] = question_analysis
            
            # 提取对话模式分析
            if "对话模式分析" in content:
                conversation_patterns = content.split("对话模式分析")[1].split("===")[0].strip()
                results['conversation_patterns'] = conversation_patterns
            
            # 提取持续时间分析
            if "对话持续时间分析" in content:
                duration_analysis = content.split("对话持续时间分析")[1].split("===")[0].strip()
                results['duration_analysis'] = duration_analysis
            
            # 提取转人工分析
            if "人工转接分析" in content:
                transfer_analysis = content.split("人工转接分析")[1].split("===")[0].strip()
                results['transfer_analysis'] = transfer_analysis
                
        return results
    except Exception as e:
        print(f"Error loading analysis results: {e}")
        return {}

def add_section_title(pdf, title):
    """添加章节标题"""
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, title, 0, 1, 'L', 1)
    pdf.ln(2)

def add_paragraph(pdf, text):
    """添加段落文本"""
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 5, text)
    pdf.ln(2)

def add_image(pdf, image_path, w=None):
    """添加图片"""
    if not os.path.exists(image_path):
        print(f"Warning: Image file not found: {image_path}")
        return False
    
    try:
        # 获取图片尺寸
        img = Image.open(image_path)
        img_w, img_h = img.size
        
        # 默认宽度为页面宽度的80%
        if w is None:
            w = pdf.w * 0.8
        
        # 计算等比例高度
        h = w * img_h / img_w
        
        # 居中放置图片
        x = (pdf.w - w) / 2
        
        # 检查是否需要新页
        if pdf.get_y() + h > pdf.h - 20:
            pdf.add_page()
        
        pdf.image(image_path, x=x, w=w)
        pdf.ln(5)
        return True
    except Exception as e:
        print(f"Error adding image {image_path}: {e}")
        return False

def format_number(num):
    """格式化数字，增加千位分隔符"""
    return f"{num:,}"

def generate_executive_summary(pdf, results):
    """生成执行摘要"""
    add_section_title(pdf, "1. 执行摘要")
    
    # 提取关键指标
    total_conversations = 0
    avg_duration = 0
    transfer_rate = 0
    
    # 从对话统计中提取总对话数
    if 'conversation_stats' in results:
        stats = results['conversation_stats']
        for line in stats.split('\n'):
            if "总对话数" in line:
                try:
                    total_conversations = int(line.split(':')[1].strip().replace(',', ''))
                except:
                    pass
    
    # 从持续时间分析中提取平均持续时间
    if 'duration_analysis' in results:
        duration = results['duration_analysis']
        for line in duration.split('\n'):
            if "平均对话持续时间" in line:
                try:
                    avg_duration = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
    
    # 从转人工分析中提取转人工率
    if 'transfer_analysis' in results:
        transfer = results['transfer_analysis']
        for line in transfer.split('\n'):
            if "转人工请求比例" in line:
                try:
                    transfer_rate = float(line.split(':')[1].strip().replace('%', ''))
                except:
                    pass
    
    # 生成摘要文本
    summary = (
        f"本报告分析了智能客服系统的对话数据，总计分析了{format_number(total_conversations)}次对话。"
        f"数据分析显示，平均对话持续时间为{avg_duration:.2f}分钟，"
        f"用户请求转人工的比例为{transfer_rate:.2f}%。\n\n"
        
        f"通过深入分析对话内容，我们识别了用户最常见的问题类型、对话模式和持续时间分布。"
        f"报告还包括对话聚类分析，揭示了不同类别的用户问题及其分布情况。\n\n"
        
        f"基于分析结果，我们为知识库扩展提供了建议，并对系统优化提出了具体措施，"
        f"以提高自动化率、减少转人工率，并提升整体服务质量。"
    )
    
    add_paragraph(pdf, summary)

def generate_data_overview(pdf, results):
    """生成数据概览"""
    add_section_title(pdf, "2. 数据概览")
    
    # 基本数据信息
    if 'basic_info' in results:
        add_paragraph(pdf, "2.1 基本数据信息")
        add_paragraph(pdf, results['basic_info'])
    
    # 对话统计
    if 'conversation_stats' in results:
        add_paragraph(pdf, "2.2 对话统计")
        add_paragraph(pdf, results['conversation_stats'])
    
    # 发送者类型分布
    if 'sender_distribution' in results:
        add_paragraph(pdf, "2.3 发送者类型分布")
        add_paragraph(pdf, results['sender_distribution'])
    
    # 添加可视化图表
    vis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    conversation_length_path = os.path.join(vis_dir, 'conversation_length_distribution.png')
    
    pdf.add_page()
    add_paragraph(pdf, "2.4 对话长度分布")
    if os.path.exists(conversation_length_path):
        add_image(pdf, conversation_length_path)
    else:
        add_paragraph(pdf, "对话长度分布图不可用")

def generate_conversation_analysis(pdf, results, intent_data):
    """生成对话分析"""
    pdf.add_page()
    add_section_title(pdf, "3. 对话内容分析")
    
    # 问题分析
    if 'question_analysis' in results:
        add_paragraph(pdf, "3.1 常见问题分析")
        add_paragraph(pdf, results['question_analysis'])
    
    # 添加词云图
    vis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    wordcloud_path = os.path.join(vis_dir, 'top_messages_wordcloud.png')
    
    if os.path.exists(wordcloud_path):
        add_image(pdf, wordcloud_path)
    
    # 聚类分析
    add_paragraph(pdf, "3.2 问题聚类分析")
    
    if intent_data and 'clustering_results' in intent_data:
        clustering = intent_data['clustering_results']
        cluster_sizes = clustering.get('cluster_sizes', {})
        cluster_keywords = clustering.get('cluster_keywords', {})
        
        # 排序聚类
        sorted_clusters = sorted([(int(k), v) for k, v in cluster_sizes.items()], 
                                key=lambda x: x[1], reverse=True)
        
        # 展示前5个最大的聚类
        top_clusters = sorted_clusters[:5]
        
        cluster_text = "主要问题聚类及其关键词：\n\n"
        
        for cluster_id, size in top_clusters:
            str_id = str(cluster_id)
            if str_id in cluster_keywords:
                keywords = ", ".join(cluster_keywords[str_id][:10])
                cluster_text += f"聚类 {cluster_id}（包含 {size} 条消息）：{keywords}\n\n"
        
        add_paragraph(pdf, cluster_text)
    else:
        add_paragraph(pdf, "聚类分析数据不可用")
    
    # 添加聚类分布图
    cluster_dist_path = os.path.join(vis_dir, 'cluster_size_distribution.png')
    
    if os.path.exists(cluster_dist_path):
        add_image(pdf, cluster_dist_path)
    
    # 意图分布
    pdf.add_page()
    add_paragraph(pdf, "3.3 用户意图分布")
    
    if intent_data and 'intent_categories' in intent_data:
        categories = intent_data['intent_categories']
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        intent_text = "用户意图类别分布：\n\n"
        total = sum(categories.values())
        
        for category, count in sorted_categories:
            percentage = (count / total) * 100
            intent_text += f"{category}: {count} ({percentage:.2f}%)\n"
        
        add_paragraph(pdf, intent_text)
    else:
        add_paragraph(pdf, "意图分布数据不可用")
    
    # 添加意图分布图
    intent_dist_path = os.path.join(vis_dir, 'intent_distribution.png')
    
    if os.path.exists(intent_dist_path):
        add_image(pdf, intent_dist_path)

def generate_conversation_patterns(pdf, results, flow_data):
    """生成对话模式分析"""
    pdf.add_page()
    add_section_title(pdf, "4. 对话模式分析")
    
    # 对话模式
    if 'conversation_patterns' in results:
        add_paragraph(pdf, "4.1 对话轮次分析")
        add_paragraph(pdf, results['conversation_patterns'])
    
    # 持续时间分析
    if 'duration_analysis' in results:
        add_paragraph(pdf, "4.2 对话持续时间分析")
        add_paragraph(pdf, results['duration_analysis'])
    
    # 添加持续时间分布图
    vis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    duration_path = os.path.join(vis_dir, 'conversation_duration_distribution.png')
    
    if os.path.exists(duration_path):
        add_image(pdf, duration_path)
    
    # 转人工分析
    pdf.add_page()
    add_paragraph(pdf, "4.3 转人工请求分析")
    
    if 'transfer_analysis' in results:
        add_paragraph(pdf, results['transfer_analysis'])
    
    # 添加转人工分布图
    transfer_path = os.path.join(vis_dir, 'transfer_request_distribution.png')
    
    if os.path.exists(transfer_path):
        add_image(pdf, transfer_path)
    
    # 对话流程分析
    add_paragraph(pdf, "4.4 对话流程模式")
    
    if flow_data:
        flow_stats = {}
        
        # 计算常见路径
        for conv in flow_data:
            flow = conv.get('flow_pattern', '')
            if flow:
                if flow in flow_stats:
                    flow_stats[flow] += 1
                else:
                    flow_stats[flow] = 1
        
        # 排序路径
        sorted_flows = sorted(flow_stats.items(), key=lambda x: x[1], reverse=True)
        
        flow_text = "常见对话流程模式（前5个）：\n\n"
        
        for i, (flow, count) in enumerate(sorted_flows[:5]):
            flow_text += f"{i+1}. {flow}: {count}次\n"
        
        add_paragraph(pdf, flow_text)
    else:
        add_paragraph(pdf, "对话流程数据不可用")

def generate_faq_suggestions(pdf, faq_data):
    """生成FAQ建议"""
    pdf.add_page()
    add_section_title(pdf, "5. 知识库扩展建议")
    
    if not faq_data:
        add_paragraph(pdf, "FAQ建议数据不可用")
        return
    
    # FAQ分类
    categories = {}
    for faq in faq_data:
        category = faq.get('category', '其他')
        if category in categories:
            categories[category] += 1
        else:
            categories[category] = 1
    
    # 排序类别
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    category_text = "5.1 建议FAQ类别分布：\n\n"
    for category, count in sorted_categories:
        category_text += f"{category}: {count}个问题\n"
    
    add_paragraph(pdf, category_text)
    
    # 添加FAQ类别分布图
    vis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    faq_dist_path = os.path.join(vis_dir, 'faq_category_distribution.png')
    
    if os.path.exists(faq_dist_path):
        add_image(pdf, faq_dist_path)
    
    # FAQ示例
    add_paragraph(pdf, "5.2 推荐新增FAQ示例")
    
    examples_text = ""
    # 从每个类别中选择一个示例
    displayed_categories = set()
    example_count = 0
    
    # 首先按类别分组
    category_faqs = {}
    for faq in faq_data:
        category = faq.get('category', '其他')
        if category not in category_faqs:
            category_faqs[category] = []
        category_faqs[category].append(faq)
    
    # 然后从每个类别中选择示例
    for category, faqs in category_faqs.items():
        if example_count >= 10:  # 最多显示10个示例
            break
        
        # 选择该类别中的第一个
        faq = faqs[0]
        question = faq.get('question', '')
        answer = faq.get('answer', '建议回答')
        cluster_id = faq.get('cluster_id', '')
        keywords = ', '.join(faq.get('keywords', [])[:5])
        
        examples_text += f"类别：{category}\n"
        examples_text += f"问题：{question}\n"
        examples_text += f"建议回答：{answer}\n"
        examples_text += f"关键词：{keywords}\n"
        examples_text += f"相关聚类：{cluster_id}\n\n"
        
        example_count += 1
    
    add_paragraph(pdf, examples_text)

def generate_optimization_suggestions(pdf, results, intent_data, faq_data, flow_data):
    """生成系统优化建议"""
    pdf.add_page()
    add_section_title(pdf, "6. 系统优化建议")
    
    # 基于分析结果生成优化建议
    suggestions = []
    
    # 1. 转人工率优化
    transfer_rate = 0
    if 'transfer_analysis' in results:
        transfer = results['transfer_analysis']
        for line in transfer.split('\n'):
            if "转人工请求比例" in line:
                try:
                    transfer_rate = float(line.split(':')[1].strip().replace('%', ''))
                except:
                    pass
    
    if transfer_rate > 0:
        suggestions.append({
            'title': "减少转人工率",
            'content': (
                f"当前转人工请求比例为{transfer_rate:.2f}%。通过分析转人工请求发生的对话轮次和内容，"
                f"建议在以下方面增强智能客服系统：\n"
                f"- 增强系统对复杂问题的处理能力\n"
                f"- 优化系统在多轮对话中的上下文理解\n"
                f"- 针对频繁触发转人工的问题类型，扩充知识库"
            )
        })
    
    # 2. 知识库覆盖率
    if intent_data and 'intent_categories' in intent_data:
        other_percentage = 0
        categories = intent_data['intent_categories']
        total = sum(categories.values())
        
        if '其他类' in categories:
            other_percentage = (categories['其他类'] / total) * 100
        
        if other_percentage > 50:
            suggestions.append({
                'title': "提高知识库覆盖率",
                'content': (
                    f"当前未分类问题比例为{other_percentage:.2f}%，表明知识库覆盖率不足。建议：\n"
                    f"- 基于聚类分析结果，扩充知识库覆盖范围\n"
                    f"- 增加{len(faq_data) if faq_data else '建议的'}个新FAQ条目\n"
                    f"- 优化现有FAQ内容，确保与用户实际问题表述一致"
                )
            })
    
    # 3. 对话效率
    avg_duration = 0
    if 'duration_analysis' in results:
        duration = results['duration_analysis']
        for line in duration.split('\n'):
            if "平均对话持续时间" in line:
                try:
                    avg_duration = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
    
    if avg_duration > 0:
        suggestions.append({
            'title': "提高对话效率",
            'content': (
                f"当前平均对话持续时间为{avg_duration:.2f}分钟。分析显示：\n"
                f"- 优化系统响应时间，减少用户等待\n"
                f"- 针对高频问题设计更直接的回答模板\n"
                f"- 改进多轮对话的上下文理解，减少澄清问题的需要"
            )
        })
    
    # 4. 用户体验
    suggestions.append({
        'title': "优化用户体验",
        'content': (
            "基于对话内容分析，建议：\n"
            "- 优化问题理解能力，减少误解和重复询问\n"
            "- 增强个性化响应，根据用户历史和偏好调整回答\n"
            "- 改进系统引导能力，在用户表述不清时提供更好的引导"
        )
    })
    
    # 5. 对话流程优化
    if flow_data:
        suggestions.append({
            'title': "优化对话流程",
            'content': (
                "基于对话流程分析，建议：\n"
                "- 识别并优化常见的低效对话路径\n"
                "- 针对特定类型问题，设计更高效的对话模板\n"
                "- 改进系统在多轮对话中的连贯性和逻辑性"
            )
        })
    
    # 输出建议
    for i, suggestion in enumerate(suggestions):
        add_paragraph(pdf, f"6.{i+1} {suggestion['title']}")
        add_paragraph(pdf, suggestion['content'])
        pdf.ln(5)

def generate_conclusion(pdf):
    """生成结论"""
    pdf.add_page()
    add_section_title(pdf, "7. 结论")
    
    conclusion = (
        "通过对大量客服对话数据的深入分析，我们获得了对用户需求和系统表现的全面理解。"
        "分析结果显示，当前智能客服系统已能处理大部分基础问题，但在复杂多轮对话、"
        "专业领域问题等方面仍有提升空间。\n\n"
        
        "本报告提出的知识库扩展建议和系统优化方向，旨在提高系统的自动化率、"
        "减少转人工需求，同时提升用户满意度。建议分阶段实施优化措施，"
        "并定期回顾分析数据，评估改进效果。\n\n"
        
        "持续的数据分析和系统优化，将帮助智能客服系统不断进化，"
        "更好地满足用户需求，提高服务效率和质量。"
    )
    
    add_paragraph(pdf, conclusion)

def generate_report():
    """生成完整报告"""
    print("开始生成报告...")
    
    # 创建输出目录
    report_dir = os.path.join(PROJECT_ROOT, 'analysis', 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    # 确保可视化目录存在
    vis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'visualizations')
    os.makedirs(vis_dir, exist_ok=True)
    
    # 创建完整分析目录
    analysis_dir = os.path.join(PROJECT_ROOT, 'analysis', 'complete_analysis')
    os.makedirs(analysis_dir, exist_ok=True)
    
    # 加载分析结果
    results = load_analysis_results()
    
    # 加载意图分析数据
    intent_data = load_data(os.path.join(analysis_dir, 'complete_intent_analysis.json'))
    
    # 加载FAQ建议数据
    faq_data = load_data(os.path.join(analysis_dir, 'extended_faq_suggestions.json'))
    
    # 加载对话流程数据
    flow_data = load_data(os.path.join(analysis_dir, 'conversation_flow_analysis.json'))
    
    # 生成报告时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建PDF对象
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 设置标题
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '智能客服系统对话数据分析报告', 0, 1, 'C')
    
    # 添加报告日期
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'生成日期：{datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'C')
    pdf.ln(10)
    
    # 生成目录（简化版）
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, '目录', 0, 1, 'L')
    pdf.ln(2)
    
    toc_items = [
        "1. 执行摘要",
        "2. 数据概览",
        "3. 对话内容分析",
        "4. 对话模式分析",
        "5. 知识库扩展建议",
        "6. 系统优化建议",
        "7. 结论"
    ]
    
    pdf.set_font('Arial', '', 10)
    for item in toc_items:
        pdf.cell(0, 8, item, 0, 1, 'L')
    
    pdf.ln(10)
    
    # 生成各个章节
    generate_executive_summary(pdf, results)
    generate_data_overview(pdf, results)
    generate_conversation_analysis(pdf, results, intent_data)
    generate_conversation_patterns(pdf, results, flow_data)
    generate_faq_suggestions(pdf, faq_data)
    generate_optimization_suggestions(pdf, results, intent_data, faq_data, flow_data)
    generate_conclusion(pdf)
    
    # 保存PDF
    output_path = os.path.join(report_dir, f'conversation_analysis_report_{timestamp}.pdf')
    pdf.output(output_path)
    
    print(f"报告生成完成，保存至: {output_path}")
    return output_path

if __name__ == "__main__":
    report_path = generate_report()
    print(f"报告已生成: {report_path}") 
# 回收宝智能客服系统

## 项目概述

回收宝智能客服系统是一个基于实际对话数据分析的客户服务解决方案，专为回收行业设计。本项目通过分析真实客户对话数据，构建针对性的知识库、分类体系和对话模型，提高自动化服务水平并优化人工客服资源配置。

## 数据分析成果

- **用户意图聚类分析**: 基于74万+真实对话记录，提取用户真实意图模式
- **问题分类体系**: 建立了基于实际业务场景的2级15类分类体系
- **FAQ知识库**: 构建了15个类别的精准FAQ，覆盖关键业务问题
- **服务模板库**: 开发了15+场景的标准回复模板
- **统计报告**: 生成HTML/Excel格式的综合分析报告

## 系统提升
- **FAQ匹配率**: 从2.19%提升至33.46%
- **问题解决路径**: 清晰定义15条解决路径，指导智能应答
- **业务覆盖**: 对"价格咨询"、"回收流程"等高频问题实现深度覆盖

## 项目结构

```
ai_service/
├── analysis/                       # 数据分析模块
│   ├── analyze_chat_data.py        # 对话数据分析脚本
│   ├── visualize_analysis.py       # 可视化和报告生成
│   ├── _intents.py     # 用户意图聚类分析
│   ├── user_intent_taxonomy.md     # 基于数据的意图分类
│   ├── question_categories.md      # 问题分类体系文档
│   ├── implementation_plan.md      # 系统升级实施计划
│   ├── analysis_results.txt        # 分析结果文本输出
│   ├── intent_analysis_details.json # 意图分析详细数据
│   └── user_intent_clusters.png    # 聚类可视化图表

├── knowledge_base/                 # 知识库模块
│   ├── faq.json                    # 常见问题及答案(15条)
│   ├── answer_templates.json       # 基础应答模板(3条)
│   └── templates.json              # 扩展业务场景模板(15条)

├── data/                           # 数据存储模块
│   ├── merged_chat_records.xlsx    # 合并后的对话数据(74.8万条)
│   └── raw/                        # 原始数据文件目录

├── scripts/                        # 工具脚本模块
│   ├── merge_excel.py              # Excel文件合并工具
│   ├── verify_data_consistency.py  # 数据一致性验证
│   ├── verify_datetime_format.py   # 日期格式验证
│   └── verify_encoding.py          # 文件编码验证

└── docs/                           # 文档与报告
    ├── chat_analysis_report.html   # HTML分析报告
    └── chat_analysis_report.xlsx   # Excel分析报告
```

## 核心功能

1. **数据分析**
   - 对话时长分析
   - 转人工场景分析
   - 问题分类统计
   - 用户意图聚类
   - 对话模式识别

2. **知识库管理**
   - 基于数据的FAQ构建
   - 行业专属回答模板
   - 多场景应答策略

3. **可视化与报告**
   - 交互式HTML报告
   - 结构化Excel报表
   - 对话数据可视化

## 技术栈

- **数据处理**: Python, Pandas, NumPy
- **机器学习**: Scikit-learn, TF-IDF, KMeans
- **自然语言处理**: Jieba分词
- **数据可视化**: Matplotlib, Seaborn
- **报告生成**: HTML, CSS, Openpyxl

## 使用指南

### 数据分析

```bash
# 运行基础对话数据分析
python ai_service/analysis/analyze_chat_data.py

# 运行用户意图聚类分析
python ai_service/analysis/_intents.py

# 生成可视化报告
python ai_service/analysis/visualize_analysis.py
```

### 数据处理

```bash
# 合并多个Excel数据文件
python ai_service/scripts/merge_excel.py

# 验证数据一致性
python ai_service/scripts/verify_data_consistency.py
```

## 后续开发计划

1. **对话机器人实现**: 基于分析结果构建智能对话机器人
2. **知识库扩展**: 扩充至100+FAQ条目
3. **客服协同系统**: 开发机器人与人工客服的协同工作流
4. **多模态交互**: 增加图像识别等能力

## 项目团队

- 数据分析师: 负责对话数据分析与洞察提取
- 知识库专家: 负责FAQ与模板库构建
- NLP工程师: 负责意图识别与分类模型
- 前端开发: 负责报告可视化与用户界面
- 业务专家: 提供回收行业专业知识

## 许可证

本项目采用MIT许可证 
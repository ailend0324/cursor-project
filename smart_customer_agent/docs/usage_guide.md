# 智能客服系统使用指南

本文档介绍如何设置和使用基于历史客服对话数据构建的智能客服系统。

## 系统概览

本系统基于历史客服对话数据构建，主要特点：
- 利用真实客服对话数据训练
- 专注于回收宝相关业务咨询场景
- 支持多业务线定制
- 具备知识库支持和智能回答能力

## 环境要求

- Python 3.8+
- 足够的磁盘空间用于存储对话数据
- 如需API服务，需要开放相应端口

## 安装步骤

1. 克隆项目代码

```bash
git clone <project-url>
cd smart_customer_agent
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量（可选）

创建`.env`文件，填入以下内容：

```
ANTHROPIC_API_KEY=your_api_key_here
```

## 数据处理

首次使用前，需要处理原始对话数据：

```bash
python run.py process --input /path/to/merged_chat_records.xlsx --output data
```

处理完成后，将在`data`目录下生成以下文件：

- `raw/conversations.json`：原始对话数据
- `processed/qa_pairs.json`：问答对数据
- `processed/train.json`：训练集
- `processed/val.json`：验证集
- `processed/test.json`：测试集
- `knowledge_base/faq_candidates.json`：FAQ候选
- `knowledge_base/faq_*.json`：按业务分组的FAQ

## 启动API服务

启动API服务，提供智能客服功能：

```bash
python run.py api --host 0.0.0.0 --port 8000
```

服务启动后，可以通过以下方式访问：

- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/

## 演示界面

启动演示界面，可视化体验智能客服功能：

```bash
python run.py demo
```

这将同时启动API服务和Web界面，并自动在浏览器中打开演示页面：http://localhost:8080

## API接口

系统提供以下API接口：

### 1. 聊天接口

```
POST /api/chat
```

请求参数：
```json
{
  "conversation_id": "可选，对话ID，新对话为空",
  "business_group": "业务组名称，如'邮寄回收-回收宝'",
  "message": "用户问题",
  "prev_messages": []
}
```

响应：
```json
{
  "conversation_id": "对话ID",
  "answer": "AI回答内容",
  "intent": "识别的意图",
  "confidence": 0.95,
  "needs_human": false,
  "sources": []
}
```

### 2. 获取对话历史

```
GET /api/conversations/{conversation_id}
```

响应：
```json
{
  "id": "对话ID",
  "business_group": "业务组",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "消息内容",
      "created_at": "时间戳"
    }
  ]
}
```

### 3. 获取业务组列表

```
GET /api/business-groups
```

响应：
```json
{
  "business_groups": ["回收宝验货宝技能组", "邮寄回收-回收宝", "..."]
}
```

## 常见问题

**Q: 如何修改知识库内容？**
A: 可以直接编辑`data/knowledge_base`目录下的JSON文件，修改后重启服务即可生效。

**Q: 如何改进回答质量？**
A: 可以通过以下方式改进：
1. 添加更多高质量的FAQ到知识库
2. 调整`src/api/app.py`中的置信度阈值
3. 定期用新的对话数据更新知识库

**Q: 如何使用自己的AI模型替代示例中的模拟响应？**
A: 修改`src/api/app.py`中的`ask_claude`函数，将模拟代码替换为实际的API调用代码。

## 项目扩展

可以通过以下方式扩展项目功能：

1. **添加更多意图分类**：在`classify_intent`函数中添加更多意图识别规则
2. **集成真实AI模型**：实现`ask_claude`函数中的API调用
3. **添加数据库存储**：替换内存存储，使用MongoDB等数据库存储对话记录
4. **添加监控和分析**：集成监控系统，记录系统性能和用户反馈

## 资源和支持

- 项目源码：[GitHub Repository](https://github.com/your-username/smart_customer_agent)
- 问题报告：使用GitHub Issues
- 贡献代码：欢迎提交Pull Request 
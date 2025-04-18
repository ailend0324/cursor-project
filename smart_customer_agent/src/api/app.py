from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import json
import os
import re
import datetime
import uuid
from pathlib import Path
import numpy as np
import logging
import httpx
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 应用配置
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
PROCESSED_DIR = DATA_DIR / "processed"

# API密钥（生产环境应放在环境变量中）
# 以下仅为示例，实际应用中请替换为真实密钥
API_KEYS = {
    "anthropic": "sk-ant-xxxx",  # 替换为实际的API密钥
}

# 应用实例
app = FastAPI(
    title="智能客服API",
    description="基于历史客服对话数据构建的智能客服API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class Message(BaseModel):
    role: str = Field(..., description="消息发送者角色: 'user', 'assistant', 或 'system'")
    content: str = Field(..., description="消息内容")
    created_at: Optional[str] = Field(None, description="消息创建时间")

class Conversation(BaseModel):
    id: str = Field(..., description="对话ID")
    business_group: str = Field(..., description="业务组")
    messages: List[Message] = Field(default_factory=list, description="对话消息列表")

class QuestionRequest(BaseModel):
    conversation_id: Optional[str] = Field(None, description="对话ID，如果是新对话则为空")
    business_group: str = Field(..., description="业务组")
    message: str = Field(..., description="用户问题")
    prev_messages: Optional[List[Message]] = Field(default_factory=list, description="之前的消息历史")

class AnswerResponse(BaseModel):
    conversation_id: str = Field(..., description="对话ID")
    answer: str = Field(..., description="回答内容")
    intent: Optional[str] = Field(None, description="识别的意图")
    confidence: float = Field(..., description="回答置信度")
    needs_human: bool = Field(False, description="是否需要人工介入")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="知识源")

# 内存存储（实际应用中应使用数据库）
conversations = {}
faqs = {}
qa_data = []

# 加载知识库数据
def load_knowledge_base():
    global faqs, qa_data
    
    # 加载FAQ数据
    if os.path.exists(KB_DIR):
        for file in os.listdir(KB_DIR):
            if file.endswith('.json') and file.startswith('faq_'):
                try:
                    with open(KB_DIR / file, 'r', encoding='utf-8') as f:
                        group_faqs = json.load(f)
                        # 提取业务组名
                        group_name = file[4:-5]  # 移除"faq_"前缀和".json"后缀
                        if group_name:
                            faqs[group_name] = group_faqs
                except Exception as e:
                    logger.error(f"加载FAQ文件 {file} 失败: {e}")
    
    # 加载QA数据（用于语义搜索）
    if os.path.exists(PROCESSED_DIR / "qa_pairs.json"):
        try:
            with open(PROCESSED_DIR / "qa_pairs.json", 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
        except Exception as e:
            logger.error(f"加载QA数据失败: {e}")
    
    logger.info(f"已加载 {len(faqs)} 个业务组的FAQ知识库")
    logger.info(f"已加载 {len(qa_data)} 条QA对")

# 简单的意图分类函数
def classify_intent(question):
    question = question.lower()
    
    # 订单查询
    if re.search(r'(订单|单号|我的订单|查(询|一下)订单)', question):
        return "订单查询"
    # 价格咨询
    elif re.search(r'(多少钱|价格|价值|回收价|估价|报价)', question):
        return "价格咨询"
    # 流程咨询
    elif re.search(r'(怎么|如何|流程|步骤|操作|使用)', question):
        return "流程咨询"
    # 物流查询
    elif re.search(r'(物流|快递|运费|邮费|顺丰|寄|邮寄|收货|发货)', question):
        return "物流查询"
    # 产品信息
    elif re.search(r'(手机|设备|产品|型号|配置|参数)', question):
        return "产品信息"
    # 投诉反馈
    elif re.search(r'(投诉|不满|差评|退款|维权|不好|问题)', question):
        return "投诉反馈"
    # 问候/闲聊
    elif re.search(r'(你好|您好|在吗|请问|谢谢|感谢)', question):
        return "问候闲聊"
    else:
        return "其他咨询"

# 简单的关键词搜索，在实际应用中应替换为语义搜索
def search_knowledge_base(question, business_group, top_k=3):
    results = []
    intent = classify_intent(question)
    
    # 1. 首先在对应业务组的FAQ中查找
    if business_group in faqs:
        group_faqs = faqs[business_group]
        # 简单的关键词匹配
        keywords = re.findall(r'\w+', question.lower())
        for faq in group_faqs:
            score = 0
            for kw in keywords:
                if kw in faq['question'].lower():
                    score += 1
            if score > 0:
                results.append({
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'score': score / len(keywords),
                    'intent': faq.get('intent', intent),
                    'business_group': business_group
                })
    
    # 2. 在全局QA数据中查找
    if len(results) < top_k:
        for qa in qa_data:
            if qa['business_group'] == business_group:
                score = 0
                keywords = re.findall(r'\w+', question.lower())
                for kw in keywords:
                    if kw in qa['question'].lower():
                        score += 1
                if score > 0:
                    results.append({
                        'question': qa['question'],
                        'answer': qa['answer'],
                        'score': score / len(keywords) * 0.8,  # 稍低的权重
                        'intent': qa.get('intent', intent),
                        'business_group': business_group
                    })
    
    # 按匹配分数排序并返回top_k个结果
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]

# 使用Anthropic Claude API处理问题（简化版）
async def ask_claude(question, context, business_group):
    """使用Claude API回答问题
    
    Args:
        question: 用户问题
        context: 上下文信息，包括之前的对话和相关FAQ
        business_group: 业务组
        
    Returns:
        回答内容和置信度
    """
    try:
        # 构建系统提示
        system_prompt = f"""你是一个专业的客服助手，专门负责"{business_group}"业务的在线咨询。
你的回答应该专业、礼貌、简洁明了。
如果你不确定答案，请坦率承认并表示可以转接人工客服。
请不要编造信息，仅基于提供的上下文进行回答。"""

        # 构建API请求
        headers = {
            "x-api-key": API_KEYS["anthropic"],
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # 准备消息历史
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加上下文信息
        if context:
            context_str = "以下是可能相关的信息：\n\n"
            for idx, item in enumerate(context):
                context_str += f"{idx+1}. 问: {item['question']}\n   答: {item['answer']}\n\n"
            
            messages.append({"role": "user", "content": f"请记住以下信息，这些是你回答问题的知识库：\n{context_str}"})
            messages.append({"role": "assistant", "content": "我已了解这些信息，将用它们来回答用户问题。"})
        
        # 添加用户问题
        messages.append({"role": "user", "content": question})
        
        # 发送请求（简化版，实际应用中需要完整的错误处理和重试机制）
        # 注意：这里使用了模拟调用，实际应用中应该发送真实请求
        # async with httpx.AsyncClient() as client:
        #    response = await client.post(
        #        "https://api.anthropic.com/v1/messages",
        #        headers=headers,
        #        json={
        #            "model": "claude-3-opus-20240229",
        #            "max_tokens": 1000,
        #            "messages": messages
        #        }
        #    )
        #    result = response.json()
        
        # 模拟API响应
        logger.info(f"向Claude API发送请求: {question}")
        
        # 从上下文中提取最佳匹配的回答
        best_match = max(context, key=lambda x: x["score"]) if context else None
        
        if best_match and best_match["score"] > 0.5:
            answer = best_match["answer"]
            confidence = best_match["score"]
        else:
            # 模拟生成的回答
            answers = {
                "订单查询": "您好，要查询订单状态，请提供您的订单号，我会立即为您查询。如果没有订单号，也可以提供下单时使用的手机号码。",
                "价格咨询": "您好，回收价格会根据设备型号、成色和市场行情决定。我们承诺给出合理的市场价格，您可以在我们的平台预估价格，也可以告诉我具体设备型号，我来为您查询最新回收价。",
                "流程咨询": "您好，回收流程很简单：1)在平台选择设备并填写信息获取预估价；2)选择回收方式(上门/邮寄/到店)；3)我们验收设备并确认价格；4)您确认后我们立即打款。整个过程快速安全。",
                "物流查询": "您好，我们合作的物流是顺丰快递，手机和平板等小件设备运费上限为25元，电脑和显示屏为40元，您可以选择顺丰到付。收件后我们会尽快为您验货并确认回收。",
                "产品信息": "您好，我们回收各类电子产品，包括手机、平板、电脑、智能手表等。不同产品的回收要求可能不同，请问您想了解哪类产品的具体信息？",
                "投诉反馈": "您好，非常抱歉给您带来不便。请详细描述您遇到的问题，提供相关订单号，我会立即为您反馈给专门的客服团队，并尽快给您答复。",
                "问候闲聊": "您好，欢迎咨询回收宝服务，我是您的专属客服助手，很高兴为您服务。请问有什么可以帮到您的呢？",
                "其他咨询": "您好，感谢您的咨询。请问您具体想了解关于我们回收服务的哪方面信息呢？我会尽力为您解答。"
            }
            
            intent = classify_intent(question)
            answer = answers.get(intent, "您好，我理解您的问题是关于我们的回收业务，但需要更多信息才能给您精确的答案。您能提供更多细节吗？或者您也可以联系我们的人工客服获取帮助。")
            confidence = 0.85 if intent != "其他咨询" else 0.6
        
        # 返回结果
        return {
            "answer": answer,
            "confidence": confidence,
            "needs_human": confidence < 0.7,  # 置信度低于0.7时建议转人工
        }
        
    except Exception as e:
        logger.error(f"调用Claude API失败: {str(e)}")
        return {
            "answer": "抱歉，我暂时无法回答您的问题，请稍后再试或联系人工客服。",
            "confidence": 0.0,
            "needs_human": True
        }

# 路由
@app.on_event("startup")
async def startup_event():
    """应用启动时加载知识库"""
    load_knowledge_base()

@app.get("/")
async def root():
    """健康检查端点"""
    return {"status": "ok", "service": "smart_customer_agent", "version": "0.1.0"}

@app.post("/api/chat", response_model=AnswerResponse)
async def chat(request: QuestionRequest):
    """处理用户问题并返回回答"""
    # 获取或创建对话
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    # 获取业务组和用户问题
    business_group = request.business_group
    question = request.message
    
    # 记录用户问题
    now = datetime.datetime.now().isoformat()
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "business_group": business_group,
            "messages": []
        }
    
    # 添加历史消息
    if request.prev_messages:
        conversations[conversation_id]["messages"].extend([
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at or now
            } for msg in request.prev_messages
        ])
    
    # 添加新问题
    conversations[conversation_id]["messages"].append({
        "role": "user",
        "content": question,
        "created_at": now
    })
    
    # 获取意图
    intent = classify_intent(question)
    
    # 搜索知识库
    search_results = search_knowledge_base(question, business_group)
    
    # 调用LLM获取回答
    llm_response = await ask_claude(question, search_results, business_group)
    
    # 构建回复
    answer = llm_response["answer"]
    confidence = llm_response["confidence"]
    needs_human = llm_response["needs_human"]
    
    # 记录回复
    conversations[conversation_id]["messages"].append({
        "role": "assistant",
        "content": answer,
        "created_at": datetime.datetime.now().isoformat()
    })
    
    # 返回结果
    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "needs_human": needs_human,
        "sources": search_results if search_results else None
    }

@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """获取特定对话的历史记录"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return conversations[conversation_id]

@app.get("/api/business-groups")
async def get_business_groups():
    """获取所有业务组"""
    return {"business_groups": list(faqs.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
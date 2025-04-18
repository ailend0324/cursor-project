import pandas as pd
import os
import re
import json
from tqdm import tqdm
from collections import defaultdict
import numpy as np
from datetime import datetime
import argparse

class ConversationProcessor:
    def __init__(self, input_file, output_dir):
        """初始化对话处理器
        
        Args:
            input_file: 输入Excel文件路径
            output_dir: 输出目录
        """
        self.input_file = input_file
        self.output_dir = output_dir
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "processed"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "knowledge_base"), exist_ok=True)
        
        # 发送者类型映射
        self.sender_mapping = {
            1: "用户",
            2: "客服",
            4: "系统"
        }
        
        # 意图类别（将根据数据动态创建）
        self.intent_categories = set()
        
    def load_data(self):
        """加载Excel数据"""
        print(f"加载数据文件: {self.input_file}")
        self.df = pd.read_excel(self.input_file)
        
        # 基本数据清洗
        # 转换时间列
        for col in ['user_start_time', 'user_end_time', 'create_time', 'send_time']:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
        
        # 处理sender_type
        if 'sender_type' in self.df.columns:
            self.df['sender_type'] = self.df['sender_type'].fillna(-1).astype(int)
            self.df['sender_category'] = self.df['sender_type'].map(
                lambda x: self.sender_mapping.get(x, f'其他({x})')
            )
        
        print(f"数据加载完成，共 {self.df.shape[0]} 行")
        
    def process_conversations(self):
        """处理所有对话"""
        print("开始处理对话...")
        
        # 按对话ID分组
        conversation_groups = self.df.groupby('touch_id')
        total_conversations = len(conversation_groups)
        
        # 保存结果的列表
        processed_conversations = []
        qa_pairs = []
        faq_candidates = []
        
        # 处理每个对话
        for conv_id, group in tqdm(conversation_groups, total=total_conversations):
            # 按序号排序消息
            conversation = group.sort_values('seq_no')
            
            # 获取对话元数据
            conv_metadata = {
                'conversation_id': conv_id,
                'business_group': conversation['group_name'].iloc[0],
                'start_time': conversation['user_start_time'].iloc[0],
                'end_time': conversation['user_end_time'].iloc[0],
                'duration_min': (conversation['user_end_time'].iloc[0] - conversation['user_start_time'].iloc[0]).total_seconds() / 60 if pd.notna(conversation['user_end_time'].iloc[0]) else None,
                'turn_count': len(conversation)
            }
            
            # 提取对话消息
            messages = []
            current_qa_pair = {'question': None, 'answer': None, 'context': []}
            
            for _, msg in conversation.iterrows():
                if pd.isna(msg['send_content']):
                    continue
                    
                sender = msg.get('sender_category', '未知')
                content = msg.get('send_content', '')
                timestamp = msg.get('send_time', None)
                
                # 添加到对话消息列表
                message = {
                    'sender': sender,
                    'content': content,
                    'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
                }
                messages.append(message)
                
                # 构建QA对
                if sender == '用户' and len(content.strip()) > 0:
                    # 如果已有未完成的QA对，保存它
                    if current_qa_pair['question'] is not None and current_qa_pair['answer'] is not None:
                        # 只保留有效的QA对
                        if len(current_qa_pair['question'].strip()) > 0 and len(current_qa_pair['answer'].strip()) > 0:
                            qa_pairs.append(current_qa_pair)
                            
                            # 判断是否是FAQ候选
                            if self.is_faq_candidate(current_qa_pair):
                                faq_candidates.append(current_qa_pair)
                    
                    # 开始新的QA对
                    current_qa_pair = {
                        'conversation_id': conv_id, 
                        'business_group': conv_metadata['business_group'],
                        'question': content, 
                        'answer': None,
                        'context': [],
                        'intent': self.classify_intent(content)
                    }
                
                elif sender == '客服' and current_qa_pair['question'] is not None and current_qa_pair['answer'] is None:
                    # 将客服回复作为答案
                    current_qa_pair['answer'] = content
                
                # 添加到上下文
                if current_qa_pair['question'] is not None:
                    current_qa_pair['context'].append(message)
            
            # 处理最后一个QA对
            if current_qa_pair['question'] is not None and current_qa_pair['answer'] is not None:
                if len(current_qa_pair['question'].strip()) > 0 and len(current_qa_pair['answer'].strip()) > 0:
                    qa_pairs.append(current_qa_pair)
                    
                    # 判断是否是FAQ候选
                    if self.is_faq_candidate(current_qa_pair):
                        faq_candidates.append(current_qa_pair)
            
            # 保存完整对话
            conv_data = {
                'metadata': conv_metadata,
                'messages': messages
            }
            processed_conversations.append(conv_data)
        
        print(f"处理完成: 共{len(processed_conversations)}个对话，{len(qa_pairs)}个QA对，{len(faq_candidates)}个FAQ候选")
        
        # 保存结果
        self.processed_conversations = processed_conversations
        self.qa_pairs = qa_pairs
        self.faq_candidates = faq_candidates
        
        # 统计意图分布
        intent_counts = defaultdict(int)
        for qa in qa_pairs:
            intent_counts[qa['intent']] += 1
        
        print("\n意图分布:")
        for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"- {intent}: {count} ({count/len(qa_pairs)*100:.2f}%)")
    
    def classify_intent(self, question):
        """简单的基于规则的意图分类
        
        Args:
            question: 用户问题
            
        Returns:
            意图分类结果
        """
        question = question.lower()
        
        # 订单查询
        if re.search(r'(订单|单号|我的订单|查(询|一下)订单)', question):
            intent = "订单查询"
        # 价格咨询
        elif re.search(r'(多少钱|价格|价值|回收价|估价|报价)', question):
            intent = "价格咨询"
        # 流程咨询
        elif re.search(r'(怎么|如何|流程|步骤|操作|使用)', question):
            intent = "流程咨询"
        # 物流查询
        elif re.search(r'(物流|快递|运费|邮费|顺丰|寄|邮寄|收货|发货)', question):
            intent = "物流查询"
        # 产品信息
        elif re.search(r'(手机|设备|产品|型号|配置|参数)', question):
            intent = "产品信息"
        # 投诉反馈
        elif re.search(r'(投诉|不满|差评|退款|维权|不好|问题)', question):
            intent = "投诉反馈"
        # 问候/闲聊
        elif re.search(r'(你好|您好|在吗|请问|谢谢|感谢)', question):
            intent = "问候闲聊"
        else:
            intent = "其他咨询"
        
        self.intent_categories.add(intent)
        return intent
    
    def is_faq_candidate(self, qa_pair):
        """判断一个QA对是否是FAQ候选
        
        标准:
        1. 问题和回答都不为空且长度适当
        2. 问题是通用的，不包含特定订单号等个人信息
        3. 回答不是简单的"是的"/"好的"等
        
        Args:
            qa_pair: QA对
            
        Returns:
            是否为FAQ候选
        """
        question = qa_pair['question']
        answer = qa_pair['answer']
        
        # 基本长度验证
        if (not question or not answer or 
            len(question.strip()) < 5 or len(question.strip()) > 100 or
            len(answer.strip()) < 10):
            return False
        
        # 检查问题是否包含特定信息
        if re.search(r'\d{10,}', question): # 订单号等数字序列
            return False
            
        # 检查答案是否是简单回复
        simple_answers = ['好的', '可以的', '是的', '谢谢', '不客气', '嗯', '我知道了']
        if any(ans in answer for ans in simple_answers) and len(answer) < 15:
            return False
            
        return True
    
    def save_results(self):
        """保存处理结果"""
        print("保存处理结果...")
        
        # 保存原始对话
        conversations_file = os.path.join(self.output_dir, "raw", "conversations.json")
        with open(conversations_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed_conversations, f, ensure_ascii=False, indent=2)
        
        # 保存QA对
        qa_file = os.path.join(self.output_dir, "processed", "qa_pairs.json")
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)
        
        # 保存FAQ候选
        faq_file = os.path.join(self.output_dir, "knowledge_base", "faq_candidates.json")
        with open(faq_file, 'w', encoding='utf-8') as f:
            json.dump(self.faq_candidates, f, ensure_ascii=False, indent=2)
        
        # 按业务分组导出FAQ
        business_faqs = defaultdict(list)
        for faq in self.faq_candidates:
            business_group = faq['business_group']
            business_faqs[business_group].append(faq)
        
        for group, faqs in business_faqs.items():
            group_name = re.sub(r'[^\w\s-]', '', group).strip().replace(' ', '_')
            if not group_name:
                group_name = "未分类"
                
            group_file = os.path.join(self.output_dir, "knowledge_base", f"faq_{group_name}.json")
            with open(group_file, 'w', encoding='utf-8') as f:
                json.dump(faqs, f, ensure_ascii=False, indent=2)
        
        # 保存训练集、验证集和测试集
        # 按8:1:1分割
        np.random.seed(42)
        qa_indices = np.random.permutation(len(self.qa_pairs))
        train_size = int(len(self.qa_pairs) * 0.8)
        val_size = int(len(self.qa_pairs) * 0.1)
        
        train_indices = qa_indices[:train_size]
        val_indices = qa_indices[train_size:train_size+val_size]
        test_indices = qa_indices[train_size+val_size:]
        
        train_data = [self.qa_pairs[i] for i in train_indices]
        val_data = [self.qa_pairs[i] for i in val_indices]
        test_data = [self.qa_pairs[i] for i in test_indices]
        
        # 保存训练集
        train_file = os.path.join(self.output_dir, "processed", "train.json")
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        
        # 保存验证集
        val_file = os.path.join(self.output_dir, "processed", "val.json")
        with open(val_file, 'w', encoding='utf-8') as f:
            json.dump(val_data, f, ensure_ascii=False, indent=2)
        
        # 保存测试集
        test_file = os.path.join(self.output_dir, "processed", "test.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
            
        print("数据已保存到:", self.output_dir)
        print(f"- 对话数: {len(self.processed_conversations)}")
        print(f"- QA对数: {len(self.qa_pairs)}")
        print(f"- FAQ候选数: {len(self.faq_candidates)}")
        print(f"- 训练集大小: {len(train_data)}")
        print(f"- 验证集大小: {len(val_data)}")
        print(f"- 测试集大小: {len(test_data)}")

def main():
    parser = argparse.ArgumentParser(description='处理客服对话数据')
    parser.add_argument('--input', default='/Users/boxie/cursor/ai_service/data/merged_chat_records.xlsx', 
                        help='输入Excel文件路径')
    parser.add_argument('--output', default='/Users/boxie/cursor/smart_customer_agent/data', 
                        help='输出目录')
    args = parser.parse_args()
    
    processor = ConversationProcessor(args.input, args.output)
    processor.load_data()
    processor.process_conversations()
    processor.save_results()

if __name__ == "__main__":
    main() 
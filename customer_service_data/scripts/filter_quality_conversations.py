import json
from collections import defaultdict
import re

class QualityScorer:
    def __init__(self):
        # 正面评价词
        self.positive_words = {
            '感谢', '谢谢', '好的', '满意', '不错', '可以', '明白',
            '好评', '点赞', '清楚', '专业', '耐心', '细心'
        }
        
        # 负面评价词
        self.negative_words = {
            '投诉', '差评', '不满意', '态度差', '太慢', '不耐烦',
            '敷衍', '不专业', '不清楚', '搪塞', '推诿'
        }
        
        # 专业术语（根据业务补充）
        self.professional_terms = {
            '验机', '质检', '评估', '邮寄', '物流', '快递',
            '回收', '维修', '保修', '售后', '退款', '换货'
        }

    def score_conversation(self, conversation):
        """对对话进行评分"""
        scores = defaultdict(float)
        
        # 1. 基础评分
        scores['base'] = 1.0
        
        # 2. 对话状态评分
        if conversation['metadata']['status'] == '已解决':
            scores['status'] = 1.0
        elif conversation['metadata']['status'] == '待处理':
            scores['status'] = 0.5
        else:
            scores['status'] = 0.0
            
        # 3. 对话长度评分
        msg_count = len(conversation['messages'])
        if 5 <= msg_count <= 20:  # 理想长度范围
            scores['length'] = 1.0
        elif msg_count < 5:
            scores['length'] = 0.3
        else:
            scores['length'] = 0.7
            
        # 4. 回复质量评分
        positive_count = 0
        negative_count = 0
        professional_count = 0
        agent_messages = [msg for msg in conversation['messages'] if msg['role'] == 'agent']
        
        for msg in agent_messages:
            content = msg['content'].lower()
            
            # 统计正面词
            positive_count += sum(1 for word in self.positive_words if word in content)
            # 统计负面词
            negative_count += sum(1 for word in self.negative_words if word in content)
            # 统计专业术语
            professional_count += sum(1 for term in self.professional_terms if term in content)
            
        # 计算回复质量分数
        scores['sentiment'] = min(1.0, max(0, (positive_count - negative_count) / len(agent_messages)))
        scores['professional'] = min(1.0, professional_count / len(agent_messages))
        
        # 5. 解决方案模板评分
        if len(conversation.get('solution_templates', [])) > 0:
            scores['solution'] = 1.0
        else:
            scores['solution'] = 0.0
            
        # 计算总分
        weights = {
            'base': 1.0,
            'status': 2.0,
            'length': 1.5,
            'sentiment': 2.0,
            'professional': 2.0,
            'solution': 1.5
        }
        
        total_score = sum(score * weights[key] for key, score in scores.items())
        max_score = sum(weights.values())
        
        return total_score / max_score, dict(scores)

def filter_quality_conversations(input_file, output_file, threshold=0.7):
    """筛选高质量对话"""
    # 加载训练数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scorer = QualityScorer()
    quality_conversations = []
    scores_distribution = defaultdict(int)
    
    print("开始评估对话质量...")
    
    # 评估每个对话
    for conv in data['conversations']:
        score, detailed_scores = scorer.score_conversation(conv)
        conv['quality_score'] = score
        conv['quality_details'] = detailed_scores
        
        # 记录分数分布
        score_bucket = round(score * 10) / 10  # 将分数四舍五入到小数点后一位
        scores_distribution[score_bucket] += 1
        
        # 筛选高质量对话
        if score >= threshold:
            quality_conversations.append(conv)
    
    # 创建新的数据集
    quality_data = {
        "metadata": {
            "original_count": len(data['conversations']),
            "filtered_count": len(quality_conversations),
            "quality_threshold": threshold,
            "version": "2.0"
        },
        "conversations": quality_conversations
    }
    
    # 保存筛选后的数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(quality_data, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print("\n=== 质量评估统计 ===")
    print(f"原始对话数量: {len(data['conversations'])}")
    print(f"高质量对话数量: {len(quality_conversations)}")
    print(f"筛选比例: {len(quality_conversations)/len(data['conversations'])*100:.1f}%")
    
    print("\n分数分布:")
    for score in sorted(scores_distribution.keys()):
        count = scores_distribution[score]
        percentage = count / len(data['conversations']) * 100
        print(f"分数 {score:.1f}: {count} 个 ({percentage:.1f}%)")

def main():
    input_file = 'customer_service_data/data/final/training_data.json'
    output_file = 'customer_service_data/data/final/quality_training_data.json'
    
    filter_quality_conversations(input_file, output_file, threshold=0.7)

if __name__ == "__main__":
    main() 
import json
import random
from datetime import datetime

def format_conversation(conv):
    """格式化对话内容展示"""
    print("\n" + "=" * 80)
    print(f"对话ID: {conv['id']}")
    print("-" * 80)
    print(f"业务类型: {conv['metadata']['business_type']}")
    print(f"主要意图: {conv['metadata']['primary_intent']}")
    print(f"状态: {conv['metadata']['status']}")
    print(f"消息数量: {len(conv['messages'])}")
    print(f"质量得分: {conv['quality_score']:.2f}")
    
    print("\n评分详情:")
    for aspect, score in conv['quality_details'].items():
        print(f"  {aspect:12s}: {score:.2f}")
    
    print("\n对话内容:")
    print("-" * 80)
    for msg in conv['messages']:
        role = "👨‍💼 客服" if msg['role'] == 'agent' else "👤 用户"
        content = msg['content'].replace('\n', ' ')
        time = msg.get('timestamp', '')
        if time:
            try:
                time = datetime.fromisoformat(time.replace('Z', '+00:00')).strftime('%H:%M:%S')
            except:
                time = ''
        time_str = f"[{time}] " if time else ""
        print(f"{time_str}{role}: {content}")
    
    if 'solution_templates' in conv and conv['solution_templates']:
        print("\n📝 解决方案模板:")
        print("-" * 80)
        for template in conv['solution_templates']:
            print(f"• {template}")
    
    print("\n" + "=" * 80)

def review_conversations(file_path, min_score=0.7, sample_size=10):
    """查看高分对话"""
    try:
        # 加载数据
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 筛选高分对话
        high_quality_convs = [
            conv for conv in data['conversations']
            if conv.get('quality_score', 0) >= min_score
        ]
        
        # 按分数排序
        high_quality_convs.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # 统计信息
        print(f"\n📊 高质量对话统计 (得分 >= {min_score})")
        print("=" * 80)
        print(f"总数: {len(high_quality_convs)} 个对话")
        
        score_ranges = {
            '0.9-1.0': len([c for c in high_quality_convs if c['quality_score'] >= 0.9]),
            '0.8-0.9': len([c for c in high_quality_convs if 0.8 <= c['quality_score'] < 0.9]),
            '0.7-0.8': len([c for c in high_quality_convs if 0.7 <= c['quality_score'] < 0.8])
        }
        
        print("\n分数分布:")
        for range_name, count in score_ranges.items():
            percentage = (count / len(high_quality_convs)) * 100 if high_quality_convs else 0
            print(f"{range_name}: {count} 个对话 ({percentage:.1f}%)")
        
        # 抽样展示
        sample_size = min(sample_size, len(high_quality_convs))
        if sample_size > 0:
            print(f"\n📝 展示 {sample_size} 个最高分对话:")
            
            # 取前N个最高分对话
            samples = high_quality_convs[:sample_size]
            
            for conv in samples:
                format_conversation(conv)
        else:
            print("\n⚠️ 没有找到符合条件的对话")
            
    except FileNotFoundError:
        print(f"\n❌ 错误: 找不到文件 {file_path}")
        print("请先运行对话质量评估脚本生成质量评分数据")
    except json.JSONDecodeError:
        print(f"\n❌ 错误: 文件格式错误 {file_path}")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")

def main():
    file_path = 'customer_service_data/data/final/quality_training_data.json'
    
    while True:
        print("\n=== 高质量对话复核工具 ===")
        print("1. 查看最高分对话 (分数 >= 0.8)")
        print("2. 查看所有高分对话 (分数 >= 0.7)")
        print("3. 随机抽样10个对话")
        print("4. 按业务类型查看")
        print("5. 退出")
        
        try:
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                review_conversations(file_path, min_score=0.8, sample_size=5)
            elif choice == '2':
                review_conversations(file_path, min_score=0.7, sample_size=10)
            elif choice == '3':
                review_conversations(file_path, min_score=0.7, sample_size=10)
            elif choice == '4':
                print("\n⚠️ 暂未实现此功能")
            elif choice == '5':
                print("\n👋 感谢使用！")
                break
            else:
                print("\n⚠️ 无效的选择，请重试")
            
            if choice in ['1', '2', '3', '4']:
                input("\n按回车键继续...")
                
        except KeyboardInterrupt:
            print("\n\n👋 感谢使用！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            input("\n按回车键继续...")

if __name__ == "__main__":
    main() 
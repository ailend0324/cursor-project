#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能客服系统启动脚本
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("smart_customer_agent")

def setup_path():
    """设置路径"""
    # 获取当前脚本所在目录
    current_path = Path(__file__).resolve().parent
    
    # 将项目根目录添加到sys.path
    sys.path.insert(0, str(current_path))
    
    # 创建必要的目录
    os.makedirs(current_path / "data", exist_ok=True)
    os.makedirs(current_path / "logs", exist_ok=True)
    
    return current_path

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="智能客服系统")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 处理数据命令
    process_parser = subparsers.add_parser("process", help="处理数据")
    process_parser.add_argument("--input", default="/Users/boxie/cursor/ai_service/data/merged_chat_records.xlsx", 
                             help="输入Excel文件路径")
    process_parser.add_argument("--output", default="data", 
                             help="输出目录")
    
    # 启动API服务命令
    api_parser = subparsers.add_parser("api", help="启动API服务")
    api_parser.add_argument("--host", default="0.0.0.0", help="主机地址")
    api_parser.add_argument("--port", type=int, default=8000, help="端口号")
    api_parser.add_argument("--reload", action="store_true", help="是否启用热加载")
    
    # 启动演示界面命令
    demo_parser = subparsers.add_parser("demo", help="启动演示界面")
    
    # 所有命令
    parser.add_argument("--verbose", "-v", action="store_true", help="是否输出详细日志")
    
    return parser.parse_args()

def main():
    """主函数"""
    # 设置路径
    project_root = setup_path()
    
    # 解析参数
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    logger.info(f"当前工作目录: {project_root}")
    
    # 根据命令执行不同操作
    if args.command == "process":
        logger.info("开始处理数据...")
        from src.data_processing.process_conversation_data import ConversationProcessor
        
        processor = ConversationProcessor(args.input, os.path.join(project_root, args.output))
        processor.load_data()
        processor.process_conversations()
        processor.save_results()
        
    elif args.command == "api":
        logger.info(f"启动API服务 (host={args.host}, port={args.port})...")
        import uvicorn
        
        uvicorn.run(
            "src.api.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
        
    elif args.command == "demo":
        logger.info("启动演示界面...")
        import http.server
        import socketserver
        from src.api.app import app
        import threading
        import webbrowser
        import uvicorn
        
        # 启动API服务
        api_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": app,
                "host": "127.0.0.1",
                "port": 8000
            }
        )
        api_thread.daemon = True
        api_thread.start()
        
        # 启动静态文件服务
        static_dir = os.path.join(project_root, "src", "api", "static")
        
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=static_dir, **kwargs)
        
        with socketserver.TCPServer(("", 8080), Handler) as httpd:
            logger.info("静态文件服务已启动在 http://localhost:8080")
            
            # 打开浏览器
            webbrowser.open("http://localhost:8080")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("服务已停止")
    else:
        logger.error("未指定命令，请使用 --help 查看帮助")

if __name__ == "__main__":
    main() 
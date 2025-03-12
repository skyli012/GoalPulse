#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GoalPulse - 智能任务提示助手
主程序入口
"""

import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("GoalPulse")

def main():
    """主程序入口函数"""
    logger.info("GoalPulse 智能任务提示助手启动中...")
    
    # 导入其他模块
    try:
        from task_manager import TaskManager
        from event_listener import EventListener
        from gui.app_window import AppWindow
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        sys.exit(1)
    
    # 初始化任务管理器
    task_manager = TaskManager()
    
    # 初始化事件监听器
    event_listener = EventListener()
    
    # 初始化GUI
    app = AppWindow(task_manager, event_listener)
    
    # 检查是否为开机启动
    if event_listener.is_startup():
        logger.info("检测到系统启动，显示今日任务...")
        app.show_today_tasks()
    
    # 启动应用
    app.run()

if __name__ == '__main__':
    main()

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GoalPulse - 智能任务提示助手
任务管理器模块 - 负责任务的增删改查
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, date
import random

logger = logging.getLogger("GoalPulse.TaskManager")

class TaskManager:
    """任务管理器类，处理任务的增删改查操作"""
    
    def __init__(self, db_path=None):
        """初始化任务管理器
        
        Args:
            db_path: 数据库文件路径，默认为None，将使用默认路径
        """
        # 确保数据目录存在
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 设置数据库路径
        if db_path is None:
            self.db_path = os.path.join(self.data_dir, "tasks.db")
        else:
            self.db_path = db_path
            
        # 初始化数据库
        self._init_database()
        
        # 加载鼓励语录库
        self.encouragements = [
            "太棒了！你今天的表现令人印象深刻！✨",
            "完成任务的感觉真好，对吧？继续保持！🚀",
            "你的坚持不懈正在创造奇迹！💪",
            "明日之星就是你！每一步都在靠近目标！✨",
            "今天又离目标近了一步！坚持就是胜利！🚀",
            "代码写得比咖啡因还提神！☕",
            "你的效率简直惊人！继续加油！💯",
            "每完成一个任务，你就离成功更近一步！🏆",
            "你的进步是有目共睹的，为你自豪！👏",
            "坚持的力量是无穷的，你做到了！🌟"
        ]
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建任务表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                priority INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                completed_at TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"数据库初始化成功: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def add_task(self, title, description="", due_date=None, priority=0):
        """添加新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            due_date: 截止日期，格式为YYYY-MM-DD
            priority: 优先级，0-3，数字越大优先级越高
            
        Returns:
            int: 新创建任务的ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(
                "INSERT INTO tasks (title, description, due_date, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (title, description, due_date, priority, "pending", created_at)
            )
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"任务添加成功: {title} (ID: {task_id})")
            return task_id
        except sqlite3.Error as e:
            logger.error(f"添加任务失败: {e}")
            raise
    
    def get_task(self, task_id):
        """获取指定ID的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 任务信息字典，如果任务不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"获取任务失败: {e}")
            raise
    
    def get_today_tasks(self):
        """获取今日任务列表
        
        Returns:
            list: 今日任务列表
        """
        today = date.today().strftime("%Y-%m-%d")
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取所有待处理的任务，按优先级排序
            cursor.execute(
                "SELECT * FROM tasks WHERE status = 'pending' ORDER BY priority DESC, due_date ASC"
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"获取今日任务失败: {e}")
            raise
    
    def update_task(self, task_id, **kwargs):
        """更新任务信息
        
        Args:
            task_id: 任务ID
            **kwargs: 要更新的字段，可以包括title, description, due_date, priority, status
            
        Returns:
            bool: 更新是否成功
        """
        allowed_fields = {"title", "description", "due_date", "priority", "status"}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            logger.warning("没有提供有效的更新字段")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 如果状态更新为已完成，记录完成时间
            if update_fields.get("status") == "completed":
                update_fields["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 构建更新SQL
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values())
            values.append(task_id)
            
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"任务更新成功: ID {task_id}")
            else:
                logger.warning(f"任务更新失败，可能任务不存在: ID {task_id}")
            
            return success
        except sqlite3.Error as e:
            logger.error(f"更新任务失败: {e}")
            raise
    
    def delete_task(self, task_id):
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"任务删除成功: ID {task_id}")
            else:
                logger.warning(f"任务删除失败，可能任务不存在: ID {task_id}")
            
            return success
        except sqlite3.Error as e:
            logger.error(f"删除任务失败: {e}")
            raise
    
    def complete_task(self, task_id):
        """将任务标记为已完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 操作是否成功
            str: 随机鼓励语
        """
        success = self.update_task(task_id, status="completed")
        
        if success:
            # 返回随机鼓励语
            encouragement = random.choice(self.encouragements)
            logger.info(f"任务已完成: ID {task_id}, 鼓励: {encouragement}")
            return True, encouragement
        
        return False, ""
    
    def get_pending_tasks_count(self):
        """获取待处理任务数量
        
        Returns:
            int: 待处理任务数量
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        except sqlite3.Error as e:
            logger.error(f"获取待处理任务数量失败: {e}")
            raise 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GoalPulse - 智能任务提示助手
GUI主窗口模块 - 实现应用的界面
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from datetime import datetime, date

# 配置日志
logger = logging.getLogger("GoalPulse.GUI")

class AppWindow:
    """应用主窗口类"""
    
    def __init__(self, task_manager, event_listener):
        """初始化应用窗口
        
        Args:
            task_manager: 任务管理器实例
            event_listener: 事件监听器实例
        """
        self.task_manager = task_manager
        self.event_listener = event_listener
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("GoalPulse - 智能任务提示助手")
        self.root.geometry("600x500")
        self.root.minsize(500, 400)
        
        # 设置图标（如果有）
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        
        # 注册关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 创建界面
        self._create_widgets()
        
        # 加载任务
        self.load_tasks()
        
        # 设置定时检查
        self._setup_periodic_check()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题标签
        title_label = ttk.Label(main_frame, text="待办任务", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建任务列表框架
        task_frame = ttk.Frame(main_frame)
        task_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建任务列表
        columns = ("id", "title", "due_date", "priority", "status")
        self.task_tree = ttk.Treeview(task_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.task_tree.heading("id", text="ID")
        self.task_tree.heading("title", text="任务")
        self.task_tree.heading("due_date", text="截止日期")
        self.task_tree.heading("priority", text="优先级")
        self.task_tree.heading("status", text="状态")
        
        # 设置列宽
        self.task_tree.column("id", width=40)
        self.task_tree.column("title", width=250)
        self.task_tree.column("due_date", width=100)
        self.task_tree.column("priority", width=80)
        self.task_tree.column("status", width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置任务列表和滚动条
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.task_tree.bind("<Double-1>", self.on_task_double_click)
        
        # 创建按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加任务按钮
        add_button = ttk.Button(button_frame, text="添加任务", command=self.add_task)
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 完成任务按钮
        complete_button = ttk.Button(button_frame, text="标记完成", command=self.complete_task)
        complete_button.pack(side=tk.LEFT, padx=5)
        
        # 删除任务按钮
        delete_button = ttk.Button(button_frame, text="删除任务", command=self.delete_task)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(button_frame, text="刷新", command=self.load_tasks)
        refresh_button.pack(side=tk.RIGHT)
        
        # 创建聊天框架
        chat_frame = ttk.LabelFrame(main_frame, text="聊天交互")
        chat_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建聊天输入框
        self.chat_entry = ttk.Entry(chat_frame)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5), pady=5)
        self.chat_entry.bind("<Return>", self.on_chat_enter)
        
        # 发送按钮
        send_button = ttk.Button(chat_frame, text="发送", command=self.on_chat_send)
        send_button.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def run(self):
        """运行应用"""
        self.root.mainloop()
    
    def load_tasks(self):
        """加载任务列表"""
        # 清空现有任务
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # 获取今日任务
        tasks = self.task_manager.get_today_tasks()
        
        # 添加任务到列表
        for task in tasks:
            priority_text = self._get_priority_text(task["priority"])
            status_text = "待处理" if task["status"] == "pending" else "已完成"
            due_date = task["due_date"] if task["due_date"] else "无截止日期"
            
            self.task_tree.insert("", tk.END, values=(
                task["id"],
                task["title"],
                due_date,
                priority_text,
                status_text
            ))
        
        # 更新状态栏
        self.status_var.set(f"共 {len(tasks)} 个任务")
    
    def _get_priority_text(self, priority):
        """获取优先级文本
        
        Args:
            priority: 优先级数值
            
        Returns:
            str: 优先级文本
        """
        priority_map = {
            0: "普通",
            1: "中等",
            2: "重要",
            3: "紧急"
        }
        return priority_map.get(priority, "普通")
    
    def add_task(self):
        """添加新任务"""
        # 创建添加任务对话框
        dialog = TaskDialog(self.root, "添加任务")
        
        if dialog.result:
            title, description, due_date, priority = dialog.result
            
            # 添加任务
            task_id = self.task_manager.add_task(title, description, due_date, priority)
            
            if task_id:
                messagebox.showinfo("成功", f"任务 '{title}' 添加成功！")
                self.load_tasks()
            else:
                messagebox.showerror("错误", "添加任务失败！")
    
    def complete_task(self):
        """完成选中的任务"""
        selected = self.task_tree.selection()
        
        if not selected:
            messagebox.showwarning("警告", "请先选择一个任务！")
            return
        
        # 获取选中任务的ID
        task_id = self.task_tree.item(selected[0], "values")[0]
        
        # 标记任务为已完成
        success, encouragement = self.task_manager.complete_task(task_id)
        
        if success:
            messagebox.showinfo("任务完成", encouragement)
            self.load_tasks()
        else:
            messagebox.showerror("错误", "无法完成任务！")
    
    def delete_task(self):
        """删除选中的任务"""
        selected = self.task_tree.selection()
        
        if not selected:
            messagebox.showwarning("警告", "请先选择一个任务！")
            return
        
        # 获取选中任务的ID和标题
        values = self.task_tree.item(selected[0], "values")
        task_id = values[0]
        task_title = values[1]
        
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除任务 '{task_title}' 吗？"):
            # 删除任务
            success = self.task_manager.delete_task(task_id)
            
            if success:
                messagebox.showinfo("成功", f"任务 '{task_title}' 已删除！")
                self.load_tasks()
            else:
                messagebox.showerror("错误", "删除任务失败！")
    
    def on_task_double_click(self, event):
        """处理任务双击事件"""
        selected = self.task_tree.selection()
        
        if not selected:
            return
        
        # 获取选中任务的ID
        task_id = self.task_tree.item(selected[0], "values")[0]
        
        # 获取任务详情
        task = self.task_manager.get_task(task_id)
        
        if task:
            # 显示任务详情对话框
            dialog = TaskDialog(self.root, "编辑任务", task)
            
            if dialog.result:
                title, description, due_date, priority = dialog.result
                
                # 更新任务
                success = self.task_manager.update_task(
                    task_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    priority=priority
                )
                
                if success:
                    self.load_tasks()
    
    def on_chat_enter(self, event):
        """处理聊天输入框回车事件"""
        self.on_chat_send()
    
    def on_chat_send(self):
        """处理聊天发送事件"""
        message = self.chat_entry.get().strip()
        
        if not message:
            return
        
        # 清空输入框
        self.chat_entry.delete(0, tk.END)
        
        # 处理聊天消息
        self._process_chat_message(message)
    
    def _process_chat_message(self, message):
        """处理聊天消息
        
        Args:
            message: 用户输入的消息
        """
        # 简单的关键词匹配
        message_lower = message.lower()
        
        if "添加任务" in message_lower or "新任务" in message_lower:
            self.add_task()
        elif "完成任务" in message_lower or "标记完成" in message_lower:
            self.complete_task()
        elif "删除任务" in message_lower:
            self.delete_task()
        elif "刷新" in message_lower or "更新" in message_lower:
            self.load_tasks()
        elif "帮助" in message_lower or "help" in message_lower:
            self._show_help()
        else:
            # 默认回复
            messagebox.showinfo("GoalPulse", "我是你的任务助手！你可以告诉我添加任务、完成任务、删除任务等。")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
GoalPulse 智能任务提示助手

功能：
1. 添加任务：点击'添加任务'按钮或在聊天框中输入'添加任务'
2. 完成任务：选中任务后点击'标记完成'按钮
3. 删除任务：选中任务后点击'删除任务'按钮
4. 编辑任务：双击任务进行编辑
5. 聊天交互：在聊天框中输入指令或问题

开机启动：
程序会在系统启动时自动运行，并提醒你今日待办任务。

关机检查：
关闭程序时会检查未完成的任务，并提醒你调整计划。
        """
        messagebox.showinfo("帮助", help_text)
    
    def _setup_periodic_check(self):
        """设置定期检查"""
        # 每小时检查一次
        def check_routine():
            while True:
                # 检查是否有新的待办任务
                pending_count = self.task_manager.get_pending_tasks_count()
                
                # 更新状态栏
                self.status_var.set(f"共 {pending_count} 个待处理任务")
                
                # 休眠一小时
                time.sleep(3600)
        
        # 启动检查线程
        check_thread = threading.Thread(target=check_routine, daemon=True)
        check_thread.start()
    
    def show_today_tasks(self):
        """显示今日任务提醒"""
        # 获取今日任务
        tasks = self.task_manager.get_today_tasks()
        
        if not tasks:
            messagebox.showinfo("今日任务", "今天没有待办任务，享受轻松的一天吧！")
            return
        
        # 构建任务列表文本
        task_text = "今日待办任务：\n\n"
        for i, task in enumerate(tasks, 1):
            priority_text = self._get_priority_text(task["priority"])
            task_text += f"{i}. {task['title']} ({priority_text})\n"
        
        # 显示任务提醒
        messagebox.showinfo("今日任务", task_text)
    
    def on_close(self):
        """处理窗口关闭事件"""
        # 获取未完成的任务
        tasks = self.task_manager.get_today_tasks()
        
        if tasks:
            # 显示任务完成状态确认
            if messagebox.askyesno("任务检查", "你还有未完成的任务，确定要退出吗？\n选择'否'可以继续处理任务。"):
                self.root.destroy()
        else:
            self.root.destroy()


class TaskDialog:
    """任务对话框类"""
    
    def __init__(self, parent, title, task=None):
        """初始化任务对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            task: 任务数据，用于编辑模式
        """
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建表单
        self._create_form(task)
        
        # 等待对话框关闭
        parent.wait_window(self.dialog)
    
    def _create_form(self, task):
        """创建表单
        
        Args:
            task: 任务数据，用于编辑模式
        """
        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 任务标题
        ttk.Label(frame, text="任务标题:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.title_var = tk.StringVar(value=task["title"] if task else "")
        ttk.Entry(frame, textvariable=self.title_var, width=40).grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        
        # 任务描述
        ttk.Label(frame, text="任务描述:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.description_text = tk.Text(frame, width=40, height=5)
        self.description_text.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        if task and task["description"]:
            self.description_text.insert("1.0", task["description"])
        
        # 截止日期
        ttk.Label(frame, text="截止日期 (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.due_date_var = tk.StringVar(value=task["due_date"] if task and task["due_date"] else date.today().strftime("%Y-%m-%d"))
        ttk.Entry(frame, textvariable=self.due_date_var).grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 5))
        
        # 优先级
        ttk.Label(frame, text="优先级:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.priority_var = tk.IntVar(value=task["priority"] if task else 0)
        priority_frame = ttk.Frame(frame)
        priority_frame.grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        
        priorities = [("普通", 0), ("中等", 1), ("重要", 2), ("紧急", 3)]
        for i, (text, value) in enumerate(priorities):
            ttk.Radiobutton(priority_frame, text=text, variable=self.priority_var, value=value).grid(row=0, column=i, padx=(0, 10))
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="确定", command=self._on_ok).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def _on_ok(self):
        """处理确定按钮点击事件"""
        title = self.title_var.get().strip()
        
        if not title:
            messagebox.showwarning("警告", "任务标题不能为空！", parent=self.dialog)
            return
        
        description = self.description_text.get("1.0", tk.END).strip()
        due_date = self.due_date_var.get().strip()
        priority = self.priority_var.get()
        
        # 验证日期格式
        try:
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("警告", "日期格式无效！请使用YYYY-MM-DD格式。", parent=self.dialog)
            return
        
        self.result = (title, description, due_date, priority)
        self.dialog.destroy() 
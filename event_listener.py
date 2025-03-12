#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GoalPulse - 智能任务提示助手
事件监听器模块 - 监听系统开关机事件
"""

import os
import sys
import logging
import platform
import psutil
from datetime import datetime, timedelta

logger = logging.getLogger("GoalPulse.EventListener")

class EventListener:
    """事件监听器类，用于监听系统开关机事件"""
    
    def __init__(self):
        """初始化事件监听器"""
        self.system = platform.system()
        logger.info(f"事件监听器初始化，操作系统: {self.system}")
        
        # 创建标记文件目录
        self.marker_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(self.marker_dir, exist_ok=True)
        
        # 启动标记文件路径
        self.startup_marker = os.path.join(self.marker_dir, "startup_marker")
        
        # 检查是否为开机启动
        self._check_startup()
    
    def _check_startup(self):
        """检查是否为开机启动"""
        # 获取系统启动时间
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        current_time = datetime.now()
        
        # 如果系统启动时间在10分钟内，认为是开机启动
        if (current_time - boot_time) < timedelta(minutes=10):
            logger.info(f"检测到系统启动: 启动时间 {boot_time}, 当前时间 {current_time}")
            # 创建启动标记文件
            with open(self.startup_marker, "w") as f:
                f.write(current_time.strftime("%Y-%m-%d %H:%M:%S"))
            return True
        
        return False
    
    def is_startup(self):
        """检查是否为开机启动
        
        Returns:
            bool: 是否为开机启动
        """
        # 如果存在启动标记文件，则认为是开机启动
        if os.path.exists(self.startup_marker):
            # 读取标记文件中的时间
            with open(self.startup_marker, "r") as f:
                startup_time_str = f.read().strip()
            
            try:
                startup_time = datetime.strptime(startup_time_str, "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                
                # 如果标记文件创建时间在10分钟内，认为是开机启动
                if (current_time - startup_time) < timedelta(minutes=10):
                    logger.info("确认为开机启动")
                    # 删除标记文件，避免重复触发
                    os.remove(self.startup_marker)
                    return True
                else:
                    # 删除过期的标记文件
                    os.remove(self.startup_marker)
            except (ValueError, FileNotFoundError):
                # 时间格式错误或文件已被删除
                pass
        
        return False
    
    def setup_autostart(self):
        """设置开机自启动
        
        Returns:
            bool: 设置是否成功
        """
        try:
            if self.system == "Windows":
                self._setup_windows_autostart()
            elif self.system == "Darwin":  # macOS
                self._setup_macos_autostart()
            elif self.system == "Linux":
                self._setup_linux_autostart()
            else:
                logger.error(f"不支持的操作系统: {self.system}")
                return False
            
            logger.info("开机自启动设置成功")
            return True
        except Exception as e:
            logger.error(f"设置开机自启动失败: {e}")
            return False
    
    def _setup_windows_autostart(self):
        """设置Windows开机自启动"""
        import winreg
        
        # 获取当前脚本的完整路径
        script_path = os.path.abspath(sys.argv[0])
        
        # 如果是.py文件，使用pythonw.exe运行
        if script_path.endswith('.py'):
            executable = sys.executable.replace('python.exe', 'pythonw.exe')
            command = f'"{executable}" "{script_path}"'
        else:
            # 如果是.exe文件，直接运行
            command = f'"{script_path}"'
        
        # 打开注册表
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # 设置启动项
        winreg.SetValueEx(key, "GoalPulse", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        logger.info(f"Windows开机自启动设置成功: {command}")
    
    def _setup_macos_autostart(self):
        """设置macOS开机自启动"""
        # 获取当前脚本的完整路径
        script_path = os.path.abspath(sys.argv[0])
        
        # 创建plist文件内容
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.goalpulse.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
'''
        
        # 保存plist文件
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.goalpulse.app.plist")
        with open(plist_path, "w") as f:
            f.write(plist_content)
        
        # 设置权限
        os.chmod(plist_path, 0o644)
        
        logger.info(f"macOS开机自启动设置成功: {plist_path}")
    
    def _setup_linux_autostart(self):
        """设置Linux开机自启动"""
        # 获取当前脚本的完整路径
        script_path = os.path.abspath(sys.argv[0])
        
        # 创建desktop文件内容
        desktop_content = f'''[Desktop Entry]
Type=Application
Name=GoalPulse
Exec={sys.executable} {script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
'''
        
        # 保存desktop文件
        autostart_dir = os.path.expanduser("~/.config/autostart")
        os.makedirs(autostart_dir, exist_ok=True)
        desktop_path = os.path.join(autostart_dir, "goalpulse.desktop")
        
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        
        # 设置权限
        os.chmod(desktop_path, 0o755)
        
        logger.info(f"Linux开机自启动设置成功: {desktop_path}")
    
    def is_shutdown_event(self):
        """检测是否为关机事件
        
        注意：这个方法不能真正检测关机事件，因为Python程序在系统关机时通常会被强制终止。
        这里提供一个模拟实现，实际应用中可能需要系统级的钩子或服务。
        
        Returns:
            bool: 是否为关机事件（模拟）
        """
        # 这里只是一个占位实现，实际上无法可靠地检测关机事件
        # 在实际应用中，我们会在GUI关闭时调用相关的检查逻辑
        return False
    
    def remove_autostart(self):
        """移除开机自启动
        
        Returns:
            bool: 移除是否成功
        """
        try:
            if self.system == "Windows":
                self._remove_windows_autostart()
            elif self.system == "Darwin":  # macOS
                self._remove_macos_autostart()
            elif self.system == "Linux":
                self._remove_linux_autostart()
            else:
                logger.error(f"不支持的操作系统: {self.system}")
                return False
            
            logger.info("开机自启动移除成功")
            return True
        except Exception as e:
            logger.error(f"移除开机自启动失败: {e}")
            return False
    
    def _remove_windows_autostart(self):
        """移除Windows开机自启动"""
        import winreg
        
        try:
            # 打开注册表
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            # 删除启动项
            winreg.DeleteValue(key, "GoalPulse")
            winreg.CloseKey(key)
            
            logger.info("Windows开机自启动移除成功")
        except FileNotFoundError:
            logger.warning("Windows开机自启动项不存在")
    
    def _remove_macos_autostart(self):
        """移除macOS开机自启动"""
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.goalpulse.app.plist")
        
        if os.path.exists(plist_path):
            os.remove(plist_path)
            logger.info(f"macOS开机自启动移除成功: {plist_path}")
        else:
            logger.warning(f"macOS开机自启动文件不存在: {plist_path}")
    
    def _remove_linux_autostart(self):
        """移除Linux开机自启动"""
        desktop_path = os.path.expanduser("~/.config/autostart/goalpulse.desktop")
        
        if os.path.exists(desktop_path):
            os.remove(desktop_path)
            logger.info(f"Linux开机自启动移除成功: {desktop_path}")
        else:
            logger.warning(f"Linux开机自启动文件不存在: {desktop_path}") 
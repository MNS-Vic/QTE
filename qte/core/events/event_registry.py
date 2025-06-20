#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件注册器和插件管理

提供插件化的事件处理器管理和动态注册机制
"""

import importlib
import inspect
import logging
import os
from typing import Dict, List, Optional, Any, Type, Callable
from pathlib import Path
from abc import ABC, abstractmethod

from .event_types import Event, EventType, EventPriority
from .event_handlers import EventHandlerInterface, HandlerRegistry
from .event_bus import EventBus, EventMetadata


class EventPlugin(ABC):
    """
    事件插件基类
    
    定义了事件插件必须实现的接口
    """
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        获取插件名称
        
        Returns
        -------
        str
            插件名称
        """
        pass
    
    @abstractmethod
    def get_plugin_version(self) -> str:
        """
        获取插件版本
        
        Returns
        -------
        str
            插件版本
        """
        pass
    
    @abstractmethod
    def get_handlers(self) -> List[EventHandlerInterface]:
        """
        获取插件提供的事件处理器
        
        Returns
        -------
        List[EventHandlerInterface]
            事件处理器列表
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        获取插件依赖
        
        Returns
        -------
        List[str]
            依赖的插件名称列表
        """
        return []
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化插件
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        return True
    
    def cleanup(self) -> bool:
        """
        清理插件资源
        
        Returns
        -------
        bool
            清理是否成功
        """
        return True


class PluginManager:
    """
    插件管理器
    
    负责插件的加载、管理和生命周期控制
    """
    
    def __init__(self, plugin_dirs: List[str] = None):
        """
        初始化插件管理器
        
        Parameters
        ----------
        plugin_dirs : List[str], optional
            插件目录列表, by default None
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 插件目录
        self.plugin_dirs = plugin_dirs or []
        
        # 插件存储
        self._plugins: Dict[str, EventPlugin] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._plugin_dependencies: Dict[str, List[str]] = {}
        
        # 统计信息
        self._stats = {
            'loaded_plugins': 0,
            'active_plugins': 0,
            'failed_plugins': 0,
            'total_handlers': 0
        }
        
        self.logger.info("✅ 插件管理器初始化完成")
    
    def add_plugin_dir(self, plugin_dir: str) -> bool:
        """
        添加插件目录
        
        Parameters
        ----------
        plugin_dir : str
            插件目录路径
            
        Returns
        -------
        bool
            添加是否成功
        """
        try:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                self.logger.warning(f"插件目录不存在: {plugin_dir}")
                return False
            
            if plugin_dir not in self.plugin_dirs:
                self.plugin_dirs.append(plugin_dir)
                self.logger.info(f"✅ 已添加插件目录: {plugin_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"添加插件目录失败: {e}")
            return False
    
    def load_plugin(self, plugin_class: Type[EventPlugin], 
                   config: Dict[str, Any] = None) -> str:
        """
        加载插件类
        
        Parameters
        ----------
        plugin_class : Type[EventPlugin]
            插件类
        config : Dict[str, Any], optional
            插件配置, by default None
            
        Returns
        -------
        str
            插件ID，失败返回空字符串
        """
        try:
            # 创建插件实例
            plugin_instance = plugin_class()
            plugin_name = plugin_instance.get_plugin_name()
            
            if plugin_name in self._plugins:
                self.logger.warning(f"插件已存在: {plugin_name}")
                return plugin_name
            
            # 检查依赖
            dependencies = plugin_instance.get_dependencies()
            for dep in dependencies:
                if dep not in self._plugins:
                    self.logger.error(f"插件 {plugin_name} 依赖的插件 {dep} 未加载")
                    return ""
            
            # 初始化插件
            if not plugin_instance.initialize(config):
                self.logger.error(f"插件 {plugin_name} 初始化失败")
                return ""
            
            # 注册插件
            self._plugins[plugin_name] = plugin_instance
            self._plugin_configs[plugin_name] = config or {}
            self._plugin_dependencies[plugin_name] = dependencies
            
            # 更新统计
            self._stats['loaded_plugins'] += 1
            self._stats['active_plugins'] = len(self._plugins)
            
            # 统计处理器数量
            handlers = plugin_instance.get_handlers()
            self._stats['total_handlers'] += len(handlers)
            
            self.logger.info(f"✅ 已加载插件: {plugin_name} v{plugin_instance.get_plugin_version()}")
            return plugin_name
            
        except Exception as e:
            self.logger.error(f"加载插件失败: {e}")
            self._stats['failed_plugins'] += 1
            return ""
    
    def load_plugins_from_dir(self, plugin_dir: str) -> List[str]:
        """
        从目录加载插件
        
        Parameters
        ----------
        plugin_dir : str
            插件目录路径
            
        Returns
        -------
        List[str]
            成功加载的插件ID列表
        """
        loaded_plugins = []
        
        try:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                self.logger.warning(f"插件目录不存在: {plugin_dir}")
                return loaded_plugins
            
            # 遍历Python文件
            for py_file in plugin_path.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                try:
                    # 动态导入模块
                    module_name = py_file.stem
                    spec = importlib.util.spec_from_file_location(module_name, py_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找插件类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, EventPlugin) and 
                            obj != EventPlugin):
                            
                            plugin_id = self.load_plugin(obj)
                            if plugin_id:
                                loaded_plugins.append(plugin_id)
                
                except Exception as e:
                    self.logger.error(f"加载插件文件 {py_file} 失败: {e}")
            
            self.logger.info(f"从目录 {plugin_dir} 加载了 {len(loaded_plugins)} 个插件")
            
        except Exception as e:
            self.logger.error(f"从目录加载插件失败: {e}")
        
        return loaded_plugins
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Parameters
        ----------
        plugin_name : str
            插件名称
            
        Returns
        -------
        bool
            卸载是否成功
        """
        try:
            if plugin_name not in self._plugins:
                self.logger.warning(f"插件不存在: {plugin_name}")
                return False
            
            # 检查是否有其他插件依赖此插件
            dependent_plugins = []
            for name, deps in self._plugin_dependencies.items():
                if plugin_name in deps and name in self._plugins:
                    dependent_plugins.append(name)
            
            if dependent_plugins:
                self.logger.error(f"无法卸载插件 {plugin_name}，以下插件依赖它: {dependent_plugins}")
                return False
            
            # 清理插件
            plugin = self._plugins[plugin_name]
            plugin.cleanup()
            
            # 从注册表中移除
            del self._plugins[plugin_name]
            del self._plugin_configs[plugin_name]
            del self._plugin_dependencies[plugin_name]
            
            # 更新统计
            self._stats['active_plugins'] = len(self._plugins)
            
            self.logger.info(f"✅ 已卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"卸载插件失败: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[EventPlugin]:
        """
        获取插件实例
        
        Parameters
        ----------
        plugin_name : str
            插件名称
            
        Returns
        -------
        Optional[EventPlugin]
            插件实例，如果不存在返回None
        """
        return self._plugins.get(plugin_name)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有插件
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            插件信息字典
        """
        plugins_info = {}
        
        for plugin_name, plugin in self._plugins.items():
            plugins_info[plugin_name] = {
                'name': plugin.get_plugin_name(),
                'version': plugin.get_plugin_version(),
                'dependencies': plugin.get_dependencies(),
                'handlers_count': len(plugin.get_handlers()),
                'config': self._plugin_configs.get(plugin_name, {})
            }
        
        return plugins_info
    
    def get_all_handlers(self) -> List[EventHandlerInterface]:
        """
        获取所有插件提供的处理器
        
        Returns
        -------
        List[EventHandlerInterface]
            所有处理器列表
        """
        all_handlers = []
        
        for plugin in self._plugins.values():
            handlers = plugin.get_handlers()
            all_handlers.extend(handlers)
        
        return all_handlers
    
    def get_stats(self) -> Dict[str, Any]:
        """获取插件管理器统计信息"""
        return self._stats.copy()


class EventRegistry:
    """
    事件注册器
    
    统一管理事件总线、处理器注册表和插件管理器
    """
    
    def __init__(self, event_bus: EventBus = None,
                 handler_registry: HandlerRegistry = None,
                 plugin_manager: PluginManager = None):
        """
        初始化事件注册器
        
        Parameters
        ----------
        event_bus : EventBus, optional
            事件总线实例, by default None
        handler_registry : HandlerRegistry, optional
            处理器注册表实例, by default None
        plugin_manager : PluginManager, optional
            插件管理器实例, by default None
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 组件实例
        self.event_bus = event_bus or EventBus()
        self.handler_registry = handler_registry or HandlerRegistry()
        self.plugin_manager = plugin_manager or PluginManager()
        
        # 注册状态
        self._initialized = False
        self._auto_register_handlers = True
        
        self.logger.info("✅ 事件注册器初始化完成")
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化事件注册器
        
        Parameters
        ----------
        config : Dict[str, Any], optional
            配置参数, by default None
            
        Returns
        -------
        bool
            初始化是否成功
        """
        try:
            config = config or {}
            
            # 启动事件总线
            if not self.event_bus.start():
                self.logger.error("事件总线启动失败")
                return False
            
            # 配置自动注册
            self._auto_register_handlers = config.get('auto_register_handlers', True)
            
            # 加载插件目录
            plugin_dirs = config.get('plugin_dirs', [])
            for plugin_dir in plugin_dirs:
                self.plugin_manager.add_plugin_dir(plugin_dir)
                self.plugin_manager.load_plugins_from_dir(plugin_dir)
            
            # 自动注册处理器
            if self._auto_register_handlers:
                self._auto_register_plugin_handlers()
            
            self._initialized = True
            self.logger.info("✅ 事件注册器初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化事件注册器失败: {e}")
            return False
    
    def shutdown(self) -> bool:
        """
        关闭事件注册器
        
        Returns
        -------
        bool
            关闭是否成功
        """
        try:
            # 清理处理器
            self.handler_registry.cleanup_all()
            
            # 卸载所有插件
            plugin_names = list(self.plugin_manager._plugins.keys())
            for plugin_name in plugin_names:
                self.plugin_manager.unload_plugin(plugin_name)
            
            # 停止事件总线
            self.event_bus.stop()
            
            self._initialized = False
            self.logger.info("✅ 事件注册器已关闭")
            return True
            
        except Exception as e:
            self.logger.error(f"关闭事件注册器失败: {e}")
            return False
    
    def register_handler(self, handler: EventHandlerInterface,
                        auto_subscribe: bool = True) -> str:
        """
        注册事件处理器
        
        Parameters
        ----------
        handler : EventHandlerInterface
            事件处理器
        auto_subscribe : bool, optional
            是否自动订阅事件, by default True
            
        Returns
        -------
        str
            处理器ID
        """
        try:
            # 注册到处理器注册表
            handler_id = self.handler_registry.register_handler(handler)
            
            if not handler_id:
                return ""
            
            # 自动订阅事件
            if auto_subscribe:
                supported_events = handler.get_supported_event_types()
                for event_type in supported_events:
                    self._subscribe_handler_to_event(handler, event_type)
            
            self.logger.info(f"✅ 已注册并订阅事件处理器: {handler.get_handler_name()}")
            return handler_id
            
        except Exception as e:
            self.logger.error(f"注册事件处理器失败: {e}")
            return ""
    
    def unregister_handler(self, handler_id: str) -> bool:
        """
        注销事件处理器
        
        Parameters
        ----------
        handler_id : str
            处理器ID
            
        Returns
        -------
        bool
            注销是否成功
        """
        try:
            # 从处理器注册表注销
            return self.handler_registry.unregister_handler(handler_id)
            
        except Exception as e:
            self.logger.error(f"注销事件处理器失败: {e}")
            return False
    
    def publish_event(self, event: Event) -> str:
        """
        发布事件
        
        Parameters
        ----------
        event : Event
            事件对象
            
        Returns
        -------
        str
            事件ID
        """
        return self.event_bus.publish(event)
    
    def _auto_register_plugin_handlers(self):
        """自动注册插件处理器"""
        try:
            all_handlers = self.plugin_manager.get_all_handlers()
            
            for handler in all_handlers:
                self.register_handler(handler, auto_subscribe=True)
            
            self.logger.info(f"✅ 自动注册了 {len(all_handlers)} 个插件处理器")
            
        except Exception as e:
            self.logger.error(f"自动注册插件处理器失败: {e}")
    
    def _subscribe_handler_to_event(self, handler: EventHandlerInterface, event_type: str):
        """订阅处理器到事件"""
        try:
            def handler_wrapper(event_data, metadata):
                return handler.handle(event_data, metadata)
            
            subscription_id = self.event_bus.subscribe(
                event_type=event_type,
                handler=handler_wrapper,
                priority=handler.get_priority(),
                async_handler=handler.can_handle_async()
            )
            
            self.logger.debug(f"处理器 {handler.get_handler_name()} 已订阅事件 {event_type}")
            
        except Exception as e:
            self.logger.error(f"订阅处理器到事件失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'event_bus': self.event_bus.get_stats(),
            'handler_registry': self.handler_registry.get_stats(),
            'plugin_manager': self.plugin_manager.get_stats(),
            'initialized': self._initialized
        }

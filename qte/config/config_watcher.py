"""
配置文件监控器 - 支持配置热更新
"""

import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from .exceptions import ConfigWatchError


@dataclass
class WatchEvent:
    """监控事件"""
    file_path: Path
    event_type: str  # 'modified', 'created', 'deleted'
    timestamp: datetime
    config_name: Optional[str] = None


class ConfigWatcher:
    """
    配置文件监控器
    
    监控配置文件变化并触发热更新
    支持多种监控策略：
    - 轮询监控 (跨平台兼容)
    - 文件系统事件监控 (需要watchdog库)
    """
    
    def __init__(self, poll_interval: float = 1.0, use_native_watcher: bool = True):
        """
        初始化配置监控器
        
        Args:
            poll_interval: 轮询间隔(秒)
            use_native_watcher: 是否使用原生文件系统监控
        """
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        self.poll_interval = poll_interval
        self.use_native_watcher = use_native_watcher
        
        # 监控状态
        self._watching = False
        self._watch_thread = None
        self._lock = threading.RLock()
        
        # 监控的文件和回调
        self._watched_files: Dict[Path, str] = {}  # file_path -> config_name
        self._file_timestamps: Dict[Path, float] = {}
        self._callbacks: List[Callable[[WatchEvent], None]] = []
        
        # 尝试导入原生监控器
        self._native_observer = None
        if use_native_watcher:
            self._setup_native_watcher()
    
    def _setup_native_watcher(self):
        """设置原生文件系统监控器"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ConfigFileHandler(FileSystemEventHandler):
                def __init__(self, watcher):
                    self.watcher = watcher
                
                def on_modified(self, event):
                    if not event.is_directory:
                        self.watcher._handle_file_event(Path(event.src_path), 'modified')
                
                def on_created(self, event):
                    if not event.is_directory:
                        self.watcher._handle_file_event(Path(event.src_path), 'created')
                
                def on_deleted(self, event):
                    if not event.is_directory:
                        self.watcher._handle_file_event(Path(event.src_path), 'deleted')
            
            self._native_observer = Observer()
            self._event_handler = ConfigFileHandler(self)
            self.logger.info("✅ 原生文件系统监控器初始化成功")
            
        except ImportError:
            self.logger.warning("⚠️ watchdog库未安装，使用轮询监控")
            self._native_observer = None
    
    def add_file(self, file_path: Path, config_name: str):
        """
        添加监控文件
        
        Args:
            file_path: 文件路径
            config_name: 配置名称
        """
        with self._lock:
            file_path = Path(file_path).resolve()
            self._watched_files[file_path] = config_name
            
            if file_path.exists():
                self._file_timestamps[file_path] = file_path.stat().st_mtime
            
            # 如果使用原生监控器，添加目录监控
            if self._native_observer and self._watching:
                self._add_native_watch(file_path)
            
            self.logger.info(f"📁 添加文件监控: {file_path} -> {config_name}")
    
    def remove_file(self, file_path: Path):
        """
        移除监控文件
        
        Args:
            file_path: 文件路径
        """
        with self._lock:
            file_path = Path(file_path).resolve()
            
            if file_path in self._watched_files:
                del self._watched_files[file_path]
            
            if file_path in self._file_timestamps:
                del self._file_timestamps[file_path]
            
            self.logger.info(f"🗑️ 移除文件监控: {file_path}")
    
    def add_callback(self, callback: Callable[[WatchEvent], None]):
        """
        添加监控回调
        
        Args:
            callback: 回调函数，接收WatchEvent参数
        """
        self._callbacks.append(callback)
        self.logger.info("📡 添加监控回调")
    
    def remove_callback(self, callback: Callable[[WatchEvent], None]):
        """移除监控回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            self.logger.info("🗑️ 移除监控回调")
    
    def start(self):
        """启动监控"""
        with self._lock:
            if self._watching:
                self.logger.warning("⚠️ 监控器已经在运行")
                return
            
            self._watching = True
            
            if self._native_observer:
                # 使用原生监控器
                self._start_native_watcher()
            else:
                # 使用轮询监控
                self._start_polling_watcher()
            
            self.logger.info("🚀 配置文件监控已启动")
    
    def stop(self):
        """停止监控"""
        with self._lock:
            if not self._watching:
                return
            
            self._watching = False
            
            # 停止原生监控器
            if self._native_observer:
                self._native_observer.stop()
                self._native_observer.join()
            
            # 停止轮询线程
            if self._watch_thread and self._watch_thread.is_alive():
                self._watch_thread.join(timeout=5.0)
            
            self.logger.info("🔒 配置文件监控已停止")
    
    def _start_native_watcher(self):
        """启动原生监控器"""
        # 为每个监控文件的目录添加监控
        watched_dirs: Set[Path] = set()
        
        for file_path in self._watched_files.keys():
            parent_dir = file_path.parent
            if parent_dir not in watched_dirs:
                self._native_observer.schedule(
                    self._event_handler,
                    str(parent_dir),
                    recursive=False
                )
                watched_dirs.add(parent_dir)
        
        self._native_observer.start()
        self.logger.info(f"✅ 原生监控器已启动，监控目录数: {len(watched_dirs)}")
    
    def _add_native_watch(self, file_path: Path):
        """为新文件添加原生监控"""
        if not self._native_observer:
            return
        
        parent_dir = file_path.parent
        
        # 检查是否已经监控了这个目录
        for watch in self._native_observer.emitters:
            if Path(watch.watch.path) == parent_dir:
                return  # 已经监控了
        
        # 添加新的目录监控
        self._native_observer.schedule(
            self._event_handler,
            str(parent_dir),
            recursive=False
        )
    
    def _start_polling_watcher(self):
        """启动轮询监控器"""
        self._watch_thread = threading.Thread(
            target=self._polling_loop,
            name="ConfigWatcher",
            daemon=True
        )
        self._watch_thread.start()
        self.logger.info(f"✅ 轮询监控器已启动，间隔: {self.poll_interval}秒")
    
    def _polling_loop(self):
        """轮询监控循环"""
        while self._watching:
            try:
                self._check_file_changes()
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"❌ 轮询监控异常: {e}")
                time.sleep(self.poll_interval)
    
    def _check_file_changes(self):
        """检查文件变化"""
        with self._lock:
            current_files = list(self._watched_files.keys())
        
        for file_path in current_files:
            try:
                if file_path.exists():
                    current_mtime = file_path.stat().st_mtime
                    last_mtime = self._file_timestamps.get(file_path, 0)
                    
                    if current_mtime > last_mtime:
                        # 文件已修改
                        self._file_timestamps[file_path] = current_mtime
                        
                        if last_mtime > 0:  # 不是第一次检查
                            self._handle_file_event(file_path, 'modified')
                        else:
                            self._handle_file_event(file_path, 'created')
                
                else:
                    # 文件已删除
                    if file_path in self._file_timestamps:
                        del self._file_timestamps[file_path]
                        self._handle_file_event(file_path, 'deleted')
            
            except Exception as e:
                self.logger.error(f"❌ 检查文件变化失败 {file_path}: {e}")
    
    def _handle_file_event(self, file_path: Path, event_type: str):
        """处理文件事件"""
        # 检查是否是我们监控的文件
        if file_path not in self._watched_files:
            return
        
        config_name = self._watched_files[file_path]
        
        # 创建事件
        event = WatchEvent(
            file_path=file_path,
            event_type=event_type,
            timestamp=datetime.now(),
            config_name=config_name
        )
        
        self.logger.info(f"📝 检测到文件变化: {file_path} ({event_type})")
        
        # 通知所有回调
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"❌ 监控回调执行失败: {e}")
    
    def get_watched_files(self) -> Dict[str, str]:
        """获取监控的文件列表"""
        with self._lock:
            return {str(path): config_name for path, config_name in self._watched_files.items()}
    
    def is_watching(self) -> bool:
        """检查是否正在监控"""
        return self._watching
    
    def get_statistics(self) -> Dict[str, any]:
        """获取监控器统计信息"""
        return {
            'watching': self._watching,
            'watched_files_count': len(self._watched_files),
            'callbacks_count': len(self._callbacks),
            'use_native_watcher': self._native_observer is not None,
            'poll_interval': self.poll_interval
        }

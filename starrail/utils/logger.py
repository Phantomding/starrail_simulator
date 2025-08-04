# starrail/utils/logger.py
import sys

class Logger:
    """
    一个简单的单例日志记录器，用于格式化战斗输出。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, verbose=False):
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return
        self.verbose = verbose
        self._indent_level = 0
        self._indent_char = "  "
        self._color_map = {
            "default": "\033[0m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "cyan": "\033[96m",
        }
        self._initialized = True

    def _get_color(self, color_name: str) -> str:
        # 在不支持颜色的环境中（如某些文件输出），返回空字符串
        if not sys.stdout.isatty():
            return ""
        return self._color_map.get(color_name, "")

    def log(self, message: str, color: str = "default"):
        """记录一条标准信息。"""
        indentation = self._indent_char * self._indent_level
        colored_message = f"{self._get_color(color)}{message}{self._get_color('default')}"
        print(f"{indentation}{colored_message}")

    def log_verbose(self, message: str, color: str = "cyan"):
        """只在verbose模式下记录信息。"""
        if self.verbose:
            self.log(f"VERBOSE: {message}", color)

    def start_block(self, title: str, color: str = "yellow"):
        """开始一个新的日志块，增加缩进。"""
        self.log(f"┌─ {title} " + "─" * (40 - len(title)), color)
        self._indent_level += 1

    def end_block(self, title: str = "", color: str = "yellow"):
        """结束当前的日志块，减少缩进。"""
        self._indent_level = max(0, self._indent_level - 1)
        if title:
            self.log(f"└─ {title} " + "─" * (40 - len(title)), color)
        else:
            self.log("└" + "─" * 43, color)

# 创建一个全局单例
logger = Logger()

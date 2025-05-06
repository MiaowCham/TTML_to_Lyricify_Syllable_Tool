#-*- coding: UTF-8-*-
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import xml
from re import compile, Pattern, Match
import string
from typing import Iterator, AnyStr
from xml.dom.minicompat import NodeList
from xml.dom.minidom import Document, Element
import threading
from queue import Queue

# 导入 pip (仅在开发环境使用)
try:
    from pip import main as pip_main
except ImportError:
    pip_main = None

# 导入必要的库
# 首先尝试直接导入，如果打包后运行则应该已经包含这些库
# 其次尝试使用pip安装（仅开发环境）
try:
    import requests
except ImportError:
    if pip_main:
        print("正在安装requests...")
        pip_main(['install', 'requests'])
        import requests
    else:
        # 打包环境中出错则显示友好错误
        messagebox.showerror("错误", "缺少requests库，程序无法正常运行。请重新下载完整版本或联系开发者。")
        sys.exit(1)

try:
    from loguru import logger
except ImportError:
    try:
        import loguru
    except ImportError:
        if pip_main:
            print("正在安装loguru...")
            pip_main(['install', 'loguru'])
            import loguru
            from loguru import logger
        else:
            # 打包环境中出错则显示友好错误
            messagebox.showerror("错误", "缺少loguru库，程序无法正常运行。请重新下载完整版本或联系开发者。")
            sys.exit(1)

# 确保pyperclip已安装
try:
    import pyperclip
except ImportError:
    if pip_main:
        print("正在安装pyperclip...")
        pip_main(['install', 'pyperclip'])
        import pyperclip
    else:
        # 打包环境中出错则显示友好错误
        messagebox.showerror("错误", "缺少pyperclip库，程序无法正常运行。请重新下载完整版本或联系开发者。")
        sys.exit(1)

# 尝试导入tkinterdnd2用于拖放功能
try:
    import tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    try:
        if pip_main:
            print("正在安装tkinterdnd2...")
            pip_main(['install', 'tkinterdnd2'])
            import tkinterdnd2
            from tkinterdnd2 import DND_FILES, TkinterDnD
            HAS_DND = True
        else:
            HAS_DND = False
            print("无法使用tkinterdnd2，拖放功能将不可用")
            # 定义一个全局变量，以便在类中使用
            DND_FILES = "*"
    except:
        HAS_DND = False
        print("无法安装tkinterdnd2，拖放功能将不可用")
        # 定义一个全局变量，以便在类中使用
        DND_FILES = "*"

from datetime import datetime

def get_app_path():
    """获取应用程序路径，处理打包后的情况"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        return os.path.dirname(sys.executable)
    else:
        # 如果是开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 日志文件夹路径
log_dir = os.path.join(get_app_path(), 'log')

# 设置日志记录
def setup_logger(enabled=False):
    if enabled:
        try:
            # 确保日志文件夹存在（仅在启用日志时创建）
            os.makedirs(log_dir, exist_ok=True)
            # 移除所有现有的处理器
            logger.remove()
            # 添加新的文件处理器
            log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d %H.%M.%S')}.log")
            logger.add(log_file, level='DEBUG', rotation="1 day", retention="7 days")
            logger.info("日志记录已启用")
            return True
        except Exception as e:
            print(f"设置日志失败: {str(e)}")
            return False
    return False

# TTML转换相关类和函数
class TTMLTime:
    __pattern: Pattern = compile(r'\d+')

    def __init__(self, centi: str = ''):
        if centi == '': return
        # 使用 finditer 获取匹配的迭代器
        matches: Iterator[Match[str]] = TTMLTime.__pattern.finditer(centi)
        # 获取下一个匹配
        iterator: Iterator[Match[str]] = iter(matches)  # 将匹配对象转换为迭代器

        self.__minute:int = int(next(iterator).group())
        self.__second:int = int(next(iterator).group())
        self.__micros:int = int(next(iterator).group())

    def __str__(self) -> str:
        return f'{self.__minute:02}:{self.__second:02}.{self.__micros:03}'

    def __int__(self) -> int:
        return (self.__minute * 60 + self.__second) * 1000 + self.__micros

    def __ge__(self, other) -> bool:
        return (self.__minute, self.__second, self.__micros) >= (other.__minute, other.__second, other.__micros)

    def __ne__(self, other) -> bool:
        return (self.__minute, self.__second, self.__micros) != (other.__minute, other.__second, other.__micros)

    def __sub__(self, other) -> int:
        return abs(int(self) - int(other))

class TTMLSyl:
    def __init__(self, element: Element):
        self.__element: Element = element

        self.__begin: TTMLTime = TTMLTime(element.getAttribute("begin"))
        self.__end: TTMLTime = TTMLTime(element.getAttribute("end"))
        self.text: str = element.childNodes[0].nodeValue

    def __str__(self) -> str:
        return f'{self.text}({int(self.__begin)},{self.__end - self.__begin})'

    def get_begin(self) -> TTMLTime:
        return self.__begin

    def get_end(self) -> TTMLTime:
        return self.__end

class TTMLLine:
    have_ts: bool = False
    have_duet: bool = False
    have_bg: bool = False
    have_pair: int = 0

    __before: Pattern[AnyStr] = compile(r'^\({2,}')
    __after: Pattern[AnyStr] = compile(r'\){2,}$')

    def __init__(self, element: Element, is_bg: bool = False):
        self.__element: Element = element
        self.__orig_line: list[TTMLSyl|str] = []
        self.__ts_line: str|None = None
        self.__bg_line: TTMLLine|None = None
        self.__is_bg: bool = is_bg

        TTMLLine.have_bg |= is_bg

        # 获取传入元素的 agent 属性
        agent: string = element.getAttribute("ttm:agent")
        self.__is_duet:bool = bool(agent and agent != 'v1')

        # 获取 <p> 元素的所有子节点，包括文本节点
        child_elements:list[Element] = element.childNodes  # iter() 会返回所有子元素和文本节点

        # 遍历所有子元素
        for child in child_elements:
            if child.nodeType == 3 and child.nodeValue:  # 如果是文本节点（例如空格或换行）
                if len(self.__orig_line) > 0 and len(child.nodeValue) < 2:
                    self.__orig_line[-1].text += child.nodeValue
                else:
                    self.__orig_line.append(child.nodeValue)
            else:
                # 获取 <span> 中的属性
                role:str = child.getAttribute("ttm:role")

                # 没有role代表是一个syl
                if role == "":
                    if child.childNodes[0].nodeValue:
                        self.__orig_line.append(TTMLSyl(child))

                elif role == "x-bg":
                    # 和声行
                    self.__bg_line = TTMLLine(child, True)
                    self.__bg_line.__is_duet = self.__is_duet
                elif role == "x-translation":
                    # 翻译行
                    TTMLLine.have_ts = True
                    self.__ts_line = f'{child.childNodes[0].data}'

        if len(self.__orig_line) != 1 or type(self.__orig_line[0]) != str:
            self.__begin = self.__orig_line[0].get_begin()
            self.__end = self.__orig_line[0].get_end()
        else:
            self.__begin: TTMLTime = TTMLTime(element.getAttribute("begin"))
            self.__end: TTMLTime = TTMLTime(element.getAttribute("end"))

        if is_bg:
            if TTMLLine.__before.search(self.__orig_line[0] if type(self.__orig_line[0]) == str else self.__orig_line[0].text):
                if type(self.__orig_line[0]) == str:
                    self.__orig_line[0] = TTMLLine.__before.sub('(', self.__orig_line[0])
                else:
                    self.__orig_line[0].text = TTMLLine.__before.sub('(', self.__orig_line[0].text)
                TTMLLine.have_pair += 1
            if TTMLLine.__after.search(self.__orig_line[-1] if type(self.__orig_line[-1]) == str else self.__orig_line[-1].text):
                if type(self.__orig_line[-1]) == str:
                    self.__orig_line[-1] = TTMLLine.__after.sub(')', self.__orig_line[-1])
                else:
                    self.__orig_line[-1].text = TTMLLine.__after.sub(')', self.__orig_line[-1].text)
                TTMLLine.have_pair += 1

    def __role(self) -> int:
        return ((int(TTMLLine.have_bg) + int(self.__is_bg)) * 3
                + int(TTMLLine.have_duet) + int(self.__is_duet))

    def __raw(self) -> tuple[str, str|None]:
        return (f'[{self.__role()}]' + (''.join([str(v) for v in self.__orig_line] if len(self.__orig_line) != 1 or type(
            self.__orig_line[0]) != str else f'{self.__orig_line[0]}({int(self.__begin)},{self.__end - self.__begin})')),
                f'[{self.__begin}]{self.__ts_line}' if self.__ts_line else None)

    def to_str(self) -> tuple[tuple[str, str|None],tuple[str, str|None]|None]:
        return self.__raw(), (self.__bg_line.__raw() if self.__bg_line else None)

def ttml_to_lyricify_syllable_text(ttml_content):
    """将TTML文本内容转换为Lyricify Syllable文本"""
    TTMLLine.have_duet = False
    TTMLLine.have_bg = False
    TTMLLine.have_ts = False
    TTMLLine.have_pair = 0

    lyric_text = []
    trans_text = []
    
    try:
        # 预处理XML内容，移除可能导致解析错误的内容
        ttml_content = ttml_content.replace('xmlns=""', '')
        
        # 解析XML内容
        logger.debug(f"尝试解析XML内容")
        dom: Document = xml.dom.minidom.parseString(ttml_content)  # 解析XML字符串
        tt: Document = dom.documentElement  # 获取根元素

        # 获取tt中的body/head元素
        logger.debug(f"尝试获取tt中的body/head元素")
        body: Element = tt.getElementsByTagName('body')[0]
        head: Element = tt.getElementsByTagName('head')[0]

        if body and head:
            # 获取body/head中的<div>/<metadata>子元素
            logger.debug(f"尝试获取<div>/<metadata>子元素")
            div: Element = body.getElementsByTagName('div')[0]
            metadata: Element = head.getElementsByTagName('metadata')[0]

            # 获取div中的所有<p>子元素
            logger.debug(f"尝试获取div中的所有<p>子元素")
            p_elements: NodeList[Element] = div.getElementsByTagName('p')
            agent_elements: NodeList[Element] = metadata.getElementsByTagName('ttm:agent')

            # 检查是否有对唱
            logger.debug(f"检查是否有对唱")
            for meta in agent_elements:
                if meta.getAttribute('xml:id') != 'v1':
                    TTMLLine.have_duet = True
                    logger.debug(f"发现对唱")

            lines: list[TTMLLine] = []
            # 遍历每个<p>元素
            logger.debug(f"开始执行转换")
            for p in p_elements:
                lines.append(TTMLLine(p))
                # 记录日志
                logger.info(f"TTML第{p_elements.index(p)}行转换结果：{lines[-1].to_str()[0][0]}")

            # 生成输出文本
            for main_line, bg_line in [line.to_str() for line in lines]:
                lyric_text.append(main_line[0])
                if main_line[1]:
                    trans_text.append(main_line[1])
                else:
                    # 如果有翻译但当前行没有，添加空行保持行数一致
                    if TTMLLine.have_ts:
                        trans_text.append(f"[{main_line[0].split(']')[0].strip('[]')}]")

                if bg_line:
                    lyric_text.append(bg_line[0])
                    if bg_line[1]:
                        trans_text.append(bg_line[1])
                    else:
                        # 如果有翻译但当前行没有，添加空行保持行数一致
                        if TTMLLine.have_ts:
                            trans_text.append(f"[{bg_line[0].split(']')[0].strip('[]')}]")

        else:
            logger.exception("错误: 找不到<body>元素")
            return False, None, None

    except Exception as e:
        logger.exception(f"无法解析TTML内容: {str(e)}")
        return False, None, None
            
    return True, "\n".join(lyric_text), "\n".join(trans_text) if TTMLLine.have_ts else None

# GUI应用类
class TTMLToLyricifySyllableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TTML转Lyricify Syllable工具")
        self.root.geometry("800x600")
        self.root.configure(bg="#eeeeee")
        
        # 初始化后设置实际窗口大小为最小窗口大小
        self.root.update_idletasks()  # 确保窗口已经绘制
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.root.minsize(width, height)  # 设置最小窗口大小为当前实际大小
        
        # 设置线程锁，用于防止多线程操作时的竞态条件
        self.thread_lock = threading.Lock()
        
        # 设置图标（如果有）
        try:
            icon_path = os.path.join(get_app_path(), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # 日志启用状态和自动换行状态
        self.log_enabled = tk.BooleanVar(value=False)
        self.word_wrap_enabled = tk.BooleanVar(value=False)
        
        # 设置样式
        self.setup_styles()
        
        # 创建主框架
        self.create_widgets()
        
        # 绑定拖放事件
        self.setup_drag_drop()
        
        # 状态消息
        self.status_message = ""
        
        # 显示欢迎信息
        self.set_status("欢迎使用TTML转Lyricify Syllable工具")
        
        # 绑定复选框的变量跟踪
        self.log_enabled.trace_add("write", self.on_log_enabled_change)
        
        # 初始化文本框换行状态
        self.toggle_word_wrap()
        
    def on_log_enabled_change(self, *args):
        """当日志启用状态改变时调用"""
        if self.log_enabled.get():
            if setup_logger(True):
                self.set_status("日志记录已启用")
            else:
                self.set_status("日志记录启用失败")
                self.log_enabled.set(False)
        else:
            # 移除所有处理器
            logger.remove()
            self.set_status("日志记录已禁用")
    
    def toggle_word_wrap(self):
        """切换文本框的自动换行状态"""
        wrap_mode = tk.WORD if self.word_wrap_enabled.get() else tk.NONE
        self.input_text.configure(wrap=wrap_mode)
        self.output_text.configure(wrap=wrap_mode)
        self.trans_text.configure(wrap=wrap_mode)
        
    def setup_styles(self):
        # 设置ttk样式
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#DDDDDD")
        style.configure("TLabel", background="#EEEEEE")
        style.configure("TCheckbutton", background="#EEEEEE")
        style.configure("TPanedwindow", background="#EEEEEE")
        style.configure("TFrame", background="#EEEEEE")
        
    def create_widgets(self):
        # 创建主分割窗口
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧框架 - 输入
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)
        
        # 右侧框架 - 输出
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=1)
        
        # 左侧标签和文本框
        ttk.Label(left_frame, text="TTML输入").pack(anchor=tk.W, pady=(0, 5))
        
        self.input_text = tk.Text(left_frame, wrap=tk.WORD, bg="#DDDDDD", fg="#111111", insertbackground="white", height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.insert(tk.END, "粘贴文本或拖动文件到此处")
        self.input_text.bind("<FocusIn>", self.clear_placeholder)
        
        # 右侧标签和文本框
        ttk.Label(right_frame, text="Lyricify Syllable输出").pack(anchor=tk.W, pady=(0, 5))
        
        # 歌词输出框
        self.output_text = tk.Text(right_frame, wrap=tk.WORD, bg="#DDDDDD", fg="#111111", state=tk.DISABLED, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 翻译标签和输出框
        ttk.Label(right_frame, text="翻译输出").pack(anchor=tk.W, pady=(10, 5))
        self.trans_text = tk.Text(right_frame, wrap=tk.WORD, bg="#DDDDDD", fg="#111111", state=tk.DISABLED, height=8)
        self.trans_text.pack(fill=tk.X, expand=False)
        
        # 底部按钮框架
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 左侧按钮
        left_buttons_frame = ttk.Frame(bottom_frame)
        left_buttons_frame.pack(side=tk.LEFT)
        
        self.paste_btn = ttk.Button(left_buttons_frame, text="粘贴", command=self.paste_from_clipboard)
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.import_btn = ttk.Button(left_buttons_frame, text="导入", command=self.import_file)
        self.import_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.amll_search_btn = ttk.Button(left_buttons_frame, text="从 AMLL DB 搜索", command=self.open_amll_search)
        self.amll_search_btn.pack(side=tk.LEFT)
        
        # 右侧按钮
        right_buttons_frame = ttk.Frame(bottom_frame)
        right_buttons_frame.pack(side=tk.RIGHT)
        
        self.convert_btn = ttk.Button(right_buttons_frame, text="转换", command=self.convert_ttml)
        self.convert_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.copy_lyrics_btn = ttk.Button(right_buttons_frame, text="复制歌词", command=self.copy_lyrics_to_clipboard, state=tk.DISABLED)
        self.copy_lyrics_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.copy_trans_btn = ttk.Button(right_buttons_frame, text="复制翻译", command=self.copy_trans_to_clipboard, state=tk.DISABLED)
        self.copy_trans_btn.pack(side=tk.RIGHT)
        
        # 状态框架
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side=tk.LEFT)
        
        # 复选框框架
        checkbox_frame = ttk.Frame(status_frame)
        checkbox_frame.pack(side=tk.RIGHT)
        
        # 自动换行复选框
        self.word_wrap_checkbox = ttk.Checkbutton(checkbox_frame, text="自动换行", variable=self.word_wrap_enabled, command=self.toggle_word_wrap)
        self.word_wrap_checkbox.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 日志复选框
        self.log_checkbox = ttk.Checkbutton(checkbox_frame, text="启用日志记录", variable=self.log_enabled)
        self.log_checkbox.pack(side=tk.RIGHT)
    
    def setup_drag_drop(self):
        # 为输入文本框绑定拖放事件
        try:
            self.input_text.drop_target_register(DND_FILES)
            self.input_text.dnd_bind('<<Drop>>', self.handle_drop)
            logger.info("拖放功能已启用")
        except Exception as e:
            logger.warning(f"拖放功能初始化失败: {str(e)}")
            # 如果拖放功能不可用，添加提示标签
            ttk.Label(self.root, text="注意：拖放功能不可用，请使用导入按钮").pack(pady=5)
    
    def handle_drop(self, event):
        # 处理文件拖放
        try:
            file_path = event.data
            # 移除可能的引号和前缀
            if isinstance(file_path, str):
                # Windows路径处理
                file_path = file_path.lstrip("&").strip(string.whitespace + "'\"")
                # 处理tkinterdnd2返回的路径格式 {filepath}
                if file_path.startswith('{') and file_path.endswith('}'): 
                    file_path = file_path[1:-1]
            
            logger.debug(f"拖放文件路径: {file_path}")
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        with open(file_path, 'r', encoding='gbk') as f:
                            content = f.read()
                            
                    self.update_input_text_threaded(content)
                    self.set_status(f"文件读取成功: {file_path}")
                except Exception as e:
                    self.set_status(f"文件读取失败: {str(e)}")
                    logger.exception(f"文件读取失败: {str(e)}")
            else:
                self.set_status("文件不存在或不是有效文件")
        except Exception as e:
            self.set_status(f"导入失败: {str(e)}")
            logger.exception("文件拖放处理失败")
    
    def clear_placeholder(self, event):
        # 清除占位文本
        if self.input_text.get(1.0, tk.END).strip() == "粘贴文本或拖动文件到此处":
            self.input_text.delete(1.0, tk.END)
    
    def paste_from_clipboard(self):
        # 从剪贴板粘贴内容
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                self.update_input_text_threaded(clipboard_content)
                logger.info("成功从剪贴板获取内容")
            else:
                self.set_status("剪切板为空")
                logger.warning("剪贴板为空")
        except Exception as e:
            self.set_status("剪切板读取失败")
            logger.exception(f"剪切板读取失败: {str(e)}")
            messagebox.showerror("剪贴板错误", f"无法读取剪贴板: {str(e)}")
    
    def import_file(self):
        # 导入文件
        file_path = filedialog.askopenfilename(
            title="选择TTML文件",
            filetypes=[("TTML文件", "*.ttml"), ("XML文件", "*.xml"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # 尝试其他编码
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                
                self.update_input_text_threaded(content)
                logger.info(f"成功读取文件: {file_path}")
            except Exception as e:
                self.set_status("导入失败")
                logger.exception(f"文件导入失败: {file_path}")
                messagebox.showerror("导入错误", f"无法导入文件: {str(e)}")
    
    def copy_lyrics_to_clipboard(self):
        # 复制歌词内容到剪贴板
        try:
            output_content = self.output_text.get(1.0, tk.END).strip()
            if output_content:
                pyperclip.copy(output_content)
                self.set_status("歌词写入剪切板成功")
                logger.info("成功复制歌词内容到剪贴板")
            else:
                self.set_status("歌词内容为空，无法复制")
                logger.warning("歌词内容为空，无法复制到剪贴板")
        except Exception as e:
            self.set_status("写入剪切板失败")
            logger.exception(f"写入剪切板失败: {str(e)}")
            messagebox.showerror("剪贴板错误", f"无法写入剪贴板: {str(e)}")
    
    def copy_trans_to_clipboard(self):
        # 复制翻译内容到剪贴板
        try:
            trans_content = self.trans_text.get(1.0, tk.END).strip()
            if trans_content:
                pyperclip.copy(trans_content)
                self.set_status("翻译写入剪切板成功")
                logger.info("成功复制翻译内容到剪贴板")
            else:
                self.set_status("翻译内容为空，无法复制")
                logger.warning("翻译内容为空，无法复制到剪贴板")
        except Exception as e:
            self.set_status("写入剪切板失败")
            logger.exception(f"写入剪切板失败: {str(e)}")
            messagebox.showerror("剪贴板错误", f"无法写入剪贴板: {str(e)}")
    
    def convert_ttml(self):
        # 转换TTML到Lyricify Syllable
        ttml_content = self.input_text.get(1.0, tk.END).strip()
        
        if not ttml_content or ttml_content == "粘贴文本或拖动文件到此处":
            self.set_status("请先输入TTML内容")
            messagebox.showinfo("提示", "请先输入TTML内容")
            return
        
        # 禁用转换按钮，防止重复点击
        self.convert_btn.config(state=tk.DISABLED)
        
        # 显示转换中状态
        self.set_status("正在转换...")
        self.root.update()
        
        # 创建一个队列用于线程间通信
        result_queue = Queue()
        
        # 定义转换线程的工作函数
        def conversion_worker():
            try:
                success, lyric_text, trans_text = ttml_to_lyricify_syllable_text(ttml_content)
                # 将结果放入队列
                result_queue.put((success, lyric_text, trans_text))
            except Exception as e:
                # 发生异常时，将异常信息放入队列
                result_queue.put((False, None, None, str(e)))
        
        # 定义处理转换结果的函数
        def process_result():
            # 检查队列中是否有结果
            if not result_queue.empty():
                # 获取结果
                result = result_queue.get()
                
                # 检查是否有异常
                if len(result) == 4:
                    success, _, _, error_msg = result
                    self.set_status("转换失败，请检查TTML格式是否正确")
                    logger.exception(f"转换失败: {error_msg}")
                    messagebox.showerror("转换错误", f"转换过程中发生错误: {error_msg}")
                    
                    # 显示详细错误信息
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.insert(tk.END, f"转换错误: {error_msg}\n\n请检查TTML格式是否正确")
                    self.output_text.config(state=tk.DISABLED)
                else:
                    success, lyric_text, trans_text = result
                    
                    if success:
                        # 更新输出文本
                        self.output_text.config(state=tk.NORMAL)
                        self.output_text.delete(1.0, tk.END)
                        self.output_text.insert(tk.END, lyric_text)
                        self.output_text.config(state=tk.DISABLED)
                        
                        # 更新翻译文本
                        self.trans_text.config(state=tk.NORMAL)
                        self.trans_text.delete(1.0, tk.END)
                        if trans_text:
                            self.trans_text.insert(tk.END, trans_text)
                        self.trans_text.config(state=tk.DISABLED)
                        
                        # 更新按钮状态
                        self.copy_lyrics_btn.config(state=tk.NORMAL if lyric_text else tk.DISABLED)
                        self.copy_trans_btn.config(state=tk.NORMAL if trans_text else tk.DISABLED)
                        
                        # 更新状态
                        status_msg = "转换成功"
                        if TTMLLine.have_pair > 0:
                            status_msg += f"，移除了 {TTMLLine.have_pair} 处括号"
                        self.set_status(status_msg)
                    else:
                        self.set_status("转换失败，请检查TTML格式是否正确")
                
                # 重新启用转换按钮
                self.convert_btn.config(state=tk.NORMAL)
                return
            
            # 如果队列为空，继续等待结果
            self.root.after(100, process_result)
        
        # 启动转换线程
        conversion_thread = threading.Thread(target=conversion_worker)
        conversion_thread.daemon = True  # 设置为守护线程，随主线程退出而退出
        conversion_thread.start()
        
        # 开始检查结果
        self.root.after(100, process_result)
    
    def set_status(self, message):
        # 更新状态消息
        self.status_label.config(text=f"提示: {message}")
        logger.info(f"状态更新: {message}")
        
    def open_amll_search(self):
        # 打开AMLL DB搜索窗口
        logger.info("打开 AMLL DB 搜索工具")
        search_window = AMLLSearchWindow(self.root, self)
        search_window.grab_set()  # 模态窗口

    def update_input_text_threaded(self, content):
        """在独立线程中更新输入文本框的内容"""
        # 禁用相关按钮
        self.paste_btn.config(state=tk.DISABLED)
        self.import_btn.config(state=tk.DISABLED)
        self.convert_btn.config(state=tk.DISABLED)
        
        # 显示加载中状态
        self.set_status("正在加载文本...")
        self.root.update_idletasks()
        
        # 创建一个队列用于线程间通信
        content_queue = Queue()
        content_queue.put(content)
        
        # 定义更新文本的工作函数
        def update_worker():
            try:
                # 从队列获取内容
                text_content = content_queue.get()
                
                # 使用after方法在主线程中安全地更新UI
                self.root.after(0, lambda: self._update_text_ui(text_content))
            except Exception as e:
                logger.exception(f"文本更新失败: {str(e)}")
                # 使用after方法在主线程中安全地显示错误
                self.root.after(0, lambda: self._show_update_error(str(e)))
        
        # 启动更新线程
        update_thread = threading.Thread(target=update_worker)
        update_thread.daemon = True
        update_thread.start()
    
    def _update_text_ui(self, content):
        """在主线程中实际更新UI"""
        try:
            # 更新文本框
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(tk.END, content)
            
            # 重新启用按钮
            self.paste_btn.config(state=tk.NORMAL)
            self.import_btn.config(state=tk.NORMAL)
            self.convert_btn.config(state=tk.NORMAL)
            
            # 更新状态
            self.set_status("内容已加载")
        except Exception as e:
            logger.exception(f"UI更新失败: {str(e)}")
            self._show_update_error(str(e))
    
    def _show_update_error(self, error_msg):
        """显示更新错误"""
        # 重新启用按钮
        self.paste_btn.config(state=tk.NORMAL)
        self.import_btn.config(state=tk.NORMAL)
        self.convert_btn.config(state=tk.NORMAL)
        
        # 更新状态
        self.set_status("内容加载失败")
        messagebox.showerror("更新错误", f"无法更新文本内容: {error_msg}")

# AMLL DB搜索窗口类
class AMLLSearchWindow(tk.Toplevel):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.title("从 AMLL DB 搜索")
        self.geometry("500x320")
        self.configure(bg="#EEEEEE")
        self.resizable(False, False)  # 设置为固定大小窗口
        # 不再需要最小尺寸设置，因为窗口大小已固定
        
        # 保存主应用引用
        self.main_app = main_app
        
        # 搜索结果
        self.search_result = None
        
        # 获取主窗口的自动换行状态
        self.word_wrap_enabled = main_app.word_wrap_enabled
        
        # 创建界面
        self.create_widgets()
        
        # 同步主窗口的自动换行状态
        self.word_wrap_enabled.trace_add("write", lambda *args: self.toggle_word_wrap())
        
        # 居中显示
        self.center_window()
        
        logger.debug("AMLL DB 搜索窗口已初始化")
        
    def center_window(self):
        # 窗口居中显示
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左右分割
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧 - 平台选择
        ttk.Label(left_frame, text="平台").pack(anchor=tk.W, pady=(0, 5))
        
        # 平台下拉框
        self.platform_var = tk.StringVar(value="网易云")
        platform_frame = ttk.Frame(left_frame)
        platform_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.platform_combobox = ttk.Combobox(platform_frame, textvariable=self.platform_var, state="readonly")
        self.platform_combobox["values"] = ("网易云", "QQ音乐", "Apple Music", "Spotify")
        self.platform_combobox.pack(fill=tk.X)
        
        # 音乐ID输入
        ttk.Label(left_frame, text="音乐ID").pack(anchor=tk.W, pady=(0, 5))
        
        self.music_id_entry = ttk.Entry(left_frame)
        self.music_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 状态显示 - 设置固定高度和宽度，防止长文本影响布局
        status_frame = ttk.Frame(left_frame, height=60, width=200)
        status_frame.pack(fill=tk.X, anchor=tk.W, pady=(10, 0))
        status_frame.pack_propagate(False)  # 防止子组件改变框架大小
        
        self.status_label = ttk.Label(status_frame, text="", wraplength=180)  # 设置更小的文本宽度确保换行
        self.status_label.pack(anchor=tk.W, fill=tk.BOTH, expand=True)
        
        # 右侧 - 搜索结果预览（设置为310*190像素）
        ttk.Label(right_frame, text="搜索结果预览").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建一个框架来控制文本框的大小
        result_frame = ttk.Frame(right_frame, width=310, height=190)
        result_frame.pack(fill=tk.BOTH, expand=True)
        result_frame.pack_propagate(False)  # 防止子组件改变框架大小
        
        # 创建文本框
        self.result_text = tk.Text(result_frame, wrap=tk.NONE, bg="#DDDDDD", fg="#111111", state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 自动换行复选框
        self.word_wrap_checkbox = ttk.Checkbutton(right_frame, text="自动换行", variable=self.word_wrap_enabled)
        self.word_wrap_checkbox.pack(anchor=tk.W, pady=(5, 0))
        
        # 底部按钮框架 - 增加高度
        bottom_frame = ttk.Frame(self, height=40)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        bottom_frame.pack_propagate(False)  # 防止子组件改变框架大小
        
        # 左侧按钮
        left_buttons_frame = ttk.Frame(bottom_frame)
        left_buttons_frame.pack(side=tk.LEFT)
        
        self.cancel_btn = ttk.Button(left_buttons_frame, text="取消", command=self.destroy)
        self.cancel_btn.pack(side=tk.LEFT)
        
        # 右侧按钮
        right_buttons_frame = ttk.Frame(bottom_frame)
        right_buttons_frame.pack(side=tk.RIGHT)
        
        self.search_btn = ttk.Button(right_buttons_frame, text="搜索", command=self.search)
        self.search_btn.pack(side=tk.RIGHT)
        
        self.copy_btn = ttk.Button(right_buttons_frame, text="复制", command=self.copy_result, state=tk.DISABLED)
        self.copy_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        self.import_btn = ttk.Button(right_buttons_frame, text="导入", command=self.import_result, state=tk.DISABLED)
        self.import_btn.pack(side=tk.RIGHT, padx=(0, 5))
    
    def toggle_word_wrap(self):
        """切换文本框的自动换行状态"""
        wrap_mode = tk.WORD if self.word_wrap_enabled.get() else tk.NONE
        self.result_text.configure(wrap=wrap_mode)
    
    def set_status(self, message):
        # 更新状态消息
        self.status_label.config(text=message)
        logger.info(f"AMLL搜索状态更新: {message}")
    
    def search(self):
        # 获取平台和音乐ID
        platform = self.platform_var.get()
        music_id = self.music_id_entry.get().strip()
        
        # 验证输入
        if not music_id:
            self.set_status("请输入音乐ID")
            messagebox.showinfo("提示", "请输入音乐ID")
            return
        
        # 平台代码映射
        platform_code = {
            "网易云": "ncm",
            "QQ音乐": "qq",
            "Apple Music": "am",
            "Spotify": "spotify"
        }.get(platform)
        
        if not platform_code:
            self.set_status("不支持的平台")
            return
        
        # 构建URL
        url = f"https://amll-ttml-db.stevexmh.net/{platform_code}/{music_id}"
        
        # 禁用搜索按钮，防止重复点击
        self.search_btn.config(state=tk.DISABLED)
        
        # 显示搜索中状态
        self.set_status("正在搜索...")
        self.update_idletasks()
        
        # 创建一个队列用于线程间通信
        result_queue = Queue()
        
        # 定义搜索线程的工作函数
        def search_worker():
            try:
                # 发送请求
                response = requests.get(url, timeout=10)
                
                # 将结果放入队列
                result_queue.put(("success", response))
            except Exception as e:
                # 发生异常时，将异常信息放入队列
                result_queue.put(("error", str(e)))
        
        # 定义处理搜索结果的函数
        def process_result():
            # 检查队列中是否有结果
            if not result_queue.empty():
                # 获取结果
                result_type, result_data = result_queue.get()
                
                if result_type == "success":
                    # 搜索成功
                    response = result_data
                    
                    # 检查响应
                    if response.status_code == 200:
                        # 保存搜索结果
                        self.search_result = response.text
                        
                        # 更新预览
                        self.result_text.config(state=tk.NORMAL)
                        self.result_text.delete(1.0, tk.END)
                        self.result_text.insert(tk.END, self.search_result)
                        self.result_text.config(state=tk.DISABLED)
                        
                        # 启用按钮
                        self.import_btn.config(state=tk.NORMAL)
                        self.copy_btn.config(state=tk.NORMAL)
                        
                        self.set_status("搜索成功!")
                    else:
                        self.set_status(f"搜索失败: HTTP {response.status_code}")
                        self.result_text.config(state=tk.NORMAL)
                        self.result_text.delete(1.0, tk.END)
                        self.result_text.insert(tk.END, f"搜索失败: HTTP {response.status_code}\n\n可能的原因:\n- 歌曲ID不存在\n- 该平台未收录此歌曲\n- 服务器暂时不可用")
                        self.result_text.config(state=tk.DISABLED)
                        
                        # 禁用按钮
                        self.import_btn.config(state=tk.DISABLED)
                        self.copy_btn.config(state=tk.DISABLED)
                else:
                    # 发生异常
                    error_msg = result_data
                    # 统一错误提示信息
                    error_tip = "搜索出错: 请检查网络或尝试使用VPN或代理"
                    self.set_status(error_tip)
                    
                    logger.exception(f"AMLL搜索出错: {error_msg}")
                    
                    self.result_text.config(state=tk.NORMAL)
                    self.result_text.delete(1.0, tk.END)
                    # 统一网络错误提示
                    if "Connection" in error_msg or "远程主机" in error_msg or "timeout" in error_msg or "refused" in error_msg:
                        self.result_text.insert(tk.END, "搜索错误：请检查网络或尝试使用VPN或代理\n\n")
                    else:
                        self.result_text.insert(tk.END, f"搜索出错: {error_msg}\n\n请检查网络或尝试使用VPN或代理\n\n")
                    
                    # 添加完整错误信息
                    self.result_text.insert(tk.END, f"完整错误信息:\n{error_msg}")
                    self.result_text.config(state=tk.DISABLED)
                    
                    # 禁用导入按钮但启用复制按钮（方便复制错误信息）
                    self.import_btn.config(state=tk.DISABLED)
                    self.copy_btn.config(state=tk.NORMAL)
                
                # 重新启用搜索按钮
                self.search_btn.config(state=tk.NORMAL)
                return
            
            # 如果队列为空，继续等待结果
            self.after(100, process_result)
        
        # 启动搜索线程
        search_thread = threading.Thread(target=search_worker)
        search_thread.daemon = True  # 设置为守护线程，随主线程退出而退出
        search_thread.start()
        
        # 开始检查结果
        self.after(100, process_result)
    
    def import_result(self):
        # 导入搜索结果到主窗口
        if self.search_result:
            self.main_app.update_input_text_threaded(self.search_result)
            self.main_app.set_status("已从AMLL DB导入TTML内容")
            self.destroy()
    
    def copy_result(self):
        # 复制搜索结果到剪贴板
        if self.search_result:
            try:
                pyperclip.copy(self.search_result)
                self.set_status("已复制到剪贴板")
            except Exception as e:
                self.set_status(f"复制失败: {str(e)}")
                logger.exception(f"复制到剪贴板失败: {str(e)}")

# 主函数
def main():
    # 根据是否成功导入tkinterdnd2创建根窗口
    if HAS_DND:
        root = TkinterDnD.Tk()
        logger.info("使用TkinterDnD创建窗口，拖放功能已启用")
    else:
        root = tk.Tk()
        logger.warning("使用普通Tk创建窗口，拖放功能不可用")
    
    # 创建应用
    app = TTMLToLyricifySyllableApp(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    # 设置版本信息
    VERSION = "v1.2.2"
    print(f"TTML转Lyricify Syllable工具 {VERSION} - GUI版本")
    print("基于 TTML_to_Lyricify_Syllable_Tool 开发")
    print("项目地址：https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool")
    
    # 启动应用
    main()
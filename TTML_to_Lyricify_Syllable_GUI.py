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

from pip import main as pip_main

# 确保必要的库已安装
try:
    import loguru
except ImportError:
    print("正在安装loguru...")
    pip_main(['install', 'loguru'])
    import loguru

finally:
    from loguru import logger

# 确保pyperclip已安装
try:
    import pyperclip
except ImportError:
    print("正在安装pyperclip...")
    pip_main(['install', 'pyperclip'])
    import pyperclip

# 尝试导入tkinterdnd2用于拖放功能
try:
    import tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    try:
        print("正在安装tkinterdnd2...")
        pip_main(['install', 'tkinterdnd2'])
        import tkinterdnd2
        from tkinterdnd2 import DND_FILES, TkinterDnD
        HAS_DND = True
    except:
        HAS_DND = False
        print("无法安装tkinterdnd2，拖放功能将不可用")
        # 定义一个全局变量，以便在类中使用
        DND_FILES = "*"

from datetime import datetime

# 日志文件夹路径
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(log_dir, exist_ok=True)  # 确保日志文件夹存在

# 设置日志记录
def setup_logger(enabled=False):
    if enabled:
        logger.add(os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d %H.%M.%S')}.log"), level='DEBUG')
        logger.info("日志记录已启用")
        return True
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
        agent = element.getAttribute("ttm:agent")
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

        self.__begin = self.__orig_line[0].get_begin()

        if is_bg:
            if TTMLLine.__before.search(self.__orig_line[0].text):
                self.__orig_line[0].text = TTMLLine.__before.sub(self.__orig_line[0].text, '(')
                TTMLLine.have_pair += 1
            if TTMLLine.__after.search(self.__orig_line[-1].text):
                self.__orig_line[-1].text = TTMLLine.__after.sub(self.__orig_line[-1].text, ')')
                TTMLLine.have_pair += 1

    def __role(self) -> int:
        return ((int(TTMLLine.have_bg) + int(self.__is_bg)) * 3
                + int(TTMLLine.have_duet) + int(self.__is_duet))

    def __raw(self) -> tuple[str, str|None]:
        return (f'[{self.__role()}]'+''.join([str(v) for v in self.__orig_line]),
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
        self.root.configure(bg="#333333")
        self.root.minsize(600, 400)  # 设置最小窗口大小
        
        # 设置图标（如果有）
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico"))
        except:
            pass
        
        # 日志启用状态
        self.log_enabled = tk.BooleanVar(value=False)
        
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
        
    def setup_styles(self):
        # 设置ttk样式
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#333333")
        style.configure("TLabel", background="#333333", foreground="#FFFFFF")
        style.configure("TCheckbutton", background="#333333", foreground="#FFFFFF")
        style.configure("TPanedwindow", background="#333333")
        style.configure("TFrame", background="#333333")
        
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
        
        self.input_text = tk.Text(left_frame, wrap=tk.WORD, bg="#1E1E1E", fg="#FFFFFF", insertbackground="white")
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_text.insert(tk.END, "粘贴文本或拖动文件到此处")
        self.input_text.bind("<FocusIn>", self.clear_placeholder)
        
        # 右侧标签和文本框
        ttk.Label(right_frame, text="Lyricify Syllable输出").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建右侧垂直分割窗口
        right_pane = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_pane.pack(fill=tk.BOTH, expand=True)
        
        # 歌词输出框
        self.output_text = tk.Text(right_pane, wrap=tk.WORD, bg="#1E1E1E", fg="#FFFFFF", state=tk.DISABLED, height=10)
        right_pane.add(self.output_text, weight=1)
        
        # 翻译输出框
        ttk.Label(right_frame, text="翻译输出").pack(anchor=tk.W, pady=(10, 5))
        self.trans_text = tk.Text(right_pane, wrap=tk.WORD, bg="#1E1E1E", fg="#FFFFFF", state=tk.DISABLED, height=10)
        right_pane.add(self.trans_text, weight=1)
        
        # 底部按钮框架
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 左侧按钮
        left_buttons_frame = ttk.Frame(bottom_frame)
        left_buttons_frame.pack(side=tk.LEFT)
        
        self.paste_btn = ttk.Button(left_buttons_frame, text="粘贴", command=self.paste_from_clipboard)
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.import_btn = ttk.Button(left_buttons_frame, text="导入", command=self.import_file)
        self.import_btn.pack(side=tk.LEFT)
        
        # 右侧按钮
        right_buttons_frame = ttk.Frame(bottom_frame)
        right_buttons_frame.pack(side=tk.RIGHT)
        
        self.copy_lyrics_btn = ttk.Button(right_buttons_frame, text="复制歌词", command=self.copy_lyrics_to_clipboard, state=tk.DISABLED)
        self.copy_lyrics_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.copy_trans_btn = ttk.Button(right_buttons_frame, text="复制翻译", command=self.copy_trans_to_clipboard, state=tk.DISABLED)
        self.copy_trans_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.convert_btn = ttk.Button(right_buttons_frame, text="转换", command=self.convert_ttml)
        self.convert_btn.pack(side=tk.RIGHT)
        
        # 状态框架
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="")
        self.status_label.pack(side=tk.LEFT)
        
        # 日志复选框
        self.log_checkbox = ttk.Checkbutton(status_frame, text="启用日志记录", variable=self.log_enabled)
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
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # 尝试其他编码
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                        
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(tk.END, content)
                self.set_status(f"文件导入成功: {file_path}")
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
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(tk.END, clipboard_content)
                self.set_status("剪切板读取成功")
                logger.info("成功从剪贴板粘贴内容")
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
                
                self.input_text.delete(1.0, tk.END)
                self.input_text.insert(tk.END, content)
                self.set_status("导入成功")
                logger.info(f"成功导入文件: {file_path}")
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
        
        # 启用日志（如果选中）
        if self.log_enabled.get():
            setup_logger(True)
        
        # 执行转换
        try:
            # 显示转换中状态
            self.set_status("正在转换...")
            self.root.update()
            
            success, lyric_text, trans_text = ttml_to_lyricify_syllable_text(ttml_content)
            
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
                
                # 自动复制歌词到剪贴板
                try:
                    pyperclip.copy(lyric_text)
                    self.set_status(status_msg + "，已自动复制歌词到剪贴板")
                except:
                    pass  # 忽略剪贴板错误
            else:
                self.set_status("转换失败，请检查TTML格式是否正确")
                messagebox.showerror("转换失败", "无法解析TTML内容，请检查格式是否正确")
        except Exception as e:
            self.set_status("转换失败，请检查TTML格式是否正确")
            logger.exception(f"转换失败: {str(e)}")
            messagebox.showerror("转换错误", f"转换过程中发生错误: {str(e)}")
            
            # 显示详细错误信息
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"转换错误: {str(e)}\n\n请检查TTML格式是否正确")
            self.output_text.config(state=tk.DISABLED)
    
    def set_status(self, message):
        # 更新状态消息
        self.status_label.config(text=f"提示: {message}")
        logger.info(f"状态更新: {message}")

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
    VERSION = "v1.0.0"
    print(f"TTML转Lyricify Syllable工具 {VERSION} - GUI版本")
    print("基于 TTML_to_Lyricify_Syllable_Tool 开发")
    print("项目地址：https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool")
    
    # 启动应用
    main()
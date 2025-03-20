import os
from re import compile, Pattern, Match
import string
import sys
import xml
from typing import Iterator, TextIO
from xml.dom.minidom import Document, Element

from pip import main as pip_main

try:
    import loguru
except ImportError:
    pip_main(['install', 'loguru'])
    import loguru

finally:
    from loguru import logger

from datetime import datetime

# 日志文件夹路径
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')

# 读取 log.set 文件并检查是否启用日志
log_set_file = os.path.join(log_dir, 'log.set')

def is_logging_enabled():
    """检查 log.set 文件中是否有 'log_on:true'（不区分大小写）"""
    if os.path.exists(log_set_file):
        with open(log_set_file, 'r') as f:
            for line in f:
                # 判断是否包含 'log_on:true'（不区分大小写）
                if 'log_on:true' in line.strip().lower():
                    return True
    return False

if is_logging_enabled():
    print(f"已启用日志记录，输出目录为 软件目录/log")
    logger.add(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log',f"{datetime.now().strftime('%Y-%m-%d %H.%M.%S')}.log"),level='DEBUG')

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

class TTMLLine:
    have_ts: bool = False
    have_duet: bool = False
    have_bg: int = 0

    def __init__(self, element: Element, is_bg: bool = False):
        self.__element: Element = element
        self.__orig_line: list[TTMLSyl|str] = []
        self.__ts_line: str|None = None
        self.__bg_line: TTMLLine|None = None
        self.__is_bg: bool = is_bg

        # 获取传入元素的 begin 属性
        self.__begin:TTMLTime = TTMLTime(element.getAttribute("begin"))
        self.__is_duet:bool = bool(element.getAttribute("ttm:agent"))

        # 获取 <p> 元素的所有子节点，包括文本节点
        child_elements:list[Element] = element.childNodes  # iter() 会返回所有子元素和文本节点

        # 遍历所有子元素
        for child in child_elements:
            if child.nodeType == 3 and child.nodeValue:  # 如果是文本节点（例如空格或换行）
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
                elif role == "x-translation":
                    # 翻译行
                    TTMLLine.have_ts = True
                    self.__ts_line = f'{child.childNodes[0].data}'

        if is_bg:
            TTMLLine.have_bg += 1
            self.__orig_line[0].text = self.__orig_line[0].text[1:]
            self.__orig_line[-1].text = self.__orig_line[-1].text[:-1]

    def __role(self) -> int:
        return ((int(TTMLLine.have_bg != 0) + int(self.__bg_line is not None)) * 3
                + int(TTMLLine.have_duet) + int(self.__is_duet))

    def __raw(self) -> tuple[str, str|None]:
        return (f'[{self.__role()}]'+''.join([str(v) for v in self.__orig_line]),
                f'[{self.__begin}]{self.__ts_line}' if self.__ts_line else None)

    def to_str(self) -> tuple[tuple[str, str|None],tuple[str, str|None]|None]:
        return self.__raw(), (self.__bg_line.__raw() if self.__bg_line else None)

def ttml_to_lys(input_path):
    """主转换函数"""
    TTMLLine.have_duet = False
    TTMLLine.have_bg = 0
    TTMLLine.have_ts = False

    try:
        # 解析XML文件
        dom = xml.dom.minidom.parse(input_path)  # 假设文件名是 'books.xml'
        tt: Document = dom.documentElement  # 获取根元素

        # 获取tt中的body/head元素
        body = tt.getElementsByTagName('body')[0]
        head = tt.getElementsByTagName('head')[0]

        if body and head:
            # 获取body/head中的<div>/<metadata>子元素
            div = body.getElementsByTagName('div')[0]
            metadata = head.getElementsByTagName('metadata')[0]

            # 获取div中的所有<p>子元素
            p_elements = div.getElementsByTagName('p')
            meta_elements = metadata.getElementsByTagName('amll:meta')

            # 检查是否有对唱
            for meta in meta_elements:
                if meta.getAttribute('xml:id') != 'v1':
                    TTMLLine.have_duet = True

            lines: list[TTMLLine] = []
            # 遍历每个<p>元素
            for p in p_elements:
                lines.append(TTMLLine(p))

                # 打印行
                logger.info(f"TTML第{p_elements.index(p)}行内容：{lines[-1].to_str()[0][0]}")

            # 获取当前.py文件的目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # 创建output目录（如果不存在的话）
            output_dir = os.path.join(script_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)  # 确保目录存在

            # 修改路径
            base_name = os.path.splitext(input_path)[0]

            lyric_file: TextIO|None = None
            trans_file: TextIO|None = None

            lyric_path = os.path.join(output_dir, f"{os.path.basename(base_name)}.lys")
            lyric_file = open(lyric_path, 'w')

            if TTMLLine.have_ts:
                trans_path = os.path.join(output_dir, f"{os.path.basename(base_name)}_trans.lrc")
                trans_file = open(trans_path, 'w')

            count: int = 0

            for main_line, bg_line in [line.to_str() for line in lines]:
                lyric_file.write(main_line[0] + '\n')
                lyric_file.flush()
                if main_line[1]:
                    trans_file.write(main_line[1] + '\n')
                    trans_file.flush()

                if bg_line:
                    lyric_file.write(bg_line[0] + '\n')
                    lyric_file.flush()
                    if bg_line[1]:
                        trans_file.write(bg_line[1] + '\n')
                        trans_file.flush()
                    count += 1

        else:
            logger.exception("错误: 找不到<body>元素")

    except Exception as e:
        logger.exception(f"无法解析TTML文件: {input_path}")
        return False, None, None
            
    return True, lyric_path, trans_path

def step(argv_h):
    if len(sys.argv) != 2 or argv_h == True: #如果第一次是图标输入，此后只能窗口输入
        input_path = input("\n请将TTML文件拖放到此窗口上或输入文件路径，按回车键进行转换\n文件路径: ")
        logger.info(f"==========================")
        logger.debug(f"窗口输入")
        logger.debug(f"图标输入历史: {argv_h}")
        logger.debug(f"len(sys.argv): {len(sys.argv)}")
    else:
        input_path = sys.argv[1]
        argv_h = True
        logger.info(f"==========================")
        logger.debug(f"图标输入")
        logger.debug(f"图标输入历史: {argv_h}")
        logger.debug(f"len(sys.argv): {len(sys.argv)}")
        
    logger.debug(f"用户输入: \"{input_path}\"")

    if input_path.startswith("&"):
        logger.debug(f"检测到 VS Code & PowerShell 受害者，尝试修复路径")
    else:
        logger.debug(f"未检测到 VS Code & PowerShell 受害者迹象，仍然尝试修复路径")
    input_path = input_path.lstrip("&").strip(string.whitespace + "'\"")

    logger.debug(f"接收到文件: \"{input_path}\"")

    if not os.path.exists(input_path):
        logger.error(f"文件不存在: \"{input_path}\"")
        print("\033[91m文件不存在！请重试\033[0m")
        step(argv_h)

    success, lyric_path, trans_path = ttml_to_lys(input_path)
    if success:
        print(f"\n================================\n\033[93m转换成功！\033[0m\n\033[94m输出文件: \033[0m\"{lyric_path}\"")
        if TTMLLine.have_ts:
            print(f"\033[94m翻译文件: \033[0m\"{trans_path}\"")
        if TTMLLine.have_bg:
            print(f"处理文件时移除了 {TTMLLine.have_bg} 对括号")
            print(f"无须担心，移除的括号只是 TTML 中用于兼容的括号，你并不需要")
        print(f"================================\n")
    else:
        print(f"\033[91m转换失败: {input_path}\033[0m")

    # 传回argv_h信息，保证后续只能窗口输入
    input_path = ""
    step(argv_h)


if __name__ == '__main__':
    argv = False
    step(argv)

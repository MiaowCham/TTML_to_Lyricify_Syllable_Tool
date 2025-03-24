import os
import re
import string
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime

from pip import main as pip_main

# install loguru and import
try:
    import loguru
except ImportError:
    pip_main(['install', 'loguru'])
    import loguru

finally:
    from loguru import logger

namespaces = {
    'tt': 'http://www.w3.org/ns/ttml',
    'ttm': 'http://www.w3.org/ns/ttml#metadata',
    'amll': 'http://www.example.com/ns/amll',
    'itunes': 'http://music.apple.com/lyric-ttml-internal'
}

# def logger.info(message, level='INFO'):
#     """记录日志到当天的日志文件"""
#     log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
#     os.makedirs(log_dir, exist_ok=True)
#     log_file = os.path.join(log_dir, f"{date.today().isoformat()}.log")
#     timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     log_line = f"[{timestamp}] [{level}] {message}\n"

#     try:
#         with open(log_file, 'a', encoding='utf-8') as f:
#             f.write(log_line)
#     except Exception as e:
#         print(f"无法写入日志文件: {e}")

# add logger to create dir and write log to specific file
logger.add(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log',
                        f"{datetime.now().strftime('%Y-%m-%d')}.log"),
           level='DEBUG')


def preprocess_ttml(content):
    """预处理TTML内容，移除xmlns=""声明"""
    # 使用正则表达式精确匹配 xmlns=""
    pattern = re.compile(r'\s+xmlns=""')
    modified = False

    # 查找所有匹配项
    matches = pattern.findall(content)
    if matches:
        modified = True
        # 移除所有匹配的xmlns声明
        content = pattern.sub('', content)
        logger.info(f"发现并移除了 {len(matches)} 处xmlns=\"\"声明")

    return content, modified


def parse_time(time_str):
    """将时间字符串转换为毫秒"""
    try:
        parts = time_str.replace(',', '.').split(':')
        if len(parts) == 3:  # hh:mm:ss.ms
            h, m, rest = parts
            s, ms = rest.split('.') if '.' in rest else (rest, 0)
        elif len(parts) == 2:  # mm:ss.ms
            m, rest = parts
            h = 0
            s, ms = rest.split('.') if '.' in rest else (rest, 0)
        else:  # ss.ms
            h, m = 0, 0
            s, ms = parts[0].split('.') if '.' in parts[0] else (parts[0], 0)

        return (int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 +
                int(str(ms).ljust(3, '0')[:3]))
    except Exception as e:
        logger.error(f"时间解析错误: {time_str} - {str(e)}")
        return 0


def format_lrc_time(millis):
    """将毫秒转换为LRC时间格式 (mm:ss.xx)"""
    millis = max(0, millis)
    m = millis // 60000
    s = (millis % 60000) // 1000
    ms = millis % 1000
    return f"{m:02d}:{s:02d}.{ms:03d}"


def calculate_property(alignment, background):
    """计算LYS属性值"""
    if background:
        return {None: 6, 'left': 7, 'right': 8}.get(alignment, 6)
    else:
        return {None: 3, 'left': 4, 'right': 5}.get(alignment, 3)


def process_segment(spans, alignment, is_background):
    """处理歌词段生成LYS行（最终空格修复版）"""
    parts = []
    pending_whitespace = ''  # 跟踪待处理的空白字符

    for span in spans:
        try:
            begin = span.get('begin')
            end = span.get('end')
            if not begin or not end:
                continue

            start = parse_time(begin)
            duration = parse_time(end) - start
            if duration <= 0:
                continue

            # 合并前导空白和当前文本
            full_text = pending_whitespace + (span.text or '')

            # 分离文本和尾部空白
            clean_text = full_text.rstrip(' ')  # 移除末尾空格但保留其他字符
            trailing_spaces = len(full_text) - len(clean_text)

            # 处理span的尾部内容
            tail = span.tail or ''
            tail_clean = tail.lstrip(' ')  # 移除头部空格
            leading_spaces = len(tail) - len(tail_clean)

            # 合并空格到前一个单词
            word = clean_text
            if trailing_spaces > 0 or leading_spaces > 0:
                word += ' ' * (trailing_spaces + leading_spaces)

            # 生成时间标记
            if word:
                parts.append(f"{word}({start},{duration})")

            # 更新待处理空白
            pending_whitespace = tail_clean if not tail_clean.strip() else ''

        except Exception as e:
            logger.warning(f"处理span失败: {str(e)}")

    # 处理最后一个单词后的空白
    if pending_whitespace.strip():
        parts.append(f"{pending_whitespace}(0,0)")

    if not parts:
        return None

    prop = calculate_property(alignment, is_background)
    return f"[{prop}]" + "".join(parts)


def process_translations(p_element):
    """处理翻译内容"""
    translations = []
    for elem in p_element.iter():
        if elem.tag == f'{{{namespaces["tt"]}}}span':
            role = elem.get(f'{{{namespaces["ttm"]}}}role')
            if role == 'x-translation':
                text = (elem.text or '').strip()
                if text:
                    translations.append(text)
    return ' '.join(translations)


def ttml_to_lys(input_path):
    """主转换函数"""
    try:
        # 读取文件内容并预处理
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # 预处理移除xmlns=""声明
        processed_content, modified = preprocess_ttml(raw_content)
        if modified:
            logger.info(f"处理文件 {input_path} 时移除了xmlns=\"\"声明")

        # 解析XML
        root = ET.fromstring(processed_content)

    except Exception as e:
        logger.exception(f"无法解析TTML文件: {input_path}")
        return False, False

    lys_lines = []
    lrc_entries = []
    has_translations = False

    # 处理歌词行
    try:
        for p in root.findall('.//tt:p', namespaces):
            try:
                # 获取基础信息
                alignment = None
                agent = p.get(f'{{{namespaces["ttm"]}}}agent')
                if agent == 'v1':
                    alignment = 'left'
                elif agent == 'v2':
                    alignment = 'right'

                logger.debug(f"开始处理Agent: {agent=}")

                # 处理翻译
                translation = process_translations(p)
                if translation:
                    has_translations = True
                    logger.debug(f"开始处理翻译: {translation=}")

                # 获取时间信息
                p_begin = p.get('begin')
                lrc_time = format_lrc_time(parse_time(p_begin))
                lrc_entries.append((lrc_time, translation))
                logger.debug(f"开始处理行: {lrc_time=} (p[begin={p_begin}])")

                # 分离主歌词和背景人声
                main_spans = []
                bg_spans = []
                current_bg = False

                for elem in p:
                    if elem.tag == f'{{{namespaces["tt"]}}}span':
                        role = elem.get(f'{{{namespaces["ttm"]}}}role')
                        if role == 'x-bg':
                            bg_spans.extend(
                                elem.findall('.//tt:span', namespaces))
                            current_bg = True
                        else:
                            if current_bg:
                                bg_spans.append(elem)
                            else:
                                main_spans.append(elem)
                    else:
                        current_bg = False

                # 处理主歌词行
                if main_spans:
                    main_line = process_segment(main_spans, alignment, False)
                    if main_line:
                        lys_lines.append(main_line)

                # 处理背景人声行
                if bg_spans:
                    bg_line = process_segment(bg_spans, alignment, True)
                    if bg_line:
                        lys_lines.append(bg_line)

            except Exception as e:
                # logger.warning(f"处理歌词行失败: {str(e)}")
                logger.exception(f"处理歌词行失败")

    except Exception as e:
        logger.exception(f"解析歌词失败")
        return False, False

    # 写入LYS文件
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}.lys"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lys_lines))
        logger.info(f"成功生成LYS文件: {output_path}")
    except Exception as e:
        logger.exception(f"写入LYS文件失败")
        return False, False

    # 写入LRC文件
    lrc_generated = False
    if has_translations:
        lrc_path = f"{base_name}_trans.lrc"
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                for time_str, text in lrc_entries:
                    f.write(f"[{time_str}]{text}\n")
            logger.info(f"成功生成翻译文件: {lrc_path}")
            lrc_generated = True
        except Exception as e:
            logger.exception(f"写入LRC文件失败")

    return True, lrc_generated


if __name__ == '__main__':
    if len(sys.argv) != 2:
        input_path = input("\n请将TTML文件拖放到此窗口上，然后按回车键...")
    else:
        input_path = sys.argv[1]

    logger.debug(f"用户输入: {input_path}")

    if input_path.startswith("&"):
        logger.debug(f"检测到 VS Code & PowerShell 受害者，尝试修复路径")
    else:
        logger.debug(f"未检测到 VS Code & PowerShell 受害者迹象，仍然尝试修复路径")
    input_path = input_path.lstrip("&").strip(string.whitespace + "'\"")

    logger.debug(f"接收到文件: {input_path}")

    if not os.path.exists(input_path):
        logger.error(f"文件不存在: {input_path}")
        input("文件不存在，按回车键退出...")
        sys.exit(1)

    success, lrc_generated = ttml_to_lys(input_path)
    if success:
        msg = f"转换成功: {input_path}"
        if lrc_generated:
            msg += " (包含翻译)"
        print(msg)
    else:
        print(f"转换失败: {input_path}")

    input("按回车键退出...")
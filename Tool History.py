import sys
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, date

namespaces = {
    'tt': 'http://www.w3.org/ns/ttml',
    'ttm': 'http://www.w3.org/ns/ttml#metadata',
    'amll': 'http://www.example.com/ns/amll',
    'itunes': 'http://music.apple.com/lyric-ttml-internal'
}

def log_message(message, level='INFO'):
    """记录日志到当天的日志文件"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{date.today().isoformat()}.log")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
    except Exception as e:
        print(f"无法写入日志文件: {e}")

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
        log_message(f"发现并移除了 {len(matches)} 处xmlns=\"\"声明")
    
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
        
        return (int(h)*3600000 + int(m)*60000 + 
                int()*1000 + int(ms.ljust(3, '0')[:3]))
    except Exception as e:
        log_message(f"时间解析错误: {time_str} - {str(e)}", 'ERROR')
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
        return {None:6, 'left':7, 'right':8}.get(alignment, 6)
    else:
        return {None:3, 'left':4, 'right':5}.get(alignment, 3)

def process_segment(spans, alignment, is_background):
    """处理歌词段生成LYS行（已修复空格问题）"""
    parts = []
    pending_space = ''  # 跟踪待处理空格
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
            
            # 合并前导空格和当前文本
            raw_text = pending_space + (span.text or '')
            text = raw_text.strip()
            if not text:
                # 处理纯空格span的情况
                if raw_text:
                    pending_space = raw_text
                continue
            
            # 处理尾部内容
            tail = span.tail or ''
            space_segment = ''
            non_space = ''
            
            # 分离空格和非空格内容
            for i, c in enumerate(tail):
                if c.isspace():
                    space_segment += c
                else:
                    non_space = tail[i:]
                    break
            
            # 空格附加到当前单词，非空格保留到pending
            text += space_segment
            pending_space = non_space if non_space else ''
            
            parts.append(f"{text}({start},{duration})")
        
        except Exception as e:
            log_message(f"处理span失败: {str(e)}", 'WARNING')
    
    # 处理最后一个span后的未消耗内容
    if pending_space.strip():
        parts.append(f"{pending_space}(0,0)")
    
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
            print("已发现并删除了xmlns=\"\"声明")
            log_message(f"处理文件 {input_path} 时移除了xmlns=\"\"声明")
        
        # 解析XML
        root = ET.fromstring(processed_content)
    
    except Exception as e:
        log_message(f"无法解析TTML文件: {input_path} - {str(e)}", 'ERROR')
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

                # 处理翻译
                translation = process_translations(p)
                if translation:
                    has_translations = True
                    log_message(f"开始处理翻译: {input_path}")
                
                # 获取时间信息
                p_begin = p.get('begin')
                lrc_time = format_lrc_time(parse_time(p_begin))
                lrc_entries.append((lrc_time, translation))

                # 分离主歌词和背景人声
                main_spans = []
                bg_spans = []
                current_bg = False

                for elem in p:
                    if elem.tag == f'{{{namespaces["tt"]}}}span':
                        role = elem.get(f'{{{namespaces["ttm"]}}}role')
                        if role == 'x-bg':
                            bg_spans.extend(elem.findall('.//tt:span', namespaces))
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
                log_message(f"处理歌词行失败: {str(e)}", 'WARNING')

    except Exception as e:
        log_message(f"解析歌词失败: {str(e)}", 'ERROR')
        return False, False

    # 写入LYS文件
    base_name = os.path.splitext(input_path)[0]
    output_path = f"{base_name}.lys"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lys_lines))
        log_message(f"成功生成LYS文件: {output_path}")
    except Exception as e:
        log_message(f"写入LYS文件失败: {str(e)}", 'ERROR')
        return False, False

    # 写入LRC文件
    lrc_generated = False
    if has_translations:
        lrc_path = f"{base_name}_trans.lrc"
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                for time_str, text in lrc_entries:
                    f.write(f"[{time_str}]{text}\n")
            log_message(f"成功生成翻译文件: {lrc_path}")
            lrc_generated = True
        except Exception as e:
            log_message(f"写入LRC文件失败: {str(e)}", 'WARNING')

    return True, lrc_generated

if __name__ == '__main__':
    if len(sys.argv) != 2:
        input("\n请将TTML文件拖放到此程序上，然后按回车键...")
    else:
        input_path = sys.argv[1]
        log_message(f"=======================")
        log_message(f"开始处理文件: {input_path}")
        
        if not os.path.exists(input_path):
            log_message(f"文件不存在: {input_path}", 'ERROR')
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

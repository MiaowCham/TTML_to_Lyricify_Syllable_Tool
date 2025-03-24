import sys
import os
import xml.etree.ElementTree as ET

namespaces = {
    'tt': 'http://www.w3.org/ns/ttml',
    'ttm': 'http://www.w3.org/ns/ttml#metadata',
    'amll': 'http://www.example.com/ns/amll',
    'itunes': 'http://music.apple.com/lyric-ttml-internal'
}

def parse_time(time_str):
    """将时间字符串转换为毫秒"""
    parts = time_str.split(':')
    hours, minutes, rest = 0, 0, ''
    
    if len(parts) == 3:
        hours, minutes, rest = parts
    elif len(parts) == 2:
        minutes, rest = parts
    else:
        rest = parts[0]
    
    rest_parts = rest.split('.')
    seconds = rest_parts[0]
    millis = rest_parts[1] if len(rest_parts) > 1 else 0
    
    return (int(hours) * 3600000 + 
            int(minutes) * 60000 + 
            int(seconds) * 1000 + 
            int(millis.ljust(3, '0')[:3]))  # 处理不足3位的毫秒值

def calculate_property(dui_chang, background):
    """计算属性值"""
    if background:
        return {None:6, 'left':7, 'right':8}[dui_chang]
    else:
        return {None:3, 'left':4, 'right':5}[dui_chang]

def process_spans(spans, dui_chang, background):
    """处理span列表生成lys行"""
    if not spans:
        return None
    
    parts = []
    for span in spans:
        begin = span.get('begin')
        end = span.get('end')
        if not begin or not end:
            continue
        
        try:
            start = parse_time(begin)
            duration = parse_time(end) - start
            if duration <= 0:
                continue
        except:
            continue
        
        word = (span.text or '').strip('()（）')  # 清理特殊字符
        if not word:
            continue
        
        parts.append(f'{word}({start},{duration})')
    
    if not parts:
        return None
    
    prop = calculate_property(dui_chang, background)
    return f'[{prop}]' + ''.join(parts)

def ttml_to_lys(input_path, output_path):
    """主转换函数"""
    try:  # 新增错误处理
        tree = ET.parse(input_path)
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_path}' 不存在")
        return False
    except ET.ParseError:
        print(f"错误：文件 '{input_path}' 不是有效的TTML文件")
        return False
    tree = ET.parse(input_path)
    root = tree.getroot()
    
    lys_lines = []
    
    # 查找所有p标签
    body = root.find('.//tt:body', namespaces)
    div = body.find('tt:div', namespaces) if body else None
    p_tags = div.findall('tt:p', namespaces) if div else []
    
    for p in p_tags:
        # 获取对唱方向
        agent = p.get(f'{{{namespaces["ttm"]}}}agent')
        dui_chang = 'left' if agent == 'v1' else 'right' if agent == 'v2' else None
        
        # 分离主歌词和背景人声
        main_spans = []
        bg_spans = []
        
        for child in p:
            if child.tag == f'{{{namespaces["tt"]}}}span':
                # 检查是否是背景人声容器
                role = child.get(f'{{{namespaces["ttm"]}}}role')
                if role == 'x-bg':
                    bg_spans.extend(child.findall('.//tt:span', namespaces))
                else:
                    main_spans.append(child)
        
        # 处理主歌词行
        if main_spans:
            main_line = process_spans(main_spans, dui_chang, background=False)
            if main_line:
                lys_lines.append(main_line)
        
        # 处理背景人声行
        if bg_spans:
            bg_line = process_spans(bg_spans, dui_chang, background=True)
            if bg_line:
                lys_lines.append(bg_line)
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lys_lines))

    try:  # 新增写入错误处理
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lys_lines))
    except IOError:
        print(f"错误：无法写入输出文件 '{output_path}'")
        return False
    
    return True  # 新增返回状态

if __name__ == '__main__':
    if len(sys.argv) != 2:
        input("\n请将TTML文件拖放到此程序上，然后按回车键...")
    else:
        input_path = sys.argv[1]
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.lys"
        
        if ttml_to_lys(input_path, output_path):
            print(f"转换成功！输出文件：{os.path.abspath(output_path)}")
        
    input("按回车键退出...")

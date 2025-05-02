# TTML to Lyricify Syllable Tool
[![MIT](https://img.shields.io/badge/License-MIT-orange.svg)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/blob/main/LICENSE)
[![Static Badge](https://img.shields.io/badge/Languages-Python-blue.svg)](https://github.com/search?q=repo%3AMiaowCham%2FTTML_to_Lyricify_Syllable_Tool++language%3APython&type=code)
[![Github Release](https://img.shields.io/github/v/release/MiaowCham/TTML_to_Lyricify_Syllable_Tool)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/releases)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/MiaowCham/TTML_to_Lyricify_Syllable_Tool/.github/workflows/build.yml)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/actions/workflows/build.yml)

>[!note]
>包含用户图形界面的工具现已推出！
>[跳转至Release下载](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/releases/)

**一个适用于 TTML (AMLL标准) 文件转 Lyricify Syllable 的小工具**

- Python 3.8+
- 依赖包：
  - tkinter
  - xml.dom.minidom
  - loguru
  - pyperclip

TTML (AMLL标准) 是 AMLL 默认使用的歌词文件；Lyricify Syllable 是 Lyricify 使用的歌词文件。他们都是为实现 Apple Music 样式歌词而制作的格式/规范。但很不幸的是：他们并不兼容。~并且使用 AMLL TTML Tool 输出的 Lyricify Syllable 格式及其不规范~。TTML to Lyricify Syllable Tool 就是为了解决这个问题而诞生的。
>***AMLL TTML Tool 现已去除（~注释掉~）相关导出功能（按键）*** <br>
>需要将 TTML 转换到别的格式？试试 [TTML TRANSLATER](https://github.com/ranhengzhang/ttml-translater)

现在，一拖、一按，即可完成规范化转换！甚至可以提取翻译并单独输出。

### 使用说明
   - 直接将待转换的 ttml 文件拖入工具图标或命令行窗口即可完成转换
   - 默认输出目录为`output`文件夹,具体输出路径可自行修改
   - 本工具需要 Python 3.x 以上环境（实际仅在3.11和3.12测试）

###### 详细信息请见 [提示词及转换原理](/Prompt_words_&_Conversion_principles.md)

## TTML to Lyricify Syllable GUI
基于 `tkinter` 实现的基础 GUI 功能，通过 `PyInstaller` 进行打包构建
>~终于不用对着黑框框转换了~

### 您可以访问 [Release](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/releases/) 下载 Release 版或前往 [Github Action](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/actions/workflows/build.yml) 下载最新构建版

GUI版本不会主动输出 `.lys` 文件，仅会在勾选日志记录后输出日志信息至 /log 文件夹。您可以点击复制按钮进行手动复制输出结果<br>
由于转换实现方式较为复杂，在部分情况下（如导入文字过多、转换时）可能会出现性能问题甚至未响应，应属正常现象

## [TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys)
**TTML to Lys on Github** 主要用于实现从 GitHub Issue 中获取歌词内容，将 ttml 格式歌词转换为 lys，然后将处理后的结果以评论的形式附加到该 Issue 中。该工具通过 Python 实现，依赖于 GitHub API 和正则表达式技术，能够高效、智能地完成歌词内容的清理工作。

### > [点击这里使用 TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys/issues/new/choose) <

## 示例
假设待处理内容为`test.ttml`：
```
<span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span>
<span begin="00:03.694" end="00:04.078">English</span> <span begin="00:04.078" end="00:04.410">version</span> <span begin="00:04.410" end="00:04.799">one</span>
```

脚本处理后会生成以下结果并输出文件`test.lys`到`output`文件夹：
```
[4]English (3694,384)version (4078,332)one(4410,389)
```

## 注意事项
 仅针对 AMLL TTML Tool 输出的 TTML 文件进行适配，不保证其他来源的 TTML 文件转换可用性和准确性

## 鸣谢
- 感谢 [**FanSh**](https://github.com/fred913/) 修改了部分不合理的内容并优化了log功能
- 感谢 [**浩彬**](https://github.com/HKLHaoBin) 将此项目部署到 Github，使此项目得以在 GitHub Issue 中使用（[前往 TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys)）
- 感谢 [**ranhengzhang**](https://github.com/ranhengzhang) 重构了本项目
- 感谢 [Trae](https://www.trae.ai/)、[Github Copilot](https://github.com/features/copilot) 和 [Cursor](https://www.cursor.com/) 共同完成的 GUI 版本

### 特别鸣谢

<div align="center">
<a href="https://www.deepseek.com/" target="_blank">
    <img src="https://github.com/deepseek-ai/DeepSeek-V2/blob/main/figures/logo.svg?raw=true" width="60%" alt="DeepSeek" />
</a>

   感谢 [**DeepSeek**](https://www.deepseek.com/) 为此项目提供的大力支持<br>本项目的初始版本由 [**DeepSeek**](https://www.deepseek.com/) 生成

</div>

###### 大力支持，指使用DeepSeek生成代码时没有服务器繁忙（doge

## 许可证
此项目使用 MIT 许可证。
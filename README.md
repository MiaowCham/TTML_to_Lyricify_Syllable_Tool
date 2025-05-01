# TTML to Lyricify Syllable Tool
[![MIT](https://img.shields.io/badge/License-MIT-orange.svg)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/blob/main/LICENSE)
[![Static Badge](https://img.shields.io/badge/Languages-Python-blue.svg)](https://github.com/search?q=repo%3AMiaowCham%2FTTML_to_Lyricify_Syllable_Tool++language%3APython&type=code)
[![Github Release](https://img.shields.io/github/v/release/MiaowCham/TTML_to_Lyricify_Syllable_Tool)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/releases)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/MiaowCham/TTML_to_Lyricify_Syllable_Tool/.github/workflows/build.yml)](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/actions/workflows/build.yml)

## TTML to Lyricify Syllable GUI
基于 `tkinter` 实现的基础 GUI 功能，通过 `PyInstaller` 进行打包构建
>~终于不用对着黑框框转换了~

### 您可以访问 [Release](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/releases/) 下载 Release 版或前往 [Github Action](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool/actions/workflows/build.yml) 下载最新构建版

GUI版本不会主动输出 `.lys` 文件，仅会在勾选日志记录后输出日志信息至 /log 文件夹。您可以点击复制按钮进行手动复制输出结果<br>
由于转换实现方式较为复杂，在部分情况下（如导入文字过多、转换时）可能会出现性能问题甚至未响应，应属正常现象

### 依赖说明

- Python 3.8+
- 依赖包：
  - tkinter
  - xml.dom.minidom
  - loguru
  - pyperclip

### 注意事项
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
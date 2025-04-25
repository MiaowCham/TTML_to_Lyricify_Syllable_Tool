# TTML转LYS工具 - GUI版本

这是一个带有图形用户界面的TTML转LYS工具，用于将Apple Music Like Lyrics (AMLL) 的TTML格式歌词转换为Lyricify Syllable (LYS) 格式。

## 功能特点

- 简洁直观的图形界面
- 支持文本直接输入或文件导入
- 支持文件拖放功能（需要tkinterdnd2库支持）
- 支持剪贴板操作（复制/粘贴）
- 自动处理翻译内容
- 自动处理背景人声和对唱视图
- 日志记录功能

## 使用方法

### 运行程序

有两种方式运行程序：

1. **直接运行Python脚本**：
   ```
   python TTML_to_LYS_GUI.py
   ```

2. **使用打包的可执行文件**：
   - 运行`build_exe.py`生成可执行文件
   - 运行生成的`TTML转LYS工具.exe`

### 界面操作

- **左侧输入区域**：粘贴TTML内容或拖放TTML文件
- **右侧输出区域**：显示转换后的LYS内容

### 按钮功能

- **粘贴**：从剪贴板读取内容到输入框
- **导入**：打开文件选择对话框导入TTML文件
- **转换**：将输入框中的TTML内容转换为LYS格式
- **复制**：将转换结果复制到剪贴板

### 其他功能

- **启用日志记录**：勾选底部的复选框启用日志记录功能
- **状态提示**：底部状态栏显示操作结果和提示信息

## 转换原理

转换遵循TTML到LYS的标准转换规则，详细信息请参考项目中的`Prompt_words_&_Conversion_principles.md`文件。

## 依赖库

- tkinter：GUI界面
- tkinterdnd2：文件拖放功能（可选）
- pyperclip：剪贴板操作
- loguru：日志记录

## 注意事项

- 首次运行时会自动安装所需依赖库
- 如果拖放功能不可用，请使用"导入"按钮导入文件
- 转换成功后会自动将结果复制到剪贴板

## 相关项目

- [TTML_to_Lyricify_Syllable_Tool](https://github.com/MiaowCham/TTML_to_Lyricify_Syllable_Tool)：命令行版本
- [AMLL TTML Tool](https://github.com/Steve-xmh/amll-ttml-tool)：用于制作TTML歌词
- [Lyricify](https://github.com/WXRIW/Lyricify-App)：支持LYS格式的歌词显示应用
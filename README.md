# TTML to Lyricify Syllable Tool
**一个适用于 AMLL TTML 文件转 Lyricify Syllable 的小工具**

开发者是[**喵锵**](https://github.com/MiaowCham)，初始版本由 DeepSeek 构建。
现在[**浩彬**](https://github.com/HKLHaoBin)将工具进行了修改，得以在 GitHub Issue 中使用

TTML 是 AMLL 使用的歌词文件，但很不幸的是：他们并不兼容。并且使用 AMLL TTML Tool 输出的 Lys 格式及其不规范，TTML to Lyricify Syllable Tool 就是为了解决这个问题而诞生的。

现在，一拖、一按，即可完成规范化转换！甚至可以提取翻译并单独输出。

### 使用说明
   - 直接将待转换的 ttml 文件拖入工具图标或命令行窗口即可完成转换
   - 默认输出目录为`output`文件夹,具体输出路径可自行修改
   - 本工具需要 Python 3.x 以上环境（实际仅在3.11和3.12测试）
   - 在`log\log.set`文件中输入"log_on:True"即可开启日志输出

### 详细信息请见 [提示词及转换原理](/Prompt_words_&_Conversion_principles.md)

## TTML to Lys on Github
**TTML to Lys on Github** 主要用于实现从 GitHub Issue 中获取歌词内容，将 ttml 格式歌词转换为 lys，然后将处理后的结果以评论的形式附加到该 Issue 中。该工具通过 Python 实现，依赖于 GitHub API 和正则表达式技术，能够高效、智能地完成歌词内容的清理工作。

### > [点击这里使用本工具](https://github.com/HKLHaoBin/ttml_to_lys/issues) <

### 使用方法
1. 新建 **issue**，选择 **TTML歌词转Lys**
3. 将需要转换的 **ttml** 格式的歌词复制到 **Description 描述** 中
4. 发送 **issue** 并等待脚本转换

**修正后的结果会以评论形式提交到相应的 Issue 中。**

### 注意事项
- 尽量将标题改为文件名或歌曲名，以便区分
- Label 需要是`ttml_to_lys`才会触发转换

### 功能特点
 **GitHub 集成**：
   - 从指定 GitHub Issue 中提取内容。
   - 将修正后的结果以评论形式提交到相应的 Issue 中。

## 示例
假设 Issue 内容为：
```
<span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span>
<span begin="00:03.694" end="00:04.078">English</span> <span begin="00:04.078" end="00:04.410">version</span> <span begin="00:04.410" end="00:04.799">one</span>
```

脚本处理后会生成以下结果并作为评论提交：
```
Processed Lyrics:
[4]English (3694,384)version (4078,332)one(4410,389)
```

## 注意事项
 输入文本格式应与工具的处理逻辑相匹配，以确保修正效果最佳。

## 许可证
此项目使用 MIT 许可证。

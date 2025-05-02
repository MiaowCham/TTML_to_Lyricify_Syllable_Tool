# 提示词及转换原理
>[!NOTE]
>该文档的部分内容已过时，脚本实际实现方式可能有所不同

你帮我写一个Python程序实现将ttml文件转换到lys文件,要求把ttml文件拖到软件.py的图标即可转换。需要生成log日志，生成路径在同路径log文件夹中

# 术语解释
**对唱视图**：通过改变歌词的对齐方式区分演唱者，有左对齐和右对齐<br>
**背景人声**：通过将文字缩小来表明该歌词不是主要人声

# Lyricify Syllable(lys) 格式规范
### [详细请见 Lyricify 仓库](https://github.com/WXRIW/Lyricify-App/blob/main/docs/Lyricify%204/Lyrics.md)
## Lyricify Syllable 歌词的标准格式为：
### 头部信息
Lyricify Syllable 的歌词头部信息参考 LRC 标准，这里不再重复。

### 歌词
```
[property]Word (start,duration)word(start,duration)
```
`property` 为歌词行属性信息。（见下） 
`start` 为起始时间，`duration` 为时长。  
`()` 中的时间戳为前方单词的起始时间和时长。  
时间戳的是大于零的整数，单位是毫秒 (ms)。  

### 歌词行属性信息:

| 属性 | 背景人声 | 对唱视图 |
| :-: | :-: | :-: |
| 0 | 未设置 | 未设置 |
| 1 | 未设置 | 左 |
| 2 | 未设置 | 右 |
| 3 | 否 | 未设置 |
| 4 | 否 | 左 |
| 5 | 否 | 右 |
| 6 | 是 | 未设置 |
| 7 | 是 | 左 |
| 8 | 是 | 右 |

这是一个示范：
```
[0]Lately (358,1336)I've (1694,487)been, (2181,673)I've (2854,268)been (3122,280)losing (3402,345)sleep(3747,1186)
[0]Dreaming (5245,696)about (5941,471)the (6412,306)things (6718,458)that (7176,292)we (7468,511)could (7979,393)be(8372,737)
```

**注意：**
1. lrc 歌词不允许重复时间轴，也不允许乱序时间轴。歌词应按照时间排序（背景人声除外，具体将在后文中 `背景人声的制作` 部分介绍）。
2. lrc 歌词允许歌词时间段重叠（即多行高亮），如：
   ```
   [124571,2326]Won't (124571,575)we? (125146,459)Yeah(126404,493)
   [125613,1118]Won't (125613,483)we?(126096,635)
   ```

# 关于 TTML 文件格式和转换方式
**TTML** 全称是`Timed Text Markup Language`，是一种基于 XML 的时序文本标记语言，主要用于记录歌词或字幕。现被 [AMLL](https://github.com/Steve-xmh/applemusic-like-lyrics) 用于标记 Apple Music 样式歌词。一般我们使用 [AMLL TTML Tool](https://github.com/Steve-xmh/amll-ttml-tool) 制作 TTML 歌词

需注意的是 TTML 的时间信息使用`mm:ss:ms`的方式记录，和lys的毫秒数不同，需要转换<br>
- 在基础的 TTML 内容外，AMLL 为了实现逐词歌词效果进行了小部分更改。我们以下面这个ttml文件举例：<br>
  [AMLL TTML Tool](https://github.com/Steve-xmh/amll-ttml-tool) 输出的 TTML 文件是没有换行的，所以会是这么一大坨
   ```xml
   <tt xmlns="http://www.w3.org/ns/ttml" xmlns:ttm="http://www.w3.org/ns/ttml#metadata" xmlns:amll="http://www.example.com/ns/amll" xmlns:itunes="http://music.apple.com/lyric-ttml-internal"><head><metadata><ttm:agent type="person" xml:id="v1"/><ttm:agent type="other" xml:id="v2"/><amll:meta key="musicName" value="song"/><amll:meta key="artists" value="singer"/></metadata></head><body dur="00:08.587"><div begin="00:00.781" end="00:08.587"><p begin="00:00.781" end="00:02.320" ttm:agent="v1" itunes:key="L1"><span begin="00:00.781" end="00:01.225">示</span><span begin="00:01.225" end="00:01.585">例</span><span begin="00:01.585" end="00:01.937">歌</span><span begin="00:01.937" end="00:02.320">词</span><span ttm:role="x-bg" begin="00:02.320" end="00:03.694"><span begin="00:02.320" end="00:02.689">(背</span><span begin="00:02.689" end="00:03.004">景</span><span begin="00:03.004" end="00:03.323">人</span><span begin="00:03.323" end="00:03.694">声)</span></span></p><p begin="00:03.694" end="00:04.799" ttm:agent="v1" itunes:key="L2"><span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span><span ttm:role="x-translation" xml:lang="zh-CN">翻译</span><span ttm:role="x-roman">音译</span></p><p begin="00:04.799" end="00:05.911" ttm:agent="v1" itunes:key="L3"><span begin="00:04.799" end="00:05.166">English</span> <span begin="00:05.166" end="00:05.539">version</span> <span begin="00:05.539" end="00:05.911">two</span><span ttm:role="x-translation" xml:lang="zh-CN">翻译</span><span ttm:role="x-roman">音译</span></p><p begin="00:05.911" end="00:07.285" ttm:agent="v2" itunes:key="L4"><span begin="00:05.911" end="00:06.281">对</span><span begin="00:06.281" end="00:06.609">唱</span><span begin="00:06.609" end="00:06.922">视</span><span begin="00:06.922" end="00:07.285">图</span><span ttm:role="x-bg" begin="00:07.285" end="00:08.587"><span begin="00:07.285" end="00:07.616">(对</span><span begin="00:07.616" end="00:07.939">唱</span><span begin="00:07.939" end="00:08.256">背</span><span begin="00:08.587" end="00:08.587">景)</span></span></p></div></body></tt>
   ```

## `<metadata>`标签记录了歌词的meta信息<br>
其子标签`<ttm:agent type="person" xml:id="v1"/><ttm:agent type="other" xml:id="v2"/>`<br>
表明该歌词有两个演唱者。一般情况下，`xml:id="v1"`对应对唱视图是左，`xml:id="v2"`对应对唱视图是右

下面的`<amll:meta key="musicName" value="song"/><amll:meta key="artists" value="singer"/>`<br>
标签是歌词的元数据，用于记录歌曲信息和音乐平台对应ID，lys不记录该内容，需要忽略

## 从`<body>`开始为歌词正文信息。
### `<dev>`标记了整首歌的歌词信息
内含歌词整体的开头和结束时间。但也可能会出现`xmlns=""`，导致命名空间错误，需要忽略
```xml
标准：
<div  begin="歌词整体开始时间" end="歌词整体结束时间">
示例：
<div xmlns="" begin="00:00.781" end="00:08.587">
```
示例中出现了`xmlns=""`，没有用途，会导致命名空间错误，无法直接通过命名空间查找，需要留意

### `<p>`标记了一整句歌词
内含有句子的开始和结束时间，以及演唱者信息。v1对应对唱视图是左，v2对应对唱视图是右。
```xml
标准：
<p begin="句子开始时间" end="句子结束时间" ttm:agent="演唱者" itunes:key="行数">
示例：
<p begin="00:00.781" end="00:02.320" ttm:agent="v1" itunes:key="L1">
```

### `<span>`标记了一个单词。
与lys不同，ttml不是记录单词时长而是开始和结尾时间,内含单词的开始和结尾时间，`<span>`会包裹住他的单词
```xml
标准：
<span begin="单词开始时间" end="单词结束时间">单词</span>
示例：
<span begin="00:00.781" end="00:01.225">词</span>
<span begin="00:04.799" end="00:05.166">English</span>
```
---
#### 转换示例
- 原文
   ```xml
   <p begin="00:00.383" end="00:02.191" ttm:agent="v1" itunes:key="L1"><span begin="00:00.383" end="00:00.845">单词1</span><span begin="00:00.845" end="00:01.258">单词2</span><span begin="00:01.258" end="00:01.648">单词3</span><span begin="00:01.648" end="00:02.191">单词4</span></p>
   ```
- 转换成（歌词行属性信息对应在后文有提）
   ```
   [4]单词1(383,462)单词2(845,413)单词3(1258,390)单词4(1648,543)
   ```
---
#### 需要注意的是：单词之间的空格可能会放到`<span>`标签中间
- 例如
   ```xml
   <span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span>
   <span begin="00:03.694" end="00:04.078">English</span> <span begin="00:04.078" end="00:04.410">version</span> <span begin="00:04.410" end="00:04.799">one</span>
   ```
   对应的文本都是 "English version one"<br>
- 都转换成：
   ```
   [4]English (3694,384)version (4078,332)one(4410,389)
   ```
   空格要放到前一个单词的后面

- 不要转换成：
   ```
   [4]English(3694,384) (0,0)version(4078,332) (0,0)one(4410,389)
   [4]English(3694,384)" "(0,0)version(4078,332)" "(0,0)one(4410,389)
   [4]English (3694,384)" "(0,0)version (4078,332)" "(0,0)one(4410,389)
   ```
   之类的，这是不规范且不美观的

---
#### `<span>`内还会出现`ttm:role=""`，用途如下

- `ttm:role="x-bg"`表明该被其包裹的内容是背景人声，例如
   ```xml
   <span ttm:role="x-bg" begin="00:02.320" end="00:03.694"><span begin="00:02.320" end="00:02.689">(背</span><span begin="00:02.689" end="00:03.004">景</span><span begin="00:03.004" end="00:03.323">人</span><span begin="00:03.323" end="00:03.694">声)</span></span>
   ```
   此时需要将这个`<span>`作为一个单独的一行句子处理。

**`ttm:role=""`信息还能用于翻译和音译**
- `ttm:role="x-translation"`表明该单词是该句子的翻译，例如
   ```xml
   <span ttm:role="x-translation" xml:lang="zh-CN">翻译</span>
   ```
  由于 lys 不内置翻译，所以需要额外输出一份 lrc 格式的歌词，在原文件名后面加上`_trans`表明是翻译文件。只要有一句翻译内容，全部句子都得有翻译输出，没有翻译的句子只输出时间轴不输出内容。<br>
  找到翻译对应的歌词行，找到其开始时间并放到 lrc 的时间轴里

  - 示例：
      ```xml
      <p begin="00:03.694" end="00:04.799" ttm:agent="v1" itunes:key="L2"><span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span><span ttm:role="x-translation" xml:lang="zh-CN">翻译</span></p>
      ```
   - 转换为 lys 和 lrc 文件
      ```lys
      [4]English (3694,384)version (4078,332)one(4410,389)
      ```
      ```lrc
      [00:03.694]翻译
      ```
- `ttm:role="x-roman"`表明该单词是该句子的音译。但由于使用lys的软件会自动生成音译，所以直接忽略

### 歌词行属性信息对应

- 如果一行歌词的演唱者是`v1`且`没有说明是背景歌词`，对应 lys 的`[property]`是[4]<br>
- 如果一行歌词的演唱者是`v2`且`没有说明是背景歌词`，对应 lys 的`[property]`是 [5]<br>
- 如果一行歌词的演唱者是`v1`且`ttm:role="x-bg"`说明是背景歌词，对应 lys 的`[property]`是 [7]<br>
- 如果一行歌词的演唱者是`v2`且`ttm:role="x-bg"`说明是背景歌词，对应 lys 的`[property]`是 [8]

在**完全没有对唱区分**的情况下允许使用带 `未设置` 属性的 `[property]`

## 示例
- 原文件`test.ttml`
   ```xml
   <tt xmlns="http://www.w3.org/ns/ttml" xmlns:ttm="http://www.w3.org/ns/ttml#metadata" xmlns:amll="http://www.example.com/ns/amll" xmlns:itunes="http://music.apple.com/lyric-ttml-internal"><head><metadata><ttm:agent type="person" xml:id="v1"/><ttm:agent type="other" xml:id="v2"/><amll:meta key="musicName" value="song"/><amll:meta key="artists" value="singer"/></metadata></head><body dur="00:08.587"><div begin="00:00.781" end="00:08.587"><p begin="00:00.781" end="00:02.320" ttm:agent="v1" itunes:key="L1"><span begin="00:00.781" end="00:01.225">示</span><span begin="00:01.225" end="00:01.585">例</span><span begin="00:01.585" end="00:01.937">歌</span><span begin="00:01.937" end="00:02.320">词</span><span ttm:role="x-bg" begin="00:02.320" end="00:03.694"><span begin="00:02.320" end="00:02.689">(背</span><span begin="00:02.689" end="00:03.004">景</span><span begin="00:03.004" end="00:03.323">人</span><span begin="00:03.323" end="00:03.694">声)</span></span></p><p begin="00:03.694" end="00:04.799" ttm:agent="v1" itunes:key="L2"><span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span><span ttm:role="x-translation" xml:lang="zh-CN">翻译1</span><span ttm:role="x-roman">音译</span></p><p begin="00:04.799" end="00:05.911" ttm:agent="v1" itunes:key="L3"><span begin="00:04.799" end="00:05.166">English</span> <span begin="00:05.166" end="00:05.539">version</span> <span begin="00:05.539" end="00:05.911">two</span><span ttm:role="x-translation" xml:lang="zh-CN">翻译2</span><span ttm:role="x-roman">音译</span></p><p begin="00:05.911" end="00:07.285" ttm:agent="v2" itunes:key="L4"><span begin="00:05.911" end="00:06.281">对</span><span begin="00:06.281" end="00:06.609">唱</span><span begin="00:06.609" end="00:06.922">视</span><span begin="00:06.922" end="00:07.285">图</span><span ttm:role="x-bg" begin="00:07.285" end="00:08.587"><span begin="00:07.285" end="00:07.616">(对</span><span begin="00:07.616" end="00:07.939">唱</span><span begin="00:07.939" end="00:08.256">背</span><span begin="00:08.587" end="00:08.587">景)</span></span></p></div></body></tt>
   ```
由于有翻译内容，转换后会生成 lys 和 lrc<br>
- 输出文件：`test.lys`
   ```lys
   [4]示(781,444)例(1225,360)歌(1585,352)词(1937,383)
   [7]背(2320,369)景(2689,315)人(3004,319)声(3323,371)
   [4]English (3694,384)version (4078,332)one(4410,389)
   [4]English (4799,367)version (5166,373)two(5539,372)
   [5]对(5911,370)唱(6281,328)视(6609,313)图(6922,363)
   [8]对(7285,331)唱(7616,323)背(7939,317)景(8587,0)
   ```
- 翻译文件：`test_trans.lrc`
   ```lrc
   [00:00.781]
   [00:02.320]
   [00:03.694]翻译1
   [00:04.799]翻译2
   [00:05.911]
   [00:07.285]
   ```

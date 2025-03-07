# TTML to Lyricify Syllable Tool

<div align=center>
   
###### English / [简体中文](./README-CN.md)

</div>

> [!WARNING]
> English readme is temporarily translated by DeepSeek

**A lightweight tool for converting AMLL TTML files to Lyricify Syllable format**  

Developer: [**MiaowCham**](https://github.com/MiaowCham), initial version built by DeepSeek.  
[**HKLHaoBin**](https://github.com/HKLHaoBin) modified the tool for GitHub Issue usage ([Visit TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys))  

TTML is the lyric format used by AMLL, but unfortunately they are incompatible. The Lys format output by AMLL TTML Tool is highly non-standard, which is why TTML to Lyricify Syllable Tool was created.  

Now simply drag-and-drop to complete standardized conversion! Even supports translation extraction and separate output.  

### Usage Instructions  
   - Drag-and-drop TTML files directly onto the tool icon or command line window  
   - Default output directory: `output` folder (customizable path)  
   - Requires Python 3.x+ environment (tested on 3.11 & 3.12)  
   - Enable logging by adding "log_on:True" in `log\log.set`  

### Detailed information: [Prompts & Conversion Principles](/Prompt_words_&_Conversion_principles.md)  

## [TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys)
**TTML to Lys on Github** enables TTML-to-Lys conversion through GitHub Issues. This Python-based tool leverages GitHub API and regex to efficiently process lyrics.  

### > [Click to Use TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys/issues/new/choose) <  

### How to Use  
1. Create new`issue`and select`TTML Lyrics to Lys`template  
2. Paste TTML lyrics into`description`
3. Submit **issue** and wait for conversion  
**Converted results will be posted as comments on the corresponding Issue.**  

### Notes  
- Rename title to filename/song name for identification  
- The issue requires `ttml_to_lys` label to trigger conversion  

### Features  
 **GitHub Integration**:  
   - Extract content from specified GitHub Issues  
   - Post processed results as Issue comments  

## Example  
For example, the pending content is`test.ttml`:  
```
<span begin="00:03.694" end="00:04.078">English </span><span begin="00:04.078" end="00:04.410">version </span><span begin="00:04.410" end="00:04.799">one</span>
<span begin="00:03.694" end="00:04.078">English</span> <span begin="00:04.078" end="00:04.410">version</span> <span begin="00:04.410" end="00:04.799">one</span>
```

The script will produce the following results and output the file`test.lys`to the`output`folder: 
```
[4]English (3694,384)version (4078,332)one(4410,389)
```

## Important Notes  
Input format should match the tool's processing logic for optimal results.  

## Acknowledgements  
- Thanks to [**FanSh**](https://github.com/fred913/) for revising unreasonable implementations and optimizing logging features  
- Thanks to [**HKLHaoBin**](https://github.com/HKLHaoBin) for deploying this project on GitHub, enabling its usage in GitHub Issues ([Visit TTML to Lys on Github](https://github.com/HKLHaoBin/ttml_to_lys))

### Special Acknowledgements

<div align="center">
<img src="image/../image/logo.webp" width="400"/>

Thanks to [**DeepSeek**](https://www.deepseek.com/) for their strong support<br>Core implementation of this project was built by [**DeepSeek**](https://www.deepseek.com/)

</div>

## License  
This project uses the MIT License.

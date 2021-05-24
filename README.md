# Falseknees-Manga-Downloadtool

> 感谢sophie-desu的帮助，sophie-desu帮助我写好⼏乎全部的代码，我要好好谢谢sophie-desu
> 
> thanks for sophie-desu's helps.sophie-desu help me done almost all code.i will haohao thanks sophie-desu

一个 https://falseknees.com/ 漫画爬虫
![](https://falseknees.com/imgs/falseknees.png)

A webcrawler for https://falseknees.com/.

## 勉勉强强可以用了！ use it that is useless!

下载`download.py`开始使用吧！

依赖的Python包：`requests`、`bs4`、`html5lib`

可下载requirements.txt后，使用：`pip install -r requirements.txt`进行一键安装

对于国内用户，你可以在 pip 指令的末尾添加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` 后缀来使用 清华 pypi 镜像 来加速下载安装。

`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

download `download.py` and use it ~!

Requirements: `requests`, `bs4`, `html5lib`

For Chinese users, you can added a `-i https://pypi.tuna.tsinghua.edu.cn/simple` prefix to the command to use Tsinghua tuna mirror to speed up the installation

`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 配置文件

配置文件位于 `config.json`

默认配置：
```
'number_of_thread': 5,
'retry_times': 10,
'log_level': 'info',
'folder_path': './falseknees'
```
### `number_of_thread`

默认值: `5`

用于设置下载时使用的线程数量

### `retry_times`

默认值: `10`

用于设置每次请求时，最多的失败重试次数

### `log_level`

默认值: `info`

用于设置日志输出等级

可选：`debug` `info` `warning` `error` `critical`

### `folder_path`

默认值: `./falseknees`

用于设置抓取到的图片的保存路径

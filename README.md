# Falseknees-Manga-Downloadtool

> 感谢sophie-desu的帮助，sophie-desu帮助我写好⼏乎全部的代码，我要好好谢谢sophie-desu
> 
> thanks for sophie-desu's helps.sophie-desu help me done almost all code.i will haohao thanks sophie-desu

一个 https://falseknees.com/ 漫画爬虫
![](https://falseknees.com/imgs/falseknees.png)

A webcrawler for https://falseknees.com/.

|    | Author   | Role   | Links   |
|----|:---------|:-------|:--------|
| ![BadElement's Avatar](https://avatars3.githubusercontent.com/u/52056834?s=32) | BadElement | Project Lead | [Contributions](https://github.com/Falseknees-Manga/Falseknees-Manga-Downloadtool/commits?author=BadElement) |
| ![sophie-desu's Avatar](https://avatars3.githubusercontent.com/u/52559014?s=32) | sophie_desu | Maintainer | [Contributions](https://github.com/Falseknees-Manga/Falseknees-Manga-Downloadtool?author=sophie-desu) |

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

配置文件位于 `config.json`(如不存在将在启动时自动创建)

默认配置：
```
'number_of_thread': 5,
'number_of_segmented_download_thread': 1,
'retry_times': 10,
'log_level': 'info',
'folder_path': './falseknees'
'http_proxy': {
	'enable': False,
	'host': '127.0.0.1',
	'port': '0'
	}
```
### `number_of_thread`

默认值: `5` 可选：`任意正整数`

用于设置下载时使用的线程数量

### `number_of_segmented_download_thread`

默认值: `1` 可选：`任意正整数`

用于设置分段下载时下载每个文件使用的线程数量

请确保该值小于`number_of_thread`，且满足`number_of_thread`是此值的整数倍数

### `retry_times`

默认值: `10` 可选：`任意正整数`

用于设置每次请求时，最多的失败重试次数

### `log_level`

默认值: `info` 可选：`debug` `info` `warning` `error` `critical`

用于设置日志输出等级

### `folder_path`

默认值: `./falseknees` 可选：`任意文件夹路径`(不存在会自动创建)

用于设置抓取到的图片的保存路径

### `http_proxy`

默认值: 
```
'enable': false,
'host': '127.0.0.1',
'port': '0'
```

用于设置http代理，开启系统代理时请务必设置，否则会出现ProxyError。下方是各项的解释

#### `enable`

默认值: `false` 可选：`true` `false`

用于设置http代理开关，设置为false时不启用且不检查代理设置

#### `host`

默认值: `127.0.0.1` 可选：`任意IP地址`

用于设置http代理的地址，不可使用域名，本地代理请设置为`127.0.0.1`或`0.0.0.0`

#### `port`

默认值: `0` 可选：`任意端口号`

用于设置http代理的端口，如使用代理软件的http接口，请按照代理软件的设置填写

## 奇怪的bug的通用解决方法
退出程序后删除`data`文件夹即可

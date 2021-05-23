from bs4 import BeautifulSoup
from requests import get as requests_get
from os.path import isfile as os_path_isfile, join as os_path_join, exists as os_path_exists
from os import makedirs, system
from logging import getLogger, StreamHandler
from colorlog import ColoredFormatter
from threading import Thread, enumerate as thread_enumerate
from psutil import Process
from math import ceil as math_ceil
from json import load as json_load, dump as json_dump
from re import split as re_split, sub as re_sub
from inspect import isclass
from ctypes import pythonapi, c_long, py_object

default_config = {
	'number_of_thread': 5,
	'retry_times': 10,
	'log_level': 'info',
	'folder_path': './falseknees'
}

log_level={
	'critical': 50,
	'error': 40,
	'warning': 30,
	'info': 20,
	'debug': 10
}

formatter = ColoredFormatter(
		'[%(asctime)s] [%(threadName)s] [%(log_color)s%(levelname)s%(reset)s]: '
		'%(message_log_color)s%(message)s%(reset)s',
		log_colors={
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'ERROR': 'red',
			'CRITICAL': 'bold_red',
		},
		secondary_log_colors={
			'message': {
				'WARNING': 'yellow',
				'ERROR': 'red',
				'CRITICAL': 'bold_red'
			}
		},
		datefmt='%H:%M:%S'
	)

logger = getLogger('FalsekneesMangaDownloader')
logger.setLevel(20)
ch = StreamHandler()
ch.setLevel(20)
ch.setFormatter(formatter)
logger.addHandler(ch)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
download_fail = []
completed = 0


class Json(dict):
	def __init__(self, file):
		self.path = file
		if os_path_isfile(self.path):
			with open(self.path, encoding='utf-8') as f:
				super().__init__(json_load(f))
		else:
			super().__init__()
			self.update(default_config)
			self.save()

	def save(self):
		with open(self.path, 'w', encoding='utf-8') as f:
			json_dump(self.copy(), f, indent=2, ensure_ascii=False)


logger.warning('程序中一部分warning提示是用于醒目的')
logger.info('正在加载配置文件')
config = Json('config.json')
if config['log_level'] not in log_level:
	logger.warning('配置文件中log_level选项设置有误，自动设置为info')
	config['log_level'] = 'info'
	config.save()
logger.setLevel(log_level[config['log_level']])
ch.setLevel(log_level[config['log_level']])


if not os_path_exists(config['folder_path']):
	makedirs(config['folder_path'])


def requests(link, times_limit, bin: bool = False):
		try_times = 0
		while try_times < times_limit:
			try:
				response = requests_get(link, headers=headers)
				response.raise_for_status()
			except Exception as e:
				try_times+=1
				logger.warning(f'{link} 加载失败[{try_times}/{times_limit}]，正在重新获取：{e}')
			else:
				if bin:
					return response.content
				else:
					return BeautifulSoup(response.text, 'html5lib')
		logger.error(f'{link} 加载失败[{try_times}/{times_limit}]，已达到重试次数上限')
		download_fail.append(link)
		return 'error'


class download_thread(Thread):
	def __init__(self, threadID, times_limit):
		Thread.__init__(self)
		self.setDaemon(True)
		self.threadID = threadID
		self.threadName = 'download-thread-' + str(self.threadID)
		self.times_limit = times_limit
		self.setName(self.threadName)
		self.thread_exit = False
		self.completed = 0
		self.has_error = False

	def run(self):
		logger.info(f"下载线程{self.name}启动")
		try:
			self.downloader(self.name, self.threadID, self.times_limit)
		except Exception as e:
			logger.critical(f'下载线程{self.name}出现问题，即将关闭：{e}')
		self.exit()

	def downloader(self, threadName, threadID, times_limit):
		global completed, task_list
		logger.debug(f'线程{threadName}已开始下载')
		for i in task_list[threadID - 1]:
			self.check_exit()
			title = i.string
			title = str.replace(title, '\\', '/')
			title = re_sub('[*:"?<>/|]', '_', title)
			page_link = i['href']
			page = requests('https://falseknees.com/' + page_link, times_limit)
			if page =='error':
				self.has_error = True
				continue
			src = page.select('link')[1]['href']
			suffix = src.split('.')[-1]
			if os_path_exists(os_path_join(config['folder_path'], title + '.' + suffix)):
				logger.info(title + '已存在，跳过下载')
				completed += 1
				self.completed += 1
				continue
			image_link = 'https://falseknees.com/' + src
			logger.info(f'正在下载：{title}[{image_link}]')
			image = requests(image_link, times_limit, True)
			if image =='error':
				self.has_error = True
				continue
			try:
				with open(os_path_join(config['folder_path'], title + '.' + suffix), "wb")as f:
					f.write(image)
					logger.debug(f'线程{threadName}完成一次文件写入')
					page_list.remove(i)
					completed += 1
					self.completed += 1
			except Exception as e:
				logger.error(f'文件{title}[{image_link}]写入失败：{e}')
		logger.debug(f'线程{threadName}已结束下载')

	def check_exit(self):
		if self.thread_exit:
			self.exit()

	def exit(self):
		global download_thread_list
		logger.warning(f'下载线程{self.name}关闭，完成任务：{self.completed}/{len(task_list[self.threadID - 1])}')
		logger.warning(f'所有任务：{completed}/{page_length}')
		if self.has_error:
			logger.error('输入 check error 查看失败的请求')
		Console.download_thread_exit(console)
		if self in download_thread_list:
			download_thread_list.remove(self)
		exit()

	def stop(self):
		self.thread_exit = True


def task_assignment(task, log: bool = False):
	task_length = len(task)
	assigned_quantity = math_ceil(task_length/config['number_of_thread'])
	new_task_list, infomation = [], []
	infomation.append(f'任务总数：{task_length}')
	for i in range(0, task_length, assigned_quantity):
		new_task_list.append(task[i:i + assigned_quantity])
	if log:
		for i in range(1, config['number_of_thread'] + 1):
			infomation.append(f' - download-thread-{i} 拥有任务数：{len(new_task_list[i - 1])}')
		logger.warning("""已分配{}个线程
		{}
		""".format(config['number_of_thread'], '\n'.join(infomation)))
	return new_task_list


# 其实到这里才开始爬233
logger.info('正在获取archive页面')
archive = requests('https://falseknees.com/archive.html', config['retry_times'])
if archive =='error':
	logger.error('https://falseknees.com/archive.html 请求失败')
logger.info('正在给各线程分配下载计划')
page_list = archive.select('div>a')[2:]
page_length = len(page_list)
task_list =  task_assignment(page_list, True)
logger.warning('按任意键开始下载')
system('pause>nul')
logger.warning('开始下载')
download_thread_list = []
for i in range(1, config['number_of_thread'] + 1):
	download_thread_list.append(download_thread(i, config['retry_times']))
	download_thread_list[i - 1].start()


def _async_raise(tid, exctype):
	"""在线程中抛出异常使线程强制关闭"""
	if not isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")
	res = pythonapi.PyThreadState_SetAsyncExc(c_long(tid), py_object(exctype))
	if res == 0:
		raise ValueError("invalid thread id")
	elif res != 1:
		# if it returns a number greater than one, you're in trouble,
		# and you should call it again with exc=NULL to revert the effect
		pythonapi.PyThreadState_SetAsyncExc(tid, None)
		raise SystemError("PyThreadState_SetAsyncExc failed")


class Console(Thread):

	def __init__(self):
		super().__init__(name='Console')
		self.p = Process()
		self.cmd = []
		logger.info('控制台已启动')
		self.setName('Console')
		self.running_dl_thread = 0
		self.wait_dl_thread_exit = False

	def run(self):
		self.running_dl_thread = config['number_of_thread']
		while True:
			try:
				raw_input = input()
				if raw_input == '':
					continue
				cmd_list = re_split(r'\s+', raw_input)
				self.cmd = [i for i in cmd_list if i != '']
				logger.debug('Console input: ')
				logger.debug(f'	Raw input: "{raw_input}"')
				logger.debug(f'	Split result: {self.cmd}')
				self.cmd_parser()
			except EOFError or KeyboardInterrupt:
				exit()

	def send_msg(self, msg):
		for i in msg.splitlines():
			logger.info(i)

	def cmd_parser(self):
		if self.cmd[0] in ['stop', '__stop__', 'exit']:
			self.stop_thread(0)
			self.p.terminate()
		elif self.cmd[0] == 'help':
			self.send_msg(help_msg)
		elif self.cmd[0] == 'thread':
			self.cmd_thread_parser()
		elif self.cmd[0] == 'check':
			self.cmd_check_parser()

	def cmd_thread_parser(self):
		if self.cmd[1] == 'list':
			thread_list = thread_enumerate()
			logger.info(f'当前线程列表, 共 {len(thread_list)} 个活跃线程:')
			for i in thread_list:
				logger.info(f'	- {i.getName()}')
		elif self.cmd[1] == 'stop':
			self.stop_thread()
		elif self.cmd[1] == 'redistribute':
			global task_list, download_thread_list
			self.stop_thread()
			self.wait_dl_thread_exit = True
		elif self.cmd[1] == 'exit':
			global download_thread_list
			logger.critical('您输入了一条隐藏的Debug指令，这会导致所有下载线程强制退出，如果线程中涉及获取释放锁，这可能会导致死锁')
			logger.critical('已在所有下载线程中抛出SystemExit')
			for i in download_thread_list:
				_async_raise(i.ident, SystemExit)
			download_thread_list = []
			self.running_dl_thread = 0
			if self.wait_dl_thread_exit:
				logger.debug('触发all_dl_thread_exit()')
				self.all_dl_thread_exit()

	def cmd_check_parser(self):
		if self.cmd[1] == 'error':
			logger.warning(f'共 {len(download_fail)} 个失败请求:')
			for i in download_fail:
				logger.warning(f'	- {i}')

	def stop_thread(self):
		if len(self.cmd) == 3:
			if 0 < self.cmd[2] < len(download_thread_list):
				target_thread = download_thread_list[self.cmd[2] - 1]
				target_thread.stop()
				logger.info('已发起线程关闭计划')
			else:
				logger.warning('编号不存在')
		else:
			logger.info('已发起全部线程关闭计划')
			for i in download_thread_list:
				i.stop()

	def download_thread_exit(self):
		self.running_dl_thread-=1
		logger.debug(str(self.running_dl_thread))
		if self.wait_dl_thread_exit and self.running_dl_thread == 0:
			logger.debug('触发all_dl_thread_exit()')
			self.all_dl_thread_exit()

	def all_dl_thread_exit(self):
		global task_list, download_thread_list, page_length
		self.wait_dl_thread_exit = False
		page_length = len(page_list)
		task_list = task_assignment(page_list, True)
		download_thread_list = []
		for i in range(1, config['number_of_thread'] + 1):
			download_thread_list.append(download_thread(i, config['retry_times']))
			download_thread_list[i - 1].start()
		self.running_dl_thread = config['number_of_thread']


help_msg = '''stop 关闭程序
help 获取帮助
thread list 查看线程列表
thread stop <可选：线程编号> 发起线程关闭计划
thread redistribute 重新分配任务给各个线程
check error 查看失败请求
'''

console = Console()
console.start()

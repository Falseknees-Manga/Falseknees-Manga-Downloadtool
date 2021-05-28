from bs4 import BeautifulSoup
from requests import get as requests_get, head as requests_head
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning 
from os.path import isfile as os_path_isfile, join as os_path_join, exists as os_path_exists
from os import makedirs, system
from shutil import rmtree
from logging import getLogger, StreamHandler
from colorlog import ColoredFormatter
from threading import Thread, enumerate as thread_enumerate
from psutil import Process
from math import ceil as math_ceil
from json import load as json_load, dump as json_dump
from re import split as re_split, sub as re_sub
from inspect import isclass
from ctypes import pythonapi, c_long, py_object
from atexit import register as atexit_register
disable_warnings(InsecureRequestWarning)

@atexit_register
def on_exit():
	logger.warning('程序退出')
	last_page_list.clear()
	if not do_not_save or page_list not in dir():
		last_page_list.update({'page_list': page_list})
	last_page_list.save(False)

	last_task_list.clear()
	if not do_not_save or task_list not in dir():
		last_task_list.update({'task_list': task_list})
	last_task_list.save(False)

	if not do_not_save:
		data.clear()
		new_data = {
			'page_length': page_length,
			'completed': completed
		}
		data.update(new_data)
		data.save(False)

	last_config.clear()
	last_config.update(config)
	last_config.save()


default_config = {
	'number_of_thread': 5,
	'number_of_segmented_download_thread': 1,
	'retry_times': 10,
	'log_level': 'info',
	'folder_path': './falseknees',
	'http_proxy': {
		'enable': False,
		'host': '127.0.0.1',
		'port': '0'
	}
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
requests_fail = []
completed = 0
do_not_save = False


class Json(dict):
	def __init__(self, file, default_json, folder = None):
		if folder is None:
			self.path = file
		else:
			if not os_path_exists(folder):
				makedirs(folder)
			self.path = os_path_join(folder, file)
		if os_path_isfile(self.path):
			with open(self.path, encoding='utf-8') as f:
				super().__init__(json_load(f))
		else:
			super().__init__()
			self.update(default_json)
			self.save()

	def save(self, use_indent = True):
		with open(self.path, 'w', encoding='utf-8') as f:
			if use_indent:
				json_dump(self.copy(), f, indent=2, ensure_ascii=False)
			else:
				json_dump(self.copy(), f, separators=(',', ':'), ensure_ascii=False)


logger.warning('程序中一部分warning提示是用于醒目的')
logger.info('正在加载配置文件')
config = Json('config.json', default_config)
if config['log_level'] not in log_level:
	logger.warning('配置文件中log_level选项设置有误，自动设置为 info')
	config['log_level'] = 'info'
	config.save()
if not 0 < config['number_of_segmented_download_thread'] <= config['number_of_thread']:
	logger.warning('配置文件中number_of_segmented_download_thread选项设置有误')
	logger.warning('请确保设置的值大于0且小于或等于总线程数')
	config['number_of_segmented_download_thread'] = 1
	config.save()
	logger.warning('自动设置为 1')
segmented_remainder = config['number_of_thread'] % config['number_of_segmented_download_thread']
if segmented_remainder != 0:
	logger.warning('配置文件中number_of_segmented_download_thread选项设置有误')
	logger.warning('请确保设置的值可以将总线程数除尽')
	config['number_of_segmented_download_thread'] = config['number_of_segmented_download_thread'] - segmented_remainder
	config.save()
	logger.warning('自动设置为 ' + str(config['number_of_segmented_download_thread']))
logger.setLevel(log_level[config['log_level']])
ch.setLevel(log_level[config['log_level']])
if config['http_proxy']['enable']:
	host = config['http_proxy']['host']
	port = config['http_proxy']['port']
	proxy = f'http://{host}:{port}'
	proxies={
		"http": proxy,
		"https": proxy
	}


logger.info('正在加载数据文件')
data = Json('data.json', {'is_new': ''}, './data')
last_config = Json('last_config.json', {'is_new': ''}, './data')
last_page_list = Json('last_page_list.json', {'is_new': ''}, './data')
last_task_list = Json('last_task_list.json', {'is_new': ''}, './data')


if not os_path_exists(config['folder_path']):
	makedirs(config['folder_path'])


def requests(link, times_limit, bin: bool = False, additional_header: dict = None):
		try_times = 0
		while try_times < times_limit:
			try:
				if additional_header is not None:
					requests_header = headers.update(additional_header)
				else:
					requests_header = headers
				response = requests_get(link, headers=requests_header, verify=False, proxies=proxies)
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
		requests_fail.append(link)
		return 'error'


class download_thread(Thread):
	def __init__(self, function_used, threadID, times_limit):
		Thread.__init__(self)
		self.setDaemon(True)
		self.threadID = threadID
		self.threadName = 'download-thread-' + str(self.threadID)
		self.times_limit = times_limit
		self.function = function_used
		self.setName(self.threadName)
		self.thread_exit = False
		self.completed = 0
		self.has_error = False
		self.task_length = len(task_list[self.threadID - 1])

	def run(self):
		logger.info(f"下载线程{self.name}启动")
		try:
			self.function(self)
		except Exception as e:
			logger.critical(f'下载线程{self.name}出现问题，即将关闭：{e}')
		self.exit()

	def check_exit(self):
		if self.thread_exit:
			self.exit()

	def exit(self):
		global download_thread_list
		logger.warning(f'下载线程{self.name}关闭，完成任务：{self.completed}/{self.task_length}')
		logger.warning(f'所有任务：{completed}/{page_length}')
		if self.has_error:
			logger.error('输入 check error 查看失败的请求')
		try:
			Console.download_thread_exit(console)
		except:
			pass
		if self in download_thread_list:
			download_thread_list.remove(self)
		exit()

	def stop(self):
		self.thread_exit = True


def not_segmented_downloader(target_thread):
	global completed, page_list
	threadName = target_thread.name
	threadID = target_thread.threadID
	times_limit = target_thread.times_limit
	logger.debug(f'线程{threadName}已开始下载')
	for i in task_list[threadID - 1]:
		target_thread.check_exit()
		title = i[0]
		page_link = i[1]
		page = requests('https://falseknees.com/' + page_link, times_limit)
		if page =='error':
			target_thread.has_error = True
			continue
		src = page.select('link')[1]['href']
		suffix = src.split('.')[-1]
		if os_path_exists(os_path_join(config['folder_path'], title + '.' + suffix)):
			logger.info(title + '已存在，跳过下载')
			page_list.remove(i)
			completed += 1
			target_thread.completed += 1
			continue
		image_link = 'https://falseknees.com/' + src
		logger.info(f'正在下载：{title}[{image_link}]')
		image = requests(image_link, times_limit, True)
		if image =='error':
			target_thread.has_error = True
			continue
		try:
			with open(os_path_join(config['folder_path'], title + '.' + suffix), "wb")as f:
				f.write(image)
				logger.debug(f'线程{threadName}完成一次文件写入')
				page_list.remove(i)
				completed += 1
				target_thread.completed += 1
		except Exception as e:
			logger.error(f'文件{title}[{image_link}]写入失败：{e}')
	logger.debug(f'线程{threadName}已结束下载')


def segmented_downloader(target_thread):
	global completed, page_list
	threadName = target_thread.name
	threadID = target_thread.threadID
	times_limit = target_thread.times_limit
	num = -1
	thread_num = int(threadID % config['number_of_segmented_download_thread'])
	if thread_num == 0:
		thread_num = config['number_of_segmented_download_thread']
	logger.debug(f'线程{threadName}已开始下载')
	logger.debug('线程' + str(threadID) + '在组中的编号为' + str(thread_num))
	for i in task_list[threadID - 1]:
		num += 1
		target_thread.check_exit()
		pos = i[3][thread_num - 1]
		image_link = 'https://falseknees.com/' + i[1]
		logger.info(f'正在下载：{i[0]}[{image_link}]')
		header_range = f"bytes={pos}-{i[3][thread_num]}"
		logger.debug(header_range)
		image = requests(image_link, times_limit, True, {"Range": header_range})
		if image =='error':
			target_thread.has_error = True
			continue
		try:
			with open(os_path_join(config['folder_path'], i[0] + '.' + i[2]), 'rb+') as f:
				f.seek(pos)
				f.write(image)
				logger.debug(f'线程{threadName}完成一次文件写入在{pos}')
				del task_list[threadID - 1][num]
		except Exception as e:
			logger.error(f'文件{i[0]}[{image_link}]写入失败：{e}')
		else:
			completed += 1
			target_thread.completed += 1
	logger.debug(f'线程{threadName}已结束下载')


def get_content_length(target_thread):
	global completed
	threadName = target_thread.name
	threadID = target_thread.threadID
	times_limit = target_thread.times_limit
	logger.debug(f'线程{threadName}已开始获取')
	for i in task_list[threadID - 1]:
		try_times = 0
		response = None
		while try_times < times_limit:
			try:
				response = requests_head('https://falseknees.com/' + i[1], verify=False, proxies=proxies).headers['Content-Length']
			except Exception as e:
				try_times+=1
				logger.warning(f'{i[1]} 加载失败[{try_times}/{times_limit}]，正在重新获取：{e}')
			else:
				response = int(response)
				break
		if response is None:
			logger.error(f'{i[1]} 加载失败[{try_times}/{times_limit}]，已达到重试次数上限')
			requests_fail.append(i[1])
			continue
		page = requests('https://falseknees.com/' + i[1], times_limit)
		if page =='error':
			target_thread.has_error = True
			continue
		src = page.select('link')[1]['href']
		suffix = src.split('.')[-1]
		completed += 1
		target_thread.completed += 1
		if os_path_exists(os_path_join(config['folder_path'], i[0] + '.' + suffix)):
			logger.info(i[0] + '已存在，跳过下载')
			continue
		if not os_path_exists(i[0] + '.' + suffix):
			open(os_path_join(config['folder_path'], i[0] + '.' + suffix), 'w').close
		s = math_ceil(response / config['number_of_segmented_download_thread'])
		pos_list = []
		for j in range(config['number_of_segmented_download_thread']):
			pos_list.append(j * s)
		pos_list.append(response)
		segmented_task_list[threadID - 1].append([i[0], src, suffix, pos_list])
		logger.debug(completed)


def task_assignment(task, log: bool = False):
	task_length = len(task)
	assigned_quantity = math_ceil(task_length / config['number_of_thread'])
	new_task_list, infomation = [], []
	infomation.append(f'任务总数：{task_length}')
	for i in range(0, task_length, assigned_quantity):
		new_task_list.append(task[i:i + assigned_quantity])
	if log:
		for i in range(1, config['number_of_thread'] + 1):
			if i > len(new_task_list):
				new_task_list.append([])
			infomation.append(f' - download-thread-{i} 拥有任务数：{len(new_task_list[i - 1])}')
		logger.warning("""已分配{}个线程
		{}
		""".format(config['number_of_thread'], '\n'.join(infomation)))
	return new_task_list


def start_download_thread(function_used, inherit = True):
	global download_thread_list, completed, page_length
	if (inherit) and ('is_new' not in data) and (config['number_of_segmented_download_thread'] == last_config['number_of_segmented_download_thread']):
		page_length = data['page_length']
		completed = data['completed']
	else:
		completed = 0
	download_thread_list = []
	for i in range(1, config['number_of_thread'] + 1):
		download_thread_list.append(download_thread(function_used, i, config['retry_times']))
		download_thread_list[i - 1].start()


def segmented_task_assignment(task, log: bool = False):
	global segmented_task_list, task_list, do_not_save
	do_not_save = True
	segmented_task_list = []
	seg_num = config['number_of_segmented_download_thread']
	task_length = len(task)
	group_length = int(config['number_of_thread'] / seg_num)
	assigned_quantity = math_ceil(task_length / group_length)
	task_list = task_assignment(task)
	logger.info('正在获取图片列表')
	for i in range(config['number_of_thread']):
		segmented_task_list.append([])
	start_download_thread(get_content_length, False)
	for i in download_thread_list:
		i.join()
	task = []
	for i in segmented_task_list:
		task.extend(i)
	logger.debug(task)
	task_length = len(task)
	new_task_list, infomation = [], []
	infomation.append(f'任务总数：{task_length} (x{seg_num})')
	for i in range(0, task_length, assigned_quantity):
		for j in range(seg_num):
			new_task_list.append(task[i:i + assigned_quantity])
	if log:
		for i in range(1, config['number_of_thread'] + 1):
			if i > len(new_task_list):
				new_task_list.append([])
			infomation.append(f' - download-thread-{i} 拥有任务数：{len(new_task_list[i - 1])}')
		logger.warning("""已分配{}个线程，{}个线程为一组，共{}组
		{}
		""".format(config['number_of_thread'], seg_num, group_length, '\n'.join(infomation)))
	do_not_save = False
	return new_task_list


def normal_start():
	global page_list, page_length, task_list
	logger.info('正在获取archive页面')
	archive = requests('https://falseknees.com/archive.html', config['retry_times'])
	if archive == 'error':
		logger.error('https://falseknees.com/archive.html 请求失败，程序退出')
		exit()
	logger.info('正在给各线程分配下载计划')
	html_list = archive.select('div>a')[2:]
	page_list = []
	for i in html_list:
		title = i.string
		title = str.replace(title, '\\', '/')
		title = re_sub('[*:"?<>/|]', '_', title)
		page_list.append([title, i['href']])
	page_length = len(page_list)
	if config['number_of_segmented_download_thread'] == 1:
		task_list = task_assignment(page_list, True)
	else:
		task_list = segmented_task_assignment(page_list, True)
	logger.warning('按任意键开始下载')
	system('pause>nul')
	logger.warning('开始下载')
	if config['number_of_segmented_download_thread'] == 1:
		
		start_download_thread(not_segmented_downloader)
	else:
		page_length *= 8
		start_download_thread(segmented_downloader)


# 其实到这里才开始爬233
def main():
	global page_list, task_list, page_length
	if 'is_new' not in last_page_list:
		logger.info('检测到未完成的下载任务，是否继续下载？(y/n)')
		user_input = input()
		if user_input == 'y':
			if config['number_of_segmented_download_thread'] != last_config['number_of_segmented_download_thread']:
				logger.warning('现在的 分段下载线程数 设置与先前不同，是否修改为上次的设置以继续下载？(y/n)')
				user_input = input()
				if user_input == 'y':
					config['number_of_segmented_download_thread'] = last_config['number_of_segmented_download_thread']
					config.save()
				else:
					if last_config['number_of_segmented_download_thread'] != 1:
						rmtree(last_config['folder_path'])
						makedirs(config['folder_path'])
					normal_start()
					return
			page_list = last_page_list['page_list']
			task_list = last_task_list['task_list']
			page_length = len(page_list)
			if config['number_of_segmented_download_thread'] == 1:
				logger.info('正在给各线程重新分配下载计划')
				task_list = task_assignment(page_list, True)
				start_download_thread(not_segmented_downloader)
			else:
				start_download_thread(segmented_downloader)
		else:
			if last_config['number_of_segmented_download_thread'] != 1:
				rmtree(last_config['folder_path'])
				makedirs(config['folder_path'])
			normal_start()
	else:
		normal_start()


main()


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
		self.clear_data = True

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
			self.clear_data = False
			self.stop_thread()
			for i in download_thread_list:
				i.join()
			on_exit()
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
			self.clear_data = False
			self.stop_thread()
		elif self.cmd[1] == 'redistribute':
			global task_list, download_thread_list
			self.stop_thread()
			self.wait_dl_thread_exit = True
		elif self.cmd[1] == 'kill':
			global download_thread_list
			logger.critical('您输入了一条隐藏的Debug指令，这会导致所有下载线程强制退出，如果线程中涉及获取释放锁，这可能会导致死锁')
			logger.critical('已在所有下载线程中抛出SystemExit')
			for i in download_thread_list:
				_async_raise(i.ident, SystemExit)
			download_thread_list = []
			self.running_dl_thread = 0
			if self.wait_dl_thread_exit:
				self.all_dl_thread_exit()

	def cmd_check_parser(self):
		if self.cmd[1] == 'error':
			logger.warning(f'共 {len(requests_fail)} 个失败请求:')
			for i in requests_fail:
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
		global page_list, task_list
		self.running_dl_thread-=1
		logger.debug(str(self.running_dl_thread))
		if self.running_dl_thread == 0:
			if self.wait_dl_thread_exit:
				self.all_dl_thread_exit()
			elif self.clear_data:
				page_list = {'is_new': ''}
				task_list = {'is_new': ''}
			if not self.clear_data:
				self.clear_data = True


	def all_dl_thread_exit(self):
		global task_list, download_thread_list, page_length
		self.wait_dl_thread_exit = False
		page_length = len(page_list)
		task_list = task_assignment(page_list, True)
		start_download_thread()
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

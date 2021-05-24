if __name__ == '__main__':
	print('此文件存储new_thread函数装饰器方法，直接运行没有效果')
	print('引入模块请使用 from .new_thread import new_thread')
	exit()

from threading import Thread
from typing import Callable
from functools import wraps as functools_wraps
from inspect import signature

def new_thread(thread_name: str or Callable = None):
	"""
	Use a new thread to execute the decorated function
	The function return value will be set to the thread instance that executes this function
	The name of the thread can be specified in parameter
	"""
	def wrapper(func):
		@functools_wraps(func)
		def wrap(*args, **kwargs):
			thread = Thread(target=func, args=args, kwargs=kwargs, name=thread_name)
			thread.setDaemon(True)
			thread.start()
			return thread
		wrap.__signature__ = signature(func)
		return wrap
	if isinstance(thread_name, Callable):
		this_is_a_function = thread_name
		thread_name = None
		return wrapper(this_is_a_function)
	return wrapper

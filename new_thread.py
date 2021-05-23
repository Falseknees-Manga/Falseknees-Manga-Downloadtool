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
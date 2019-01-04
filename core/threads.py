from utils.singleton import singleton

import threading
import inspect
import ctypes

def _async_raise(tid, exctype):
	"""raises the exception, performs cleanup if needed"""
	if not inspect.isclass(exctype):
		raise TypeError("Only types can be raised (not instances)")

	res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))

	if res == 0:
		raise ValueError("invalid thread id")
	elif res != 1:
		# """if it returns a number greater than one, you're in trouble,
		# and you should call it again with exc=NULL to revert the effect"""
		ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
		raise SystemError("PyThreadState_SetAsyncExc failed")

class Thread(threading.Thread):
	def _get_my_tid(self):
		"""determines this (self's) thread id"""
		if not self.isAlive():
			raise threading.ThreadError("the thread is not active")

		# do we have it cached?
		if hasattr(self, "_thread_id"):
			return self._thread_id

		# no, look for it in the _active dict
		for tid, tobj in threading._active.items():
			if tobj is self:
				self._thread_id = tid
				return tid

		raise AssertionError("could not determine the thread's id")

	def raise_exc(self, exctype):
		"""raises the given exception type in the context of this thread"""
		_async_raise(self._get_my_tid(), exctype)

	def terminate(self):
		"""raises SystemExit in the context of the given thread, which should
		cause the thread to exit silently (unless caught)"""
		self.raise_exc(SystemExit)

@singleton
class Kthreads(object):
	def __init__(self):
		self.thread_pool = []

	def apply_async(self, func, args):
		t = Thread(target = func, args = args)

		t.daemon = True
		t.start()

		self.thread_pool.append(t)

	def interrupt_all(self):
		for t in self.thread_pool:
			if t.isAlive():
				t.terminate()

	def join(self):
		while True:
			try:
				allok = True

				for t in self.thread_pool:
					if t.isAlive():
						t.join(0.5)
						allok = False

				if allok:
					break
			except KeyboardInterrupt:
				print("Press [ENTER] to interrupt the job")
				#self.interrupt_all()
				break

	def all_finished(self):
		for t in self.thread_pool:
			if t.isAlive():
				return False

		return True

	def get_name(self):
		return threading.currentThread().name

	def set_name(self, name):
		threading.currentThread().setName(name)

	def set_daemon(self):
		threading.currentThread().setDaemon(True)

	def is_daemon(self):
		return threading.currentThread().isDaemon()

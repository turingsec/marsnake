import os, sys, psutil, time
from core.threads import Kthreads
from utils import common
from core.event import Kevent
from core.pipe import KPipe
from core import addition_import
import traceback

def python_main(child_end):
	try:
		common.set_work_dir()
		common.setdefaultencoding("utf8")

		Kevent().init_signal()

		if not Kevent().do_initializing():
			sys.exit(1)

		if child_end:
			Kthreads().apply_async(KPipe().start, (child_end, ))

		Kthreads().apply_async(Kevent().do_start, ())
		Kthreads().join()

	except Exception as e:
		traceback.print_exc(file = sys.stdout)

if __name__ == '__main__':
	python_main(None)
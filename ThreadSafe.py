import importlib
import threading
import time

gdb = importlib.import_module("gdb")


def thread_safe(arg):
    def decorator(func):
        def _thread_safe(*args, **kwargs):
            lock_counter = AtomicInteger()
            is_main_thread = threading.current_thread() is threading.main_thread()
            result = None

            def _exec():
                nonlocal result
                result = func(*args, **kwargs)
                lock_counter.decr()
            if not is_main_thread:
                lock_counter.incr()
                gdb.post_event(_exec)
                while lock_counter.get() > 0:
                    time.sleep(0.1)
            else:
                _exec()
            return result
        return _thread_safe
    return decorator


class AtomicInteger:
    def __init__(self, num=0):
        self.num = num
        self.lock = threading.Lock()

    def incr(self, diff=1):
        self.lock.acquire()
        self.num += diff
        self.lock.release()

    def decr(self, diff=1):
        self.lock.acquire()
        self.num -= diff
        self.lock.release()

    def set(self, val):
        self.lock.acquire()
        self.num = val
        self.lock.release()

    def get(self):
        self.lock.acquire()
        num = self.num
        self.lock.release()
        return num

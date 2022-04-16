from threading import Lock, Condition

class StandardLock:
    def __init__(self):
        self.lock = Lock()

    def acquire_read(self):
        self.lock.acquire()

    def release_read(self):
        self.lock.release()

    def acquire_write(self):
        self.lock.acquire()
    
    def release_write(self):
        self.lock.release()


class ReadWriteLock:
    def __init__(self):
        self.cv = Condition(Lock())
        self.readers = 0

    def acquire_read(self):
        with self.cv: 
            self.readers += 1

    def release_read(self):
        with self.cv:
            self.readers -= 1
            if self.readers == 0:
                self.cv.notify()

    def acquire_write(self):
        self.cv.acquire()
        self.cv.wait_for(lambda: self.readers == 0)

    def release_write(self):
        self.cv.release()
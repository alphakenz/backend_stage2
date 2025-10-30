import threading

class RefreshLock:
    """Simple in-memory lock to prevent concurrent refreshes"""
    def __init__(self):
        self.lock = threading.Lock()
        self.is_locked_flag = False
    
    def lock(self):
        self.lock.acquire()
        self.is_locked_flag = True
    
    def unlock(self):
        self.is_locked_flag = False
        self.lock.release()
    
    def is_locked(self):
        return self.is_locked_flag
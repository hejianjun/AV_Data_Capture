import ctypes
import platform
import os

class WindowsInhibitor:
    '''Prevent OS sleep/hibernate in windows; code from:
    https://stackoverflow.com/questions/57647034/prevent-sleep-mode-python-wake-on-lan
    '''
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):
        if platform.system() == 'Windows':
            try:
                print("[!]Preventing Windows from going to sleep")
                ctypes.windll.kernel32.SetThreadExecutionState(
                    self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED)
            except Exception:
                pass

    def uninhibit(self):
        if platform.system() == 'Windows':
            try:
                print("[!]Allowing Windows to go to sleep")
                ctypes.windll.kernel32.SetThreadExecutionState(
                    self.ES_CONTINUOUS)
            except Exception:
                pass

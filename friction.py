"""Scale physical mouse motion. No motion is generated without user input."""
import ctypes
from ctypes import wintypes
import threading
import time


class MouseFriction:
    def __init__(self, user32, input_type, mouse_type, factor):
        self.user32 = user32
        self.input_type = input_type
        self.mouse_type = mouse_type
        self.factor = factor
        self.until = 0.0
        self.error = None
        self.ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def activate(self, active, factor=None):
        if factor is not None:
            self.factor = factor
        self.until = time.monotonic() + 0.15 if active else 0.0

    def start(self):
        self.thread.start()
        if not self.ready.wait(5):
            raise RuntimeError('O hook do rato não iniciou.')
        if self.error:
            raise self.error

    def close(self):
        self.activate(False)
        if getattr(self, 'thread_id', None):
            self.user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            self.thread.join(timeout=2)

    def _run(self):
        user32 = self.user32
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        class MouseEvent(ctypes.Structure):
            _fields_ = [('pt', wintypes.POINT), ('mouseData', wintypes.DWORD),
                        ('flags', wintypes.DWORD), ('time', wintypes.DWORD),
                        ('dwExtraInfo', ctypes.c_size_t)]

        user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, callback_type, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HANDLE
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
        user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        remainder = [0.0, 0.0]

        @callback_type
        def hook(code, message, pointer):
            if code >= 0 and message == 0x0200:
                event = ctypes.cast(pointer, ctypes.POINTER(MouseEvent)).contents
                if not event.flags & 0x01:  # Never rescale injected events.
                    if time.monotonic() < self.until and not user32.GetAsyncKeyState(0x76) & 0x8000:
                        cursor = wintypes.POINT()
                        if user32.GetCursorPos(ctypes.byref(cursor)):
                            raw = (event.pt.x - cursor.x, event.pt.y - cursor.y)
                            scaled = [raw[i] * self.factor + remainder[i] for i in (0, 1)]
                            delta = [int(v) for v in scaled]
                            remainder[:] = [scaled[i] - delta[i] for i in (0, 1)]
                            if any(delta):
                                item = self.input_type(type=0, mi=self.mouse_type(dx=delta[0], dy=delta[1], dwFlags=1))
                                if user32.SendInput(1, ctypes.byref(item), ctypes.sizeof(item)) != 1:
                                    self.until = 0.0
                                    self.error = RuntimeError('Windows recusou a entrada reduzida do rato.')
                                    return user32.CallNextHookEx(None, code, message, pointer)
                            return 1
                    remainder[:] = [0.0, 0.0]
            return user32.CallNextHookEx(None, code, message, pointer)

        self.thread_id = kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)
        handle = user32.SetWindowsHookExW(14, hook, kernel32.GetModuleHandleW(None), 0)
        if not handle:
            self.error = ctypes.WinError(ctypes.get_last_error())
        self.ready.set()
        if not handle:
            return
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            user32.UnhookWindowsHookEx(handle)

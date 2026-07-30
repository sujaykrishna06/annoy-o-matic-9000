"""
Win32 process name whitelist window focus and UI Automation (UIA) text-field targeting module.
"""
import os
import ctypes
import ctypes.wintypes
import time
from annoy_app.config import CHAT_APP_EXECUTABLES
from annoy_app.core.win32_dwm import safe_print

try:
    from pywinauto import Application, Desktop
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

# Win32 Constants
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
SW_RESTORE = 9
SW_SHOW = 5

class WindowInfo:
    def __init__(self, title, hwnd, exe_name):
        self.title = title
        self.hwnd = hwnd
        self.exe_name = exe_name

    def __repr__(self):
        return f"<WindowInfo '{self.title}' (PID Exe: {self.exe_name}, HWND: {self.hwnd})>"


def get_process_name_from_hwnd(hwnd):
    """Retrieves the exact executable file name (e.g. WhatsApp.exe) for a window handle."""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_process:
            return None

        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = ctypes.wintypes.DWORD(1024)
            if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(size)):
                full_path = buf.value
                return os.path.basename(full_path)
        finally:
            kernel32.CloseHandle(h_process)
    except Exception as e:
        safe_print(f"[WindowFocus] Process name resolution notice: {e}")
    return None


def get_running_chat_apps():
    """
    Scans top-level visible windows and matches specifically against CHAT_APP_EXECUTABLES whitelist.
    Returns list of WindowInfo objects.
    """
    chat_windows = []
    user32 = ctypes.windll.user32

    def enum_windows_callback(hwnd, extra):
        if not user32.IsWindowVisible(hwnd):
            return True

        # Ignore zero-width/height windows
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        if (rect.right - rect.left) <= 0 or (rect.bottom - rect.top) <= 0:
            return True

        exe_name = get_process_name_from_hwnd(hwnd)
        if not exe_name:
            return True

        # Strict case-insensitive process executable name whitelist check
        for allowed_exe in CHAT_APP_EXECUTABLES:
            if exe_name.lower() == allowed_exe.lower():
                # Get window title text
                length = user32.GetWindowTextLengthW(hwnd)
                title_buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title_buf, length + 1)
                title = title_buf.value.strip() or exe_name

                # Avoid adding duplicate windows for the same handle
                if not any(w.hwnd == hwnd for w in chat_windows):
                    chat_windows.append(WindowInfo(title, hwnd, exe_name))
                break
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
    return chat_windows


def focus_window(hwnd):
    """Brings window handle to the foreground on Windows."""
    try:
        user32 = ctypes.windll.user32
        
        # Restore if minimized
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        else:
            user32.ShowWindow(hwnd, SW_SHOW)

        # Attach thread input to bypass SetForegroundWindow restrictions if needed
        foreground_hwnd = user32.GetForegroundWindow()
        if foreground_hwnd != hwnd:
            foreground_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None)
            target_thread = user32.GetWindowThreadProcessId(hwnd, None)
            current_thread = ctypes.windll.kernel32.GetCurrentThreadId()

            if foreground_thread and foreground_thread != current_thread:
                user32.AttachThreadInput(current_thread, foreground_thread, True)

            user32.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)

            if foreground_thread and foreground_thread != current_thread:
                user32.AttachThreadInput(current_thread, foreground_thread, False)
        return True
    except Exception as e:
        safe_print(f"[WindowFocus] Focus notice: {e}")
        return False


def focus_and_target_input(hwnd, exe_name):
    """
    1. Brings target window to foreground.
    2. Uses UIA via pywinauto to locate and click the chat text box input element.
    3. Returns (success: bool, status_msg: str).
    """
    # Step 1: Window level focus
    focused_ok = focus_window(hwnd)
    if not focused_ok:
        return False, "⚠️ Could not bring target window to front"

    time.sleep(0.15)  # Allow OS window transition

    if not PYWINAUTO_AVAILABLE:
        return False, f"⚠️ Focused {exe_name} window (click text box if needed)"

    # Step 2: UI Automation Text Field Discovery
    try:
        app = Application(backend="uia").connect(handle=hwnd)
        main_win = app.window(handle=hwnd)

        # Search for Edit / Document controls under main window
        candidates = []
        
        # Primary search: Edit or Document ControlTypes
        for control_type in ["Edit", "Document", "Custom"]:
            try:
                ctrls = main_win.descendants(control_type=control_type)
                for c in ctrls:
                    name = (c.window_text() or "").lower()
                    class_name = (c.class_name() or "").lower()
                    # Filter out search boxes or title bars if possible
                    if "search" not in name:
                        candidates.append((c, name, class_name))
            except Exception:
                pass

        if candidates:
            # Pick best candidate (e.g. matching "type a message", "write a message", or first Edit)
            best_ctrl = None
            for ctrl, name, class_name in candidates:
                if any(kw in name for kw in ["type a message", "write a message", "message", "type"]):
                    best_ctrl = ctrl
                    break

            if not best_ctrl:
                best_ctrl = candidates[0][0]

            try:
                best_ctrl.click_input()
                safe_print(f"[WindowFocus] UIA clicked input field for {exe_name}")
                return True, f"🎯 Focused {exe_name} text box!"
            except Exception as e:
                safe_print(f"[WindowFocus] UIA click notice: {e}")

    except Exception as e:
        safe_print(f"[WindowFocus] UIA search notice for {exe_name}: {e}")

    # Fallback to window-level focus if UIA text field couldn't be clicked
    return False, f"⚠️ Focused {exe_name} window (click text box if needed)"

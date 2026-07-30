"""
Win32 C-types API structures for DWM Acrylic blur behind and Windows 11 rounded window frame corners.
"""
import sys
import ctypes

from annoy_app.config import GLASS_TRANSPARENCY_ALPHA, GLASS_COLOR_RGB

def safe_print(*args, **kwargs):
    """Safely prints text without UnicodeEncodeError on Windows terminals."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(arg) for arg in args)
        safe_text = text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
        print(safe_text, **kwargs)

def get_acrylic_bg_color():
    """Computes 32-bit ABGR uint from alpha & RGB constants."""
    r, g, b = GLASS_COLOR_RGB
    a = GLASS_TRANSPARENCY_ALPHA
    return (a << 24) | (b << 16) | (g << 8) | r

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ('AccentState', ctypes.c_uint),
        ('AccentFlags', ctypes.c_uint),
        ('GradientColor', ctypes.c_uint),
        ('AnimationId', ctypes.c_uint)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ('Attribute', ctypes.c_int),
        ('Data', ctypes.POINTER(ACCENT_POLICY)),
        ('SizeOfData', ctypes.c_size_t)
    ]

DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWCP_ROUND = 2

def set_windows_rounded_corners(hwnd):
    """Applies Windows 11 DWM native rounded corners to the DWM acrylic blur frame."""
    try:
        dwmapi = ctypes.windll.dwmapi
        corner_pref = ctypes.c_int(DWMWCP_ROUND)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(corner_pref),
            ctypes.sizeof(corner_pref)
        )
    except Exception:
        pass

def enable_windows_acrylic_blur(hwnd, bg_color=None):
    """Enables real Windows DWM Acrylic Blur-Behind effect on window handle."""
    if bg_color is None:
        bg_color = get_acrylic_bg_color()
    try:
        user32 = ctypes.windll.user32
        SetWindowCompositionAttribute = user32.SetWindowCompositionAttribute
        
        accent = ACCENT_POLICY()
        accent.AccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND
        accent.GradientColor = bg_color
        accent.AccentFlags = 2

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)

        SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))
    except Exception:
        pass

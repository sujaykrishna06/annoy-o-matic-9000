"""
Safe non-destructive OS clipboard operations with lock retry protection and automatic restoration/clearing.
"""
import time
import pyperclip
from annoy_app.core.win32_dwm import safe_print

class ClipboardGuard:
    def __init__(self):
        self._original_content = None

    def backup(self):
        """Backs up the user's current clipboard text before typing runs."""
        try:
            self._original_content = pyperclip.paste()
            safe_print("[ClipboardGuard] Original clipboard backed up.")
        except Exception as e:
            self._original_content = ""
            safe_print(f"[ClipboardGuard] Backup notice: {e}")

    def safe_copy(self, text, retries=3, delay=0.02):
        """Copies text to clipboard with automatic lock retries."""
        for attempt in range(1, retries + 1):
            try:
                pyperclip.copy(text)
                return True
            except Exception as e:
                safe_print(f"[ClipboardGuard] Copy attempt {attempt}/{retries} locked: {e}")
                time.sleep(delay)
        return False

    def clear(self):
        """Empties/cleans the OS clipboard completely."""
        try:
            pyperclip.copy("")
            safe_print("[ClipboardGuard] Clipboard cleared successfully.")
        except Exception as e:
            safe_print(f"[ClipboardGuard] Clear notice: {e}")

    def restore_or_clear(self):
        """Restores original content if it existed, otherwise wipes transient clipboard data."""
        if self._original_content and self._original_content.strip():
            try:
                pyperclip.copy(self._original_content)
                safe_print("[ClipboardGuard] Original clipboard content restored.")
            except Exception:
                self.clear()
        else:
            self.clear()

# 😈 Annoy-O-Matic 9000 • Modular Architecture (v2.0)

A production-grade, modular desktop auto-typer built with **PyQt6** and **Windows DWM Acrylic Blur**, featuring see-through glassmorphism, non-destructive clipboard protection, zero-CPU idle sleep, 10px rounded curves, F5/F8/ESC shortcuts, and a clean package architecture.

---

## 🏗️ Modular Package Architecture

```
annoy_app/
├── config.py              # Constants, color themes, prank pack dictionaries
├── core/
│   ├── win32_dwm.py       # Win32 C-types DWM blur & corner attribute APIs
│   ├── clipboard.py       # Non-destructive clipboard backup, retry & restoration
│   └── engine.py          # AutoTyper worker signals & Zalgo chaos transforms
└── ui/
    └── glass_widget.py    # Main Apple-inspired glass card UI & paint events
main.py                    # Clean ~15-line entry point
```

---

## 🌟 Key Upgrades in v2.0

### 1. 🛡️ Non-Destructive Clipboard Guard (`ClipboardGuard`)
- **Automatic Backup & Restoration**: Backs up the user's original clipboard content (`pyperclip.paste()`) before typing begins and restores it automatically when typing finishes.
- **Lock Retry Protection**: Automatically retries clipboard copy operations up to 3 times to protect against transient Win32 clipboard locks from background managers.

### 2. ⚡ Zero-CPU Idle Sleep
- **Conditional Timer Activation**: Border glow timer is completely stopped when idle (`is_running == False`) and started strictly when typing begins, lowering idle CPU/GPU usage to 0%.

### 3. 🪟 Windows 11 DWM Acrylic Glass & Sleek 10px Curves
- **DWM Frame Clipping**: Windows 11 `DWMWA_WINDOW_CORNER_PREFERENCE` (`DWMWCP_ROUND = 2`) natively clips the Acrylic blur frame to 10px rounded corners.
- **Specular Edge Highlighting**: Rendered top (90°) and left (180°) linear specular highlights over ultra-transparent (`0x02` alpha) glass.

### 4. ⌨️ Global Keyboard Shortcuts
- **`F5`**: Start Auto-Typer (`▶ Start (F5)`).
- **`F8`**: Pause / Resume (`⏸ Pause (F8)`).
- **`ESC`**: Full Emergency Abort (`⬛ Abort (ESC)`).

---

## 🚀 How to Run

```powershell
python main.py
```

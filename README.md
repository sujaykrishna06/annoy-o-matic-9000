# 😈 Annoy-O-Matic 9000 v2.0

A floating, see-through desktop auto-typer built with **PyQt6** and **Windows 11 DWM Acrylic Blur**. Type messages into any chat app — letter by letter, word by word, or line by line — with prank packs, chaos mode, and a chaos meter that tracks your reign of terror.

---

## ✨ Features

### 🪟 Glassmorphism UI
- **DWM Acrylic Blur** — Real Windows 11 backdrop blur, not a fake overlay.
- **Hardware Rounded Corners** — Native `DWMWA_WINDOW_CORNER_PREFERENCE` clipping (no software masking artifacts).
- **Specular Highlights** — Painted top and left edge light refractions over ultra-transparent glass (`0x02` alpha).
- **macOS Traffic Lights** — Close (red), Minimize (yellow), Pin (green) header dots.
- **Always-On-Top + Draggable** — Frameless floating window you can drag anywhere.

### ⌨️ Typing Modes
| Mode | What it does |
|------|-------------|
| 🔤 **Letter** | Pastes and sends one character at a time |
| 💬 **Word** | Pastes and sends one word at a time |
| 📄 **Line** | Pastes and sends one line at a time |

### 🔥 Chaos Mode
Toggle **Chaos: ON** to randomly transform outgoing text with:
- aLtErNaTiNg cApS
- 🤪 Random emoji injection
- Reversed text
- FULL CAPS SCREAMING

### 📦 Prank Packs
Pre-loaded text packs selectable from a dropdown:
- **🤡 Emoji Flood** — 35 rapid-fire emojis
- **(╯°□°)╯ Kaomoji Spam** — 10 classic text faces (auto-switches to Line mode)
- **📦 ASCII Art Block** — Cat face and emoji art blocks
- **📢 Escalating CAPS** — Passive-aggressive message escalation
- **Custom Input** — Write your own message

### 📊 Chaos Meter
A smooth progress bar that fills from 0% → 100% as you send messages:

| Messages | Rank | Bar Color |
|----------|------|-----------|
| 0 – 9 | 😊 Mild Annoyance | 🟢 Green |
| 10 – 24 | 😈 Nuisance | 🟡 Yellow |
| 25 – 49 | 🔥 Menace | 🟠 Orange |
| 50 – 99 | 💀 Certified Chaos Agent | 🔴 Red |
| 100+ | 👑 GOD OF TROLLING | 🟣 Purple |

- The **entire bar** shifts to the current tier's color (unified, no segments).
- Count **persists across runs** — only resets when you close the app.

### 🛡️ Clipboard Protection
- **Auto Backup** — Saves your clipboard before typing starts.
- **Auto Restore** — Restores your original clipboard when typing finishes.
- **Lock Retry** — Retries clipboard operations up to 3× to handle transient Win32 clipboard locks.

### ⚡ Performance
- **Zero-CPU Idle** — The glow animation timer is completely stopped when not typing.
- **Humanized Jitter** — ±35% random delay variation with 5% chance of extra pause for natural-feeling typing.
- **60ms Paste-Enter Delay** — Tuned for Electron-based chat apps (Discord, WhatsApp Web).

### ⌨️ Global Hotkeys
| Key | Action |
|-----|--------|
| `F5` | Start typing |
| `F8` | Pause / Resume |
| `ESC` | Emergency abort |

Works globally via `pynput` — no need to focus the app window.

---

## 🏗️ Architecture

```
annoy_app/
├── __init__.py
├── config.py                # Constants, themes, prank packs, chat app whitelist
├── core/
│   ├── win32_dwm.py         # DWM acrylic blur + rounded corner Win32 APIs
│   ├── clipboard.py         # ClipboardGuard — backup, retry, restore
│   ├── engine.py            # WorkerSignals + chaos text transforms
│   └── window_focus.py      # Chat app window focus utilities
└── ui/
    ├── glass_widget.py      # Main glassmorphism widget (UI + typing loop)
    └── assets/
        ├── arrow_up.svg     # Spinbox up arrow
        └── arrow_down.svg   # Spinbox down arrow
main.py                      # ~17-line entry point
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Windows 10/11** (required for DWM Acrylic Blur APIs)

### Install

```powershell
pip install -r requirements.txt
```

### Run

```powershell
python main.py
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt6` | UI framework |
| `pyautogui` | Simulated keyboard input (Ctrl+V, Enter) |
| `pyperclip` | Cross-platform clipboard access |
| `pynput` | Global hotkey listener (F5, F8, ESC) |
| `pywinauto` | Window enumeration utilities |
| `comtypes` | COM interface support |

---

## 🎮 How to Use

1. **Launch** → `python main.py`
2. **Pick a prank pack** or type your own message
3. **Choose a mode** — Letter, Word, or Line
4. **Toggle Chaos** if you want random text transforms
5. **Set delays** — message delay and start countdown
6. **Click Start (F5)** → quickly click into your target chat window during the countdown
7. Watch the chaos meter fill up as messages fly 🔥
8. **F8** to pause, **ESC** to abort at any time

---

## 📄 License

MIT

"""
Worker signals and chaos text transform logic.
"""
import random
from PyQt6.QtCore import QObject, pyqtSignal

def apply_chaos_transform(text):
    transforms = [
        lambda t: "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(t)),
        lambda t: "".join({'a':'4','A':'4','e':'3','E':'3','i':'1','I':'1','o':'0','O':'0','s':'5','S':'5','t':'7','T':'7'}.get(c, c) for c in t),
        lambda t: "".join(c.upper() if random.random() > 0.45 else c.lower() for c in t),
        lambda t: "".join(c + (random.choice([chr(i) for i in range(0x0300, 0x034f)]) if c.isalnum() and random.random() > 0.35 else "") for c in t)
    ]
    return random.choice(transforms)(text)

class WorkerSignals(QObject):
    update_status = pyqtSignal(str, str)
    update_meter = pyqtSignal(int)
    finished = pyqtSignal(str)
    trigger_glitch = pyqtSignal(int)
    request_start = pyqtSignal()
    request_pause = pyqtSignal()
    request_stop = pyqtSignal()

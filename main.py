import os
import sys

# Suppress Qt QPA Windows DPI context warning
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window.warning=false"

from PyQt6.QtWidgets import QApplication
from annoy_app.ui.glass_widget import AppleGlassCardWidget

def main():
    app = QApplication(sys.argv)
    widget = AppleGlassCardWidget()
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

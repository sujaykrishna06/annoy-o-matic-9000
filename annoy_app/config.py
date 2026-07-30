"""
Application configuration constants, theme palettes, and prank pack presets.
"""

GLASS_TRANSPARENCY_ALPHA = 0x02  # Ultra transparent glass
GLASS_COLOR_RGB = (0x12, 0x12, 0x16)  # Dark glass tint RGB
CORNER_RADIUS = 9  # DWM 9px corner curvature

# Paste-to-Enter micro-delay (60ms default for reliable Electron/Web chat app processing)
PASTE_ENTER_DELAY_MS = 0.06

# Whitelist of target chat app executable process names (case-insensitive)
CHAT_APP_EXECUTABLES = [
    "WhatsApp.exe",
    "Discord.exe",
    "Telegram.exe",
    "Messenger.exe",
    "slack.exe",
    "Teams.exe",
    "Signal.exe",
    "skype.exe"
]

PRANK_PACKS = {
    "Custom Input": None,
    "🤡 Emoji Flood": "🤡 💥 🔥 💀 🚀 👀 ✨ 🤪 👺 🎃 🤖 👽 👾 🎭 💣 🍿 🌶️ 🗿 🌮 🍉 🎪 🎡 🌋 🪐 🔮 🎯 🧨 🌀 💎 🛸 🏆 🎁 🥳 👑 ⚡",
    " (╯°□°)╯ Kaomoji Spam": "( ͡° з ͡°)\n(╯°□°)╯︵ ┻━┻\n¯\\_(ツ)_/¯\n(⊙_☉)\n(•_•) ( •_•)>⌐■-■ (⌐■_■)\nಠ_ಠ\n(ง'̀-'́)ง\n(づ｡◕‿‿◕｡)づ\n(╯3╰)\n(t(-_-t))",
    "📦 ASCII Art Block": "  /\\_/\\\n ( o.o )\n  > ^ <\n---------\n  (>.<)\n----------\n /|_|\\\n(='.'=)",
    "📢 Escalating CAPS": "hey\nhey you\nHEY YOU\nHEYYY YOU\nCAN YOU HEAR ME\nRESPOND PLEASE\nHELLO???\nOK FINE BYE\nWAIT NO HELLO\nI AM INSIDE YOUR PHONE"
}

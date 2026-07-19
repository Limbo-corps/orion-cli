# tui/theme.py
#
# Dark, JARVIS-grade palette: near-black mono base + a glowing arc-reactor
# cyan for ORION and a soft violet for the user, chat-bubble style.

BG = "#0b0c0e"  # app background (near black)
PANEL = "#101216"  # panel background
FG = "#e2e6ea"  # primary text
MUTED = "#8a929c"  # secondary text
DIM = "#4a4f57"  # tertiary text / separators
BORDER = "#242a31"  # neutral panel borders

# --- ORION identity (arc-reactor cyan) ---
ORION_ACCENT = "#35c9ff"  # ORION name / icon
ORION_EDGE = "#2597c9"  # ORION bubble border (the glowing edge)
ORION_BUBBLE = "#0d1a22"  # ORION bubble fill (very dark cyan tint)
ORION_ICON = "◉"  # arc-reactor glyph beside the name

# --- User identity (soft violet) ---
USER_ACCENT = "#b9a7ff"  # user name
USER_EDGE = "#7c5cff"  # user bubble border
USER_BUBBLE = "#141327"  # user bubble fill (very dark violet tint)
# The user's messages are always labelled "Me" in the UI, regardless of
# their actual name. ORION still learns and uses the real name in
# conversation (via memory) — it just isn't shown as the bubble label.
USER_NAME = "Me"

# --- Status states ---
DANGER = "#e0736f"  # errors (muted red)
OK = "#8fce9b"  # success (muted green)

STATE_COLORS = {
    "IDLE": MUTED,
    "RECORDING": DANGER,
    "TRANSCRIBING": ORION_ACCENT,
    "THINKING": ORION_ACCENT,
    "SYNTHESIZING": ORION_ACCENT,
    "ERROR": DANGER,
}

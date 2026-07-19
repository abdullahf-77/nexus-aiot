# =============================================================================
# config.py
# Nexus AIoT  |  AI-Powered Touchless Smart Environment System
# Central configuration — edit here to tune any aspect of the system.
# =============================================================================

# ── Project Identity ──────────────────────────────────────────────────────────
PROJECT_NAME     = "Nexus AIoT"
PROJECT_SUBTITLE = "AI-Powered Touchless Smart Environment System"
PROJECT_VERSION  = "v4.4"
WINDOW_TITLE     = "Nexus AIoT  |  AI-Powered Touchless Smart Environment System"

# ── Window & Layout ───────────────────────────────────────────────────────────
WIN_W  = 1280
WIN_H  = 720
CAM_W  = 460
CAM_H  = 345

# =============================================================================
# COLOR PALETTE  —  Soft-Dark Premium Theme  (all values are BGR for OpenCV)
#
# Design language:
#   • Three-layer depth: canvas → panel → card  (each ~8 BGR units lighter)
#   • One primary accent (soft teal #2ABFBF) + one secondary (calm blue #4A90D9)
#   • Warm-white text hierarchy: primary / body / muted  (never pure 255,255,255)
#   • Semantic status colors: muted, not neon
#   • Borders are 1 step above the surface they sit on — barely visible
#   • Shadows are 1 step below the canvas — they deepen the depth illusion
#
# Reference hex → BGR conversion table (for human readability):
#   Canvas  #1E1E22  →  (34,  30,  30)    Panels  #26262C  →  (44,  38,  38)
#   Cards   #2E2E36  →  (54,  46,  46)    CardAlt #323239  →  (57,  50,  50)
#   Accent  #2ABFBF  →  (191, 191,  42)   Blue    #4A90D9  →  (217, 144,  74)
#   PrimTxt #E8E8EC  →  (236, 232, 232)   BodyTxt #A8A8B0  →  (176, 168, 168)
#   Muted   #606070  →  (112, 96,  96)    Border  #3C3C46  →  (70,  60,  60)
# =============================================================================

# ── Canvas & panel layers ─────────────────────────────────────────────────────
C_BG            = ( 34,  30,  30)    # #1E1E22  deepest background canvas
C_PANEL         = ( 44,  38,  38)    # #26262C  panel / sidebar surface
C_CARD          = ( 54,  46,  46)    # #2E2E36  card surface (elevated)
C_CARD_ALT      = ( 57,  50,  50)    # #323239  alternate card (slightly warmer)
C_CARD_DEEP     = ( 40,  34,  34)    # #222228  recessed / inset surface
C_SHADOW        = ( 22,  18,  18)    # #121216  shadow beneath cards

# ── Primary accent — soft teal / cyan ────────────────────────────────────────
C_ACCENT        = (191, 191,  42)    # #2ABFBF  primary interactive teal
C_ACCENT_LO     = (130, 130,  30)    # dimmed teal for outer rings / secondary
C_ACCENT_HI     = (215, 218,  90)    # brighter teal — freshly appeared log line
C_ACCENT_BG     = ( 65,  56,  36)    # very dark teal tint (card accent bg)
C_ACCENT_BORDER = ( 95,  90,  35)    # teal-tinted border

# ── Secondary accent — calm steel blue ───────────────────────────────────────
C_BLUE          = (217, 144,  74)    # #4A90D9  calm blue
C_BLUE_LO       = (150,  95,  50)    # dimmed blue
C_BLUE_BG       = ( 62,  50,  36)    # very dark blue tint

# ── Text hierarchy ────────────────────────────────────────────────────────────
C_TEXT_PRIMARY  = (236, 232, 232)    # warm near-white — headings & key values (~9:1 on card)
C_TEXT_BODY     = (195, 190, 190)    # medium gray — body text             (~6:1 on card)
C_TEXT_MUTED    = (148, 142, 142)    # soft gray — labels, hints           (~3.8:1 on card)

# ── Status semantics ──────────────────────────────────────────────────────────
C_SUCCESS       = ( 80, 200, 100)    # muted emerald green — ON / active
C_SUCCESS_BG    = ( 48,  58,  36)    # dark green tint
C_SUCCESS_BORD  = ( 65,  90,  40)    # green-tinted border

C_WARNING       = ( 60, 150, 220)    # muted amber — cooldown / caution
C_WARNING_BG    = ( 52,  50,  38)    # dark amber tint
C_WARNING_BORD  = ( 68,  72,  45)    # amber-tinted border

C_DANGER        = ( 80,  80, 210)    # muted red-orange — locked / alert
C_DANGER_BG     = ( 55,  38,  40)    # dark red tint
C_DANGER_BORD   = ( 72,  44,  50)    # red-tinted border

C_STANDBY       = ( 75,  70,  68)    # flat gray — inactive / OFF
C_STANDBY_BG    = ( 46,  42,  42)    # near-card gray for standby cards

# ── Accessibility ─────────────────────────────────────────────────────────────
C_ACCESS        = (110, 200, 130)    # soft sage green
C_ACCESS_BG     = ( 46,  58,  36)    # dark sage tint

# ── Borders & dividers ────────────────────────────────────────────────────────
C_BORDER        = ( 68,  60,  60)    # card border — 1 step above card
C_BORDER_LO     = ( 58,  52,  52)    # very subtle border (almost invisible)
C_DIVIDER       = ( 62,  56,  56)    # horizontal rule inside cards

# ── Mode accent palette ───────────────────────────────────────────────────────
# Each mode has (pill_bg, pill_fg, button_active_bg, button_active_border)
MODE_COLORS = {
    "NORMAL":    (C_ACCENT_BG,    C_ACCENT,   C_ACCENT_BG,    C_ACCENT),
    "STUDY":     (C_BLUE_BG,      C_BLUE,     C_BLUE_BG,      C_BLUE),
    "SLEEP":     (C_BLUE_BG,      C_BLUE_LO,  C_BLUE_BG,      C_BLUE_LO),
    "CINEMA":    (( 52, 40, 56),  (180, 80, 200), ( 52, 40, 56), (180, 80, 200)),
    "GAMING":    (C_WARNING_BG,   C_WARNING,  C_WARNING_BG,   C_WARNING),
    "SECURITY":  (C_DANGER_BG,    C_DANGER,   C_DANGER_BG,    C_DANGER),
    "EMERGENCY": (C_DANGER_BG,    C_DANGER,   C_DANGER_BG,    C_DANGER),
}

# Legacy alias kept so face_module / password_module don't need changes
C_WHITE = C_TEXT_PRIMARY

# ── Gesture Engine ────────────────────────────────────────────────────────────
GESTURE_COOLDOWN    = 1.4    # seconds between accepted gesture triggers
GESTURE_HOLD_FRAMES = 7      # frames same gesture must hold before accepted

# ── OK Sign (mode cycling) detection threshold ────────────────────────────────
# Thumb tip (4) to index tip (8) distance, normalised by hand_size
# (wrist-to-middle-MCP distance).  Must be BELOW this value to count as pinch.
# Empirical range:   pinching   ≈ 0.08 – 0.22
#                    not pinching ≈ 0.28 – 0.80
# Set conservatively at 0.25 — easy to form deliberately, hard to trigger by accident.
OK_PINCH_RATIO = 0.25

# ── Gesture Password ──────────────────────────────────────────────────────────
PASSWORD_SEQUENCE = ["Thumbs Up", "Peace Sign", "Open Palm"]
PASSWORD_TIMEOUT  = 8.0

# ── Boot Sequence ─────────────────────────────────────────────────────────────
BOOT_MESSAGES = [
    ("Nexus AIoT  v4.4", 0.0),
    ("Initializing AI Core...", 0.6),
    ("Loading MediaPipe Gesture Engine...", 1.3),
    ("Activating Computer Vision Pipeline...", 2.1),
    ("Face Detection Module Ready...", 2.9),
    ("Voice Synthesis Interface Online...", 3.6),
    ("Accessibility Module Loaded...", 4.3),
    ("Smart Environment Interface Active...", 5.0),
    ("AIoT Integration Complete...", 5.7),
    ("ALL SYSTEMS OPERATIONAL", 6.3),
]
BOOT_DURATION = 7.0

# ── Voice & Sound ─────────────────────────────────────────────────────────────
VOICE_ENABLED = True
SOUND_ENABLED = True

# ── Analytics ─────────────────────────────────────────────────────────────────
MAX_LOG_ENTRIES = 7

# ── Accessibility ─────────────────────────────────────────────────────────────
ACCESSIBILITY_GESTURE = "ILY Sign"

# =============================================================================
# ui_renderer.py
# Nexus AIoT  |  Sharp Premium Dashboard  v4.2
#
# Readability-first design decisions:
#
#  TEXT RENDERING
#   • FONT_HERSHEY_SIMPLEX instead of DUPLEX — Simplex has thinner strokes
#     that scale more crisply at small sizes.  DUPLEX adds weight that smears.
#   • bold=True raises thickness to 2 ONLY for scale >= 0.55.  Below that,
#     thickness stays at 1 — thicker strokes on small glyphs create mud.
#   • Minimum rendered scale is 0.40 (≈ 12 px cap height at 1280 wide).
#     Labels that were 0.32–0.34 are raised to 0.40.
#   • Three explicit text levels: HEADING (0.52 bold), BODY (0.44), LABEL (0.40)
#
#  CONTRAST
#   • C_TEXT_PRIMARY  → (236,232,232)  on C_CARD (54,46,46)  ≈ 9:1
#   • C_TEXT_BODY     → (190,186,186)  on C_CARD (54,46,46)  ≈ 5:1
#   • C_TEXT_MUTED    → (140,135,135)  on C_CARD (54,46,46)  ≈ 3.5:1  min label
#   All three pass the 3:1 minimum for non-decorative text.
#
#  ALPHA / BLEND ELIMINATION
#   • _glow_dot() alpha halo removed.  Status dot is now a clean solid circle
#     + an opaque ring. Zero blending == zero smear around nearby text.
#   • _divider() alpha blend removed; drawn as a direct cv2.line (opaque).
#   • _shadow_rect() shadow depth raised from 2–3 px to a distinct 4 px and
#     drawn in C_SHADOW — no alpha, purely positional offset.
#   • Notification banner: drawn opaque when visible, removed during fade
#     rather than blending at 0.94 over the whole scene.
#   • Flash overlay capped at 0.25 alpha (was 0.40) and only during active
#     flash frames.
#
#  SPACING
#   • Section headings now sit 4px above the card top border.
#   • Line-height for multi-line areas raised from 22 → 26 px.
#   • Card internal padding standardised to 14px left / 10px top.
#
#  EFFECTS REMOVED
#   • Pulsing halo on glow_dot  (addWeighted per frame)
#   • Animated outer rings on boot screen  (4× addWeighted per frame)
#   • Divider alpha blend
#   • Notification full-canvas blend
#
# Layout 1280 x 720  (unchanged):
#   ┌──────────────────────────────────────────────────────────────┐
#   │  HEADER  52 px                                               │
#   ├────────────┬──────────────────┬───────────────────────────── ┤
#   │ LEFT ~482  │  MIDDLE ~352     │  RIGHT  ~378                 │
#   │  Camera    │  7 Device cards  │  Gesture guide               │
#   │  Cooldown  │  Smart modes     │  Analytics                   │
#   │  Gesture   │                  │  Voice / Access              │
#   │  Password  │                  │                              │
#   ├────────────┴──────────────────┴──────────────────────────────┤
#   │  FOOTER  36 px                                               │
#   └──────────────────────────────────────────────────────────────┘
# =============================================================================

import cv2
import numpy as np
import time
import math
import config

# ─────────────────────────────────────────────────────────────────────────────
# FONT CONSTANTS  — one place to change the whole UI's type
# ─────────────────────────────────────────────────────────────────────────────
# SIMPLEX has thinner, cleaner strokes than DUPLEX at small sizes.
_FONT       = cv2.FONT_HERSHEY_SIMPLEX
_FONT_BOLD  = cv2.FONT_HERSHEY_DUPLEX   # used only for scale >= 0.55

# Typography scale ladder (approximate cap-height at 1280-wide window)
#   HEADING : 0.52 → ~18 px cap height — section titles, card headers
#   BODY    : 0.44 → ~15 px — values, gesture names, status text
#   LABEL   : 0.40 → ~13 px — small labels, hints, footer
_S_HEAD  = 0.52
_S_BODY  = 0.44
_S_LABEL = 0.40


# ─────────────────────────────────────────────────────────────────────────────
# PRIMITIVE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _clamp(x, y, w, h, iw, ih):
    x = max(0, int(x)); y = max(0, int(y))
    w = max(0, min(int(w), iw - x))
    h = max(0, min(int(h), ih - y))
    return x, y, w, h


def _rect(img, x, y, w, h, color, radius=10):
    """Solid filled rounded rectangle — zero alpha, pixel-perfect edges."""
    if w <= 0 or h <= 0:
        return
    iw, ih = img.shape[1], img.shape[0]
    x, y, w, h = _clamp(x, y, w, h, iw, ih)
    if w <= 0 or h <= 0:
        return
    r = max(0, min(int(radius), w // 2, h // 2))
    if r < 2:
        cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
        return
    cv2.rectangle(img, (x + r, y),     (x + w - r, y + h),     color, -1)
    cv2.rectangle(img, (x,     y + r), (x + w,     y + h - r), color, -1)
    for cx, cy in [(x+r, y+r), (x+w-r, y+r), (x+r, y+h-r), (x+w-r, y+h-r)]:
        cv2.circle(img, (cx, cy), r, color, -1)


def _card(img, x, y, w, h, color, radius=12):
    """
    Card with a sharp drop shadow.
    Shadow is a solid C_SHADOW rect at +4,+4 offset — no blending.
    """
    _rect(img, x + 4, y + 4, w, h, config.C_SHADOW, radius)
    _rect(img, x,     y,     w, h, color,            radius)


def _border(img, x, y, w, h, color, thickness=1, radius=10):
    """Rounded border outline — sharp, no antialiasing on straight edges."""
    if w <= 0 or h <= 0:
        return
    iw, ih = img.shape[1], img.shape[0]
    x, y, w, h = _clamp(x, y, w, h, iw, ih)
    if w <= 0 or h <= 0:
        return
    r = max(0, min(int(radius), w // 2, h // 2))
    if r < 2:
        cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness)
        return
    cv2.line(img, (x+r,   y),     (x+w-r, y),     color, thickness)
    cv2.line(img, (x+r,   y+h),   (x+w-r, y+h),   color, thickness)
    cv2.line(img, (x,     y+r),   (x,     y+h-r), color, thickness)
    cv2.line(img, (x+w,   y+r),   (x+w,   y+h-r), color, thickness)
    for cx, cy, a1, a2 in [
        (x+r,   y+r,   180, 270), (x+w-r, y+r,   270, 360),
        (x+r,   y+h-r,  90, 180), (x+w-r, y+h-r,   0,  90),
    ]:
        cv2.ellipse(img, (cx, cy), (r, r), 0, a1, a2,
                    color, thickness, cv2.LINE_AA)


def _txt(img, text, x, y,
         scale=_S_BODY, color=None, bold=False, font=None):
    """
    Sharp text.  Rules:
      • thickness=2 only when scale >= 0.55 AND bold=True
      • thickness=1 for everything else — thinner strokes = sharper glyphs
      • Uses _FONT (SIMPLEX) by default; pass font=_FONT_BOLD for headings
    """
    c  = color if color is not None else config.C_TEXT_PRIMARY
    f  = font if font is not None else (_FONT_BOLD if bold and scale >= 0.55 else _FONT)
    th = 2 if (bold and scale >= 0.55) else 1
    cv2.putText(img, str(text), (int(x), int(y)),
                f, scale, c, th, cv2.LINE_AA)


def _divider(img, x1, x2, y, color=None):
    """1-pixel horizontal rule. Direct draw — no blending, no smear."""
    c = color or config.C_DIVIDER
    cv2.line(img, (int(x1), int(y)), (int(x2), int(y)), c, 1)


def _pill(img, x, y, w, h, bg, text, fg, scale=_S_LABEL):
    """Filled pill badge with centered text."""
    _rect(img, x, y, w, h, bg, radius=h // 2)
    # Centre text: rough estimate (no getTextSize to keep it fast)
    tx = x + max(6, (w - len(text) * int(scale * 11)) // 2)
    ty = y + h // 2 + int(scale * 7)
    _txt(img, text, tx, ty, scale=scale, color=fg, bold=True)


def _bar(img, x, y, w, h, pct, track, fill, radius=4):
    """Simple progress bar — fully opaque."""
    _rect(img, x, y, w, h, track, radius)
    fw = max(0, int(w * min(pct, 1.0)))
    if fw > 0:
        _rect(img, x, y, fw, h, fill, radius)


def _dot(img, cx, cy, r, active, t=0, idx=0):
    """
    Status indicator dot — no alpha blending.
    Active:  filled teal-green circle + bright ring (opaque).
    Standby: filled muted-gray circle.
    Pulse is simulated by varying the ring radius via math.sin.
    """
    if active:
        # Outer ring pulses size but stays opaque
        ring_r = r + 3 + int(2 * math.sin(t * 3.0 + idx * 1.1))
        cv2.circle(img, (cx, cy), ring_r, config.C_SUCCESS_BORD, 1)
        cv2.circle(img, (cx, cy), r,      config.C_SUCCESS,      -1)
    else:
        cv2.circle(img, (cx, cy), r, config.C_STANDBY, -1)


# ─────────────────────────────────────────────────────────────────────────────
# BOOT SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def draw_boot(canvas, elapsed, messages):
    """
    Sharp dark boot screen.
    All drawing is opaque — no addWeighted calls in the hot path.
    Returns True when boot duration is complete.
    """
    H, W = canvas.shape[:2]
    t    = elapsed

    # Solid background
    canvas[:] = config.C_BG

    # ── Dot grid (direct pixel write — no alpha) ──────────────────────
    dot_col = (config.C_BG[0] + 12, config.C_BG[1] + 10, config.C_BG[2] + 10)
    for gx in range(0, W, 44):
        for gy in range(0, H, 44):
            if 0 <= gx < W and 0 <= gy < H:
                canvas[gy, gx] = dot_col

    # ── Logo ring ─────────────────────────────────────────────────────
    cx, cy  = W // 2, H // 2 - 80
    base_r  = 64

    # Static outer ring (opaque, no blend)
    cv2.circle(canvas, (cx, cy), base_r + 18,
               config.C_ACCENT_LO, 1, cv2.LINE_AA)

    # Pulsing main ring — solid, no blend
    pulse_r = base_r + int(5 * math.sin(t * 2.2))
    cv2.circle(canvas, (cx, cy), pulse_r,
               config.C_ACCENT, 2, cv2.LINE_AA)

    # Solid centre disc
    cv2.circle(canvas, (cx, cy), 10, config.C_ACCENT, -1)

    # Four rotating tick marks — opaque lines
    for i in range(4):
        angle = math.radians(90 * i + t * 28)
        r1 = base_r - 8;  r2 = base_r + 8
        x1 = int(cx + r1 * math.cos(angle))
        y1 = int(cy + r1 * math.sin(angle))
        x2 = int(cx + r2 * math.cos(angle))
        y2 = int(cy + r2 * math.sin(angle))
        cv2.line(canvas, (x1, y1), (x2, y2),
                 config.C_ACCENT_HI, 2, cv2.LINE_AA)

    # ── Project name + subtitle ───────────────────────────────────────
    name_y = cy + base_r + 50
    _txt(canvas, "Nexus AIoT",
         W // 2 - 130, name_y,
         scale=1.10, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)

    _txt(canvas, "AI-Powered Touchless Smart Environment System",
         W // 2 - 258, name_y + 36,
         scale=_S_BODY, color=config.C_TEXT_BODY)

    # Accent underline — opaque rect
    _rect(canvas, W // 2 - 110, name_y + 10, 220, 2, config.C_ACCENT, radius=1)

    # ── Boot log ──────────────────────────────────────────────────────
    log_y = name_y + 60
    for msg, start_t in messages:
        if elapsed < start_t:
            break
        age = elapsed - start_t
        c   = config.C_ACCENT if age < 0.4 else config.C_TEXT_BODY
        _txt(canvas, msg, W // 2 - 230, log_y, scale=_S_LABEL, color=c)
        log_y += 26

    # ── Progress bar ──────────────────────────────────────────────────
    bar_x = W // 2 - 220
    bar_y = H - 58
    bar_w = 440
    pct   = min(elapsed / config.BOOT_DURATION, 1.0)

    _bar(canvas, bar_x, bar_y, bar_w, 5, pct,
         config.C_CARD_DEEP, config.C_ACCENT, radius=2)

    _txt(canvas, f"{int(pct * 100)}%",
         bar_x + bar_w + 12, bar_y + 10,
         scale=_S_LABEL, color=config.C_ACCENT)

    _txt(canvas, "Initializing system components...",
         bar_x, bar_y + 22,
         scale=_S_LABEL, color=config.C_TEXT_MUTED)

    return elapsed >= config.BOOT_DURATION


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD RENDERER
# ─────────────────────────────────────────────────────────────────────────────

class DashboardRenderer:
    """Main stateful renderer. Call render() once per frame."""

    def __init__(self):
        self._t0         = time.time()
        self._frame      = 0
        self._flash      = 0
        self._gd         = None
        self._notif_text = ""
        self._notif_t    = 0.0
        self._notif_dur  = 2.6

    def trigger_flash(self):
        self._flash = 8

    def notify(self, text):
        self._notif_text = str(text)
        self._notif_t    = time.time()

    # ─────────────────────────────────────────────────────────────────
    def render(self, canvas, cam_frame, room, gesture_det,
               face_mod, pwd_mod, voice_mod, fps):
        self._frame += 1
        self._gd     = gesture_det
        t            = time.time() - self._t0

        W, H = config.WIN_W, config.WIN_H
        canvas[:] = config.C_BG

        # Layout constants
        HDR_H  = 54
        FTR_H  = 36
        PAD    = 9
        BODY_Y = HDR_H + PAD
        BODY_H = H - HDR_H - FTR_H - PAD * 2

        LEFT_W = config.CAM_W + 24        # ≈ 484
        MID_W  = 348
        LEFT_X = PAD
        MID_X  = LEFT_X + LEFT_W + PAD
        RGT_X  = MID_X + MID_W + PAD
        RGT_W  = W - RGT_X - PAD

        self._header(canvas, t, room, fps, W, HDR_H)
        self._left  (canvas, cam_frame, room, gesture_det,
                     pwd_mod, face_mod, LEFT_X, BODY_Y, LEFT_W, BODY_H, t)
        self._middle(canvas, room,      MID_X, BODY_Y, MID_W, BODY_H, t)
        self._right (canvas, room, gesture_det, voice_mod, face_mod,
                     RGT_X, BODY_Y, RGT_W, BODY_H, t)
        self._footer(canvas, room, W, H, FTR_H)
        self._notif (canvas, W, H)

    # ═════════════════════════════════════════════════════════════════
    # HEADER
    # ═════════════════════════════════════════════════════════════════
    def _header(self, canvas, t, room, fps, W, H):
        _rect(canvas, 0, 0, W, H, config.C_PANEL, radius=0)
        # Bottom accent line — 2 px, opaque
        _rect(canvas, 0, H - 2, W, 2, config.C_ACCENT, radius=0)

        # Logo tile
        _rect(canvas, 12, 11, 30, 30, config.C_ACCENT, radius=6)
        _txt(canvas, "N", 17, 33,
             scale=0.64, color=config.C_BG, bold=True, font=_FONT_BOLD)

        # Product name
        _txt(canvas, "Nexus AIoT", 50, 26,
             scale=0.64, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)
        _txt(canvas, "AI-Powered Touchless Smart Environment System",
             50, 43, scale=_S_LABEL, color=config.C_TEXT_MUTED)

        # Active mode pill — center
        mode    = room.current_mode
        mc      = config.MODE_COLORS.get(mode,
                  (config.C_ACCENT_BG, config.C_ACCENT, None, config.C_ACCENT))
        pill_bg = mc[0];  pill_fg = mc[1]
        px      = W // 2 - 70
        _rect  (canvas, px,     13, 140, 26, pill_bg, radius=13)
        _border(canvas, px,     13, 140, 26, mc[3] or pill_fg, radius=13)
        _txt   (canvas, mode,   px + 14, 31,
                scale=_S_LABEL, color=pill_fg, bold=True)

        # Lock status pill
        locked = room.system_locked
        lb     = config.C_DANGER_BG  if locked else config.C_SUCCESS_BG
        lbrd   = config.C_DANGER     if locked else config.C_SUCCESS
        ltxt   = "LOCKED"            if locked else "UNLOCKED"
        _rect  (canvas, W - 248, 14,  96, 24, lb,   radius=12)
        _border(canvas, W - 248, 14,  96, 24, lbrd, radius=12)
        _txt   (canvas, ltxt, W - 240, 31,
                scale=_S_LABEL, color=lbrd, bold=True)

        # Clock
        _txt(canvas, time.strftime("%H:%M:%S"),
             W - 140, 30, scale=0.54,
             color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)
        _txt(canvas, f"{fps} fps",
             W - 44, 30, scale=_S_LABEL, color=config.C_TEXT_MUTED)

    # ═════════════════════════════════════════════════════════════════
    # LEFT COLUMN
    # ═════════════════════════════════════════════════════════════════
    def _left(self, canvas, cam_frame, room, gesture_det,
              pwd_mod, face_mod, x, y, w, h, t):
        PAD   = 8
        cur_y = y

        # ── Camera card ───────────────────────────────────────────────
        cw, ch  = config.CAM_W, config.CAM_H
        cam_h   = ch + 32
        _card  (canvas, x, cur_y, w, cam_h, config.C_CARD, radius=12)
        _border(canvas, x, cur_y, w, cam_h, config.C_BORDER, radius=12)

        # Card title
        _txt(canvas, "Live Vision Feed",
             x + 14, cur_y + 18,
             scale=_S_LABEL, color=config.C_TEXT_MUTED)

        # Face status pill — top-right of card
        fa     = face_mod.authorized
        fp     = face_mod.face_present
        fs_bg  = config.C_SUCCESS_BG if fa else config.C_WARNING_BG if fp else config.C_CARD_DEEP
        fs_brd = config.C_SUCCESS    if fa else config.C_WARNING    if fp else config.C_BORDER
        fs_txt = ("Authorized" if fa else "Unknown" if fp else "No Face")
        _rect  (canvas, x + w - 120, cur_y + 8,  108, 20, fs_bg,  radius=10)
        _border(canvas, x + w - 120, cur_y + 8,  108, 20, fs_brd, radius=10)
        _txt   (canvas, fs_txt, x + w - 114, cur_y + 21,
                scale=_S_LABEL, color=fs_brd, bold=True)

        # Camera image — direct blit, no blend
        cam_x = x + (w - cw) // 2
        cam_y = cur_y + 24
        cam   = cv2.resize(cam_frame, (cw, ch))

        # Flash: very light opaque tint overlay
        if self._flash > 0:
            alpha = (self._flash / 8.0) * 0.22   # max 22% tint
            tint  = np.full_like(cam, config.C_ACCENT_BG)
            cam   = cv2.addWeighted(cam, 1.0 - alpha, tint, alpha, 0)
            self._flash -= 1

        cam = face_mod.draw(cam)
        canvas[cam_y:cam_y + ch, cam_x:cam_x + cw] = cam
        _border(canvas, cam_x - 1, cam_y - 1, cw + 2, ch + 2,
                config.C_BORDER, radius=4)

        cur_y += cam_h + PAD

        # ── Cooldown bar ──────────────────────────────────────────────
        cd    = self._gd.cooldown_pct() if self._gd else 1.0
        ready = cd >= 1.0
        c_f   = config.C_ACCENT  if ready else config.C_WARNING
        c_t   = config.C_CARD_DEEP

        _rect(canvas, x, cur_y, w, 16, c_t, radius=8)
        fw = max(0, int(w * cd))
        if fw > 0:
            _rect(canvas, x, cur_y, fw, 16, c_f, radius=8)

        # Label on the bar — only drawn when bar is wide enough
        if cd > 0.15:
            lbl = "Ready" if ready else \
                  f"Cooldown  {(1-cd)*(self._gd.COOLDOWN if self._gd else 1.4):.1f}s"
            # White text if bar fills the label area, else use accent color
            lc = config.C_BG if (fw > 72 and ready) else c_f
            _txt(canvas, lbl, x + 10, cur_y + 11,
                 scale=_S_LABEL, color=lc)

        cur_y += 16 + PAD

        # ── Gesture status card ───────────────────────────────────────
        gest_h = 80
        _card  (canvas, x, cur_y, w, gest_h, config.C_CARD, radius=12)
        _border(canvas, x, cur_y, w, gest_h, config.C_BORDER, radius=12)

        raw    = self._gd.raw_gesture   if self._gd else "No Hand"
        hold   = self._gd._hold_count   if self._gd else 0
        req    = self._gd.HOLD_REQUIRED if self._gd else 7
        active = raw not in ("No Hand", "Unknown")

        _txt(canvas, "Detected Gesture",
             x + 14, cur_y + 18,
             scale=_S_LABEL, color=config.C_TEXT_MUTED)

        # Large gesture name — the most important piece of information
        if raw == config.ACCESSIBILITY_GESTURE:
            gc = config.C_ACCESS
        elif active:
            gc = config.C_ACCENT_HI
        else:
            gc = config.C_TEXT_MUTED

        _txt(canvas, raw, x + 14, cur_y + 52,
             scale=0.68, color=gc, bold=active, font=_FONT_BOLD if active else _FONT)

        # Hold-stability dots — opaque, no blend
        dot_x0 = x + w - req * 12 - 14
        for i in range(req):
            dc = config.C_ACCENT if i < hold else config.C_CARD_DEEP
            cv2.circle(canvas, (dot_x0 + i * 12, cur_y + 24), 4, dc, -1)

        # Last action — body-weight text
        _txt(canvas, room.last_action[:44],
             x + 14, cur_y + gest_h - 10,
             scale=_S_LABEL, color=config.C_TEXT_BODY)

        cur_y += gest_h + PAD

        # ── Password card ─────────────────────────────────────────────
        pwd_h = h - (cur_y - y)
        if pwd_h > 36:
            self._pwd_card(canvas, x, cur_y, w, pwd_h, pwd_mod)

    # ─────────────────────────────────────────────────────────────────
    def _pwd_card(self, canvas, x, y, w, h, pwd_mod):
        state = pwd_mod.state
        bg  = {"SUCCESS":     config.C_SUCCESS_BG,
               "FAILED":      config.C_DANGER_BG,
               "IN_PROGRESS": config.C_WARNING_BG
               }.get(state, config.C_CARD)
        brd = {"SUCCESS":     config.C_SUCCESS_BORD,
               "FAILED":      config.C_DANGER_BORD,
               "IN_PROGRESS": config.C_WARNING_BORD
               }.get(state, config.C_BORDER)

        _card  (canvas, x, y, w, h, bg,  radius=12)
        _border(canvas, x, y, w, h, brd, radius=12)

        _txt(canvas, "Gesture Password",
             x + 14, y + 18,
             scale=_S_LABEL, color=config.C_TEXT_MUTED)

        mc = {"SUCCESS":     config.C_SUCCESS,
              "FAILED":      config.C_DANGER,
              "IN_PROGRESS": config.C_WARNING
              }.get(state, config.C_TEXT_BODY)

        _txt(canvas, pwd_mod.message[:46],
             x + 14, y + 42,
             scale=_S_BODY, color=mc,
             bold=(state in ("SUCCESS", "FAILED")))

        # Sequence dots — opaque
        seq  = len(pwd_mod.sequence)
        done = int(pwd_mod.progress * seq)
        dy   = y + h - 24
        for i in range(seq):
            dc  = config.C_SUCCESS      if i < done else config.C_CARD_DEEP
            bdc = config.C_SUCCESS_BORD if i < done else config.C_BORDER
            cv2.circle(canvas, (x + 18 + i * 24, dy), 8, dc,  -1)
            cv2.circle(canvas, (x + 18 + i * 24, dy), 8, bdc,  1)

        if pwd_mod.hint:
            _txt(canvas, pwd_mod.hint,
                 x + 18 + seq * 24 + 10, dy + 6,
                 scale=_S_LABEL, color=config.C_TEXT_MUTED)

        if state == "IN_PROGRESS":
            _txt(canvas, f"{pwd_mod.time_remaining:.1f}s",
                 x + w - 52, dy + 6,
                 scale=_S_BODY, color=config.C_WARNING, bold=True)

    # ═════════════════════════════════════════════════════════════════
    # MIDDLE COLUMN
    # ═════════════════════════════════════════════════════════════════
    def _middle(self, canvas, room, x, y, w, h, t):
        PAD = 8

        # Section heading — sits directly on canvas (no card bg behind it)
        _txt(canvas, "Smart Devices",
             x + 4, y + 16,
             scale=_S_HEAD, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)

        MODES_H = 84
        dev_top = y + 26
        dev_h   = h - 26 - PAD - MODES_H
        n       = len(room.DEVICE_KEYS)
        CPAD    = 5
        card_h  = max(26, (dev_h - CPAD * (n - 1)) // n)

        labels = {
            "lights":           "Smart Lights",
            "air_conditioner":  "Air Conditioner",
            "door":             "Smart Door",
            "curtains":         "Smart Curtains",
            "security_camera":  "Security Camera",
            "alarm":            "Alarm System",
            "music":            "Music System",
        }

        for i, dev in enumerate(room.DEVICE_KEYS):
            active = room.devices[dev]
            dy     = dev_top + i * (card_h + CPAD)
            bg     = config.C_ACCENT_BG if active else config.C_CARD
            brd    = config.C_ACCENT_BORDER if active else config.C_BORDER

            _card  (canvas, x, dy, w, card_h, bg,  radius=10)
            _border(canvas, x, dy, w, card_h, brd, radius=10)

            # Left accent bar — solid, 3 px
            bar_c = config.C_ACCENT if active else config.C_STANDBY
            cv2.rectangle(canvas,
                          (x + 10, dy + 5),
                          (x + 13, dy + card_h - 5), bar_c, -1)

            # Status dot — opaque ring + fill, no alpha blend
            _dot(canvas, x + 26, dy + card_h // 2, 5, active, t, i)

            # Device label
            nc = config.C_TEXT_PRIMARY if active else config.C_TEXT_BODY
            _txt(canvas, labels.get(dev, dev),
                 x + 40, dy + card_h // 2 + 6,
                 scale=_S_BODY, color=nc, bold=active)

            # Status pill — right
            if active:
                _pill(canvas, x + w - 82, dy + card_h // 2 - 11,
                      68, 22, config.C_SUCCESS_BG,
                      "ACTIVE", config.C_SUCCESS, scale=_S_LABEL)
            else:
                _pill(canvas, x + w - 82, dy + card_h // 2 - 11,
                      68, 22, config.C_STANDBY_BG,
                      "STANDBY", config.C_STANDBY, scale=_S_LABEL)

        # ── Smart modes strip ─────────────────────────────────────────
        my = dev_top + dev_h + PAD
        _txt(canvas, "Smart Modes",
             x + 4, my + 16,
             scale=_S_LABEL, color=config.C_TEXT_MUTED)

        modes  = ["NORMAL","STUDY","SLEEP","CINEMA","GAMING","SECURITY","EMERGENCY"]
        btn_y  = my + 24
        btn_h  = MODES_H - 32
        gap    = 3
        btn_w  = (w - gap * (len(modes) - 1)) // len(modes)

        for i, mode in enumerate(modes):
            bx  = x + i * (btn_w + gap)
            act = room.current_mode == mode
            mc  = config.MODE_COLORS.get(
                  mode, (config.C_CARD, config.C_TEXT_MUTED, None, config.C_BORDER_LO))
            bg  = mc[0] if act else config.C_CARD_DEEP
            brd = mc[3] if act else config.C_BORDER_LO
            lc  = mc[1] if act else config.C_TEXT_MUTED

            _rect  (canvas, bx, btn_y, btn_w, btn_h, bg,  radius=8)
            _border(canvas, bx, btn_y, btn_w, btn_h, brd, radius=8)

            label = mode[:4] if btn_w < 52 else mode[:6]
            tx    = bx + max(3, (btn_w - len(label) * int(_S_LABEL * 11)) // 2)
            _txt(canvas, label,
                 tx, btn_y + btn_h // 2 + 5,
                 scale=_S_LABEL, color=lc, bold=act)

    # ═════════════════════════════════════════════════════════════════
    # RIGHT COLUMN
    # ═════════════════════════════════════════════════════════════════
    def _right(self, canvas, room, gesture_det, voice_mod,
               face_mod, x, y, w, h, t):
        PAD   = 8
        cur_y = y

        # ── Gesture guide card ────────────────────────────────────────
        guide_h = 252
        _card  (canvas, x, cur_y, w, guide_h, config.C_CARD, radius=12)
        _border(canvas, x, cur_y, w, guide_h, config.C_BORDER, radius=12)

        _txt(canvas, "Gesture Commands",
             x + 14, cur_y + 20,
             scale=_S_HEAD, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)
        _divider(canvas, x + 14, x + w - 14, cur_y + 30)

        entries = [
            ("Open Palm",    "Lights ON",      False),
            ("Fist",         "Lights OFF",     False),
            ("Thumbs Up",    "AC ON",          False),
            ("Thumbs Down",  "AC OFF",         False),
            ("Peace Sign",   "Door OPEN",      False),
            ("One Finger",   "Door CLOSE",     False),
            ("3 Fingers",    "Curtains OPEN",  False),
            ("4 Fingers",    "Curtains CLOSE", False),
            ("OK Sign",      "Cycle Mode",     False),
            ("ILY Sign",     "Accessibility",  True),
        ]
        col_w = (w - 28) // 2
        for i, (gest, act, is_acc) in enumerate(entries):
            row = i // 2;  col = i % 2
            gx  = x + 14 + col * col_w
            gy  = cur_y + 38 + row * 22
            if gy > cur_y + guide_h - 8:
                break
            gc = config.C_ACCESS if is_acc else config.C_ACCENT
            _txt(canvas, gest,  gx,       gy, scale=_S_LABEL, color=gc,               bold=is_acc)
            _txt(canvas, act,   gx + 84,  gy, scale=_S_LABEL, color=config.C_TEXT_BODY)

        cur_y += guide_h + PAD

        # ── Analytics card ────────────────────────────────────────────
        anal_h = 136
        _card  (canvas, x, cur_y, w, anal_h, config.C_CARD, radius=12)
        _border(canvas, x, cur_y, w, anal_h, config.C_BORDER, radius=12)

        _txt(canvas, "Session Analytics",
             x + 14, cur_y + 20,
             scale=_S_HEAD, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)
        _divider(canvas, x + 14, x + w - 14, cur_y + 30)

        cw2   = (w - 28) // 2
        stats = [
            ("Session Time",    room.session_time()),
            ("Total Gestures",  str(room.total_gestures)),
            ("Top Gesture",     room.most_used_gesture()[:14]),
            ("Active Devices",  f"{room.active_devices_count()} / 7"),
        ]
        for i, (lbl, val) in enumerate(stats):
            col = i % 2;  row = i // 2
            sx  = x + 14 + col * cw2
            sy  = cur_y + 40 + row * 44
            _txt(canvas, lbl, sx, sy,
                 scale=_S_LABEL, color=config.C_TEXT_MUTED)
            _txt(canvas, val, sx, sy + 24,
                 scale=_S_BODY, color=config.C_TEXT_PRIMARY, bold=True)

        cur_y += anal_h + PAD

        # ── Voice + Accessibility card ────────────────────────────────
        rem = h - (cur_y - y)
        if rem < 40:
            return

        _card  (canvas, x, cur_y, w, rem, config.C_CARD, radius=12)
        _border(canvas, x, cur_y, w, rem, config.C_BORDER, radius=12)

        _txt(canvas, "Voice Interface",
             x + 14, cur_y + 20,
             scale=_S_HEAD, color=config.C_TEXT_PRIMARY, bold=True, font=_FONT_BOLD)
        _divider(canvas, x + 14, x + w - 14, cur_y + 30)

        sr_c = {"LISTENING":   config.C_SUCCESS,
                "PROCESSING":  config.C_WARNING,
                "CALIBRATING": config.C_BLUE,
                "NO NETWORK":  config.C_DANGER,
                "OFFLINE":     config.C_STANDBY
                }.get(voice_mod.sr_status, config.C_STANDBY)

        # Mic dot — solid circle
        cv2.circle(canvas, (x + 22, cur_y + 46), 7, sr_c, -1)
        _txt(canvas, voice_mod.sr_status,
             x + 36, cur_y + 52,
             scale=_S_BODY, color=sr_c, bold=True)

        if voice_mod.last_spoken:
            _txt(canvas, f'"{voice_mod.last_spoken[:34]}"',
                 x + 14, cur_y + 72,
                 scale=_S_LABEL, color=config.C_TEXT_BODY)

        # Accessibility sub-section
        if rem > 108:
            acc_y = cur_y + 88
            _divider(canvas, x + 14, x + w - 14, acc_y)
            _txt(canvas, "Accessibility Mode",
                 x + 14, acc_y + 18,
                 scale=_S_LABEL, color=config.C_TEXT_MUTED)

            acc    = getattr(room, 'accessibility_active', False)
            ab     = config.C_ACCESS_BG   if acc else config.C_CARD_DEEP
            abrd   = config.C_ACCESS      if acc else config.C_BORDER_LO
            ac     = config.C_ACCESS      if acc else config.C_TEXT_MUTED
            txt    = "ACTIVE — Door Unlocked" if acc else "ILY Sign to activate"

            _rect  (canvas, x + 14, acc_y + 26, w - 28, 28, ab, radius=6)
            _border(canvas, x + 14, acc_y + 26, w - 28, 28, abrd, radius=6)
            _txt   (canvas, txt, x + 22, acc_y + 45,
                    scale=_S_LABEL, color=ac, bold=acc)

    # ═════════════════════════════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════════════════════════════
    def _footer(self, canvas, room, W, H, FTR_H):
        fy = H - FTR_H
        _rect(canvas, 0, fy, W, FTR_H, config.C_PANEL, radius=0)
        _rect(canvas, 0, fy, W, 1, config.C_BORDER_LO, radius=0)

        if room.activity_log:
            ts, msg = room.activity_log[-1]
            _txt(canvas, f"{ts}   {msg[:48]}", 14, fy + 24,
                 scale=_S_LABEL, color=config.C_TEXT_BODY)

        hc = {"Optimal":  config.C_SUCCESS,
              "Warning":  config.C_WARNING,
              "Critical": config.C_DANGER
              }.get(room.health_status, config.C_TEXT_MUTED)
        _txt(canvas, f"System: {room.health_status}",
             W // 2 - 58, fy + 24,
             scale=_S_LABEL, color=hc)

        _txt(canvas, "1-7 Modes   L Lock   U Unlock   Q Quit",
             W - 360, fy + 24,
             scale=_S_LABEL, color=config.C_TEXT_MUTED)

    # ═════════════════════════════════════════════════════════════════
    # NOTIFICATION BANNER
    # ═════════════════════════════════════════════════════════════════
    def _notif(self, canvas, W, H):
        if not self._notif_text:
            return
        age = time.time() - self._notif_t
        if age >= self._notif_dur:
            self._notif_text = ""
            return

        # Only apply alpha blend during the fade-out tail (last 0.4s).
        # For most of the display time the banner is drawn opaque — sharp.
        fade_s = self._notif_dur - 0.4
        if age < fade_s:
            # Fully opaque — draw direct
            self._draw_notif_opaque(canvas, W, H)
        else:
            # Fade out: blend only for 0.4 s
            alpha = max(0.0, (self._notif_dur - age) / 0.4)
            ov = canvas.copy()
            self._draw_notif_opaque(ov, W, H)
            cv2.addWeighted(ov, alpha, canvas, 1.0 - alpha, 0, canvas)

    def _draw_notif_opaque(self, img, W, H):
        bw, bh = 460, 44
        bx     = W // 2 - bw // 2
        by     = 62
        _rect  (img, bx,     by,     bw,     bh, config.C_CARD_ALT,  radius=10)
        _border(img, bx,     by,     bw,     bh, config.C_ACCENT,    radius=10)
        _rect  (img, bx,     by + 6, 3, bh - 12, config.C_ACCENT,    radius=1)
        _txt   (img, self._notif_text[:54],
                bx + 16, by + 30,
                scale=_S_BODY, color=config.C_TEXT_PRIMARY, bold=True)


# Backwards compat shim
gesture_det_placeholder_ref = [None]

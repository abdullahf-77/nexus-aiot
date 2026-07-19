# =============================================================================
# sound_module.py
# NEXUS-AI  |  Sound Effects Module
#
# Plays futuristic beep sequences using the Windows winsound module (built-in,
# no extra install). Each effect runs in a background thread so it never
# blocks the rendering loop.
#
# On non-Windows systems, winsound is unavailable and sounds are silently
# skipped — the rest of the system still works fine.
# =============================================================================

import threading
import config

try:
    import winsound
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False


def _play(sequences):
    """
    sequences: list of (frequency_hz, duration_ms) tuples.
    Plays each beep in sequence in a background thread.
    """
    if not (_SOUND_AVAILABLE and config.SOUND_ENABLED):
        return

    def _run():
        for freq, dur in sequences:
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass

    threading.Thread(target=_run, daemon=True).start()


# ── Named effects ─────────────────────────────────────────────────────────────

def play_boot():
    """Ascending chord played during boot."""
    _play([(440, 80), (550, 80), (660, 80), (880, 160)])

def play_success():
    """Short positive confirmation."""
    _play([(700, 60), (900, 100)])

def play_gesture():
    """Subtle click-beep for gesture detection."""
    _play([(1200, 40)])

def play_unlock():
    """Three-note unlock fanfare."""
    _play([(523, 80), (659, 80), (784, 160)])

def play_alert():
    """Pulsing alarm for security / wrong password."""
    _play([(400, 120), (400, 120), (400, 120)])

def play_mode_switch():
    """Two-note mode-change chime."""
    _play([(600, 80), (800, 120)])

def play_denied():
    """Descending two-note failure."""
    _play([(600, 100), (400, 160)])

def play_voice_detected():
    """Single soft ping on voice command recognition."""
    _play([(1000, 60)])

# =============================================================================
# smart_room.py
# Nexus AIoT  |  Smart Environment State Manager  v4.3
#
# Changes from v4.2:
#   • Removed MODE_GESTURES dict (Swipe Right / Swipe Left are gone).
#   • Added cycle_mode() — advances to the next mode in the fixed sequence.
#     Called by main.py when C Gesture is detected.
#   • apply_gesture() no longer handles any mode-switch gesture directly;
#     mode cycling is routed from main.py for clarity.
# =============================================================================

import time
import config


class SmartRoom:

    DEVICE_KEYS = [
        "lights", "air_conditioner", "door",
        "curtains", "security_camera", "alarm", "music",
    ]

    DEVICE_DISPLAY = {
        "lights":           "Smart Lights",
        "air_conditioner":  "Air Conditioner",
        "door":             "Smart Door",
        "curtains":         "Curtains",
        "security_camera":  "Security Camera",
        "alarm":            "Alarm System",
        "music":            "Music System",
    }

    MODES = {
        "NORMAL":    {"lights": True,  "air_conditioner": False, "door": False,
                      "curtains": True,  "security_camera": False, "alarm": False, "music": False},
        "STUDY":     {"lights": True,  "air_conditioner": True,  "door": False,
                      "curtains": True,  "security_camera": False, "alarm": False, "music": False},
        "CINEMA":    {"lights": False, "air_conditioner": False, "door": False,
                      "curtains": False, "security_camera": False, "alarm": False, "music": True},
        "SLEEP":     {"lights": False, "air_conditioner": True,  "door": False,
                      "curtains": False, "security_camera": True,  "alarm": True,  "music": False},
        "GAMING":    {"lights": True,  "air_conditioner": True,  "door": False,
                      "curtains": False, "security_camera": False, "alarm": False, "music": True},
        "SECURITY":  {"lights": True,  "air_conditioner": False, "door": False,
                      "curtains": True,  "security_camera": True,  "alarm": True,  "music": False},
        "EMERGENCY": {"lights": True,  "air_conditioner": False, "door": True,
                      "curtains": True,  "security_camera": True,  "alarm": True,  "music": False},
    }

    # Ordered sequence for C Gesture cycling
    MODE_CYCLE = ["NORMAL", "STUDY", "CINEMA", "SLEEP",
                  "GAMING", "SECURITY", "EMERGENCY"]

    # Gesture → (device_key, new_state, display_message)
    GESTURE_ACTIONS = {
        "Open Palm":     ("lights",          True,   "Lights ON"),
        "Fist":          ("lights",          False,  "Lights OFF"),
        "Thumbs Up":     ("air_conditioner", True,   "Air Conditioner ON"),
        "Thumbs Down":   ("air_conditioner", False,  "Air Conditioner OFF"),
        "Peace Sign":    ("door",            True,   "Door OPENED"),
        "One Finger":    ("door",            False,  "Door CLOSED"),
        "Three Fingers": ("curtains",        True,   "Curtains OPENED"),
        "Four Fingers":  ("curtains",        False,  "Curtains CLOSED"),
        "ILY Sign":      ("door",            True,   "Accessibility Access Activated"),
    }

    def __init__(self):
        self.devices              = {k: False for k in self.DEVICE_KEYS}
        self.current_mode         = "NORMAL"
        self.last_action          = "System ready. Awaiting input."
        self.system_locked        = True
        self.accessibility_active = False

        # Analytics
        self.session_start  = time.time()
        self.gesture_counts = {}
        self.total_gestures = 0
        self.activity_log   = []
        self.health_status  = "Optimal"

        self._apply_mode("NORMAL", log=False)

    # ------------------------------------------------------------------
    def apply_gesture(self, gesture):
        """
        Route a confirmed stable gesture.
        Returns (triggered: bool, voice_text: str).

        Note: OK Sign is NOT handled here — it is routed directly
        through cycle_mode() from main.py so the notification message
        can be built with the new mode name before this method is called.
        """
        if self.system_locked:
            self._log("System locked — enter gesture password.")
            return False, ""

        # Accessibility gesture — special path
        if gesture == "ILY Sign":
            self.devices["door"]      = True
            self.accessibility_active = True
            self.last_action          = "Accessibility Access Activated"
            self._log("Accessibility access — door unlocked")
            self._track(gesture)
            return True, "Accessibility access activated. Door is now open."

        # Standard device-control gestures
        if gesture in self.GESTURE_ACTIONS:
            device, state, desc = self.GESTURE_ACTIONS[gesture]
            self.devices[device]      = state
            self.last_action          = desc
            self.accessibility_active = False
            self._log(desc)
            self._track(gesture)
            return True, desc

        return False, ""

    # ------------------------------------------------------------------
    def cycle_mode(self):
        """
        Advance to the next mode in MODE_CYCLE and apply it.
        Wraps around after EMERGENCY → NORMAL.
        Returns the new mode name string.
        """
        try:
            idx = self.MODE_CYCLE.index(self.current_mode)
        except ValueError:
            idx = -1
        next_idx  = (idx + 1) % len(self.MODE_CYCLE)
        next_mode = self.MODE_CYCLE[next_idx]
        self._apply_mode(next_mode)
        self._track("OK Sign")
        return next_mode

    # ------------------------------------------------------------------
    def apply_mode(self, mode_name):
        """Direct mode switch (used by keyboard shortcuts and voice)."""
        if mode_name in self.MODES:
            self._apply_mode(mode_name)
            return True
        return False

    # ------------------------------------------------------------------
    def apply_voice_command(self, text):
        text = text.lower().strip()
        mode_cmds = {
            "cinema mode":    "CINEMA",    "study mode":  "STUDY",
            "sleep mode":     "SLEEP",     "gaming mode": "GAMING",
            "security mode":  "SECURITY",  "emergency mode": "EMERGENCY",
            "normal mode":    "NORMAL",
        }
        device_cmds = {
            "lights on":      ("lights",          True),
            "lights off":     ("lights",          False),
            "open door":      ("door",            True),
            "close door":     ("door",            False),
            "open curtains":  ("curtains",        True),
            "close curtains": ("curtains",        False),
            "fan on":         ("air_conditioner", True),
            "fan off":        ("air_conditioner", False),
            "music on":       ("music",           True),
            "music off":      ("music",           False),
            "alarm on":       ("alarm",           True),
            "alarm off":      ("alarm",           False),
        }
        for phrase, mode in mode_cmds.items():
            if phrase in text:
                self._apply_mode(mode)
                return True, f"{mode.capitalize()} mode activated"
        for phrase, (device, state) in device_cmds.items():
            if phrase in text:
                self.devices[device] = state
                msg = f"{device.replace('_', ' ').title()} {'on' if state else 'off'}"
                self.last_action = msg
                self._log(msg)
                return True, msg
        return False, "Command not recognised"

    # ------------------------------------------------------------------
    def unlock(self):
        self.system_locked = False
        self._log("System unlocked via gesture password")

    def lock(self):
        self.system_locked = True
        self._log("System locked")

    def session_time(self):
        s = int(time.time() - self.session_start)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

    def most_used_gesture(self):
        if not self.gesture_counts:
            return "None"
        return max(self.gesture_counts, key=self.gesture_counts.get)

    def active_devices_count(self):
        return sum(1 for v in self.devices.values() if v)

    # ------------------------------------------------------------------
    def _apply_mode(self, name, log=True):
        for dev, state in self.MODES.get(name, {}).items():
            self.devices[dev] = state
        self.current_mode = name
        self.last_action  = f"Mode: {name}"
        if log:
            self._log(f"Mode activated: {name}")

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.activity_log.append((ts, msg))
        if len(self.activity_log) > config.MAX_LOG_ENTRIES * 4:
            self.activity_log = self.activity_log[-config.MAX_LOG_ENTRIES * 2:]

    def _track(self, gesture):
        self.gesture_counts[gesture] = self.gesture_counts.get(gesture, 0) + 1
        self.total_gestures += 1

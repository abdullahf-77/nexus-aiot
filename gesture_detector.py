# =============================================================================
# gesture_detector.py
# Nexus AIoT  |  Hand Gesture Recognition Engine  v4.4
#
# Changes from v4.3:
#   • Removed C Gesture (unreliable — hard to distinguish from Fist at speed).
#   • Added OK Sign detection — replaces C Gesture for mode cycling.
#
# OK SIGN DETECTION — geometry and conflict analysis
# ---------------------------------------------------
# The OK sign (👌) is formed when the thumb tip touches the index fingertip
# while the other three fingers (middle, ring, pinky) extend upward.
#
# MediaPipe landmark IDs used:
#   Wrist=0, Thumb tip=4, Index tip=8, Index PIP=6
#   Middle tip=12, Middle PIP=10
#   Ring tip=16,   Ring PIP=14
#   Pinky tip=20,  Pinky PIP=18
#   Middle MCP=9  (reference point for hand_size normalisation)
#
# Detection conditions (ALL must be satisfied):
#
#   A. PINCH: thumb tip (4) is close to index tip (8).
#      Distance(4, 8) < OK_PINCH_RATIO × hand_size
#      This is the defining feature of the OK sign.
#
#   B. THREE FINGERS UP: middle, ring, and pinky tips are all above
#      their respective PIP joints (tip_y < pip_y in screen coords).
#      These three fingers must be clearly extended.
#
#   C. INDEX NOT EXTENDED AS A STRAIGHT FINGER: the index tip (8)
#      must NOT be significantly above the index MCP (5).
#      This guards against false fires from a "pointing + pinch" posture
#      where the index is fully extended and the thumb happens to be near
#      the side of it.
#      Condition: pts[8][1] > pts[5][1] - 0.10 × hand_size
#      (tip cannot be much higher than the MCP knuckle)
#
# Conflict matrix — why this doesn't collide with anything:
#   Open Palm    : index extended, no pinch           → A fails
#   Fist         : middle/ring/pinky not up           → B fails
#   Peace Sign   : index extended, no pinch, only 2   → A fails
#   One Finger   : index extended, no pinch           → A fails
#   Thumbs Up    : middle/ring/pinky not up           → B fails
#   Three Fingers: index extended, no pinch           → A fails
#   Four Fingers : index extended, no pinch           → A fails
#   ILY Sign     : index up, pinky up, no pinch       → A fails (no pinch)
#
# The OK Sign is uniquely identified by the pinch + three-up combination.
#
# STABILITY + COOLDOWN:
#   Gesture must hold for GESTURE_HOLD_FRAMES consecutive frames.
#   Global cooldown of GESTURE_COOLDOWN seconds between triggers.
# =============================================================================

import mediapipe as mp
import math
import time
import config


def _dist(p1, p2):
    """2-D Euclidean distance between two (x, y, ...) landmark tuples."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


class GestureDetector:

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands    = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.80,
            min_tracking_confidence=0.80,
        )
        self.mp_draw   = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        # ── Stability buffer ──────────────────────────────────────────
        self._candidate    = None
        self._hold_count   = 0
        self.HOLD_REQUIRED = config.GESTURE_HOLD_FRAMES

        # ── Cooldown ──────────────────────────────────────────────────
        self.last_trigger_time = 0.0
        self.COOLDOWN          = config.GESTURE_COOLDOWN

        # ── Public state ──────────────────────────────────────────────
        self.raw_gesture    = "No Hand"
        self.stable_gesture = None

    # ------------------------------------------------------------------
    def detect(self, frame):
        """
        Process one BGR frame.
        Returns (results, stable_gesture, hand_landmarks).
        stable_gesture is a string only when the gesture has been stable
        for HOLD_REQUIRED frames; otherwise None.
        """
        rgb     = frame[:, :, ::-1]
        results = self.hands.process(rgb)

        hand_landmarks      = None
        self.stable_gesture = None

        if results.multi_hand_landmarks:
            hand_landmarks   = results.multi_hand_landmarks[0]
            self.raw_gesture = self._classify(hand_landmarks, frame.shape)
        else:
            self.raw_gesture = "No Hand"
            self._candidate  = None
            self._hold_count = 0

        # ── Stability buffer ──────────────────────────────────────────
        if self.raw_gesture not in ("No Hand", "Unknown"):
            if self.raw_gesture == self._candidate:
                self._hold_count += 1
            else:
                self._candidate  = self.raw_gesture
                self._hold_count = 1

            if self._hold_count >= self.HOLD_REQUIRED:
                self.stable_gesture = self._candidate
        else:
            self._candidate  = None
            self._hold_count = 0

        return results, self.stable_gesture, hand_landmarks

    # ------------------------------------------------------------------
    def is_ready(self):
        """True when the global cooldown has expired."""
        return (time.time() - self.last_trigger_time) >= self.COOLDOWN

    def trigger(self):
        """Call after a gesture is acted upon — resets hold and starts cooldown."""
        self.last_trigger_time = time.time()
        self._hold_count = 0

    def cooldown_pct(self):
        """0.0 → 1.0 fraction of cooldown elapsed."""
        return min((time.time() - self.last_trigger_time) / self.COOLDOWN, 1.0)

    # ------------------------------------------------------------------
    # Internal classification
    # ------------------------------------------------------------------
    def _classify(self, hand_landmarks, shape):
        h, w, _ = shape
        lm  = hand_landmarks.landmark
        pts = {i: (p.x * w, p.y * h, p.z) for i, p in enumerate(lm)}

        # ── OK Sign checked FIRST — its pinch condition means it will
        #    never be confused with purely finger-count rules below. ──
        if self._is_ok_sign(pts):
            return "OK Sign"

        # Compute finger states for remaining rules
        fingers = self._fingers_up(pts)
        thumb, index, middle, ring, pinky = fingers
        n_up = sum(fingers)

        # ── ILY Sign (accessibility): thumb + index + pinky ──────────
        if thumb and index and not middle and not ring and pinky:
            return "ILY Sign"

        # ── Peace: index + middle only ────────────────────────────────
        if index and middle and not ring and not pinky and not thumb:
            return "Peace Sign"

        # ── One finger: index only ────────────────────────────────────
        if index and not middle and not ring and not pinky and not thumb:
            return "One Finger"

        # ── Thumb only — direction from wrist y ──────────────────────
        if thumb and not index and not middle and not ring and not pinky:
            return "Thumbs Up" if pts[4][1] < pts[0][1] else "Thumbs Down"

        # ── Three fingers: index + middle + ring ─────────────────────
        if index and middle and ring and not pinky and not thumb:
            return "Three Fingers"

        # ── Four fingers: all except thumb ───────────────────────────
        if index and middle and ring and pinky and not thumb:
            return "Four Fingers"

        # ── Open palm: all five ───────────────────────────────────────
        if n_up == 5:
            return "Open Palm"

        # ── Fist: all fingers down ────────────────────────────────────
        if n_up == 0:
            return "Fist"

        return "Unknown"

    # ------------------------------------------------------------------
    def _is_ok_sign(self, pts):
        """
        Returns True when the hand forms an OK sign (👌).

        Three independent conditions must all pass:

        A) PINCH — thumb tip (4) is close to index tip (8).
           Distance normalised by hand_size (wrist to middle MCP).
           Threshold: OK_PINCH_RATIO from config.

        B) THREE FINGERS EXTENDED — middle (12), ring (16), pinky (20)
           tips are each above their PIP joints (smaller y = higher on screen).

        C) INDEX NOT STRAIGHT — index tip (8) is NOT significantly
           above the index MCP knuckle (5). This blocks the edge case
           where someone points with the index fully extended and the thumb
           happens to rest near the index side.
        """
        # Reference scale: wrist (0) to middle MCP (9)
        hand_size = _dist(pts[0], pts[9])
        if hand_size < 1.0:          # degenerate / too-small detection
            return False

        # A — thumb-to-index pinch
        pinch_dist = _dist(pts[4], pts[8])
        if pinch_dist / hand_size >= config.OK_PINCH_RATIO:
            return False             # too far apart — not a pinch

        # B — middle, ring, pinky all extended upward
        three_up = (
            pts[12][1] < pts[10][1] and   # middle tip above middle PIP
            pts[16][1] < pts[14][1] and   # ring   tip above ring   PIP
            pts[20][1] < pts[18][1]        # pinky  tip above pinky  PIP
        )
        if not three_up:
            return False

        # C — index finger is NOT straight/pointing (tip not high above MCP)
        # pts[8][1] > pts[5][1] - margin  means tip is near or below MCP level
        margin = 0.10 * hand_size
        if pts[8][1] < pts[5][1] - margin:
            return False             # index is extended upward — not OK sign

        return True

    # ------------------------------------------------------------------
    def _fingers_up(self, pts):
        """
        [thumb, index, middle, ring, pinky] booleans.
        Thumb: X-axis spread from wrist.
        Others: tip Y above PIP Y (tip_y < pip_y in screen coords).
        """
        wrist_x  = pts[0][0]
        thumb_up = abs(pts[4][0] - wrist_x) > abs(pts[2][0] - wrist_x)

        tips   = [8,  12, 16, 20]
        pips   = [6,  10, 14, 18]
        others = [pts[t][1] < pts[p][1] for t, p in zip(tips, pips)]
        return [thumb_up] + others

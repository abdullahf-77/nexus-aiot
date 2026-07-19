# =============================================================================
# password_module.py
# NEXUS-AI  |  Gesture Password & Security System
#
# The user must perform a predefined sequence of gestures within a time
# limit to unlock the system. Wrong sequences trigger a security alert.
# =============================================================================

import time
import config


class PasswordModule:
    """
    Tracks gesture input against a secret sequence.
    Reports state: WAITING, IN_PROGRESS, SUCCESS, or FAILED.
    """

    STATE_WAITING     = "WAITING"
    STATE_IN_PROGRESS = "IN_PROGRESS"
    STATE_SUCCESS     = "SUCCESS"
    STATE_FAILED      = "FAILED"

    def __init__(self):
        self.sequence    = config.PASSWORD_SEQUENCE   # ["Thumbs Up", "Peace Sign", "Open Palm"]
        self.timeout     = config.PASSWORD_TIMEOUT

        self._entered     = []          # gestures entered so far
        self._start_time  = None        # when the sequence began
        self._state       = self.STATE_WAITING
        self._message     = "Perform password sequence to unlock"
        self._alert_until = 0.0        # timestamp until alert expires
        self._attempt_count = 0

    # ------------------------------------------------------------------
    def push_gesture(self, gesture):
        """
        Feed the latest stable gesture into the password checker.
        Returns state string.
        """
        # Ignore if already settled in SUCCESS
        if self._state == self.STATE_SUCCESS:
            return self._state

        # Start or continue a sequence
        if self._state in (self.STATE_WAITING, self.STATE_FAILED):
            if gesture == self.sequence[0]:
                self._entered    = [gesture]
                self._start_time = time.time()
                self._state      = self.STATE_IN_PROGRESS
                self._message    = self._progress_msg()
            return self._state

        # In progress
        if self._state == self.STATE_IN_PROGRESS:
            self._check_timeout()
            if self._state != self.STATE_IN_PROGRESS:
                return self._state

            expected = self.sequence[len(self._entered)]

            if gesture == expected:
                self._entered.append(gesture)
                if len(self._entered) == len(self.sequence):
                    # Correct!
                    self._state   = self.STATE_SUCCESS
                    self._message = "ACCESS GRANTED"
                    self._attempt_count = 0
                else:
                    self._message = self._progress_msg()
            else:
                # Wrong gesture
                self._attempt_count += 1
                self._state       = self.STATE_FAILED
                self._alert_until = time.time() + 3.0
                self._message     = f"ACCESS DENIED  |  Attempt {self._attempt_count}"
                self._entered     = []

        return self._state

    # ------------------------------------------------------------------
    def update(self):
        """Call every frame to handle timeout transitions."""
        if self._state == self.STATE_IN_PROGRESS:
            self._check_timeout()

        # After alert window, return to waiting
        if self._state == self.STATE_FAILED:
            if time.time() > self._alert_until:
                self._state   = self.STATE_WAITING
                self._message = "Perform password sequence to unlock"

    # ------------------------------------------------------------------
    def reset(self):
        """Re-lock the system."""
        self._entered    = []
        self._start_time = None
        self._state      = self.STATE_WAITING
        self._message    = "Perform password sequence to unlock"

    # ------------------------------------------------------------------
    @property
    def state(self):
        return self._state

    @property
    def message(self):
        return self._message

    @property
    def progress(self):
        """Fraction complete (0.0 – 1.0)."""
        return len(self._entered) / len(self.sequence)

    @property
    def progress_text(self):
        return f"{len(self._entered)} / {len(self.sequence)}"

    @property
    def is_alerting(self):
        return self._state == self.STATE_FAILED

    @property
    def hint(self):
        """Short string showing the expected next gesture."""
        if self._state == self.STATE_IN_PROGRESS and len(self._entered) < len(self.sequence):
            return f"Next: {self.sequence[len(self._entered)]}"
        return ""

    @property
    def time_remaining(self):
        if self._start_time and self._state == self.STATE_IN_PROGRESS:
            remaining = self.timeout - (time.time() - self._start_time)
            return max(remaining, 0.0)
        return self.timeout

    # ------------------------------------------------------------------
    def _check_timeout(self):
        if self._start_time and (time.time() - self._start_time) > self.timeout:
            self._state       = self.STATE_FAILED
            self._alert_until = time.time() + 3.0
            self._message     = "TIMEOUT  |  Sequence expired"
            self._entered     = []

    def _progress_msg(self):
        done = len(self._entered)
        return f"Step {done}/{len(self.sequence)} complete  |  {self.hint}"

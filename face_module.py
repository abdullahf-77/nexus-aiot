# =============================================================================
# face_module.py
# Nexus AIoT  |  Face Detection & Authorization Module
# Colors updated for soft-dark theme v4.1
# =============================================================================

import cv2
import time


class FaceModule:

    CHECK_INTERVAL   = 20
    PRESENCE_TIMEOUT = 3.0
    AUTH_DELAY       = 2.0

    def __init__(self):
        self.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._frame_count  = 0
        self._face_present = False
        self._face_rect    = None
        self._authorized   = False
        self._last_seen    = 0.0
        self._first_seen   = None

    def process(self, frame):
        self._frame_count += 1
        if self._face_present:
            if time.time() - self._last_seen > self.PRESENCE_TIMEOUT:
                self._face_present = False
                self._authorized   = False
                self._first_seen   = None
        if self._frame_count % self.CHECK_INTERVAL != 0:
            return
        small = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = self.cascade.detectMultiScale(
            gray, scaleFactor=1.15, minNeighbors=5, minSize=(40, 40)
        )
        if len(faces) > 0:
            x, y, w, h    = faces[0]
            s             = 1 / 0.4
            self._face_rect    = (int(x*s), int(y*s), int(w*s), int(h*s))
            self._face_present = True
            self._last_seen    = time.time()
            if self._first_seen is None:
                self._first_seen = time.time()
            if time.time() - self._first_seen >= self.AUTH_DELAY:
                self._authorized = True
        else:
            if time.time() - self._last_seen > self.PRESENCE_TIMEOUT:
                self._face_present = False
                self._authorized   = False
                self._first_seen   = None

    def draw(self, frame):
        """Draw face bounding box and label on the camera frame."""
        if not self._face_present or not self._face_rect:
            return frame
        x, y, w, h = self._face_rect
        # Soft teal for authorized, muted amber for unknown — matches dark theme
        border = (191, 191, 42) if self._authorized else (60, 150, 220)
        label  = "Authorized" if self._authorized else "Unknown"
        cv2.rectangle(frame, (x, y), (x + w, y + h), border, 2)
        cv2.rectangle(frame, (x, y - 22), (x + w, y), border, -1)
        cv2.putText(frame, label, (x + 4, y - 5),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40, (20, 18, 18), 1, cv2.LINE_AA)
        return frame

    @property
    def face_present(self):  return self._face_present
    @property
    def authorized(self):    return self._authorized
    @property
    def status_text(self):
        if not self._face_present: return "No face detected"
        return "Authorized User" if self._authorized else "Unknown User"
    @property
    def status_color(self):
        if not self._face_present: return (75, 70, 68)
        return (80, 200, 100) if self._authorized else (60, 150, 220)

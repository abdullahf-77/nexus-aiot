# Nexus AIoT

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/status-exhibition%20demo-orange.svg)

## AI-Powered Touchless Smart Environment System  v4.4

A university exhibition-grade AIoT platform combining Artificial Intelligence
and the Internet of Things for a fully touchless smart environment experience.
Control smart devices with hand gestures, voice commands, and face-presence detection.

---

## Key Features

- 10 hand gestures recognized in real time via MediaPipe (see full reference below)
- 7 smart devices: Lights, AC, Door, Curtains, Camera, Alarm, Music
- 7 intelligent modes: Normal, Study, Sleep, Cinema, Gaming, Security, Emergency — cycled with the OK Sign gesture
- Gesture password lock/unlock system (Thumbs Up + Peace Sign + Open Palm)
- Accessibility gesture: ILY Sign (thumb + index + pinky) unlocks the door
- Presence-based face detection with a 2-second authorization timer via Haar Cascade (see **Face Detection & Authorization** below — this is not identity recognition)
- AI voice feedback via pyttsx3 (offline text-to-speech)
- Voice command input via SpeechRecognition (online STT) — mode and device commands (full list below)
- Futuristic light premium UI with animated device cards and live analytics
- Clean notification banners for every interaction
- Keyboard shortcuts for fast exhibition demos

---

## Tech Stack

| Category          | Technology                              |
|--------------------|-------------------------------------------|
| Language            | Python 3.11                              |
| Computer Vision     | OpenCV, MediaPipe (hand landmark detection), Haar Cascade (face detection) |
| Voice               | pyttsx3 (offline TTS), SpeechRecognition + PyAudio (online STT) |
| Sound               | winsound (Windows built-in beeps)         |
| UI                  | Custom OpenCV-rendered dashboard (`ui_renderer.py`) |
| Platform            | Windows 10/11 (winsound dependency)       |

---

## Project Structure

```
nexus-aiot/
|
+-- main.py              <- Entry point and main orchestration loop
+-- config.py            <- All settings, colors, constants
+-- gesture_detector.py  <- MediaPipe engine + swipe + ILY gesture
+-- smart_room.py        <- Device states, smart modes, analytics
+-- face_module.py       <- Haar face detection + authorization
+-- password_module.py   <- Gesture password lock system
+-- voice_module.py      <- TTS + speech recognition (background threads)
+-- sound_module.py      <- Windows beep sound effects
+-- ui_renderer.py       <- Full premium light dashboard (749 lines)
+-- requirements.txt     <- Python dependencies
+-- README.md            <- This file
+-- LICENSE              <- MIT License
+-- .gitignore
+-- assets/               <- Place exhibition images/poster here
+-- faces/                <- Reserved for future face registration (not yet implemented)
+-- sounds/               <- Reserved for future custom sound assets
+-- docs/images/          <- Screenshots (see Screenshots section)
+-- .github/workflows/    <- CI: dependency install + import verification
```

---

## Gesture Command Reference

This is the actual gesture set implemented in `gesture_detector.py` v4.4.
(Earlier versions used swipe gestures for mode switching — those were
removed in v4.4 in favor of the OK Sign, see below.)

| Gesture          | Action                          |
|-------------------|----------------------------------|
| Open Palm          | Lights ON                       |
| Fist               | Lights OFF                      |
| Thumbs Up          | Air Conditioner ON              |
| Thumbs Down        | Air Conditioner OFF             |
| Peace Sign         | Door OPEN                       |
| One Finger         | Door CLOSE                      |
| Three Fingers      | Curtains OPEN                   |
| Four Fingers       | Curtains CLOSE                  |
| OK Sign            | Cycle to next Smart Mode         |
| ILY Sign (*)       | Accessibility Access + Door ON  |

(*) ILY Sign: thumb + index finger + pinky extended simultaneously.
    Designed for users with hearing disabilities — demonstrates inclusive AIoT.

All gestures require holding the pose for `GESTURE_HOLD_FRAMES` (7) frames
before triggering, and are subject to a `GESTURE_COOLDOWN` (1.4s) between
triggers — this prevents a single held pose from firing repeatedly.

### Gesture Password (default)

Thumbs Up  -->  Peace Sign  -->  Open Palm

Perform all three within 8 seconds to unlock the system.

---

## Smart Modes Reference

| Mode      | Lights | AC  | Door | Curtains | Camera | Alarm | Music |
|-----------|--------|-----|------|----------|--------|-------|-------|
| NORMAL    | ON     | OFF | OFF  | OPEN     | OFF    | OFF   | OFF   |
| STUDY     | ON     | ON  | OFF  | OPEN     | OFF    | OFF   | OFF   |
| SLEEP     | OFF    | ON  | OFF  | CLOSED   | ON     | ON    | OFF   |
| CINEMA    | OFF    | OFF | OFF  | CLOSED   | OFF    | OFF   | ON    |
| GAMING    | ON     | ON  | OFF  | CLOSED   | OFF    | OFF   | ON    |
| SECURITY  | ON     | OFF | OFF  | OPEN     | ON     | ON    | OFF   |
| EMERGENCY | ON     | OFF | ON   | OPEN     | ON     | ON    | OFF   |

---

## Voice Control

Voice input only works when the system is **unlocked** (`system_locked =
False`). `VoiceModule` runs speech recognition in a background thread via
`SpeechRecognition` + Google's Web Speech API (requires internet), and
offline text-to-speech via `pyttsx3` for spoken feedback. Recognized phrases
are matched (substring match, case-insensitive) against the command tables
in `smart_room.py`'s `apply_voice_command()`:

**Mode commands** — say the full phrase, e.g. "cinema mode":

| Phrase           | Mode      |
|--------------------|-----------|
| "normal mode"        | NORMAL    |
| "study mode"          | STUDY     |
| "sleep mode"           | SLEEP     |
| "cinema mode"          | CINEMA    |
| "gaming mode"          | GAMING    |
| "security mode"        | SECURITY  |
| "emergency mode"       | EMERGENCY |

**Device commands:**

| Phrase           | Effect                  |
|--------------------|---------------------------|
| "lights on" / "lights off"       | Toggle lights              |
| "open door" / "close door"       | Toggle door                |
| "open curtains" / "close curtains" | Toggle curtains          |
| "fan on" / "fan off"             | Toggle air conditioner     |
| "music on" / "music off"         | Toggle music                |
| "alarm on" / "alarm off"         | Toggle alarm                |

If `pyttsx3` or `SpeechRecognition`/`PyAudio` aren't installed, `VoiceModule`
disables the corresponding feature gracefully (see the try/except imports at
the top of `voice_module.py`) — the rest of the system keeps working without
voice.

---

## Extensibility

The codebase is organized so common additions don't require touching the
main loop:

**Add a new gesture:**
1. Add a classification rule in `GestureDetector._classify()` (`gesture_detector.py`) returning a new gesture name string.
2. Map it to a device/action in `SmartRoom.GESTURE_ACTIONS` (`smart_room.py`) — format is `"Gesture Name": (device_key, new_state, display_message)`.
3. Add a row to the Gesture Command Reference table in this README.

**Add a new smart device:**
1. Add the key to `SmartRoom.DEVICE_KEYS` and a friendly name in `DEVICE_DISPLAY`.
2. Add its default state to each entry in `SmartRoom.MODES`.
3. Wire a gesture and/or voice phrase to it if desired.
4. Add a device card in `ui_renderer.py`'s `_middle()` section.

**Add a new smart mode:**
1. Add an entry to `SmartRoom.MODES` with a state for every device key.
2. Add it to `SmartRoom.MODE_CYCLE` (controls OK Sign cycling order) and to the keyboard `mode_map` in `main.py` if you want a dedicated hotkey.

**Add a new voice command:**
- Add an entry to `mode_cmds` or `device_cmds` inside `SmartRoom.apply_voice_command()`.

## Setup Instructions (Windows + VS Code + Python 3.11)

### Step 1 — Install Python 3.11
Download: https://www.python.org/downloads/
IMPORTANT: Check "Add Python to PATH" during installation.

### Step 2 — Open project in VS Code
File -> Open Folder -> select nexus-aiot/

### Step 3 — Create virtual environment
In VS Code terminal (Ctrl + backtick):

```
python -m venv venv
venv\Scripts\activate
```

### Step 4 — Install dependencies

```
pip install -r requirements.txt
```

If PyAudio fails, use:
```
pip install pipwin
pipwin install pyaudio
```

Minimal install (no microphone, still fully functional):
```
pip install opencv-python mediapipe numpy pyttsx3
```

### Step 5 — Run the system

```
python main.py
```

The Nexus AIoT boot sequence will appear.
After boot, perform the gesture password to unlock.

---

## Keyboard Shortcuts

| Key   | Action                             |
|-------|------------------------------------|
| 1     | Normal Mode                        |
| 2     | Study Mode                         |
| 3     | Sleep Mode                         |
| 4     | Cinema Mode                        |
| 5     | Gaming Mode                        |
| 6     | Security Mode                      |
| 7     | Emergency Mode                     |
| L     | Lock system                        |
| U     | Unlock instantly (exhibition demo) |
| Space | Skip boot sequence                 |
| Q/ESC | Quit                               |

---

## Troubleshooting

| Problem                          | Fix                                              |
|----------------------------------|--------------------------------------------------|
| ModuleNotFoundError: cv2         | pip install opencv-python                        |
| ModuleNotFoundError: mediapipe   | pip install mediapipe                            |
| Cannot open webcam               | Close Zoom/Teams; try VideoCapture(1) in main.py |
| Hand not detected                | Better lighting; plain background; 30-60cm range |
| OK Sign not triggering           | Make sure thumb and index fingertips touch while middle/ring/pinky are clearly extended upward |
| PyAudio fails to install         | pip install pipwin && pipwin install pyaudio      |
| No voice output                  | pip install pyttsx3                              |
| Window too small/large           | Resize by dragging or edit WIN_W/WIN_H in config |
| Gestures trigger too fast        | Increase GESTURE_COOLDOWN in config.py           |

---

## How It Works (Architecture)

```
Webcam Frame
     |
     v
GestureDetector
  |-- MediaPipe Hands -> 21 landmark coords
  |-- OK Sign checked first: thumb-index pinch + 3 fingers up + index not
  |     straight (geometric rule, see gesture_detector.py header comment
  |     for the full conflict analysis against the other 9 gestures)
  |-- Static finger-up/down geometry rules for the remaining 9 gestures
  |-- Hold-frame stability buffer (7 frames must agree before trigger)
  |-- Global cooldown (1.4s) between accepted triggers
     |
     +---> PasswordModule (when locked)
     |       -> Sequence: Thumbs Up + Peace Sign + Open Palm
     |       -> Unlock on success; alert + sound on failure
     |
     +---> SmartRoom (when unlocked)
             -> OK Sign -> cycle_mode() advances to the next of 7 modes
             -> Other gestures -> device state updates (GESTURE_ACTIONS)
             -> Accessibility gesture (ILY Sign)
             -> Analytics tracking

FaceModule (every 20 frames, parallel)
  -> Haar Cascade face detection (presence only, not identity)
  -> "Authorized" after any face stays visible for 2 continuous seconds
  -> Resets to "Unknown"/no-face after a 3-second absence timeout

VoiceModule (background threads)
  -> TTS: pyttsx3 (offline, instant)
  -> STT: SpeechRecognition via Google (needs internet)
  -> Recognised phrases are matched against SmartRoom's mode/device command tables

SoundModule -> winsound beep sequences (Windows built-in)

UIRenderer -> 1280x720 premium light dashboard
  -> Header, left (camera + gesture + password)
  -> Middle (7 device cards + 7 mode buttons)
  -> Right (gesture guide + analytics + voice)
  -> Footer (activity log + keyboard hints)
  -> Floating notification banners
```

---

## Face Detection & Authorization

`face_module.py` uses OpenCV's Haar Cascade classifier to detect **whether a
face is present** in the frame — it does not identify *who* it is. The
current behavior is:

1. A face is checked every 20 frames (`CHECK_INTERVAL`).
2. If a face stays continuously visible for 2 seconds (`AUTH_DELAY`), the
   status becomes **"Authorized"**.
3. If no face has been seen for 3 seconds (`PRESENCE_TIMEOUT`), it resets to
   **"No face detected"**.

This is a presence/liveness heuristic suited to a single-user exhibition
demo, not a security-grade access control system — anyone's face triggers
"Authorized" after 2 seconds. The `faces/` folder is reserved for a future
per-identity registration feature (see below) but is currently unused by
any code.

**Suggested design for real face registration** (not yet implemented):
- A registration script that captures N reference frames per user into `faces/<username>/`.
- Compute face embeddings (e.g. via `face_recognition` or a lightweight ONNX model) at startup.
- On detection, compare the live embedding against registered users instead of just checking presence.

---

## Why AIoT?

AIoT = Artificial Intelligence + Internet of Things.

This project demonstrates how AI (computer vision, gesture recognition, face
detection, voice synthesis) can be combined with smart environment control
(IoT devices) to create a fully touchless, accessible, and automated system.

Real-world applications:
- Smart hospitals and hygienic clinical environments
- Accessible interfaces for users with mobility or hearing disabilities
- Contactless security systems in banks and government buildings
- Intelligent smart home automation
- Future-proof office environments

---

Built with: Python 3.11 | OpenCV | MediaPipe | pyttsx3 | SpeechRecognition
Exhibition target: University AI + IoT Technology Showcase

---

## Future Improvements

- Replace the simulated device states with real IoT integrations (smart plugs, MQTT, Home Assistant, etc.).
- Implement real per-identity face registration/recognition (see suggested design under **Face Detection & Authorization**) — the `faces/` folder is currently reserved but unused.
- Cross-platform sound backend (winsound is Windows-only).
- Configurable/persisted gesture password instead of the hardcoded default sequence.
- Automated tests for gesture classification and mode-switching logic.

## Screenshots

This is a native OpenCV desktop application that requires a webcam and an
interactive display, so it can't be run or screenshotted headlessly in this
environment. No fabricated screenshots are included. To add real ones:

| # | Screen to capture | What should be visible | Suggested filename | Where it goes in README |
|---|---|---|---|---|
| 1 | Boot sequence | The animated boot messages and progress | `docs/images/boot_sequence.png` | Top of this section |
| 2 | Locked dashboard, password entry in progress | Password card showing step progress (e.g. "1/3") and the camera feed with hand landmarks drawn | `docs/images/gesture_password.png` | Under a new "Locking & Unlocking" subsection |
| 3 | Unlocked dashboard, NORMAL mode | Full 1280×720 dashboard: device cards, mode buttons, gesture guide, analytics panel | `docs/images/dashboard_normal.png` | Main dashboard screenshot for this section |
| 4 | A gesture being recognized | Camera feed with MediaPipe hand landmarks overlaid and the gesture name/cooldown ring visible | `docs/images/gesture_recognition.png` | Under "Gesture Command Reference" |
| 5 | A different smart mode active (e.g. SECURITY or EMERGENCY) | Device cards showing the mode's distinct device states | `docs/images/mode_security.png` | Under "Smart Modes Reference" |
| 6 | Face detected with "Authorized"/"Unknown" label | The bounding box + label drawn by `FaceModule.draw()` | `docs/images/face_detection.png` | Under "Face Detection & Authorization" |

## License

Distributed under the [MIT License](./LICENSE).

## Author

**Abdullah**

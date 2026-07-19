# Nexus AIoT
## AI-Powered Touchless Smart Environment System  v4.4

A university exhibition-grade AIoT platform combining Artificial Intelligence
and the Internet of Things for a fully touchless smart environment experience.
Control smart devices with hand gestures, voice commands, and face recognition.

---

## Key Features

- 11 hand gestures recognized in real time via MediaPipe
- 7 smart devices: Lights, AC, Door, Curtains, Camera, Alarm, Music
- 7 intelligent modes: Normal, Study, Sleep, Cinema, Gaming, Security, Emergency
- Gesture password lock/unlock system (Thumbs Up + Peace Sign + Open Palm)
- Accessibility gesture: ILY Sign (thumb + index + pinky) unlocks the door
- Face detection: Authorized User / Unknown User via Haar Cascade
- AI voice feedback via pyttsx3 (offline text-to-speech)
- Voice command input via SpeechRecognition (online STT)
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
+-- faces/                <- Reserved for future face registration
+-- sounds/               <- Reserved for future custom sound assets
```

---

## Gesture Command Reference

| Gesture          | Action                         |
|------------------|--------------------------------|
| Open Palm        | Lights ON                      |
| Fist             | Lights OFF                     |
| Thumbs Up        | Air Conditioner ON             |
| Thumbs Down      | Air Conditioner OFF            |
| Peace Sign       | Door OPEN                      |
| One Finger Up    | Door CLOSE                     |
| 3 Fingers        | Curtains OPEN                  |
| 4 Fingers        | Curtains CLOSE                 |
| Swipe Right      | Activate Cinema Mode           |
| Swipe Left       | Activate Security Mode         |
| ILY Sign (*)     | Accessibility Access + Door ON |

(*) ILY Sign: thumb + index finger + pinky extended simultaneously.
    Designed for users with hearing disabilities — demonstrates inclusive AIoT.

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
| Swipe triggers Open Palm         | Fixed — velocity window swipe detection (v4.0)   |
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
  |-- Velocity-window swipe detection (motion-first, highest priority)
  |-- Post-swipe lock suppresses static gestures (eliminates false Open Palm)
  |-- Static finger geometry rules (10 gestures + ILY accessibility)
  |-- Hold-frame stability buffer (7 frames must agree before trigger)
     |
     +---> PasswordModule (when locked)
     |       -> Sequence: Thumbs Up + Peace Sign + Open Palm
     |       -> Unlock on success; alert + sound on failure
     |
     +---> SmartRoom (when unlocked)
             -> Device state updates
             -> Smart mode activation
             -> Accessibility gesture (ILY Sign)
             -> Analytics tracking

FaceModule (every 20 frames, parallel)
  -> Haar Cascade face detection
  -> Authorization: first 2 seconds = Unknown, after = Authorized

VoiceModule (background threads)
  -> TTS: pyttsx3 (offline, instant)
  -> STT: SpeechRecognition via Google (needs internet)

SoundModule -> winsound beep sequences (Windows built-in)

UIRenderer -> 1280x720 premium light dashboard
  -> Header, left (camera + gesture + password)
  -> Middle (7 device cards + 7 mode buttons)
  -> Right (gesture guide + analytics + voice)
  -> Footer (activity log + keyboard hints)
  -> Floating notification banners
```

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
- Add persistent face registration (the `faces/` folder is currently reserved but unused).
- Cross-platform sound backend (winsound is Windows-only).
- Configurable/persisted gesture password instead of the hardcoded default sequence.
- Automated tests for gesture classification and mode-switching logic.

## Screenshots

_Add dashboard screenshots / demo GIFs here._

```
assets/
└── dashboard_preview.png
└── demo.gif
```

## License

Distributed under the [MIT License](./LICENSE).

## Author

**Abdullah**

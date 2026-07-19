# =============================================================================
# voice_module.py
# NEXUS-AI  |  Voice I/O Module
#
# Text-to-speech: uses pyttsx3 (offline, no internet, no API key).
# Speech recognition: uses SpeechRecognition + Google Web Speech API.
#
# Both engines run in background threads so they never block the main loop.
# If either library is missing, the module disables itself gracefully.
# =============================================================================

import threading
import queue
import time
import config

# ── Optional imports — disable module if not installed ────────────────────────
try:
    import pyttsx3
    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False


class VoiceModule:
    """
    Manages TTS output and voice command input.
    Call speak(text) to queue a TTS utterance.
    Check pending_command() each frame for recognised speech commands.
    """

    def __init__(self):
        self._tts_queue   = queue.Queue()
        self._cmd_queue   = queue.Queue()
        self._tts_engine  = None
        self._listening   = False
        self.tts_enabled  = config.VOICE_ENABLED and _TTS_AVAILABLE
        self.sr_enabled   = config.VOICE_ENABLED and _SR_AVAILABLE

        # ── Boot TTS engine in its own thread ────────────────────────
        if self.tts_enabled:
            self._tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self._tts_thread.start()

        # ── Speech recognition thread ─────────────────────────────────
        if self.sr_enabled:
            self._sr_thread = threading.Thread(target=self._sr_worker, daemon=True)
            self._sr_thread.start()

        # Status text shown on dashboard
        self.last_spoken  = ""
        self.sr_status    = "LISTENING" if self.sr_enabled else "OFFLINE"

    # ------------------------------------------------------------------
    def speak(self, text):
        """Queue a TTS utterance (non-blocking)."""
        self.last_spoken = text
        if self.tts_enabled:
            self._tts_queue.put(text)

    def pending_command(self):
        """
        Returns the next recognised voice command string, or None.
        Call each frame.
        """
        try:
            return self._cmd_queue.get_nowait()
        except queue.Empty:
            return None

    # ------------------------------------------------------------------
    # TTS worker — runs in its own thread
    # ------------------------------------------------------------------
    def _tts_worker(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate",   165)
            engine.setProperty("volume", 0.9)
            # Prefer a female voice if available
            voices = engine.getProperty("voices")
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
        except Exception:
            self.tts_enabled = False
            return

        while True:
            try:
                text = self._tts_queue.get(timeout=1)
                engine.say(text)
                engine.runAndWait()
            except queue.Empty:
                pass
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Speech recognition worker — runs in its own thread
    # ------------------------------------------------------------------
    def _sr_worker(self):
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        while True:
            try:
                with sr.Microphone() as source:
                    self.sr_status = "CALIBRATING"
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    self.sr_status = "LISTENING"
                    self._listening = True

                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    self.sr_status = "PROCESSING"
                    self._listening = False

                    text = recognizer.recognize_google(audio)
                    self._cmd_queue.put(text.lower())
                    self.sr_status = "LISTENING"

            except sr.WaitTimeoutError:
                self.sr_status = "LISTENING"
            except sr.UnknownValueError:
                self.sr_status = "LISTENING"
            except sr.RequestError:
                self.sr_status = "NO NETWORK"
                time.sleep(5)
            except Exception:
                self.sr_status = "OFFLINE"
                time.sleep(5)
# =============================================================================
# main.py
# Nexus AIoT  |  AI-Powered Touchless Smart Environment System
# Main orchestrator — boots the system and drives the render loop.
#
# Modules:
#   config.py          - All constants and color palette
#   gesture_detector   - MediaPipe hand landmark + gesture engine
#   smart_room         - 7 devices, 7 modes, analytics, state
#   face_module        - Haar face detection + authorization
#   password_module    - Gesture password lock/unlock
#   voice_module       - TTS output + speech recognition
#   sound_module       - Windows winsound effects
#   ui_renderer        - Full premium light dashboard
#
# Run:   python main.py
# Quit:  Press Q or ESC
# =============================================================================

import cv2
import numpy as np
import time
import sys

import config
from gesture_detector import GestureDetector
from smart_room       import SmartRoom
from face_module      import FaceModule
from password_module  import PasswordModule
from voice_module     import VoiceModule
import sound_module   as sound
from ui_renderer      import DashboardRenderer, draw_boot


def main():
    print("=" * 62)
    print(f"  {config.PROJECT_NAME}  |  {config.PROJECT_SUBTITLE}")
    print(f"  {config.PROJECT_VERSION}  —  Initializing...")
    print("=" * 62)

    # ── Webcam ────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open webcam. Check connection and try again.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS,          30)

    # ── Modules ────────────────────────────────────────────────────────
    print("  Loading all modules...")
    gesture_det = GestureDetector()
    room        = SmartRoom()
    face_mod    = FaceModule()
    pwd_mod     = PasswordModule()
    voice_mod   = VoiceModule()
    renderer    = DashboardRenderer()

    # ── Window ─────────────────────────────────────────────────────────
    cv2.namedWindow(config.WINDOW_TITLE, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(config.WINDOW_TITLE, config.WIN_W, config.WIN_H)
    canvas = np.zeros((config.WIN_H, config.WIN_W, 3), dtype=np.uint8)

    # ── Boot sequence ──────────────────────────────────────────────────
    sound.play_boot()
    boot_start = time.time()
    print("  Boot sequence running... (Space to skip)")

    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1) if ret else np.zeros((480, 640, 3), np.uint8)
        elapsed = time.time() - boot_start
        done    = draw_boot(canvas, elapsed, config.BOOT_MESSAGES)
        cv2.imshow(config.WINDOW_TITLE, canvas)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            cap.release(); cv2.destroyAllWindows(); return
        if done or key == ord(' '):
            break

    print("  Boot complete. Main loop starting.")
    voice_mod.speak(
        f"{config.PROJECT_NAME} online. "
        "Please perform the gesture password sequence to unlock the system."
    )

    # ── FPS counter ────────────────────────────────────────────────────
    fps_count, fps_display = 0, 0
    fps_timer = time.time()

    # ── Main loop ──────────────────────────────────────────────────────
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)

        # ── Gesture detection ─────────────────────────────────────────
        results, stable_gesture, hand_landmarks = gesture_det.detect(frame)

        # Draw MediaPipe landmarks — colors match the soft-dark theme
        if hand_landmarks:
            gesture_det.mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                gesture_det.mp_hands.HAND_CONNECTIONS,
                gesture_det.mp_draw.DrawingSpec(
                    color=config.C_ACCENT_LO, thickness=2, circle_radius=3),
                gesture_det.mp_draw.DrawingSpec(
                    color=config.C_BLUE, thickness=2, circle_radius=2),
            )

        # ── Face detection ────────────────────────────────────────────
        face_mod.process(frame)

        # ── Password + gesture routing ────────────────────────────────
        pwd_mod.update()

        if stable_gesture and gesture_det.is_ready():
            if room.system_locked:
                # Feed into password checker
                prev_state = pwd_mod.state
                new_state  = pwd_mod.push_gesture(stable_gesture)
                gesture_det.trigger()

                if new_state == "SUCCESS" and prev_state != "SUCCESS":
                    room.unlock()
                    sound.play_unlock()
                    voice_mod.speak("Access granted. System unlocked. Welcome.")
                    renderer.trigger_flash()
                    renderer.notify("System Unlocked — Welcome")

                elif new_state == "FAILED" and prev_state != "FAILED":
                    sound.play_denied()
                    voice_mod.speak("Access denied. Incorrect gesture sequence.")
                    renderer.notify("Access Denied")

            else:
                # System unlocked — route gesture to room
                # ── OK Sign: cycle to next mode ───────────────────────
                if stable_gesture == "OK Sign":
                    new_mode   = room.cycle_mode()
                    voice_txt  = f"{new_mode.lower()} mode activated"
                    notif_txt  = f"Mode changed to {new_mode}"
                    gesture_det.trigger()
                    renderer.trigger_flash()
                    sound.play_mode_switch()
                    voice_mod.speak(voice_txt)
                    renderer.notify(notif_txt)

                else:
                    # All other device-control gestures
                    triggered, voice_txt = room.apply_gesture(stable_gesture)
                    if triggered:
                        gesture_det.trigger()
                        renderer.trigger_flash()

                        if stable_gesture == config.ACCESSIBILITY_GESTURE:
                            sound.play_unlock()
                            voice_mod.speak(
                                "Accessibility access activated. Door is now open.")
                            renderer.notify("Accessibility Access Activated")
                        else:
                            sound.play_gesture()
                            if voice_txt:
                                voice_mod.speak(voice_txt)

        # ── Voice commands ────────────────────────────────────────────
        voice_cmd = voice_mod.pending_command()
        if voice_cmd and not room.system_locked:
            triggered, response = room.apply_voice_command(voice_cmd)
            if triggered:
                sound.play_voice_detected()
                voice_mod.speak(response)
                renderer.trigger_flash()
                renderer.notify(response)

        # ── Render ────────────────────────────────────────────────────
        renderer.render(
            canvas, frame, room, gesture_det,
            face_mod, pwd_mod, voice_mod, fps_display,
        )
        cv2.imshow(config.WINDOW_TITLE, canvas)

        # ── FPS ───────────────────────────────────────────────────────
        fps_count += 1
        if time.time() - fps_timer >= 1.0:
            fps_display = fps_count
            fps_count   = 0
            fps_timer   = time.time()

        # ── Keyboard ──────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break

        # Mode shortcuts 1-7
        mode_map = {
            ord('1'): "NORMAL",   ord('2'): "STUDY",
            ord('3'): "SLEEP",    ord('4'): "CINEMA",
            ord('5'): "GAMING",   ord('6'): "SECURITY",
            ord('7'): "EMERGENCY",
        }
        if key in mode_map and not room.system_locked:
            mode = mode_map[key]
            room.apply_mode(mode)
            sound.play_mode_switch()
            voice_mod.speak(f"{mode.lower()} mode activated")
            renderer.notify(f"{mode} Mode Activated")

        # Lock / Unlock
        if key in (ord('l'), ord('L')):
            room.lock()
            pwd_mod.reset()
            sound.play_alert()
            voice_mod.speak("System locked.")
            renderer.notify("System Locked")

        if key in (ord('u'), ord('U')):
            room.unlock()
            pwd_mod._state = "SUCCESS"
            renderer.notify("System Unlocked")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n  {config.PROJECT_NAME} session ended. Goodbye.")


if __name__ == "__main__":
    main()

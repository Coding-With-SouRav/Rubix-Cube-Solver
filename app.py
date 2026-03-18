import webview
from Cube.rxsol import solve
import logging
import json
import os
import sys
import time
import threading
import signal
import ctypes
from datetime import datetime

# Windows‑specific imports and helpers
if sys.platform == "win32":
    from ctypes import wintypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HISTORY_FILE = 'Cube/history.json'
BASE = os.path.dirname(os.path.abspath(__file__))
WINDOW_STATE_FILE = os.path.join(BASE, "Cube/window_state.json")

# ----------------------------------------------------------------------
# Resource path helper (for icon, etc.)
# ----------------------------------------------------------------------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ICON_PATH = resource_path(r"Cube/icon.ico")

# ----------------------------------------------------------------------
# Window state manager (copied from run.py)
# ----------------------------------------------------------------------
class WindowStateManager:
    def __init__(self):
        self.last_state = None
        self.is_tracking = True

    def get_window_state(self, title):
        """Get complete window state including placement."""
        if sys.platform != "win32":
            return None

        user32 = ctypes.windll.user32

        class WINDOWPLACEMENT(ctypes.Structure):
            _fields_ = [
                ("length", wintypes.UINT),
                ("flags", wintypes.UINT),
                ("showCmd", wintypes.UINT),
                ("ptMinPosition", wintypes.POINT),
                ("ptMaxPosition", wintypes.POINT),
                ("rcNormalPosition", wintypes.RECT),
            ]

        hwnd = user32.FindWindowW(None, title)
        if not hwnd:
            return None

        current_rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(current_rect))

        wp = WINDOWPLACEMENT()
        wp.length = ctypes.sizeof(WINDOWPLACEMENT)
        user32.GetWindowPlacement(hwnd, ctypes.byref(wp))

        is_maximized = (wp.showCmd == 3)  # SW_SHOWMAXIMIZED
        style = user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
        is_resizeable = (style & 0x00040000) != 0  # WS_SIZEBOX

        state = {
            "current_x": current_rect.left,
            "current_y": current_rect.top,
            "current_width": current_rect.right - current_rect.left,
            "current_height": current_rect.bottom - current_rect.top,
            "is_maximized": is_maximized,
            "normal_x": wp.rcNormalPosition.left,
            "normal_y": wp.rcNormalPosition.top,
            "normal_width": wp.rcNormalPosition.right - wp.rcNormalPosition.left,
            "normal_height": wp.rcNormalPosition.bottom - wp.rcNormalPosition.top,
            "is_resizeable": is_resizeable,
            "timestamp": time.time()
        }
        return state

    def save_window_state(self, title, force_save=False):
        """Save window state to file."""
        if sys.platform != "win32":
            return False

        state = self.get_window_state(title)
        if not state:
            return False

        has_changed = False
        if self.last_state is None:
            has_changed = True
        else:
            if (abs(state["current_x"] - self.last_state.get("current_x", 0)) > 2 or
                abs(state["current_y"] - self.last_state.get("current_y", 0)) > 2 or
                abs(state["current_width"] - self.last_state.get("current_width", 0)) > 2 or
                abs(state["current_height"] - self.last_state.get("current_height", 0)) > 2 or
                state["is_maximized"] != self.last_state.get("is_maximized", False)):
                has_changed = True

        if not has_changed and not force_save:
            return False

        self.last_state = state

        try:
            data = {}
            if os.path.exists(WINDOW_STATE_FILE):
                with open(WINDOW_STATE_FILE, "r") as f:
                    data = json.load(f)

            window_data = {
                "x": state["normal_x"],
                "y": state["normal_y"],
                "width": state["normal_width"],
                "height": state["normal_height"],
                "is_maximized": state["is_maximized"],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "is_resizeable": state["is_resizeable"]
            }
            data[title] = window_data

            with open(WINDOW_STATE_FILE, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
            return False

    def restore_window_state(self, title):
        """Restore window state from file."""
        if sys.platform != "win32":
            return False

        if not os.path.exists(WINDOW_STATE_FILE):
            return False

        try:
            with open(WINDOW_STATE_FILE, "r") as f:
                data = json.load(f)

            if title not in data:
                return False

            state = data[title]
            hwnd = None
            for _ in range(50):  # wait up to 5 seconds
                hwnd = ctypes.windll.user32.FindWindowW(None, title)
                if hwnd:
                    break
                time.sleep(0.1)

            if not hwnd:
                return False

            ctypes.windll.user32.ShowWindow(hwnd, 1)  # SW_SHOWNORMAL
            ctypes.windll.user32.MoveWindow(
                hwnd,
                state["x"],
                state["y"],
                state["width"],
                state["height"],
                True
            )

            if state.get("is_maximized", False):
                time.sleep(0.1)
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE

            time.sleep(0.2)
            self.save_window_state(title, force_save=True)
            return True
        except Exception as e:
            logger.error(f"Error restoring window state: {e}")
            return False

    def track_window_changes(self, title, interval=0.1):
        """Track window changes in real-time."""
        while self.is_tracking:
            try:
                state = self.get_window_state(title)
                if state:
                    is_resizing = False
                    if self.last_state and not state["is_maximized"]:
                        if (abs(state["current_width"] - self.last_state.get("current_width", 0)) > 10 or
                            abs(state["current_height"] - self.last_state.get("current_height", 0)) > 10):
                            is_resizing = True

                    if not state["is_maximized"]:
                        if is_resizing:
                            self.save_window_state(title, force_save=True)
                            time.sleep(0.05)
                            continue
                        self.save_window_state(title)
                    else:
                        self.save_window_state(title)
            except Exception:
                pass  # ignore transient errors
            time.sleep(interval)

    def stop_tracking(self):
        self.is_tracking = False

# ----------------------------------------------------------------------
# Title bar and icon helpers (Windows only)
# ----------------------------------------------------------------------
def set_black_titlebar(title):
    """Set dark title bar (Windows 10/11)."""
    if sys.platform != "win32":
        return
    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi
    DWMWA_CAPTION_COLOR = 35
    DWMWA_TEXT_COLOR = 36

    # Wait for window handle
    hwnd = None
    for _ in range(50):
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            break
        time.sleep(0.05)
    if not hwnd:
        return

    black = ctypes.c_int(0x000000)
    white = ctypes.c_int(0xFFFFFF)
    dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(black), ctypes.sizeof(black))
    dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_TEXT_COLOR, ctypes.byref(white), ctypes.sizeof(white))

class WindowIconSetter:
    def __init__(self, title, icon_path):
        self.title = title
        self.icon_path = icon_path
        self.user32 = ctypes.windll.user32

    def set_icon(self):
        if sys.platform != "win32" or not os.path.exists(self.icon_path):
            return

        hwnd = None
        for _ in range(50):
            hwnd = self.user32.FindWindowW(None, self.title)
            if hwnd:
                break
            time.sleep(0.1)
        if not hwnd:
            return

        LR_LOADFROMFILE = 0x10
        IMAGE_ICON = 1
        WM_SETICON = 0x80

        small = self.user32.LoadImageW(0, self.icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        big = self.user32.LoadImageW(0, self.icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)

        if small:
            self.user32.SendMessageW(hwnd, WM_SETICON, 0, small)
        if big:
            self.user32.SendMessageW(hwnd, WM_SETICON, 1, big)

# ----------------------------------------------------------------------
# History management (unchanged)
# ----------------------------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history_entry(cube_string, solution):
    history = load_history()
    entry = {
        'cube_string': cube_string,
        'solution': solution,
        'timestamp': datetime.now().isoformat()
    }
    history.append(entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    return entry

# ----------------------------------------------------------------------
# API (unchanged)
# ----------------------------------------------------------------------
class Api:
    def solve(self, cube_string):
        try:
            if len(cube_string) != 54:
                return {'error': 'Cube string must be 54 characters'}
            solution = solve(cube_string)
            return {'solution': solution}
        except Exception as e:
            logger.error(f"Solver error: {e}")
            return {'error': str(e)}

    def get_history(self):
        return load_history()

    def add_history(self, cube_string, solution):
        save_history_entry(cube_string, solution)
        return {'status': 'ok'}

    def delete_history(self, timestamp):
        try:
            history = load_history()
            new_history = [entry for entry in history if entry.get('timestamp') != timestamp]
            if len(new_history) == len(history):
                return {'error': 'Entry not found'}
            with open(HISTORY_FILE, 'w') as f:
                json.dump(new_history, f, indent=2)
            return {'status': 'ok'}
        except Exception as e:
            logger.error(f"Delete history error: {e}")
            return {'error': str(e)}

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Set Windows app ID (optional, for taskbar grouping)
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.rubikssolver.app")

    WINDOW_TITLE = "3D Rubik's Cube Solver"

    window_manager = WindowStateManager()

    def handle_shutdown(*_):
        logger.info("Saving window state on shutdown...")
        window_manager.save_window_state(WINDOW_TITLE, force_save=True)
        window_manager.stop_tracking()
        os._exit(0)

    # Create the webview window
    window = webview.create_window(
        WINDOW_TITLE,
        "Cube/index.html",
        js_api=Api(),
        width=900,
        height=700,
        resizable=True,
        text_select=True,
        background_color='#000000'
    )

    # Patch the destroy method to save state on close
    original_destroy = window.destroy
    def patched_destroy():
        handle_shutdown()
        original_destroy()
    window.destroy = patched_destroy

    # Signal handlers for console interrupt
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    def on_start():
        """Called after the window is shown."""
        if sys.platform == "win32":
            set_black_titlebar(WINDOW_TITLE)
            window_manager.restore_window_state(WINDOW_TITLE)
            WindowIconSetter(WINDOW_TITLE, ICON_PATH).set_icon()
            # Start tracking thread
            threading.Thread(
                target=window_manager.track_window_changes,
                args=(WINDOW_TITLE, 0.1),
                daemon=True
            ).start()

    webview.start(on_start, debug=False)
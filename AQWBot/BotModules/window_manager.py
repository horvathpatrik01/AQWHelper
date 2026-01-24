from PIL import Image
import win32gui
import win32ui
import win32con
import win32api
import ctypes
import time

class WindowManager:
    def __init__(self):
        self.target_handle = None

    def find_target_window(self):
        """Finds the active window and tries to locate the game renderer child."""
        try:
            parent = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(parent)
            if not parent: return None, "No active window"

            # Search for specific child renderers (Flash, Unity, etc.)
            children = []
            def enum_handler(hwnd, ctx): children.append(hwnd)
            try: win32gui.EnumChildWindows(parent, enum_handler, None)
            except: pass

            target = parent 
            found_specific = False
            for child in children:
                class_name = win32gui.GetClassName(child)
                if any(x in class_name for x in ["Macromedia", "Chrome_Render", "Unity", "d3d"]):
                    target = child
                    found_specific = True
                    break
            
            if not found_specific and children:
                target = children[0]

            self.target_handle = target
            return target, title
        except Exception as e:
            return None, str(e)

    def capture_client_area(self):
        """
        Captures screenshot of the target window using PrintWindow.
        This works even if the window is covered by other applications.
        """
        if not self.target_handle: return None
        try:
            left, top, right, bot = win32gui.GetClientRect(self.target_handle)
            w, h = right - left, bot - top
            
            # Create Device Contexts
            hwndDC = win32gui.GetDC(self.target_handle)
            mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            # Create Bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
            saveDC.SelectObject(saveBitMap)
            
            # --- CHANGE: Use PrintWindow instead of BitBlt ---
            # 2 = PW_CLIENTONLY (Windows 8.1+). Captures only the client area.
            # This forces the window to render to our bitmap even if obscured.
            result = ctypes.windll.user32.PrintWindow(self.target_handle, saveDC.GetSafeHdc(), 2)

            if result != 1:
                # Fallback for older windows or failures
                result = ctypes.windll.user32.PrintWindow(self.target_handle, saveDC.GetSafeHdc(), 0)
            
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
            
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.target_handle, hwndDC)
            return img
        except Exception as e: 
            print(f"Capture Error: {e}")
            return None

    def send_background_click(self, x, y):
        """Sends a click to the target window at coordinates x, y."""
        if not self.target_handle: return
        try:
            lparam = (y << 16) | (x & 0xFFFF)
            win32gui.PostMessage(self.target_handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            time.sleep(0.05) 
            win32gui.PostMessage(self.target_handle, win32con.WM_LBUTTONUP, 0, lparam)
        except: pass

    def get_mouse_client_coords(self):
        """Returns mouse position relative to the target window."""
        if not self.target_handle: return 0, 0
        mx, my = win32api.GetCursorPos()
        return win32gui.ScreenToClient(self.target_handle, (mx, my))
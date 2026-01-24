import tkinter as tk
from tkinter import Canvas
from PIL import ImageTk

class SnippingTool(tk.Toplevel):
    def __init__(self, parent, image, callback):
        super().__init__(parent)
        self.title("Select Drop Name")
        self.attributes("-fullscreen", True)
        self.callback = callback
        self.image = image
        self.photo = ImageTk.PhotoImage(image)
        
        self.canvas = Canvas(self, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        if x2 - x1 > 5 and y2 - y1 > 5:
            self.callback(self.image.crop((x1, y1, x2, y2)))
            self.destroy()
        else:
            self.canvas.delete(self.rect)

import os
from tkinter import *
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageOps

class ImageMaskEditor:
    def __init__(self, master):
        self.master = master
        master.title("Image Mask Editor")

        # Initialize directories and image list
        self.rgb_directory = filedialog.askdirectory(title="Select RGB Image Directory")
        self.mask_directory = filedialog.askdirectory(title="Select Mask Directory")
        self.image_files = sorted(os.listdir(self.rgb_directory)) if self.rgb_directory else []
        self.current_image_index = -1

        # Initialize variables
        self.image = None
        self.mask = None
        self.mask_path = None
        self.result = None
        self.opacity = 0.5
        self.drawing = False
        self.erasing = False
        self.last_x, self.last_y = None, None
        self.zoom = 1.0
        self.pen_thickness = 5
        self.pen_color = "white"
        self.eraser_color = "black"

        self.status_label = Label(master, text="")
        self.status_label.pack(side=BOTTOM)

        # UI elements
        self.canvas = Canvas(master, cursor="cross")
        self.canvas.pack(fill=BOTH, expand=True)

        # Mouse events
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<MouseWheel>", self.zoom_image)

        # Buttons
        prev_img_btn = Button(master, text="Previous Image", command=self.load_previous_image)
        prev_img_btn.pack(side=LEFT)

        next_img_btn = Button(master, text="Next Image", command=self.load_next_image)
        next_img_btn.pack(side=LEFT)

        opacity_scale = Scale(master, from_=0, to=1, resolution=0.1, orient=HORIZONTAL, label="Opacity", command=self.update_opacity)
        opacity_scale.set(self.opacity)
        opacity_scale.pack(side=LEFT)

        thickness_scale = Scale(master, from_=1, to=20, orient=HORIZONTAL, label="Pen Thickness", command=self.update_thickness)
        thickness_scale.set(self.pen_thickness)
        thickness_scale.pack(side=LEFT)

        color_btn = Button(master, text="Choose Pen Color", command=self.choose_pen_color)
        color_btn.pack(side=LEFT)

        eraser_btn = Button(master, text="Eraser", command=self.toggle_eraser)
        eraser_btn.pack(side=LEFT)

        save_btn = Button(master, text="Save Mask", command=self.save_mask)
        save_btn.pack(side=LEFT)

    def load_image(self, index_change):
        new_index = self.current_image_index + index_change
        if 0 <= new_index < len(self.image_files):
            self.current_image_index = new_index
            image_file = self.image_files[self.current_image_index]
            image_path = os.path.join(self.rgb_directory, image_file)
            self.mask_path = os.path.join(self.mask_directory, image_file)

            if os.path.exists(image_path):
                self.image = Image.open(image_path)
                self.mask = Image.open(self.mask_path).convert("L") if os.path.exists(self.mask_path) else Image.new("L", self.image.size, 0)
                self.display_image()
                self.master.title(f"Image Mask Editor - {image_file}")
            else:
                messagebox.showinfo("Info", "No more images in the directory.")
        else:
            messagebox.showinfo("Info", "No more images in the direction.")

    def load_next_image(self):
        self.load_image(1)

    def load_previous_image(self):
        self.load_image(-1)
    def update_opacity(self, value):
        self.opacity = float(value)
        self.display_image()

    def update_thickness(self, value):
        self.pen_thickness = int(value)

    def choose_pen_color(self):
        color = colorchooser.askcolor(color=self.pen_color)[1]
        if color:
            self.pen_color = color
            self.erasing = False

    def toggle_eraser(self):
        self.erasing = not self.erasing

    def zoom_image(self, event):
        if event.delta > 0:
            self.zoom *= 1.1
        elif event.delta < 0:
            self.zoom /= 1.1

        self.display_image()

    def display_image(self):
        if self.image and self.mask:
            resized_image = self.image.resize((int(self.image.width * self.zoom), int(self.image.height * self.zoom)), Image.Resampling.LANCZOS)
            resized_mask = self.mask.resize((int(self.mask.width * self.zoom), int(self.mask.height * self.zoom)), Image.Resampling.LANCZOS)
            
            # Create an RGBA version of the mask with the specified opacity
            mask_rgba = ImageOps.colorize(resized_mask, (0, 0, 0), (255, 255, 255))
            mask_rgba.putalpha(int(self.opacity * 255))

            # Composite the mask over the image
            self.result = Image.alpha_composite(resized_image.convert("RGBA"), mask_rgba)

            self.tk_image = ImageTk.PhotoImage(self.result)
            self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
            self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)
            self.canvas.image = self.tk_image

    def start_draw(self, event):
        if self.mask:
            self.drawing = True
            self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        if self.drawing and self.mask:
            draw = ImageDraw.Draw(self.mask)
            color = self.eraser_color if self.erasing else self.pen_color
            # Drawing circular pen head
            r = self.pen_thickness // 2
            draw.ellipse([(event.x / self.zoom - r, event.y / self.zoom - r), (event.x / self.zoom + r, event.y / self.zoom + r)], fill=color, outline=color)
            self.last_x, self.last_y = event.x, event.y
            self.display_image()

    def save_mask(self):
        if self.mask and self.mask_path:
            self.mask.resize(self.image.size, Image.Resampling.LANCZOS).save(self.mask_path)
            self.status_label.config(text="Saved!")
            self.master.after(3000, lambda: self.status_label.config(text=""))  # Clears the message after 3 seconds

root = Tk()
my_gui = ImageMaskEditor(root)
root.mainloop()

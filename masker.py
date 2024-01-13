import os
from tkinter import *
from tkinter import filedialog, colorchooser, messagebox, simpledialog
from PIL import Image, ImageTk, ImageDraw, ImageOps

class ImageMaskEditor:
    def __init__(self, master):
        self.mask_history = []
        
        self.master = master
        master.title("Image Mask Editor")

        self.rgb_directory = filedialog.askdirectory(title="Select RGB Image Directory")
        self.mask_directory = filedialog.askdirectory(title="Select Mask Directory")
        self.image_files = sorted(os.listdir(self.rgb_directory)) if self.rgb_directory else []
        self.current_image_index = -1
        
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

        self.image_number_label = Label(master, text="")
        self.image_number_label.pack(side=BOTTOM)

        self.canvas = Canvas(master, cursor="cross")
        self.canvas.pack(fill=BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonPress-3>", self.start_erase)
        self.canvas.bind("<B3-Motion>", self.erase)
        self.canvas.bind("<MouseWheel>", self.zoom_image)

        prev_img_btn = Button(master, text="<<<<<", command=self.load_previous_image)
        prev_img_btn.pack(side=LEFT)
        
        save_btn = Button(master, text="Save", command=self.save_mask)
        save_btn.pack(side=LEFT)
        
        next_img_btn = Button(master, text=">>>>>", command=self.load_next_image)
        next_img_btn.pack(side=LEFT)
        
        jump_to_img_btn = Button(master, text="Jump to", command=self.jump_to_image)
        jump_to_img_btn.pack(side=LEFT)

        delete_btn = Button(master, text="Delete", command=self.delete_image)
        delete_btn.pack(side=LEFT)
        
        opacity_scale = Scale(master, from_=0, to=1, resolution=0.1, orient=HORIZONTAL, label="Opacity", command=self.update_opacity)
        opacity_scale.set(self.opacity)
        opacity_scale.pack(side=LEFT)

                # Thickness Scale
        self.thickness_scale = Scale(master, from_=1, to=20, orient=HORIZONTAL, label="Pen Thickness", command=self.update_thickness)
        self.thickness_scale.set(self.pen_thickness)
        self.thickness_scale.pack(side=LEFT)

        master.bind("<Control-z>", self.undo_last_action)

        if self.image_files:
            self.current_image_index = 0
            self.load_image(0)
            
        # Pen size selection buttons
        for size in [1, 3, 5, 10, 20]:
            btn = Button(master, text=str(size), command=lambda s=size: self.set_pen_thickness(s))
            btn.pack(side=LEFT)

        big_btn = Button(master, text="BIG", command=lambda: self.set_pen_thickness(40))
        big_btn.pack(side=LEFT)
        
        self.eraser_btn = Button(master, text="Mode:Drawing", command=self.toggle_eraser)
        self.eraser_btn.pack(side=LEFT)

    ####
        undo_btn = Button(master, text="Undo", command=self.undo_last_action)
        undo_btn.pack(side=LEFT)

    def save_to_history(self):
        """Save the current mask state to the history."""
        if self.mask:
            self.mask_history.append(self.mask.copy())

    def undo_last_action(self, event=None):  # 'event' parameter added for keyboard binding
        """Undo the last drawing action."""
        if self.mask_history:
            self.mask = self.mask_history.pop()
            self.display_image()
        else:
            self.status_label.config(text="Nothing to undo.")
            
    def start_draw(self, event):
        self.save_to_history()  # Save the state before drawing
        self.drawing = True
        self.last_x, self.last_y = event.x, event.y
        self.draw_or_erase(event, self.pen_color)

    def start_erase(self, event):
        self.save_to_history()  # Save the state before erasing
        self.drawing = True
        self.last_x, self.last_y = event.x, event.y

    #####
    def set_pen_thickness(self, size):
        self.pen_thickness = size
        self.thickness_scale.set(size)  # Update the slider position
        self.status_label.config(text=f"Pen size set to {size}")

    def jump_to_image(self):
        num = simpledialog.askinteger("Jump to", "Enter Image Number", parent=self.master, minvalue=1, maxvalue=len(self.image_files))
        if num is not None:
            self.current_image_index = num - 1  # Convert to zero-based index
            self.load_image(0) 
            
    def delete_image(self):
        if self.current_image_index >= 0 and self.current_image_index < len(self.image_files):
            rgb_path = os.path.join(self.rgb_directory, self.image_files[self.current_image_index])
            mask_path = os.path.join(self.mask_directory, self.image_files[self.current_image_index])

            if os.path.exists(rgb_path):
                os.remove(rgb_path)
            if os.path.exists(mask_path):
                os.remove(mask_path)

            # Remove the filename from the list and update the index
            del self.image_files[self.current_image_index]
            self.current_image_index -= 1
            self.load_next_image()  # Load next image or update display if no more images

            self.status_label.config(text="Image and mask deleted.")
        else:
            self.status_label.config(text="No image to delete.")

    def toggle_eraser(self):
        self.erasing = not self.erasing
        if self.erasing:
            # In Erase mode, left click to erase, right click to draw
            self.canvas.bind("<ButtonPress-1>", self.start_erase)
            self.canvas.bind("<B1-Motion>", self.erase)
            self.canvas.bind("<ButtonPress-3>", self.start_draw)
            self.canvas.bind("<B3-Motion>", self.draw)
            self.eraser_btn.config(text="Mode:Eraseing")
            self.status_label.config(text="Mode: Erase")
        else:
            # In Draw mode, left click to draw, right click to erase
            self.canvas.bind("<ButtonPress-1>", self.start_draw)
            self.canvas.bind("<B1-Motion>", self.draw)
            self.canvas.bind("<ButtonPress-3>", self.start_erase)
            self.canvas.bind("<B3-Motion>", self.erase)
            self.eraser_btn.config(text="Mode:Drawing")
            self.status_label.config(text="Mode: Draw")

    def draw(self, event):
        if self.drawing and self.mask:
            self.draw_or_erase(event, self.pen_color)

    def erase(self, event):
        if self.drawing and self.mask:
            self.draw_or_erase(event, self.eraser_color)
         
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
                self.image_number_label.config(text=f"{self.current_image_index + 1}/{len(self.image_files)}")
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
            mask_rgba = ImageOps.colorize(resized_mask, (0, 0, 0), (255, 255, 255))
            mask_rgba.putalpha(int(self.opacity * 255))
            self.result = Image.alpha_composite(resized_image.convert("RGBA"), mask_rgba)
            self.tk_image = ImageTk.PhotoImage(self.result)
            self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
            self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image)
            self.canvas.image = self.tk_image

    def draw_or_erase(self, event, color):
        if self.last_x is not None and self.last_y is not None:
            draw = ImageDraw.Draw(self.mask)
            if self.pen_thickness == 1:
                # Draw a single pixel for the thinnest line
                x, y = int(event.x / self.zoom), int(event.y / self.zoom)
                draw.point([x, y], fill=color)
            else:
                r = self.pen_thickness // 2
                x0, y0 = (event.x / self.zoom - r, event.y / self.zoom - r)
                x1, y1 = (event.x / self.zoom + r, event.y / self.zoom + r)
                draw.ellipse([x0, y0, x1, y1], fill=color, outline=color)
            self.display_image()
        self.last_x, self.last_y = event.x, event.y

    def save_mask(self):
        if self.mask and self.mask_path:
            self.mask.resize(self.image.size, Image.Resampling.LANCZOS).save(self.mask_path)
            self.status_label.config(text="Saved!")
            self.master.after(3000, lambda: self.status_label.config(text=""))

root = Tk()
my_gui = ImageMaskEditor(root)
root.mainloop()

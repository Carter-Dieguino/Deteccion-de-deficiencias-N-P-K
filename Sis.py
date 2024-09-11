import cv2
import numpy as np
import pandas as pd
import datetime
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

class LiveFeed:
    def __init__(self, root, reference_area_cm2=1):
        self.cap = cv2.VideoCapture(3)
        self.reference_area_cm2 = reference_area_cm2
        self.reference_area_pixels = None
        self.image_counter = 1
        self.data = []
        self.session_folder = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trash_folder = "trash"
        os.makedirs(self.session_folder, exist_ok=True)
        os.makedirs(self.trash_folder, exist_ok=True)
        self.create_gui(root)
        self.update_frame()

    def process_frame(self, frame):
        frame_height, frame_width, _ = frame.shape
        reference_area = frame[frame_height-150:frame_height-50, 50:150]
        gray = cv2.cvtColor(reference_area, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_contour) > 100:
                cv2.drawContours(reference_area, [max_contour], -1, (0, 255, 255), 2)
                if self.reference_area_pixels is None:
                    self.reference_area_pixels = cv2.contourArea(max_contour)
        
        cv2.rectangle(frame, (50, frame_height-150), (150, frame_height-50), (0, 0, 255), 2)
        cv2.putText(frame, "Área de referencia", (50, frame_height-160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame

    def detect_leaf(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
            return frame, max_contour
        
        return frame, None

    def calculate_leaf_area(self, leaf_contour):
        if self.reference_area_pixels is None:
            return None
        
        leaf_area_pixels = cv2.contourArea(leaf_contour)
        leaf_area_cm2 = (leaf_area_pixels / self.reference_area_pixels) * self.reference_area_cm2
        return leaf_area_cm2, leaf_area_pixels

    def save_image_with_metadata(self, frame, leaf_area_cm2, leaf_area_pixels):
        timestamp = datetime.datetime.now()
        filename = f"hoja_{self.image_counter}_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.session_folder, filename)

        frame_height, frame_width, _ = frame.shape
        black_bar = np.zeros((100, frame_width, 3), dtype=np.uint8)
        cv2.putText(black_bar, f"Filename: {filename}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Reference Area: {self.reference_area_pixels:.2f} pixels, {self.reference_area_cm2} cm^2", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Leaf Area: {leaf_area_pixels:.2f} pixels, {leaf_area_cm2:.2f} cm^2", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Date: {timestamp.strftime('%Y-%m-%d')}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Time: {timestamp.strftime('%H:%M:%S')}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Researcher: Diego Ramos", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Imagen procesada correctamente", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        frame_with_metadata = np.vstack((frame, black_bar))
        cv2.imwrite(filepath, frame_with_metadata)
        
        self.data.append([filename, self.reference_area_pixels, self.reference_area_cm2, leaf_area_pixels, leaf_area_cm2, timestamp.strftime('%Y-%m-%d'), timestamp.strftime('%H:%M:%S'), 'Diego Ramos'])
        self.image_counter += 1
        self.save_data_to_excel()

        self.display_captured_image(filepath)
        self.show_message("Imagen procesada correctamente", 3)

    def save_data_to_excel(self):
        df = pd.DataFrame(self.data, columns=['Filename', 'Reference Area (pixels)', 'Reference Area (cm^2)', 'Leaf Area (pixels)', 'Leaf Area (cm^2)', 'Date', 'Time', 'Researcher'])
        excel_filename = os.path.join(self.session_folder, "leaf_data.xlsx")
        df.to_excel(excel_filename, index=False)
        self.display_data(excel_filename)

    def run(self):
        self.root.mainloop()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = self.process_frame(frame)
            frame, leaf_contour = self.detect_leaf(frame)
            self.display_transmission(frame)

            if self.capturing and leaf_contour is not None:
                leaf_area_cm2, leaf_area_pixels = self.calculate_leaf_area(leaf_contour)
                self.save_image_with_metadata(frame, leaf_area_cm2, leaf_area_pixels)
                self.capturing = False

        self.root.after(10, self.update_frame)

    def capture_image(self, event):
        self.capturing = True

    def create_gui(self, root):
        self.root = root
        self.root.geometry("1500x750")
        self.capturing = False

        self.transmission_label = ttk.Label(self.root, text="Transmisión")
        self.transmission_label.place(x=0, y=0, width=750, height=550)
        self.transmission_canvas = tk.Canvas(self.root, bg="black")
        self.transmission_canvas.place(x=0, y=0, width=750, height=550)

        self.captured_label = ttk.Label(self.root, text="Imagen capturada")
        self.captured_label.place(x=750, y=0, width=750, height=550)
        self.captured_canvas = tk.Canvas(self.root, bg="black")
        self.captured_canvas.place(x=750, y=0, width=750, height=550)

        self.file_explorer_label = ttk.Label(self.root, text="Explorador de archivos")
        self.file_explorer_label.place(x=0, y=550, width=750, height=200)
        self.file_explorer_tree = ttk.Treeview(self.root)
        self.file_explorer_tree.place(x=0, y=550, width=960, height=200)
        self.file_explorer_tree.bind('<Button-3>', self.show_file_options)

        self.data_label = ttk.Label(self.root, text="Datos")
        self.data_label.place(x=750, y=550, width=750, height=200)
        self.data_text = tk.Text(self.root, wrap=tk.WORD)
        self.data_text.place(x=750, y=550, width=750, height=200)

        self.load_file_explorer()

        self.root.bind('<s>', self.capture_image)

    def display_transmission(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(frame_pil)
        self.transmission_canvas.create_image(0, 0, anchor=tk.NW, image=frame_tk)
        self.transmission_canvas.image = frame_tk

    def display_captured_image(self, filepath):
        frame_pil = Image.open(filepath)
        frame_pil.thumbnail((960, 800))
        frame_tk = ImageTk.PhotoImage(frame_pil)
        self.captured_canvas.create_image(0, 0, anchor=tk.NW, image=frame_tk)
        self.captured_canvas.image = frame_tk

    def show_message(self, message, duration):
        self.message_label = ttk.Label(self.root, text=message, background="yellow")
        self.message_label.place(x=960, y=400, width=960, height=100)
        self.root.after(duration * 1000, self.message_label.destroy)

    def load_file_explorer(self):
        self.file_explorer_tree.delete(*self.file_explorer_tree.get_children())
        for folder in sorted(os.listdir(".")):
            if os.path.isdir(folder) and folder.startswith("session_"):
                session_node = self.file_explorer_tree.insert("", "end", text=folder, open=False)
                for file in sorted(os.listdir(folder)):
                    self.file_explorer_tree.insert(session_node, "end", text=file)
        trash_node = self.file_explorer_tree.insert("", "end", text="trash", open=False)
        for file in sorted(os.listdir(self.trash_folder)):
            self.file_explorer_tree.insert(trash_node, "end", text=file)

    def show_file_options(self, event):
        item_id = self.file_explorer_tree.identify_row(event.y)
        if not item_id:
            return
        item_text = self.file_explorer_tree.item(item_id, "text")
        item_path = os.path.join(self.file_explorer_tree.item(self.file_explorer_tree.parent(item_id), "text"), item_text)

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Abrir", command=lambda: self.open_file(item_path))
        if "trash" not in item_path:
            menu.add_command(label="Eliminar", command=lambda: self.move_to_trash(item_path))
        else:
            menu.add_command(label="Restaurar", command=lambda: self.restore_from_trash(item_text))
            menu.add_command(label="Eliminar permanentemente", command=lambda: self.delete_permanently(item_text))
        menu.post(event.x_root, event.y_root)

    def open_file(self, item_path):
        if item_path.endswith(".xlsx"):
            self.display_data(item_path)
        else:
            self.display_captured_image(item_path)

    def move_to_trash(self, item_path):
        if messagebox.askyesno("Confirmar eliminación", "¿Está seguro de que desea eliminar este archivo?"):
            shutil.move(item_path, self.trash_folder)
            self.load_file_explorer()

    def restore_from_trash(self, item_text):
        original_path = os.path.join(".", item_text.split("_", 1)[0], item_text)
        shutil.move(os.path.join(self.trash_folder, item_text), original_path)
        self.load_file_explorer()

    def delete_permanently(self, item_text):
        if messagebox.askyesno("Confirmar eliminación permanente", "¿Está seguro de que desea eliminar este archivo permanentemente?"):
            os.remove(os.path.join(self.trash_folder, item_text))
            self.load_file_explorer()

    def display_data(self, filepath):
        self.data_text.delete(1.0, tk.END)
        df = pd.read_excel(filepath)
        self.data_text.insert(tk.END, df.to_string(index=False))

if __name__ == "__main__":
    root = tk.Tk()
    live_feed = LiveFeed(root)
    live_feed.run()

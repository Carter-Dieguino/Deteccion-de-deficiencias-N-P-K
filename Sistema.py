##Programa que mide el área foliar en base a un área de referencia (i.e. 1 cm^32)
##Detecta tres tipos de deficiencias: nitrógeno, fósforo y hierro en función de los colores.

import cv2
import numpy as np
import pandas as pd
import datetime
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import serial
import time

# Configuración de la comunicación serie con Arduino
# arduino = serial.Serial('COM3', 9600)  # Asegúrate de cambiar 'COM3' al puerto correcto de tu Arduino
time.sleep(13)  # Espera para asegurarse de que la conexión esté establecida

# Define un diccionario con la información de las deficiencias
deficiency_info = {
    'Nitrógeno (N)': {
        'color_range': ([20, 143, 112], [23, 179, 137]),  # HSV range for yellow ([min], [max])
        'symptoms': 'Clorosis uniforme en las hojas más viejas, senescencia prematura, defoliación, reducción en el crecimiento',
        'treatment': 'Aplicación de fertilizantes ricos en nitrógeno'
    },
    'Fósforo (P)': {
        'color_range': ([153, 22, 115], [167, 134, 169]),  # HSV range for reddish-brown
        'symptoms': 'Manchas rojizas y marrones, retardo en el crecimiento en plantas jóvenes',
        'treatment': 'Uso de fertilizantes con alto contenido de fósforo'
    },
    'Hierro (Fe)': {
        'color_range': ([23, 37, 118], [32, 124, 162]),  # HSV range for light green to white
        'symptoms': 'Manchas de color verde claro a blanco en las hojas',
        'treatment': 'Aplicación de quelatos de hierro o fertilizantes foliares con hierro'
    }
}

class LiveFeed:
    def __init__(self, root, reference_area_cm2=1):
        self.cap = cv2.VideoCapture(3)
        self.reference_area_cm2 = reference_area_cm2
        self.reference_area_pixels = None
        self.image_counter = 1
        self.data = []
        self.create_new_session()
        self.create_gui(root)
        self.update_frame()

    def create_new_session(self):
        self.session_folder = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.trash_folder = os.path.join(self.session_folder, "trash")
        os.makedirs(self.session_folder, exist_ok=True)
        os.makedirs(self.trash_folder, exist_ok=True)
        self.excel_filename = os.path.join(self.session_folder, f"leaf_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        # Crear archivo Excel vacío
        pd.DataFrame(columns=['Filename', 'Reference Area (pixels)', 'Reference Area (cm^2)', 'Leaf Area (pixels)', 'Leaf Area (cm^2)', 'Deficiency', 'Symptoms', 'Treatment', 'Date', 'Time', 'Researcher']).to_excel(self.excel_filename, index=False)

    def process_frame(self, frame):
        frame_height, frame_width, _ = frame.shape
        reference_area = frame[frame_height-150:frame_height-50, 50:150]
        gray = cv2.cvtColor(reference_area, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        reference_detected = False
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(max_contour) > 100:
                cv2.drawContours(reference_area, [max_contour], -1, (0, 255, 255), 2)
                if self.reference_area_pixels is None:
                    self.reference_area_pixels = cv2.contourArea(max_contour)
                reference_detected = True

        cv2.rectangle(frame, (50, frame_height-150), (150, frame_height-50), (0, 0, 255), 2)
        reference_text = "Referencia detectada" if reference_detected else "Referencia NO detectada"
        cv2.putText(frame, reference_text, (50, frame_height-160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return frame, reference_detected

    def detect_leaf(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        edged = cv2.Canny(threshold, 50, 150)
        
        kernel = np.ones((5, 5), np.uint8)
        morphed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        leaf_detected = False
        if contours:
            max_contour = max(contours, key=cv2.contourArea)
            cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
            leaf_detected = True
        
        if leaf_detected:
            cv2.putText(frame, "Hoja detectada", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame, max_contour if leaf_detected else None

    def calculate_leaf_area(self, leaf_contour):
        if self.reference_area_pixels is None:
            return None
        
        leaf_area_pixels = cv2.contourArea(leaf_contour)
        leaf_area_cm2 = (leaf_area_pixels / self.reference_area_pixels) * self.reference_area_cm2
        return leaf_area_cm2, leaf_area_pixels

    def save_image_with_metadata(self, frame, leaf_area_cm2, leaf_area_pixels, deficiency, symptoms, treatment):
        timestamp = datetime.datetime.now()
        filename = f"hoja_{self.image_counter}_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.session_folder, filename)

        frame_height, frame_width, _ = frame.shape
        black_bar = np.zeros((200, frame_width, 3), dtype=np.uint8)
        cv2.putText(black_bar, f"Filename: {filename}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Reference Area: {self.reference_area_pixels:.2f} pixels, {self.reference_area_cm2} cm^2", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Leaf Area: {leaf_area_pixels:.2f} pixels, {leaf_area_cm2:.2f} cm^2", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Date: {timestamp.strftime('%Y-%m-%d')}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Time: {timestamp.strftime('%H:%M:%S')}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(black_bar, f"Researcher: Diego Ramos", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if deficiency:
            cv2.putText(black_bar, f"Deficiency: {deficiency}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(black_bar, f"Symptoms: {symptoms}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(black_bar, f"Treatment: {treatment}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(black_bar, f"Status: Hoja sana", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        frame_with_metadata = np.vstack((frame, black_bar))
        cv2.imwrite(filepath, frame_with_metadata)
        
        self.data.append([filename, self.reference_area_pixels, self.reference_area_cm2, leaf_area_pixels, leaf_area_cm2, deficiency if deficiency else '-', symptoms if symptoms else '-', treatment if treatment else '-', timestamp.strftime('%Y-%m-%d'), timestamp.strftime('%H:%M:%S'), 'Diego Ramos'])
        self.image_counter += 1
        self.save_data_to_excel()

        self.display_captured_image(filepath)
        self.display_image_metadata(filename)
        self.show_message("Imagen procesada correctamente", 3)

    def save_data_to_excel(self):
        df = pd.DataFrame(self.data, columns=['Filename', 'Reference Area (pixels)', 'Reference Area (cm^2)', 'Leaf Area (pixels)', 'Leaf Area (cm^2)', 'Deficiency', 'Symptoms', 'Treatment', 'Date', 'Time', 'Researcher'])
        if not os.path.exists(self.excel_filename):
            df.to_excel(self.excel_filename, index=False)
        else:
            existing_df = pd.read_excel(self.excel_filename)
            if existing_df.empty:
                df.to_excel(self.excel_filename, index=False)
            else:
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_excel(self.excel_filename, index=False)

    def run(self):
        self.root.mainloop()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame, reference_detected = self.process_frame(frame)
            frame, leaf_contour = self.detect_leaf(frame)
            self.display_transmission(frame)

            if self.capturing:
                if leaf_contour is not None and self.reference_area_pixels is not None:
                    leaf_area_cm2, leaf_area_pixels = self.calculate_leaf_area(leaf_contour)
                    deficiency, symptoms, treatment = detect_deficiency(frame)
                    self.save_image_with_metadata(frame, leaf_area_cm2, leaf_area_pixels, deficiency, symptoms, treatment)
                    if deficiency:
                        arduino.write(f"Deficiencia:\n{deficiency}".encode())
                    else:
                        arduino.write("Hoja sana\n".encode())
                    self.capturing = False
                else:
                    if not reference_detected:
                        arduino.write("No se detecto el\narea de referenc".encode())
                    elif leaf_contour is None:
                        arduino.write("No se detecto la\nhoja".encode())
                    self.show_message("No se detectó la\nhoja o referenci", 5)
                    self.capturing = False

        self.root.after(10, self.update_frame)

    def capture_image(self, event=None):
        self.capturing = True

    def create_gui(self, root):
        self.root = root
        self.root.geometry("1500x750")
        self.capturing = False

        ## Transmisión
        self.transmission_label = ttk.Label(self.root, text="Live Feed")
        self.transmission_label.place(x=0, y=0, width=750, height=550)
        self.transmission_canvas = tk.Canvas(self.root, bg="black")
        self.transmission_canvas.place(x=0, y=0, width=750, height=550)
        ## Imagen
        self.captured_label = ttk.Label(self.root, text="Captured Image")
        self.captured_label.place(x=750, y=0, width=750, height=550)
        self.captured_canvas = tk.Canvas(self.root, bg="black")
        self.captured_canvas.place(x=750, y=0, width=750, height=550)

        # Variables for zoom and pan
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.captured_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.captured_canvas.bind("<B1-Motion>", self.do_pan)
        self.captured_canvas.bind("<MouseWheel>", self.do_zoom)

        ## Explorador
        self.file_explorer_label = ttk.Label(self.root, text="File Explorer")
        self.file_explorer_label.place(x=0, y=550, width=350, height=200)
        self.file_explorer_tree = ttk.Treeview(self.root)
        self.file_explorer_tree.place(x=0, y=550, width=350, height=200)
        self.file_explorer_tree.bind('<Button-3>', self.show_file_options)
        self.file_explorer_tree.bind('<Double-1>', self.open_file)
        
        ## Datos
        self.data_label = ttk.Label(self.root, text="Data")
        self.data_label.place(x=350, y=550, width=1150, height=200)
        self.data_text = tk.Text(self.root, wrap=tk.WORD)
        self.data_text.place(x=350, y=550, width=1150, height=200)

        self.new_session_button = ttk.Button(self.root, text="New Session", command=self.create_new_session_gui)
        self.new_session_button.place(x=1150, y=500, width=100, height=35)

        self.rename_session_button = ttk.Button(self.root, text="Rename Session", command=self.rename_session)
        self.rename_session_button.place(x=1250, y=500, width=100, height=35)

        self.center_image_button = ttk.Button(self.root, text="Center Image", command=self.center_image)
        self.center_image_button.place(x=1350, y=500, width=100, height=35)

        self.load_file_explorer()

        self.root.bind('<s>', self.capture_image)

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_pan(self, event):
        self.pan_x += event.x - self.pan_start_x
        self.pan_y += event.y - self.pan_start_y
        self.display_captured_image(self.current_image_path)
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def do_zoom(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        elif event.delta < 0:
            self.zoom_level /= 1.1
        self.zoom_level = min(max(self.zoom_level, 0.1), 3.0)
        self.display_captured_image(self.current_image_path)
        self.show_message(f"Zoom: {self.zoom_level:.1f}x", 2)

    def center_image(self):
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_captured_image(self.current_image_path)

    def display_transmission(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_tk = ImageTk.PhotoImage(frame_pil)
        self.transmission_canvas.create_image(0, 0, anchor=tk.NW, image=frame_tk)
        self.transmission_canvas.image = frame_tk

    def display_captured_image(self, filepath):
        self.current_image_path = filepath
        frame_pil = Image.open(filepath)
        width, height = frame_pil.size
        frame_pil = frame_pil.resize((int(width * self.zoom_level), int(height * self.zoom_level)), Image.LANCZOS)
        frame_tk = ImageTk.PhotoImage(frame_pil)
        self.captured_canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=frame_tk)
        self.captured_canvas.image = frame_tk

    def show_message(self, message, duration):
        self.message_label = ttk.Label(self.root, text=message, background="yellow")
        self.message_label.place(x=1160, y=450, width=200, height=20)
        self.root.after(duration * 1000, self.message_label.destroy)

    def load_file_explorer(self):
        self.file_explorer_tree.delete(*self.file_explorer_tree.get_children())
        for folder in sorted(os.listdir(".")):
            if os.path.isdir(folder) and folder.startswith("session_"):
                session_node = self.file_explorer_tree.insert("", "end", text=folder, open=False)
                for file in sorted(os.listdir(folder)):
                    self.file_explorer_tree.insert(session_node, "end", text=file)
            if folder == "trash":
                trash_node = self.file_explorer_tree.insert("", "end", text="trash", open=False)
                for file in sorted(os.listdir(os.path.join(folder))):
                    self.file_explorer_tree.insert(trash_node, "end", text=file)

    def show_file_options(self, event):
        item_id = self.file_explorer_tree.identify_row(event.y)
        if not item_id:
            return
        item_text = self.file_explorer_tree.item(item_id, "text")
        parent_text = self.file_explorer_tree.item(self.file_explorer_tree.parent(item_id), "text")
        item_path = os.path.join(parent_text, item_text)

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open", command=lambda: self.open_file(None, item_path))
        if "trash" not in item_path:
            menu.add_command(label="Delete", command=lambda: self.move_to_trash(item_path))
        else:
            menu.add_command(label="Restore", command=lambda: self.restore_from_trash(item_path))
            menu.add_command(label="Delete Permanently", command=lambda: self.delete_permanently(item_path))
        menu.post(event.x_root, event.y_root)

    def open_file(self, event, item_path=None):
        if not item_path:
            item_id = self.file_explorer_tree.selection()
            if not item_id:
                return
            item_id = item_id[0]
            item_text = self.file_explorer_tree.item(item_id, "text")
            parent_text = self.file_explorer_tree.item(self.file_explorer_tree.parent(item_id), "text")
            item_path = os.path.join(parent_text, item_text)

        if not os.path.isfile(item_path):
            messagebox.showwarning("Open File", "Cannot open directory.")
            return

        if item_path.endswith(".xlsx"):
            self.display_data(item_path)
        else:
            self.display_captured_image(item_path)
            self.display_image_metadata(os.path.basename(item_path))

    def display_image_metadata(self, image_name):
        if not os.path.exists(self.excel_filename):
            return
        
        df = pd.read_excel(self.excel_filename)
        metadata = df[df['Filename'] == image_name]
        if not metadata.empty:
            self.data_text.insert(tk.END, metadata.to_string(index=False))
            self.data_text.insert(tk.END, '\n\n')
            self.data_text.see(tk.END)  # Scroll to the end

    def move_to_trash(self, item_path):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this file?"):
            shutil.move(item_path, self.trash_folder)
            self.load_file_explorer()
            self.show_message("Archivo movido a la papelera", 3)

    def restore_from_trash(self, item_path):
        original_path = os.path.join(self.session_folder, os.path.basename(item_path))
        shutil.move(item_path, original_path)
        self.load_file_explorer()
        self.show_message("Archivo restaurado", 3)

    def delete_permanently(self, item_path):
        if messagebox.askyesno("Confirm Permanent Delete", "Are you sure you want to permanently delete this file?"):
            os.remove(item_path)
            self.load_file_explorer()
            self.show_message("Archivo eliminado permanentemente", 3)

    def display_data(self, filepath):
        self.data_text.delete(1.0, tk.END)
        df = pd.read_excel(filepath)
        self.data_text.insert(tk.END, df.to_string(index=False))
        self.data_text.see(tk.END)  # Scroll to the end

    def create_new_session_gui(self):
        if self.image_counter == 1:
            shutil.rmtree(self.session_folder)
        self.create_new_session()
        self.load_file_explorer()
        self.show_message("New session created", 3)

    def rename_session(self):
        new_name = filedialog.asksaveasfilename(initialdir=".", initialfile=self.session_folder, title="Rename Session", filetypes=[("All Files", "*.*")])
        if new_name:
            new_name = new_name.split("/")[-1]
            new_path = os.path.join(".", new_name)
            os.rename(self.session_folder, new_path)
            self.session_folder = new_path
            self.trash_folder = os.path.join(self.session_folder, "trash")
            self.excel_filename = os.path.join(self.session_folder, os.path.basename(self.excel_filename))
            self.load_file_explorer()
            self.show_message("Session renamed", 3)

def detect_deficiency(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    for deficiency, info in deficiency_info.items():
        lower, upper = info['color_range']
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower, upper)
        if cv2.countNonZero(mask) > 0:
            return deficiency, info['symptoms'], info['treatment']
    
    return None, None, None

if __name__ == "__main__":
    root = tk.Tk()
    live_feed = LiveFeed(root)
    
    def arduino_listener():
        while True:
            if arduino.in_waiting > 0:
                incoming_data = arduino.readline().decode().strip()
                if incoming_data == 'P':
                    time.sleep(2)
                    live_feed.capture_image()
    
    import threading
    arduino_thread = threading.Thread(target=arduino_listener)
    arduino_thread.daemon = True
    arduino_thread.start()
    
    live_feed.run()

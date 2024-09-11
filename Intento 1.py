from tkinter import Tk, Button, Canvas
import cv2
from PIL import Image, ImageTk

def start_webcam():
    global cap, streaming
    if not streaming:
        cap = cv2.VideoCapture(1)  # Usar el índice de cámara 1
        if not cap.isOpened():
            raise Exception("No se pudo abrir la cámara. Verifique que esté conectada y funcional.")
        # Obtener un frame para ajustar el tamaño del canvas
        ret, frame = cap.read()
        if ret:
            canvas.config(width=frame.shape[1], height=frame.shape[0])  # Ajustar el tamaño del canvas
        streaming = True
        show_frame()

def show_frame():
    if streaming:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo capturar un frame de la cámara. Reintentando...")
            root.after(10, show_frame)
            return
        
        img = Image.fromarray(frame)
        tk_image = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor='nw', image=tk_image)
        canvas.image = tk_image
        root.after(10, show_frame)  # Continuar mostrando frames

def capture_image():
    global streaming
    if streaming:
        streaming = False
        cap.release()

root = Tk()
root.title("Webcam Viewer")

button_start = Button(root, text="Iniciar Webcam", command=start_webcam)
button_start.pack(pady=5)

button_capture = Button(root, text="Capturar Imagen", command=capture_image)
button_capture.pack(pady=5)

canvas = Canvas(root, width=640, height=480)  # Dimensiones iniciales
canvas.pack()

cap = None
streaming = False

root.mainloop()

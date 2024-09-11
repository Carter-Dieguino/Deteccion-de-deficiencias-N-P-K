import cv2
import numpy as np
import easygui

# Variables globales para almacenar los puntos seleccionados
points = []
hsv_values = []

# Función de callback para manejar clics del mouse
def select_points(event, x, y, flags, param):
    global points, frame
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f'Punto añadido: ({x}, {y})')

# Función para calcular los rangos HSV
def calculate_hsv_range(frame):
    global points
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [np.array(points)], 255)
    
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    selected_area = cv2.bitwise_and(hsv_frame, hsv_frame, mask=mask)
    
    h_vals = selected_area[:, :, 0][mask == 255]
    s_vals = selected_area[:, :, 1][mask == 255]
    v_vals = selected_area[:, :, 2][mask == 255]
    
    lower_hue = np.min(h_vals)
    lower_saturation = np.min(s_vals)
    lower_value = np.min(v_vals)
    upper_hue = np.max(h_vals)
    upper_saturation = np.max(s_vals)
    upper_value = np.max(v_vals)

    lower_bound = np.array([lower_hue, lower_saturation, lower_value])
    upper_bound = np.array([upper_hue, upper_saturation, upper_value])

    hsv_values.append((np.mean(h_vals), np.mean(s_vals), np.mean(v_vals)))  # Almacenar los valores promedio de HSV

    return lower_bound, upper_bound

# Función para seleccionar la fuente de entrada
def select_input_source():
    choices = ["Capturar desde cámara", "Cargar imagen", "Cargar video", "Pegar imagen del portapapeles"]
    choice = easygui.buttonbox("Selecciona la fuente de entrada", choices=choices)
    return choice

# Función principal para manejar la estimación de HSV
def estimate_hsv():
    global points, frame, hsv_values
    hsv_estimates = []
    
    while True:
        points = []
        input_source = select_input_source()
        
        if input_source == "Capturar desde cámara":
            cap = cv2.VideoCapture(3)
            if not cap.isOpened():
                print("Error al abrir la cámara")
                return

            ret, frame = cap.read()
            if not ret:
                print("Error al capturar el frame")
                return
            cap.release()
        
        elif input_source == "Cargar imagen":
            image_path = easygui.fileopenbox(title="Selecciona una imagen", filetypes=[["*.jpg", "*.png", "*.jpeg", "Imágenes"]])
            if image_path is None:
                continue
            frame = cv2.imread(image_path)
        
        elif input_source == "Cargar video":
            video_path = easygui.fileopenbox(title="Selecciona un video", filetypes=[["*.mp4", "*.avi", "Videos"]])
            if video_path is None:
                continue
            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            if not ret:
                print("Error al leer el video")
                return
            cap.release()
        
        elif input_source == "Pegar imagen del portapapeles":
            try:
                from PIL import ImageGrab
                frame = np.array(ImageGrab.grabclipboard())
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print("Error al pegar la imagen del portapapeles:", e)
                continue
        
        # Mostrar la imagen y permitir la selección de área
        cv2.namedWindow('Original')
        cv2.setMouseCallback('Original', select_points)

        while True:
            frame_copy = frame.copy()
            for point in points:
                cv2.circle(frame_copy, point, 5, (0, 255, 0), -1)
            
            if len(points) > 1:
                cv2.polylines(frame_copy, [np.array(points)], isClosed=True, color=(0, 255, 0), thickness=2)
            
            cv2.imshow('Original', frame_copy)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s') and len(points) > 2:
                break

        cv2.destroyWindow('Original')

        if len(points) > 2:
            lower_bound, upper_bound = calculate_hsv_range(frame)
            hsv_estimates.append((lower_bound, upper_bound))
            print(f'Rango HSV inferior: {lower_bound}')
            print(f'Rango HSV superior: {upper_bound}')
            
            # Permitir ver la transmisión completa con la máscara aplicada
            while True:
                if input_source == "Capturar desde cámara":
                    cap = cv2.VideoCapture(3)
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
                        result = cv2.bitwise_and(frame, frame, mask=mask)
                        
                        cv2.imshow('Original', frame)
                        cv2.imshow('Mask', mask)
                        cv2.imshow('Result', result)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            cap.release()
                            cv2.destroyAllWindows()
                            break
                elif input_source == "Cargar video":
                    cap = cv2.VideoCapture(video_path)
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
                        result = cv2.bitwise_and(frame, frame, mask=mask)
                        
                        cv2.imshow('Original', frame)
                        cv2.imshow('Mask', mask)
                        cv2.imshow('Result', result)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            cap.release()
                            cv2.destroyAllWindows()
                            break
                else:
                    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
                    result = cv2.bitwise_and(frame, frame, mask=mask)
                    
                    while True:
                        cv2.imshow('Original', frame)
                        cv2.imshow('Mask', mask)
                        cv2.imshow('Result', result)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            cv2.destroyAllWindows()
                            break
        else:
            print("No se seleccionó un área suficiente para calcular los rangos HSV.")
        
        if easygui.ynbox("¿Quieres realizar otra estimación?", choices=["Sí", "No"]) == False:
            break

    # Mostrar todos los valores estimados de HSV
    print("Valores estimados de HSV:")
    for i, (lower, upper) in enumerate(hsv_estimates, start=1):
        print(f'Estimación {i}:')
        print(f'  Rango HSV inferior: {lower}')
        print(f'  Rango HSV superior: {upper}')

    # Calcular y mostrar el promedio de todas las mediciones de HSV
    if hsv_values:
        avg_h = np.mean([val[0] for val in hsv_values])
        avg_s = np.mean([val[1] for val in hsv_values])
        avg_v = np.mean([val[2] for val in hsv_values])
        print(f'Promedio de Hue: {avg_h}')
        print(f'Promedio de Saturación: {avg_s}')
        print(f'Promedio de Valor: {avg_v}')
    else:
        print("No se realizaron suficientes estimaciones para calcular el promedio.")

if __name__ == "__main__":
    estimate_hsv()

import cv2
import numpy as np
import serial
import time

# Configuración de la comunicación serie con Arduino
arduino = serial.Serial('COM4', 9600)  # Asegúrate de cambiar 'COM4' al puerto correcto de tu Arduino
time.sleep(2)  # Espera para asegurarse de que la conexión esté establecida

# Define un diccionario con la información de las deficiencias
deficiency_info = {
    'Nitrógeno (N)': {
        'color_range': ([16, 122, 133], [21, 160, 174]),  # HSV range for yellow ([min], [max])
        'síntomas': 'Clorosis uniforme en las hojas más viejas, senescencia prematura, defoliación, reducción en el crecimiento',
        'tratamiento': 'Aplicación de fertilizantes ricos en nitrógeno'
    },
    'Fósforo (P)': {
        'color_range': ([141, 38, 102], [175, 101, 255]),  # HSV range for reddish-brown
        'síntomas': 'Manchas rojizas y marrones, retardo en el crecimiento en plantas jóvenes',
        'tratamiento': 'Uso de fertilizantes con alto contenido de fósforo'
    },
    'Hierro (Fe)': {
        'color_range': ([15, 38, 162], [24, 76, 194]),  # HSV range for light green to white
        'síntomas': 'Manchas de color verde claro a blanco en las hojas',
        'tratamiento': 'Aplicación de quelatos de hierro o fertilizantes foliares con hierro'
    }
}

# Función para detectar deficiencia
def detect_deficiency(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    for deficiency, info in deficiency_info.items():
        lower, upper = info['color_range']
        lower = np.array(lower, dtype=np.uint8)
        upper = np.array(upper, dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower, upper)
        if cv2.countNonZero(mask) > 0:
            return deficiency, info['síntomas'], info['tratamiento']
    
    return None, None, None

# Función para capturar una imagen con la cámara
def capture_image():
    cap = cv2.VideoCapture(3)  # Asegúrate de tener una cámara conectada
    ret, frame = cap.read()
    if ret:
        return frame
    else:
        return None

# Inicializa la captura de video
cap = cv2.VideoCapture(0)

# Bucle principal
while True:
    if arduino.in_waiting > 0:
        incoming_data = arduino.readline().decode().strip()
        if incoming_data == 'e':
            time.sleep(1)  # Espera 1 segundo
            ret, frame = cap.read()  # Lee el fotograma actual de la cámara
            if ret:
                deficiency, síntomas, tratamiento = detect_deficiency(frame)
                if deficiency:
                    result_text = f"{deficiency}\nSíntomas: {síntomas}\nTratamiento: {tratamiento}"
                else:
                    result_text = "No se detectó ninguna deficiencia nutricional."
                
                # Envía la información al Arduino
                arduino.write(result_text.encode())
                print(result_text)
            else:
                print("Error al capturar la imagen.")

# Libera la captura de video cuando el bucle se cierra
cap.release()
cv2.destroyAllWindows()

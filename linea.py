import cv2

# Carga la imagen
imagen = cv2.imread('IMG.png')

# Convierte la imagen a escala de grises
gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

# Aplica un umbral para obtener una imagen binaria
_, umbral = cv2.threshold(gris, 50, 255, cv2.THRESH_BINARY)

# Encuentra los contornos en la imagen binaria
contornos, _ = cv2.findContours(umbral, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Encuentra el contorno más largo (que se supone que es la línea negra)
contorno_largo = max(contornos, key=cv2.contourArea)

# Calcula la longitud del contorno
longitud_pixeles = cv2.arcLength(contorno_largo, True)

# Muestra la longitud en píxeles
print("Longitud de la línea en píxeles:", longitud_pixeles)

# Dibuja el contorno sobre la imagen original (solo para visualización)
cv2.drawContours(imagen, [contorno_largo], -1, (0, 255, 0), 2)

# Muestra la imagen con el contorno dibujado
cv2.imshow('Imagen con contorno', imagen)
cv2.waitKey(0)
cv2.destroyAllWindows()

import numpy as np
import cv2
import os

chunk_size = 50
w, h = 640, 480  # tamaño de la imagen original

# Matriz vacía donde irán los datos reconstruidos
reconstructed = np.zeros((h, w, 3), dtype=np.uint8)

# Ejemplo de función para procesar un chunk recibido
def procesar_chunk(data_bytes, x, y):
    """Coloca el chunk en la posición correspondiente"""
    # Decodificar bytes a imagen (si se transmitió comprimido como PNG/JPEG)
    chunk = cv2.imdecode(np.frombuffer(data_bytes, np.uint8), cv2.IMREAD_COLOR)
    reconstructed[y:y+chunk.shape[0], x:x+chunk.shape[1]] = chunk

# Simulación: reconstrucción a partir de archivos desordenados
for file in os.listdir("chunks_left"):
    # Ejemplo: nombre = chunk_0012_150_200.png
    parts = file.split("_")
    x = int(parts[2])
    y = int(parts[3].split(".")[0])
    path = os.path.join("chunks_left", file)
    data = open(path, "rb").read()
    procesar_chunk(data, x, y)
    

cv2.imshow("Reconstruida", reconstructed)
cv2.waitKey(0)
cv2.destroyAllWindows()

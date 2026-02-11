import cv2
import numpy as np
import os

# Parámetros
chunk_size = 50
output_dir_left = "chunks_left"
output_dir_right = "chunks_right"

# Crear carpetas de salida si no existen
os.makedirs(output_dir_left, exist_ok=True)
os.makedirs(output_dir_right, exist_ok=True)

# --- 1. Capturar imágenes estéreo ---
cap_left = cv2.VideoCapture(2)   # Cámara izquierda
cap_right = cv2.VideoCapture(4)  # Cámara derecha

cap_left.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap_left.set(cv2.CAP_PROP_FPS, 30)

cap_right.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap_right.set(cv2.CAP_PROP_FPS, 30)

retL, left_img = cap_left.read()
retR, right_img = cap_right.read()

cap_left.release()
cap_right.release()

# Asegurar que tengan el mismo tamaño
h, w = left_img.shape[:2]
right_img = cv2.resize(right_img, (w, h))

print(f"Imágenes capturadas: tamaño {w}x{h}")

# --- 2. Función para dividir en chunks ---
def dividir_en_chunks(img, chunk_size):
    h, w = img.shape[:2]
    chunks = []
    for y in range(0, h, chunk_size):
        for x in range(0, w, chunk_size):
            chunk = img[y:y+chunk_size, x:x+chunk_size]
            chunks.append((x, y, chunk))
    return chunks

chunks_left = dividir_en_chunks(left_img, chunk_size)
chunks_right = dividir_en_chunks(right_img, chunk_size)

# --- 3. Guardar chunks ---
for i, (x, y, chunk) in enumerate(chunks_left):
    cv2.imwrite(f"{output_dir_left}/chunk_{i:04d}_{x}_{y}.png", chunk)
for i, (x, y, chunk) in enumerate(chunks_right):
    cv2.imwrite(f"{output_dir_right}/chunk_{i:04d}_{x}_{y}.png", chunk)

print(f"✅ Se guardaron {len(chunks_left)} chunks por cámara.")

# --- 4. Función para reconstruir desde chunks ---
def reconstruir_desde_chunks(chunks, img_shape, chunk_size):
    h, w = img_shape[:2]
    img_reconstruida = np.zeros(img_shape, dtype=chunks[0][2].dtype)
    for (x, y, chunk) in chunks:
        img_reconstruida[y:y+chunk.shape[0], x:x+chunk.shape[1]] = chunk
    return img_reconstruida

recon_left = reconstruir_desde_chunks(chunks_left, left_img.shape, chunk_size)
recon_right = reconstruir_desde_chunks(chunks_right, right_img.shape, chunk_size)

# --- 5. Visualización ---
cv2.imshow("Left - Reconstructed", recon_left)
cv2.imshow("Right - Reconstructed", recon_right)

print("Mostrando imágenes reconstruidas. Presiona una tecla para salir.")
cv2.waitKey(0)
cv2.destroyAllWindows()

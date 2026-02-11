import cv2
import numpy as np
import time

# --- Configuración de cámaras ---
capL = cv2.VideoCapture(2)
capR = cv2.VideoCapture(4)

frame_width = 320
frame_height = 240
fps = 30

for cam in (capL, capR):
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cam.set(cv2.CAP_PROP_FPS, fps)
    cam.set(cv2.CAP_PROP_BUFFERSIZE,1)

# --- StereoBM: más rápido que SGBM ---
num_disp = 16 * 4  # rango de disparidad
block_size = 15     # tamaño del bloque de correlación

stereo = cv2.StereoBM_create(numDisparities=num_disp, blockSize=block_size)

# --- Parámetros físicos (estimativos) ---
focal_length_px = 800  # focal en píxeles (ajustar)
baseline_m = 0.06      # distancia entre cámaras (6 cm)

print("Vision estereoscópica optimizada (presiona 'q' para salir)")

while True:
    start_time = time.time()

    retL, frameL = capL.read()
    retR, frameR = capR.read()
    if not (retL and retR):
        print("No se pudo capturar de ambas cámaras.")
        break

    # --- Convertir a escala de grises ---
    grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

    # --- Calcular disparidad ---
    disparity = stereo.compute(grayL, grayR)

    # --- Normalizar disparidad rápidamente ---
    disp_vis = cv2.convertScaleAbs(disparity, alpha=255/num_disp)

    # --- Estimar profundidad simple ---
    disparity_float = disparity.astype(np.float32)
    disparity_float[disparity_float <= 0.0] = 0.1  # evitar división por cero
    depth = (focal_length_px * baseline_m) / disparity_float

    # --- Mapear profundidad a color (azul=lejos, rojo=cerca) ---
    depth_vis = np.clip(depth, 0, 2.0)
    depth_vis = (depth_vis / 2.0 * 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(255 - depth_vis, cv2.COLORMAP_JET)

    # --- Mostrar ---
    cv2.imshow("Izquierda", frameL)
    cv2.imshow("Profundidad", depth_color)

    # --- Calcular FPS real ---
    elapsed = time.time() - start_time
    fps_now = 1.0 / elapsed if elapsed > 0 else 0
    print(f"\rFPS: {fps_now:.1f}", end="")

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

capL.release()
capR.release()
cv2.destroyAllWindows()

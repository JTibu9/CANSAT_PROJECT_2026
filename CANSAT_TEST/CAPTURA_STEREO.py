import cv2
import numpy as np

# --- 1. Captura de las dos cámaras ---
capL = cv2.VideoCapture(2)
capR = cv2.VideoCapture(4)
capL.set(cv2.CAP_PROP_BUFFERSIZE, 1)
capR.set(cv2.CAP_PROP_BUFFERSIZE, 1)
capL.set(cv2.CAP_PROP_FPS, 30)
capR.set(cv2.CAP_PROP_FPS, 30)

retL, imgL = capL.read()
retR, imgR = capR.read()

capL.release()
capR.release()

if not (retL and retR):
    raise RuntimeError("No se pudieron capturar las imágenes")

# Asegurar mismo tamaño
h, w = imgL.shape[:2]
imgR = cv2.resize(imgR, (w, h))

# --- 2. (Opcional) Rectificación si ya calibraste las cámaras ---
# Si tienes los mapas de rectificación (map1x, map1y, etc.) puedes aplicarlos aquí.
# imgL = cv2.remap(imgL, map1x, map1y, cv2.INTER_LINEAR)
# imgR = cv2.remap(imgR, map2x, map2y, cv2.INTER_LINEAR)

# --- 3. Fusión básica por blending ---
# Definir la zona de solapamiento (en píxeles)
zona_inicio = int(w * 0.4)
zona_fin = int(w * 0.6)

# Partes izquierda y derecha
left_part = imgL[:, :zona_inicio]
right_part = imgR[:, zona_fin:]
zona_left = imgL[:, zona_inicio:zona_fin]
zona_right = imgR[:, zona_inicio:zona_fin]

# Fusión en zona común
zona_fusion = cv2.addWeighted(zona_left, 0.5, zona_right, 0.5, 0)

# Unir todo
fusionada = np.hstack([left_part, zona_fusion, right_part])

# --- 4. Visualizar ---
cv2.imshow("Fusion Estereo", fusionada)
cv2.waitKey(0)
cv2.destroyAllWindows()

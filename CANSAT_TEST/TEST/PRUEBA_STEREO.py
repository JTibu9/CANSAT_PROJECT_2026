import cv2
import numpy as np

# --- Inicializar las cámaras ---
# Asegúrate de que los índices 0 y 1 correspondan a tus cámaras izquierda y derecha.
cap_left = cv2.VideoCapture(2)
cap_right = cv2.VideoCapture(4)

# Configurar tamaño de imagen (opcional, pero recomendable)
frame_width = 640
frame_height = 480
cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)

#--Configuracion del buffer y fps---
cap_left.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap_right.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap_left.set(cv2.CAP_PROP_FPS, 30)
cap_right.set(cv2.CAP_PROP_FPS, 30)

# --- Crear objeto estéreo (SGBM) ---
min_disp = 0
num_disp = 16*6 # Debe ser múltiplo de 16
block_size = 5

stereo = cv2.StereoSGBM_create(
    minDisparity=min_disp,
    numDisparities=num_disp,
    blockSize=block_size,
    P1=8 * 3 * block_size ** 2,
    P2=32 * 3 * block_size ** 2,
    disp12MaxDiff=0.5,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32
)


while True:
    retL, frameL = cap_left.read()
    retR, frameR = cap_right.read()

    if not (retL and retR):
        print("No se pudieron capturar frames de ambas cámaras")
        break

    # Convertir a escala de grises
    grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

    # --- Calcular disparidad ---
    disparity = stereo.compute(grayL, grayR)

    # Normalizar para visualizar mejor
    disp_vis = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX)
    disp_vis = np.uint8(disp_vis)
    disp_vis = cv2.medianBlur(disp_vis, 5)

    # --- Mostrar resultados ---
    cv2.imshow("Camara Izquierda", frameL)
    cv2.imshow("Camara Derecha", frameR)
    cv2.imshow("Mapa de Disparidad", disp_vis)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Liberar recursos ---
cap_left.release()
cap_right.release()
cv2.destroyAllWindows()

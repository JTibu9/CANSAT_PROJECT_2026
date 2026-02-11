import cv2 as cv
import numpy as np

# Configurar cámaras
source = cv.VideoCapture(4)
source.set(cv.CAP_PROP_BUFFERSIZE, 1)
source.set(cv.CAP_PROP_FPS, 30)

source2 = cv.VideoCapture(2)
source2.set(cv.CAP_PROP_BUFFERSIZE, 1)
source2.set(cv.CAP_PROP_FPS, 30)

frame_count= int(source.get(cv.CAP_PROP_FRAME_COUNT))
fps= int(source.get(cv.CAP_PROP_FPS))



# Parámetros del stereo matcher
stereo = cv.StereoBM_create(numDisparities=16*5, blockSize=15)

nombre_ventana = "Camara Izquierda"
nombre_ventana2 = "Camara Derecha"
nombre_disparity = "Mapa de Disparidad"

while cv.waitKey(1) != 27:
    has_frame, frame_left = source.read()
    has_frame2, frame_right = source2.read()

    
    if not has_frame or not has_frame2:
        break
    
    # Convertir a escala de grises
    gray_left = cv.cvtColor(frame_left, cv.COLOR_BGR2GRAY)
    gray_right = cv.cvtColor(frame_right, cv.COLOR_BGR2GRAY)
    
    # Calcular mapa de disparidad
    disparity = stereo.compute(gray_left, gray_right)
    
    # Normalizar para visualización
    disparity_visual = cv.normalize(disparity, None, 0, 255, cv.NORM_MINMAX, cv.CV_8U)
    disparity_color = cv.applyColorMap(disparity_visual, cv.COLORMAP_JET)
    
    # Mostrar ventanas
    cv.imshow(nombre_ventana, frame_left)
    cv.imshow(nombre_ventana2, frame_right)
    cv.imshow(nombre_disparity, disparity_color)
    
    print(f"Numero de frames: {frame_count},FPS: {fps}")

source.release()
source2.release()
cv.destroyAllWindows()
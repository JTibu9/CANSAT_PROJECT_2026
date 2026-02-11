import cv2 as cv
import numpy as np

#CAM CONFIG
source = cv.VideoCapture(4)
source.set(cv.CAP_PROP_BUFFERSIZE, 1)
source.set(cv.CAP_PROP_FPS, 30)

source2 = cv.VideoCapture(2)
source2.set(cv.CAP_PROP_BUFFERSIZE, 1)
source2.set(cv.CAP_PROP_FPS, 30)

#STEREO MATCHER, PARAMETERS : MAXIMUN DISPARITY RANGE TO SEARCH BETWEEN 2 IMAGES, BLOCK SIZE TO MATCH
stereo = cv.StereoBM_create(numDisparities=16*5, blockSize=15)

# CHUNK PARAMETERS
chunk_height = 100 #filas
chunk_width = 100 #columnas

while cv.waitKey(1) != 27:
    has_frame, frame_left = source.read()
    has_frame2, frame_right = source2.read()

    if not has_frame or not has_frame2:
        break

    gray_left = cv.cvtColor(frame_left, cv.COLOR_BGR2GRAY)
    gray_right = cv.cvtColor(frame_right, cv.COLOR_BGR2GRAY)
    
    height, width = gray_left.shape
    disparity_full = np.zeros((height, width), dtype=np.float32)

    for y in range(0, height, chunk_height):
        for x in range(0, width, chunk_width):
            # Límites del chunk
            y_end = min(y + chunk_height, height)
            x_end = min(x + chunk_width, width)
            
            # Extraer chunk
            chunk_left = gray_left[y:y_end, x:x_end]
            chunk_right = gray_right[y:y_end, x:x_end]
            
            # Procesar chunk
            chunk_disparity = stereo.compute(chunk_left, chunk_right)
            
            # Guardar resultado
            disparity_full[y:y_end, x:x_end] = chunk_disparity

    disparity_visual = cv.normalize(disparity_full, None, 0, 255, cv.NORM_MINMAX, cv.CV_8U)
    disparity_color = cv.applyColorMap(disparity_visual, cv.COLORMAP_JET)

    cv.imshow("Camara Izquierda", frame_left)
    cv.imshow("Camara Derecha", frame_right)
    cv.imshow("Mapa de Disparidad", disparity_color)

cv.imshow("Mapa de Disparidad", chunk_disparity)
source.realease()
source2.release()
cv.destroyAllWindows()

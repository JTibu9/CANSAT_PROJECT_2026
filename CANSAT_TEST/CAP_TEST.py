import cv2 as cv
import numpy as np

source = cv.VideoCapture(0)
#source_2= cv.VideoCapture(2)

#source_2.set(cv.CAP_PROP_BUFFERSIZE,1)
#source_2.set(cv.CAP_PROP_FPS, 30)

source.set(cv.CAP_PROP_BUFFERSIZE, 1)
source.set(cv.CAP_PROP_FPS, 30)

scale_down = 0.4

while cv.waitKey(1) != 27:
    has_frame, frame = source.read()
    #has_frame_2, frame_2 = source_2.read()
    if not has_frame:
        break
    frame = cv.resize(frame, None, fx=scale_down, fy=scale_down, interpolation=cv.INTER_LINEAR)
    #frame_2 = cv.resize(frame_2, None, fx=scale_down, fy=scale_down, interpolation=cv.INTER_LINEAR)

    #cv.imshow ("Camara 2", frame_2)
    cv.imshow("Camara 1", frame)

source.release()
#source_2.release()
cv.destroyAllWindows()
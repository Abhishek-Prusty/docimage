import argparse
import json
import os
import pickle as pkl 
import cv2
import numpy as np
import colorsys

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--page", required=True,
                help="Path to the image")

args = vars(ap.parse_args())
imgs=args["page"]
img=cv2.imread(imgs,0)
img2=cv2.imread(imgs,0)


with open('segments.pkl','rb') as f:
    segments=pkl.load(f)

print(len(segments))
'''
cv2.imshow('image', template)
cv2.waitKey(0)
cv2.destroyAllWindows()
'''
no_segs=len(segments)
cols=list()
for i in range(no_segs):
    rgb = colorsys.hsv_to_rgb(i / 300., 1.0, 1.0)
    cols.append([round(255*x) for x in rgb])

count=0
for segment in segments:
    img=cv2.imread(imgs,0)
    template=img[segment[1]:segment[3],segment[0]:segment[2]]
    cv2.imshow("tmp",template)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(img,template,cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    loc = np.where( res >= threshold) 
    for pt in zip(*loc[::-1]):
        colo=(cols[count][0],cols[count][1],cols[count][2])
        cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2)
        #cv2.rectangle(img2, pt, (pt[0] + w, pt[1] + h), (0,255,0), 2)

    cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("output", (int(img.shape[1]/2), int(img.shape[0]/2 )))
    cv2.imshow("output",img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    count=count+1
    print(count)

cv2.namedWindow("output", cv2.WINDOW_NORMAL)
cv2.resizeWindow("output", (int(img.shape[1]), int(img.shape[0])))
cv2.imshow("output",img2)
cv2.waitKey(0)
cv2.destroyAllWindows()

    




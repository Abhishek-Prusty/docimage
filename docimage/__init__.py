import json
import logging
import os
import sys
from pprint import pprint

import cv2
import numpy as np
from PIL import Image
from sanskrit_data.schema import ullekhanam

from docimage import preprocessing

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

class DisjointRectangles:
  def __init__(self, segments=None):
    if segments is None:
      segments = []
    self.img_targets = []
    self.merge(segments)

  def overlap(self, testseg):
    #testrect = self.to_rect(testseg)
    for i in range(len(self.img_targets)):
      if self.img_targets[i] == testseg:
        return i
    return -1

  def insert(self, newseg):
    #print "Inserting " + str(newseg)
    i = self.overlap(newseg)
    if i >= 0:
      if self.img_targets[i].score >= newseg.score:
        #print "Skipping " + str(newseg) + " < " + str(self.segments[i])
        return False
      else:
        self.remove(i)
        #for r in self.segments:
        #    print "->  " + str(r)
    #print "--> at " + str(len(self.segments))
    self.img_targets.append(newseg)
    return True

  def merge(self, segments):
    merged = [r for r in segments if self.insert(r)]
    return merged

  def get(self, i):
    return self.img_targets[i] if 0 <= i < len(self.img_targets) else None

  def remove(self, i):
    #print "deleting " + str(i) + "(" + str(len(self.segments)) + "): " + str(self.segments[i])
    if 0 <= i < len(self.img_targets):
      del self.img_targets[i]


class DocImage:
  def __init__(self, imgfile = None, workingImgFile = None):
    self.fname = ""
    self.working_img_rgb = None
    self.working_img_gray = None
    self.img_rgb = None
    self.img_gray = None
    self.w = 0
    self.h = 0
    self.ww = 0
    self.wh = 0
    self.img_bin = None

    if imgfile:
      #print "DocImage: loading ", imgfile
      self.update_image_file(imgfile)
    if workingImgFile:
      #print "DocImage: loading ", origImgFile
      self.update_working_file(workingImgFile)

  def update_image_file(self, imgfile):
    self.fname = imgfile
    self.img_rgb = cv2.imread(self.fname)
    self.init()

  def update_working_file(self, workingImgFile):
    self.fname = workingImgFile
    self.working_img_rgb = cv2.imread(self.fname)
    if (self.working_img_rgb is None) :
      temp_img = cv2.cvtColor(self.img_rgb, cv2.COLOR_RGB2BGR)
      pil_im = Image.fromarray(temp_img)
      self.working_img_rgb = DocImage.resize(pil_im, (1920, 1080), False)
      self.working_img_rgb = cv2.cvtColor(np.array(pil_im), cv2.COLOR_RGB2BGR)

      cv2.imwrite(workingImgFile, self.working_img_rgb)
    self.working_img_gray = cv2.cvtColor(self.working_img_rgb, cv2.COLOR_BGR2GRAY)
    self.ww, self.wh = self.working_img_gray.shape[::-1]
    logging.info("W width = " + str(self.ww) + ", W ht = " + str(self.wh))

  def init(self):
    self.img_gray = cv2.cvtColor(self.img_rgb, cv2.COLOR_BGR2GRAY)
    self.img_bin = preprocessing.binary_img(self.img_gray)
    self.w, self.h = self.img_gray.shape[::-1]
    logging.info("width = " + str(self.w) + ", ht = " + str(self.h))

  def from_image(self, img_cv):
    self.img_rgb = img_cv
    self.init()

  @classmethod
  def from_path(cls, path):
    from os.path import join
    [base_path, ext] = os.path.splitext(path)
    workingImgPath = join(base_path + "_working.jpg")
    logging.info("Image path = " + path)
    logging.info("Working Image path = " + workingImgPath)
    return DocImage(path, workingImgPath)

  @staticmethod
  def resize( img, box, fit):
    """Downsample the image.
    @param img: Image -  an Image-object
    @param box: tuple(x, y) - the bounding box of the result image
    @param fit: boolean - crop the image to fill the box

    @:returns: file-like-object - save the image into the output stream
    """
    #preresize image with factor 2, 4, 8 and fast algorithm
    factor = 1
    while img.size[0]/factor > 2*box[0] and img.size[1]*2/factor > 2*box[1]:
      factor *=2

    if factor > 1:
      img.thumbnail((img.size[0]/factor, img.size[1]/factor), Image.NEAREST)

    #calculate the cropping box and get the cropped part
    if fit:
      x1 = y1 = 0
      x2, y2 = img.size
      wRatio = 1.0 * x2/box[0]
      hRatio = 1.0 * y2/box[1]
      if hRatio > wRatio:
        y1 = int(y2/2-box[1]*wRatio/2)
        y2 = int(y2/2+box[1]*wRatio/2)
      else:
        x1 = int(x2/2-box[0]*hRatio/2)
        x2 = int(x2/2+box[0]*hRatio/2)
      img = img.crop((x1,y1,x2,y2))

    #Resize the image with best quality algorithm ANTI-ALIAS
    img.thumbnail(box, Image.ANTIALIAS)
    return img

    #save it into a file-like object
  #    img.save(out, "JPEG", quality=100)
  #resize

  def save(self, dstfile):
    cv2.imwrite(dstfile, self.img_rgb)

  def find_matches(self, template_img, thres = 0.7, known_segments = None):
    res = cv2.matchTemplate(self.img_bin,  template_img.img_bin, cv2.TM_CCOEFF_NORMED )

    loc = np.where(res >= float(thres))
    def ptToImgTarget(pt):
      return ullekhanam.Rectangle.from_details(x=pt[0], y= pt[1],
                                               w=template_img.w, h=template_img.h,
                                               score = float("{0:.2f}".format(res[pt[1], pt[0]]))
                                               )
    matches = map(ptToImgTarget, zip(*loc[::-1]))

    if known_segments is None:
      known_segments = DisjointRectangles()
    disjoint_matches = known_segments.merge(matches)
    known_segments.img_targets.sort()
    #for r in known_segments.segments:
    #   logging.info(str(r))
    return disjoint_matches

  def snippet(self, r):
    template_img = self.img_rgb[r.y:(r.y+r.h), r.x:(r.x+r.w)]
    template = DocImage()
    template.from_image(template_img)
    return template

  def find_recurrence(self, r, thres = 0.7, known_segments = None):
    #logging.info("Searching for recurrence of " + json.dumps(r))

    template = self.snippet(r)

    if known_segments is None:
      known_segments = DisjointRectangles()
    known_segments.insert(ullekhanam.Rectangle.from_details(x=r['x'], y=r['y'], w=r['w'], h=r['h']))
    return self.find_matches(template, thres, known_segments)

  def self_to_image(self):
    return self.img_rgb


  def find_text_regions(self, show_int=0, pause_int=0):

    if self.working_img_gray is None:
      img = self.img_gray
      totalArea = self.w * self.h
    else:
      img = self.working_img_gray
      totalArea = self.ww * self.wh

    kernel1 = np.ones((2,2),np.uint8)

    def show_img(name, fname):
      if int(show_int) != 0:
        screen_res = 1280.0, 720.0
        scale_width = screen_res[0] / fname.shape[1]
        scale_height = screen_res[1] / fname.shape[0]
        scale = min(scale_width, scale_height)
        window_width = int(fname.shape[1] * scale)
        window_height = int(fname.shape[0] * scale)

        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(name, window_width, window_height)

        cv2.imshow(name, fname)
      if int(pause_int) != 0:
        cv2.waitKey(0)

    show_img('Output0',img)

    ret,th1 = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
    show_img('Global Thresholding (v = 127)', th1)

    crop_img = th1[5:th1.shape[0]-10, 5:th1.shape[1]-10]
    show_img('CroppedOutput',crop_img)

    img= cv2.copyMakeBorder(crop_img,5,5,5,5,cv2.BORDER_CONSTANT,value=(0,0,0))
    show_img('BorderedOutput',img)

    boxes_temp = np.zeros(img.shape[:2],np.uint8)
    logging.info("boxes generated")

    binary = 255-img

    dilation = cv2.dilate(binary,kernel1,iterations = 1)
    show_img('Dilation', dilation)

    dilation = cv2.dilate(dilation,kernel1,iterations = 1)
    show_img('Dilation2', dilation)

    if self.working_img_gray is None:
      factorX = float(1.0)
      factorY = float(1.0)
    else:
      factorX = float(self.w) / float(self.ww)
      factorY = float(self.h) / float(self.wh)
    #        logging.info("factorx:"+str(factorX)+"factory:"+str(factorY))

    # Bounds are a guess work, more can be on it.
    lower_bound = totalArea / 3000
    upper_bound = totalArea / 4

    ret,thresh = cv2.threshold(dilation,127,255,0)
    im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
      x,y,w,h = cv2.boundingRect(c)
      if (((w*h) <= lower_bound or (w*h) >= upper_bound)) :
        continue
      cv2.rectangle(boxes_temp,(x,y),(x+w,y+h),(255,0,0),-1)

    show_img('Boxes_temp',boxes_temp)
    print("Contours Len = "+str(len(contours)))

    #        ret,thresh = cv2.threshold(boxes_temp,127,255,0)
    #        im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    #        for c in contours:
    #            x,y,w,h = cv2.boundingRect(c)
    #            if (((w*h) <= lower_bound or (w*h) >= upper_bound)) :
    #                continue
    #            cv2.rectangle(boxes_temp,(x,y),(x+w,y+h),(255,0,0),-1)

    #        show_img('Boxes_temp 2',boxes_temp)
    #        print("Contours 2 Len = "+str(len(contours)))


    allsegments = []

    ret,thresh = cv2.threshold(boxes_temp,127,255,0)
    im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    print("Lower="+str(lower_bound)+" Upper="+str(upper_bound))

    print("Contours 3 Len = "+str(len(contours)))

    for c in contours:
      coordinates = {'x': 0, 'y':0, 'h':0, 'w':0, 'score':float(0.0)}
      x,y,w,h = cv2.boundingRect(c)
      #            logging.info("x:"+str(x)+"y:"+str(y)+"w:"+str(w)+"h"+str(h))
      if (((w*h) <= lower_bound or (w*h) >= upper_bound)) :
        continue
      cv2.rectangle(boxes_temp,(x,y),(x+w,y+h),(255,0,0),1)

      coordinates['x'] = int(x * factorX)
      coordinates['y'] = int(y * factorY)
      coordinates['w'] = int(w * factorX)
      coordinates['h'] = int(h * factorY)

      #            logging.info("x*:"+str(coordinates['x'])+"y:"+str(coordinates['y'])+"w:"+str(coordinates['w'])+"h"+str(coordinates['h']))
      allsegments.append(
        ullekhanam.Rectangle.from_details(x=coordinates['x'], y=coordinates['y'], w=coordinates['w'], h=coordinates['h']))

    show_img('Boxes_temp 3',boxes_temp)

    return allsegments

  def add_rectangles(self, sel_areas, color = (0, 0, 255), thickness = 2):
    for rect in sel_areas:
      cv2.rectangle(self.img_rgb, (rect['x'], rect['y']),
                    (rect['x'] + rect['w'], rect['y'] + rect['h']), color, thickness)


def main(args):
  img = DocImage(args[0])
  rect = { 'x' : int(args[1]),
           'y' : int(args[2]),
           'w' : int(args[3]), 'h' : int(args[4]), 'score' : float(1.0) }
  logging.info("Template rect = " + json.dumps(rect))
  matches = img.find_recurrence(rect, 0.7)
  pprint(matches)
  logging.info("Total", len(matches), "matches found.")

  #logging.info(json.dumps(matches))
  img.add_rectangles(matches)
  img.add_rectangles([rect], (0, 255, 0))

  cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
  cv2.imshow('Annotated image', img.img_rgb)
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  sys.exit(0)

def mainTEST(arg):
  [bpath, filename] = os.path.split(arg)
  [fname, ext] = os.path.splitext(filename)

  image = Image.open(arg).convert('RGB')
  workingFilename = fname+"_working.jpg"
  out = open(workingFilename, "w")
  img = DocImage.resize(image, (1920,1080), False)
  img.save(out, "JPEG", quality=100)
  out.close()

  img = DocImage(arg,fname+"_working.jpg")
  segments = img.find_text_regions(0, 0)

  first_snippet = img.snippet(segments[5])
  cv2.imshow('First snippet', first_snippet.img_rgb)
  cv2.waitKey(0)
  first_snippet.save(fname + "_snippet1.jpg")

  anno_img = DocImage()
  anno_img.from_image(img.img_rgb)
  anno_img.add_rectangles(segments)
  #    img.annotate(img.find_sections(1,1))
  #img.annotate(img.find_segments(1,1))

  screen_res = 1280.0, 720.0
  scale_width = screen_res[0] / anno_img.w
  scale_height = screen_res[1] / anno_img.h
  scale = min(scale_width, scale_height)
  window_width = int(anno_img.w * scale)
  window_height = int(anno_img.h * scale)

  cv2.namedWindow('Final image', cv2.WINDOW_NORMAL)
  cv2.resizeWindow('Final image', window_width, window_height)

  cv2.imshow('Final image', anno_img.img_rgb)
  cv2.waitKey(0)


  cv2.destroyAllWindows()


if __name__ == "__main__":
  #main(sys.argv[1:])
  mainTEST(sys.argv[1])

# -*- coding: utf-8 -*-
"""image_maskgenerator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1F05cfQnwqFcl5sAAi4aEZGkTnpc1XBo4
"""

import cv2
from random import randint
import numpy as np

class MaskGenerator():
    
    def __init__ (self,X=None,scale_ratio = 0.03) :
        
        self.height, self.width , self.channels = X.shape
        self.mask = np.zeros((self.height,self.width,self.channels),dtype='uint8')
        self.scale_ratio = scale_ratio
        self.masker()
        
        
    def masker(self,line=True,circle=True,ellipse=True,rectangle=False,polygon=False) :
        
        scale = int((self.height+self.width)*self.scale_ratio)
        if line :
            for i in range(randint(1,15)):
                x1,x2 = randint(1,self.width) ,randint(1,self.width)
                y1,y2 = randint(1,self.height) ,randint(1,self.height)
                cv2.line(self.mask,(x1,x2),(y1,y2),(1,1,1),randint(4,scale))
        if circle :
            for i in range(randint(1,15)):
                cx,cy  = randint(1,self.width), randint(1,self.height)
                radius = randint(30,50)
                cv2.circle(self.mask, (cx,cy), radius, (1,1,1), randint(4,scale))
        if ellipse :
            for i in range(randint(1,15)):
                x1, y1 = randint(1, self.width), randint(1, self.height)
                s1, s2 = randint(1, self.width), randint(1, self.height)
                a1, a2, a3 = randint(3, 180), randint(3, 180), randint(3, 180)
                thickness = randint(20, scale)
                cv2.ellipse(self.mask, (x1,y1), (s1,s2), a1, a2, a3,(1,1,1), thickness)
                
        if rectangle :
             for i in range(randint(1,15)):
                x1,x2 = randint(1,self.width) ,randint(1,self.width)
                y1,y2 = randint(1,self.height) ,randint(1,self.height)
                cv2.rectangle(self.mask, (x1,y1), (x2,y2), (1,1,1), randint(4,20)) 
                
        self.mask = 1 - self.mask


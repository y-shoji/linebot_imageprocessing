import cv2
import numpy as np
from random import random

def wite_noise(img,k):
    height,width= img.shape[:2] 
    P_img = np.random.rand(height,width)
    T_img = (1.0-k)*(1.0-img.astype(np.float)/255.0)
    noise_img = np.where(P_img>T_img,255,0)

    return noise_img       
            
                
def hatching(img,LIY):
    height,width= img.shape[:2]
    noise_img = wite_noise(img, 0.7)

    l = width // (2*LIY)
    l = l+1 if l%2==0 else l
    noise_img  =  np.pad(noise_img,(l,l),'constant').astype(np.uint64)    

    kernel_135deg = np.diag([1 for _ in range(l*2)])
    kernel_45deg  = np.fliplr(kernel_135deg)

    hatching_45deg_img = cv2.filter2D(noise_img,-1,kernel_45deg)
    hatching_45deg_img = hatching_45deg_img[l:l+height, l:l+width] // (2*l+1)
    hatching_45deg_img = hatching_45deg_img.astype(np.uint8)

    hatching_135deg_img = cv2.filter2D(noise_img,-1,kernel_135deg)
    hatching_135deg_img = hatching_135deg_img[l:l+height, l:l+width] // (2*l+1)
    hatching_135deg_img = hatching_135deg_img.astype(np.uint8)
 
    return hatching_45deg_img, hatching_135deg_img
            
def CrH(img1,img2):
    height,width,= img1.shape[:2]
    CrH_img = 255.0*(img1.astype(np.float32)/255.0) * (img2.astype(np.float32)/255.0)

    return CrH_img

def BD(img1,img2,n=0):
    CrH_img = CrH(img1,img2)
    if n == 0:
        return CrH_img

    for _ in range(n):
        CrH_img=cv2.GaussianBlur(CrH_img,(5,5),0)
    
    return CrH_img
           
def Posterization_color(img, q):
    for l in range(q):
        t1 = l * (255/q)
        t2 = (l+1) * (255/q)
        img = np.where(( (t1<=img) & (img<=t2)), (t1+t2)/2,img)
    
    return img

def Highpass_filter(img, n):
    img2 = img.copy()
    for t in range(n):
        img2 = cv2.GaussianBlur(img2,(3,3,),0)

    return img-img2+128

def Posterization_transfer(img):
    img2 = img.copy()
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    img = Posterization_color(img, 4)
    img2 = Highpass_filter(img2, 1)

    img2 = img2.astype(np.float) 
    img2 -= 128
    img2 = np.where(img2<0, -img2, img2)
    img2 = np.where(img2>15,-500,0)

    img = img.astype(np.float)
    for c in range(3):
        img[:,:,c] += img2
    img = np.where(img<0,0,img)
    img + np.where(img>255,255,img)

    return img.astype(np.uint8)

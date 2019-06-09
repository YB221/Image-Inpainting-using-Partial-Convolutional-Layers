# Image-Inpainting-using-Partial-Convolutional-Layers <br/>
## Table of contents
* [Introduction](#introduction)
* [Details](#details)
* [Setup](#setup)
* [Implementation Details](#implementation-details)
* [Partial Convolutional Layer](#partial-convolutional-layer)
* [Visualizing Results](#visualizing-results)

## Introduction
* Implemented the paper https://arxiv.org/pdf/1804.07723 by <b>Guilin Liu, Fitsum A. Reda, Kevin J. Shih, Ting-Chun Wang, Andrew Tao, Bryan Catanzaro</b> 
* Implementation has been done in <b>Keras</b>.
* Achieved <b>PSNR(Peak-Signal-to-Noise-Ratio) of 15.76</b> on validation images.

## Details
* <b>Requirements</b>  : Python 3.6 onwards, keras 2.2.4
* <b>Notebook used</b> : Google Colaboratory notebook
* <b>Hardware Accelerator</b>  : GPU
* <b>Dataset Download link</b> : https://s3-ap-southeast-1.amazonaws.com/he-public-data/DL%23+Beginner.zip

## Setup
* From <b>training on the dataset provided</b> in the Details section, directly run [inpainting-notebook](https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/inpainting_notebook.ipynb)
* For <b>training on your own dataset</b>, use the same architecture with a dataset of your own.


## Implementation Details
* The first task required creating <b>masks</b> for the images.
  Used OpenCV to make a [random mask generator](https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/image%20masker/image_maskgenerator.py).</br>
  Here are a few results of the random masks:</br>
  <img src='https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/data/download%20(1).png' />
</br>
* <h3>Architecture Used : UNET</h3> 
  <img src='https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/data/unet-architecture.png' />
  
## Partial Convolutional Layer: 
* As cited in the paper </br>
* Let W be the convolution filter weights
for the convolution filter and b its the corresponding bias. X are the feature
values (pixels values) for the current convolution (sliding) window and M is the
corresponding binary mask. The partial convolution at every location, is expressed as:
<img src = 'https://ask.qcloudimg.com/http-save/yehe-1407979/xcd0vilkyi.jpeg?imageView2/2/w/1620' />


## Visualizing Results :
* <img src = 'https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/data/download.png' />
* Left to right : Maksed Image, Predicted Image , Original Image
* Training takes a lot of time and an average epoch through the entire dataset takes about 3 hrs.



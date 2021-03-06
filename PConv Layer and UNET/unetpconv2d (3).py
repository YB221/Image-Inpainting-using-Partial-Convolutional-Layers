# -*- coding: utf-8 -*-
"""UnetPconv2D.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dIE1MQZl6_FRdlJhEDDM2-C_0FJZ2-vy

# ***Importing necessary libraries***
"""

import tensorflow as tf
from keras import backend as K
from keras.engine import InputSpec
from keras.models import Model
from keras.optimizers import Adam
from keras.layers import Input, Conv2D, UpSampling2D, Dropout, LeakyReLU, BatchNormalization, Activation, Lambda
from keras.layers.merge import Concatenate
from keras.applications import VGG16
import numpy as np
from keras.utils import conv_utils

"""---



---



---

# Partial Convolution Layer 

---

Creating a custom keras layer that has trainable weights, 
by extending the existing Conv2D layer(class) of keras.

Resource used : [https://keras.io/layers/writing-your-own-keras-layers/]


Mathematical representation of Pconv2D :

![](https://ask.qcloudimg.com/http-save/yehe-1407979/xcd0vilkyi.jpeg?imageView2/2/w/1620)
"""

class Pconv(Conv2D):
    
    def __init__(self,*args,**kwargs):
        '''The following piece of code signifies that the input will be 4-dimensional that is N,C,H,W
        N - No of examples
        C - No of Channels or filters
        H - Height
        W - Width
        Note that the image and mask will have identical shapes
        
        the input_spec attribute specifies to the class that
        a list is expected as input........'''
        super().__init__(*args,**kwargs)
        self.input_spec = [InputSpec(ndim=4), InputSpec(ndim=4)]
        
        
    def build(self, input_shape):
        ''' As a custom layer with mask is implemented it is necessary to assert,
            that the input is a list of [img,mask]. The build function is to define the weights 
            and biases that would be used in the Pconv layer'''
        assert isinstance(input_shape, list)
        # Create a trainable weight variable for this layer.
        
        if self.data_format == 'channels_first' :
            n = 1
        else :
            n = -1 
            
        n_channels = input_shape[0][n]
        
        #Custom made kernel for image convolutions
        kernel_shape = self.kernel_size + (n_channels,self.filters)
        self.kernel = self.add_weight(name='kernel',
                                      shape=kernel_shape,
                                      initializer=self.kernel_initializer,
                                      regularizer=self.kernel_regularizer,
                                      trainable=True,
                                      )
        
        #Custom made kernel for convolutions on mask
        self.kernel_mask = K.ones(shape=kernel_shape,name='mask-kernel')
        
        #this is done to ensure that the output shape is obtained as expected
        self.pconv_padding = (
            (int((self.kernel_size[0]-1)/2), int((self.kernel_size[0]-1)/2)), 
            (int((self.kernel_size[0]-1)/2), int((self.kernel_size[0]-1)/2)), 
        )

        # Window size - used for normalization
        self.window_size = self.kernel_size[0] * self.kernel_size[1]
        
        
        #bias to add after the custom task in completed
        if self.use_bias :
            self.bias = self.add_weight(shape=(self.filters,),
                                        initializer=self.bias_initializer,
                                        name='bias',
                                        regularizer=self.bias_regularizer,
                                        constraint=self.bias_constraint)
            
        #super(Pconv, self).build(input_shape)
        self.built = True
        
        
    def call(self,inputs) :
        ''' This portion includes the actual implementation :
            the image is elementally multiplied to the masks
            which is fed to the network and later the masks are
            updated on the basis of the output generated'''
        assert isinstance(inputs, list)
        
        images = inputs[0]
        masks  = inputs[1]
        
        #padding layer
        images = K.spatial_2d_padding(inputs[0], self.pconv_padding, self.data_format)
        masks = K.spatial_2d_padding(inputs[1], self.pconv_padding, self.data_format)
        
        X = images*masks
        
        out = K.conv2d(X,self.kernel,
                       strides=self.strides,
                       padding='valid',
                       data_format = self.data_format)
        
        #################################################
        def mask_update(masks):
            ''' mask update function that updates the mask
                after a succesful Partial conv layer
                '''
            out = K.conv2d(masks, self.kernel_mask,
                       strides=self.strides, padding='valid',
                       data_format = self.data_format)
            out = K.clip(out,0,1)
            eps = 1e-6
            mask_ratio = self.window_size / (out + eps)
            mask_ratio *= out
        
            return out,mask_ratio
        #################################################
        
        updated_mask,mask_ratio = mask_update(masks)
        out = out * mask_ratio
        
        if self.use_bias :
            out = K.bias_add(out, self.bias, data_format=self.data_format)
            
        if self.activation :
            out = self.activation(out)
        
        return [out, updated_mask]
    
    
    def compute_output_shape(self, input_shape):
        ''' in case your layer modifies the shape of its input,
        you should specify here the shape transformation logic,
        as done in this case'''
        assert isinstance(input_shape, list)
        
        '''if self.data_format == 'channels_last':
            shape = input_shape[1:-1]
            new_shape = [conv_utils.conv_output_length(
                    space[i],
                    self.kernel_size[i],
                    padding='same',
                    stride=self.strides[i],
                    dilation=self.dilation_rate[i]) for i in range(len(shape))]
            new_shape = (input_shape[0][0],)+tuple(new_shape)+(input_shape[0][-1],)
            
        if self.data_format == 'channels_first':
            shape = input_shape[2:]
            new_shape = [conv_utils.conv_output_length(
                    space[i],
                    self.kernel_size[i],
                    padding='same',
                    stride=self.strides[i],
                    dilation=self.dilation_rate[i]) for i in range(len(shape))]
            new_shape = (input_shape[0][0],)+tuple(new_shape)+(input_shape[0][-1],)
            
        return [new_shape,new_shape]'''
        if self.data_format == 'channels_last':
            space = input_shape[0][1:-1]
            new_space = []
            for i in range(len(space)):
                new_dim = conv_utils.conv_output_length(
                    space[i],
                    self.kernel_size[i],
                    padding='same',
                    stride=self.strides[i],
                    dilation=self.dilation_rate[i])
                new_space.append(new_dim)
            new_shape = (input_shape[0][0],) + tuple(new_space) + (self.filters,)
            return [new_shape, new_shape]
        if self.data_format == 'channels_first':
            space = input_shape[2:]
            new_space = []
            for i in range(len(space)):
                new_dim = conv_utils.conv_output_length(
                    space[i],
                    self.kernel_size[i],
                    padding='same',
                    stride=self.strides[i],
                    dilation=self.dilation_rate[i])
                new_space.append(new_dim)
            new_shape = (input_shape[0], self.filters) + tuple(new_space)
            return [new_shape, new_shape]

"""---

# U-NET ARCHITECTURE

## ![alt text](https://github.com/chefpr7/Image-Inpainting-using-Partial-Convolutional-Layers/blob/master/data/unet-architecture.png?raw=true)
"""

class PConvUNET(object):
    
    def __init__(self,h,w,c,data_format='channels_last',weights='imagenet'):
        
        self.h = h
        self.w = w
        self.c = c
        self.data_format = data_format
        self.mean = [0.485, 0.456, 0.406]
        self.std = [0.229, 0.224, 0.225]
        self.no_of_pixels = h*w*c
        self.vgg_layers=[3,6,10]
        self.vgg = self.vgg_model(weights)
        self.model,self.masks = self.build_pconv_UNet()
        self.model_compile(self.model,self.masks)
        
        
    def vgg_model(self,weights):
        '''A non-trainable vgg-model trained on imagenet
           is used to extract features from higher level
           layers namely : pool1,pool2,pool3 which will be
           used for calculating perceptual and style losses'''
        if weights == 'imagenet' :
            vgg = VGG16(include_top=False,weights='imagenet')
        else :
            vgg = VGG16(weights=None, include_top=False)
            vgg.load_weights(weights, by_name=True)
        imgs = Input((self.h,self.w,self.c))
        processed = Lambda(lambda x: (x-self.mean) / self.std)(imgs)
        vgg.outputs = [vgg.layers[i].output for i in self.vgg_layers]
        model = Model(inputs=imgs,outputs=vgg(processed))
        model.trainable = False
        model.compile(loss='mse',optimizer='adam')
        return model
        
    def build_pconv_UNet(self,train_bn=True):
        
        inputs_img = Input((self.h, self.w, 3), name='inputs_img')
        inputs_mask = Input((self.h, self.w, 3), name='inputs_mask')
        
        def encoder_layer(imgs,masks,filters,kernel_size,bn=True):
            I_out , Mask_out = Pconv(filters,kernel_size,strides=2,padding='same')([imgs,masks])
            if bn :
                I_out = BatchNormalization()(I_out,training=train_bn)
            I_out = Activation('relu')(I_out)
            
            return I_out,Mask_out
        
        en_img1, en_mask1 = encoder_layer(inputs_img,inputs_mask,64,7,False)
        en_img2, en_mask2 = encoder_layer(en_img1,en_mask1,128,5)
        en_img3, en_mask3 = encoder_layer(en_img2,en_mask2,256,5)
        en_img3, en_mask3 = encoder_layer(en_img2,en_mask2,256,5)
        en_img3, en_mask3 = encoder_layer(en_img2,en_mask2,256,5)
        en_img4, en_mask4 = encoder_layer(en_img3,en_mask3,512,3)
        en_img5, en_mask5 = encoder_layer(en_img4,en_mask4,512,3)
        en_img6, en_mask6 = encoder_layer(en_img5,en_mask5,512,3)
        en_img7, en_mask7 = encoder_layer(en_img6,en_mask6,512,3)
        en_img8, en_mask8 = encoder_layer(en_img7,en_mask7,512,3)
        
        
        def decoder_layer(imgs,masks,en_img,en_mask,filters,kernel_size,bn=True,**kwargs):
            I_up    = UpSampling2D(size=(2,2),data_format=self.data_format)(imgs)
            mask_up = UpSampling2D(size=(2,2),data_format=self.data_format)(masks)
            if self.data_format == 'channels_first' :
                axis = 1
            else :
                axis = 3
            
            I_up_concat    = Concatenate(axis)([I_up,en_img])
            mask_up_concat = Concatenate(axis)([mask_up,en_mask])
            
            I_out, Mask_out = Pconv(filters,kernel_size,padding='same')([I_up,mask_up])
            if bn:
                I_out = BatchNormalization()(I_out)
            I_out = LeakyReLU(alpha=0.2)(I_out)
            return I_out, Mask_out
        
        dec_conv1, dec_mask1 = decoder_layer(en_img8,en_mask8,en_img7,en_mask7,512,3)
        dec_conv2, dec_mask2 = decoder_layer(dec_conv1,dec_mask1,en_img6,en_mask6,512,3)
        dec_conv3, dec_mask3 = decoder_layer(dec_conv2,dec_mask2,en_img5,en_mask5,512,3)
        dec_conv4, dec_mask4 = decoder_layer(dec_conv3,dec_mask3,en_img4,en_mask4,512,3)
        dec_conv5, dec_mask5 = decoder_layer(dec_conv4,dec_mask4,en_img3,en_mask3,256,3)
        dec_conv6, dec_mask6 = decoder_layer(dec_conv5,dec_mask5,en_img2,en_mask2,128,3)
        dec_conv7, dec_mask7 = decoder_layer(dec_conv6,dec_mask6,en_img1,en_mask1,64,3)
        dec_conv8, dec_mask8 = decoder_layer(dec_conv7,dec_mask7,inputs_img,inputs_mask,3,3,bn=False)
        
        outputs = Conv2D(3, 1, activation = 'sigmoid', name='outputs_img')(dec_conv8)
        model = Model(inputs=[inputs_img, inputs_mask], outputs=outputs)

        return model, inputs_mask 
                
    
    def model_compile(self,model,masks,lr=0.001):
        model.compile(
                     loss=self.loss_total(masks),
                     optimizer= Adam(lr=lr),
                     metrics=[self.PSNR]
                     ) 
        
    
    def loss_total(self,M):
        
        def loss(I_out,I_gt):
            '''I_comp is obtained by setting all the non hole pixels of I_out directly to ground truth'''
            I_comp   = I_out*(1-M) + I_gt*M
            vgg_out  = self.vgg(I_out)
            vgg_comp = self.vgg(I_comp)
            vgg_gt   = self.vgg(I_gt)
        
            l1 = self.hole_loss(I_out,I_gt,M)
            l2 = self.loss_valid(I_out,I_gt,M)
            l3 = self.loss_perceptual(vgg_out,vgg_gt,vgg_comp)
            l4 = self.style_loss(vgg_out,vgg_gt)
            l5 = self.style_loss(vgg_comp,vgg_gt)
            l6 = self.loss_tv(M,I_comp)
        
            return l1 + 6*l2 + 0.05*l3 + 120*(l4+l5) + 0.1*l6
        return loss
        
        
    def hole_loss(self,I_out,I_gt,M):
        '''Per pixel loss defined as the L1 distance between the ground truth and the output image 
           after multiplying by (1-M) where M is the corresponding mask'''
        return self.l1((1-M)*I_out,(1-M)*I_gt)
    
    def loss_valid(self,I_out,I_gt,M):
        ''' loss_valid = L1 distance of M * (I_out-I_gt)'''
        return self.l1(M*I_out,M*I_gt)
    
    def loss_perceptual(self,vgg_out,vgg_gt,vgg_comp):
        loss = 0
        for i,j,k in zip(vgg_out,vgg_comp,vgg_gt) :
            '''if K.ndim(i) == 4:
                _,n1,n2,n3 = K.shape(i)
            else :
                n1,n2,n3 = K.shape(i)
            n = n1*n2*n3'''
            loss += self.l1(i,k) + self.l1(j,k)
        return loss
    
    def style_loss(self,output,vgg_gt):
        loss = 0
        for o, g in zip(output, vgg_gt):
            loss += self.l1(self.gram_matrix(o), self.gram_matrix(g))
        return loss
    
    def loss_tv(self, mask, y_comp):
        """Total variation loss, used for smoothing the hole region, see. eq. 6"""

        # Create dilated hole region using a 3x3 kernel of all 1s.
        kernel = K.ones(shape=(3, 3, mask.shape[3], mask.shape[3]))
        dilated_mask = K.conv2d(1-mask, kernel, data_format='channels_last', padding='same')

        # Cast values to be [0., 1.], and compute dilated hole region of y_comp
        dilated_mask = K.cast(K.greater(dilated_mask, 0), 'float32')
        P = dilated_mask * y_comp

        # Calculate total variation loss
        a = self.l1(P[:,1:,:,:], P[:,:-1,:,:])
        b = self.l1(P[:,:,1:,:], P[:,:,:-1,:])        
        return a+b

    def model_summary(self):
        return self.model.summary()
    
    
    def generator(self,generator,*args,**kwargs):
        self.model.fit_generator(generator,*args,**kwargs)
        
    ##############################################################################
    '''Gram-matrix function taken from github.
       It is required for the style loss terms'''
    
    def gram_matrix(self,x, norm_by_channels=False):
        """Calculate gram matrix used in style loss"""
        
        # Assertions on input
        assert K.ndim(x) == 4, 'Input tensor should be a 4d (B, H, W, C) tensor'
        assert K.image_data_format() == 'channels_last', "Please use channels-last format"        
        
        # Permute channels and get resulting shape
        x = K.permute_dimensions(x, (0, 3, 1, 2))
        shape = K.shape(x)
        B, C, H, W = shape[0], shape[1], shape[2], shape[3]
        
        # Reshape x and do batch dot product
        features = K.reshape(x, K.stack([B, C, H*W]))
        gram = K.batch_dot(features, features, axes=2)
        
        # Normalize with channels, height and width
        gram = gram /  K.cast(C * H * W, x.dtype)
        
        return gram
    ################################################################################################
    
    
    def l1(self,y_true, y_pred):
        """Calculate the L1 loss used in all loss calculations"""
        if K.ndim(y_true) == 4:
            return K.mean(K.abs(y_pred - y_true), axis=[1,2,3])
        elif K.ndim(y_true) == 3:
            return K.mean(K.abs(y_pred - y_true), axis=[1,2])
        else:
            raise NotImplementedError("Calculating L1 loss on 1D tensors? should not occur for this network")
            
    def PSNR(self,y_true, y_pred):
        """
        PSNR is Peek Signal to Noise Ratio, see https://en.wikipedia.org/wiki/Peak_signal-to-noise_ratio
        The equation is:
        PSNR = 20 * log10(MAX_I) - 10 * log10(MSE)
        
        Our input is scaled with be within the range -2.11 to 2.64 (imagenet value scaling). We use the difference between these
        two values (4.75) as MAX_I        
        """        
        #return 20 * K.log(4.75) / K.log(10.0) - 10.0 * K.log(K.mean(K.square(y_pred - y_true))) / K.log(10.0) 
        return - 10.0 * K.log(K.mean(K.square(y_pred - y_true))) / K.log(10.0) 

            
    def predict(self,test,**kwargs):
        return self.model.predict(test,**kwargs)
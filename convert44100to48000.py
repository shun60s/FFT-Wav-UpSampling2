#coding:utf-8

#
#  stero WAV file convert sampling rate from 44.1KHz to 48KHz, or to 96KHz
#--------------------------------------------------------------
#  Using 
# Python 3.6.4, 64bit on Win32 (Windows 10)
# numpy 1.18.4
# scipy 1.4.1
# soundfile 0.10.3
#  ------------------------------------------------------------

import sys
import os
import glob
import copy
import argparse
import numpy as np
from scipy import signal
from scipy.fftpack import fft, ifft
from scipy.io.wavfile import read as wavread
from scipy.io.wavfile import write as wavwrite




class convert441to480(object):
    def __init__(self,path_input_wav, path_output_wav=None, output_bit=16, factor=1, method="COWM"):
        # initalize
        self.wavfile= path_input_wav    # input wav file name
        if path_output_wav is None:
            new_dir= os.path.join(os.path.dirname(self.wavfile), method)
            if not os.path.exists( new_dir):
                os.mkdir( new_dir)
            if factor == 1:
                sufix0='_48KHz'
            elif factor == 2:
                sufix0='_96KHz'
            else:
                sufix0='_out'
            self.wavfile2= os.path.join(new_dir ,os.path.splitext(os.path.basename(self.wavfile))[0] + sufix0 +  '.wav')
            
        else:
            self.wavfile2= path_output_wav  # output file name
        self.output_bit= output_bit
        self.factor= factor  #  48KHz is 1, 96KHz is 2.
        
        ###############################
        # sampling rate 
        self.original= 44100 
        self.target= 48000
        self.duration= 0.08  # frame length uint is second
        
        # multiplication coefficient
        self.original_mc = int(160 * self.factor)  # for 44100
        self.target_mc   = int(147 * self.factor)  # for 48000
        
        
        self.original_points = self.original * self.duration
        if self.original_points - int(self.original_points) != 0.:
            print ("Error: original_points is not integral number.", self.original_points )
            sys.exit()
        elif int(self.original_points) % 2 != 0:
            print ("Error: original_points must be even number.", int(self.original_points) % 2 )
            sys.exit()
        else:
            self.original_points= int(self.original_points)
            print ('original points ', self.original_points )
            self.original_points_mc=  int(self.original_points * self.original_mc)
            print ('original points mc ',  self.original_points_mc )
        
        self.target_points = self.target *  self.factor * self.duration
        if self.target_points - int(self.target_points) != 0.:
            print ("Error: target_points is not integral number.", self.target_points )
            sys.exit()
        elif int(self.target_points) % 2 != 0:
            print ("Error: target_points must be even number.", int(self.target_points) % 2 )
            sys.exit()
        else:
            self.target_points= int(self.target_points)
            print ('target points ',  self.target_points )
            self.target_points_mc=  int(self.target_points *  self.target_mc / self.factor)
            print ('target points mc ',  self.target_points_mc )
        
        if self.original_points_mc != self.target_points_mc:
            print ("Error: original_points_mc and target_points_mc must be same." )
            sys.exit()
        
        # FFT point and every shift
        self.N =  self.original_points
        self.SHIFT= int(self.N/2)  # shift must be N/2
        self.N2=  self.target_points   # output point
        self.SHIFT2= int(self.N2/2) 
        
        # read input wav file
        self.wdata, self.fs= self.read_wav( self.wavfile) 
        
        self.stmono= self.wdata.shape[1]
        self.size0= self.wdata.shape[0]
        
        # show WAV information
        print ("sampling rate ", self.fs)
        print ("original size ", self.size0)
        
        
        if self.fs != self.original:
            print ("Sorry, sampling rate should be ", self.original, self.wavfile)
            sys.exit()
        if self.stmono != 2:
            print ("Sorry, only stereo wav file is available")
            sys.exit()
        
        # count shift number
        self.num0= int((self.size0 - self.N)/ self.SHIFT) + 1
        print ("number ", self.num0)
        
        self.size0_new = self.SHIFT2 * (self.num0 + 1)
        print ("target size ", self.size0_new)
        
        
        # process
        self.method= method
        if self.method == "SDOM":
            print ("method", self.method)
            self.wavo= self.sub_main_SDOM()
        elif self.method == "COWM":
            print ("method", self.method)
            if 0:  # check window combination response
                self.plot_COWM()
            self.wavo= self.sub_main_COWM()
        else:
            print ("Error: there is no such method.", self.method )
            sys.exit()
            
        # write output wav
        if self.output_bit == 16:
            self.save_wav16(self.wavfile2, self.wavo, sr= int(self.target * self.factor) )
        elif self.output_bit == 24:
            import soundfile as sf
            sf.write(self.wavfile2, self.wavo, int(self.target * self.factor), 'PCM_24')
            print ('wrote ', self.wavfile2)
        
        
    def sub_main_SDOM(self):
        ###############################################################
        #
        #  SHIFT DATA OVERLAP METHOD:
        #
        #
        #     BBBMMMCCCCCCMMMBBB
        #              BBBMMMCCCCCCMMMBBB
        #     B: zero, ignore, Suteru
        #     M: linearly MIX
        #     C: sonomama tukau
        #
        ###############################################################
        # MIX value
        M=3  # bunkatu suu of half duration
        NL0=int(self.N2/(M*2))    # duration CCC and BBB,  ex It's 682 when N=4096
        NL= int(self.N2/2 - (NL0 *2))  # duration MMM           ex It's 684 when N=4096
        print ("NL0, NL ", NL0, NL)
        k0=np.linspace(0,1,NL)
        k1=np.linspace(1,0,NL)
        
        N_0= int(self.N)
        N_M1= int(self.N-1)
        N_2= int(self.N/2)
        N_2P1= int(self.N/2+1)
        N_MC = int( self.N * (self.original_mc -2))
        
        # output data
        wavo=np.zeros( (int(self.size0_new), self.stmono) )
        
        for loop in range(self.num0):
            print (" " +  str(loop)+"/" + str(self.num0) +"\r",end="")
            
            sp0= int(self.SHIFT * loop)     # input point
            sp2= int(self.SHIFT2 * loop)  # output point
            
            for ch0 in range( self.stmono ):
                
                # read N points via every SHIFT
                fw1= self.wdata[sp0: int(sp0 + self.N), ch0]
                
                # Fourier transform via FFT
                yf = fft(fw1)
                # 1/N ga kakarukara node *2baisuru,  center Value ha ryouhou ni huru
                yf2=np.concatenate([yf[0:1] , yf[1:N_2], yf[N_2:N_2P1]*0.5, np.zeros(N_M1), np.zeros(N_MC), yf[N_2:N_2P1]*0.5, yf[N_2+1:N_0] ]) 
                iyf2_all= ifft(yf2 * self.original_mc).real
                
                iyf2= iyf2_all.reshape(self.N2, int(self.target_mc/self.factor))[:,0]
                
                # 1st loop
                if loop == 0:
                    wavo[0:int(self.N2/2+NL0),ch0]=iyf2[0:int(self.N2/2+NL0)]
                
                else:
                # mix, duration of mmm
                    if ch0 == 0:
                        dmix=(iyf2[int(self.N2/2-NL0-NL):int(self.N2/2-NL0)] * k0)  + dch0[:]  # for ch0
                    elif ch0 == 1:
                        dmix=(iyf2[int(self.N2/2-NL0-NL):int(self.N2/2-NL0)] * k0)  + dch1[:]  # for ch0
                    
                    wavo[int(sp2+self.N2/2-NL0-NL) : int(sp2+ self.N2/2-NL0) ,ch0]=dmix[:]
                    
                    # duration of ccc
                    wavo[int(sp2+self.N2/2-NL0) : int(sp2+self.N2/2+NL0) ,ch0]=iyf2[ int(self.N2/2-NL0) : int(self.N2/2+NL0)]
                
                # copy to backup
                if ch0 == 0:
                    dch0=iyf2[int( self.N2/2+NL0) : int(self.N2/2+NL0+NL) ] * k1
                elif ch0 == 1:
                    dch1=iyf2[int( self.N2/2+NL0) : int(self.N2/2+NL0+NL) ] * k1
        print(' ')
        return  np.clip( wavo,-1., 1.) 
    
    
    def sub_main_COWM(self):
        ###############################################################
        #
        #  combine OVERLAP WINDOW METHOD:
        #
        ###############################################################
        
        N_0= int(self.N)
        N_M1= int(self.N-1)
        N_2= int(self.N/2)
        N_2P1= int(self.N/2+1)
        N_MC = int( self.N * (self.original_mc -2))
        
        # make Hann window
        original_win1= self.evenHANNwindow(self.N)
        original_win1st= np.concatenate( [np.ones( self.SHIFT), original_win1[self.SHIFT:] ])
        original_win1last= np.concatenate( [ original_win1[0:self.SHIFT], np.ones( self.SHIFT)])
        
        # output data
        wavo=np.zeros( (int(self.size0_new), self.stmono) )
        
        for loop in range(self.num0):
            print (" " +  str(loop)+"/" + str(self.num0) +"\r",end="")
            
            sp0= int(self.SHIFT * loop)     # input point
            sp2= int(self.SHIFT2 * loop)  # output point
            
            for ch0 in range( self.stmono ):
                
                # read N points via every SHIFT
                if loop == 0:  # 1st loop
                    fw1= self.wdata[sp0: int(sp0 + self.N), ch0] * original_win1st
                elif loop == ( self.num0 -1):  # last
                    fw1= self.wdata[sp0: int(sp0 + self.N), ch0] * original_win1last
                else:
                    fw1= self.wdata[sp0: int(sp0 + self.N), ch0] * original_win1
                
                # Fourier transform via FFT
                yf = fft(fw1)
                # 1/N ga kakarukara node *2baisuru,  center Value ha ryouhou ni huru
                yf2=np.concatenate([yf[0:1] , yf[1:N_2], yf[N_2:N_2P1]*0.5, np.zeros(N_M1), np.zeros(N_MC), yf[N_2:N_2P1]*0.5, yf[N_2+1:N_0] ]) 
                iyf2_all= ifft(yf2 * self.original_mc).real
                
                iyf2= iyf2_all.reshape(self.N2, int(self.target_mc/self.factor))[:,0]
                
                
                if loop == 0:  # 1st loop
                    wavo[0:self.SHIFT2,ch0]= iyf2[0:self.SHIFT2]
                    
                elif loop == ( self.num0 -1):  # last
                    if ch0 == 0:
                        wavo[sp2 : int(sp2+ self.SHIFT2) ,ch0] = dch0[self.SHIFT2:] + iyf2[0:self.SHIFT2]
                    elif ch0 == 1:
                        wavo[sp2 : int(sp2+ self.SHIFT2) ,ch0] = dch1[self.SHIFT2:] + iyf2[0:self.SHIFT2]
                    wavo[int(sp2+ self.SHIFT2) : int(sp2 + self.N2),ch0] = iyf2[self.SHIFT2:]
                else:
                    # combine with window
                    if ch0 == 0:
                        wavo[sp2 : int(sp2+ self.SHIFT2) ,ch0] = dch0[self.SHIFT2:] + iyf2[0:self.SHIFT2]
                    elif ch0 == 1:
                        wavo[sp2 : int(sp2+ self.SHIFT2) ,ch0] = dch1[self.SHIFT2:] + iyf2[0:self.SHIFT2]
                    	
                # copy to backup
                if ch0 == 0:
                    dch0=iyf2.copy()
                elif ch0 == 1:
                    dch1=iyf2.copy()
                    
        print(' ')
        return  np.clip( wavo,-1., 1.) 
    
    
    def evenHANNwindow(self, size0):
        # size0 should be even number.
        # return  a similar to HANN window
        size0_half= int(size0/2)
        x=np.linspace(0, np.pi/2.0, size0_half)
        y=np.square( np.sin(x))
        window=np.concatenate([y,y[::-1]])
        
        if 0:
            for i in range(size0_half):
                print( window[i] + window[size0_half+i])
        return window
        
    
    def plot_COWM(self,):
        from matplotlib import pyplot as plt
        
        
        color_list = ["r", "g", "b", "c", "m", "y", "k", "w"]
        x_time= np.linspace(0, self.N, self.N)
        LNG0=5
        x_timex2= np.linspace(0, self.SHIFT * LNG0, int(self.SHIFT * LNG0))
        x_time2= np.linspace(0, self.N2, self.N2)
        
        fig = plt.figure()
        ax1 = fig.add_subplot(2, 1, 1)
        
        original_win1= self.evenHANNwindow(self.N)
        original_win1st= np.concatenate( [np.ones( self.SHIFT), original_win1[self.SHIFT:] ])
        original_win1last= np.concatenate( [ original_win1[0:self.SHIFT], np.ones( self.SHIFT)])
        
        ax1.plot(x_time, original_win1st, color=color_list[0])
        ax1.plot(x_time+self.SHIFT, original_win1, color=color_list[1])
        ax1.plot(x_time+self.SHIFT*2, original_win1, color=color_list[2])
        ax1.plot(x_time+self.SHIFT*3, original_win1last, color=color_list[3])
        
        ax2 = fig.add_subplot(2, 1, 2)
        y= np.zeros( int(self.SHIFT * LNG0) )
        
        for loop in range(LNG0):
            sp0= int(self.SHIFT * loop) 
            if loop == 0:
            	y[0:self.SHIFT]= original_win1st[0:self.SHIFT]
            elif loop==(LNG0-1):
                y[ sp0: int(sp0+ self.SHIFT)]= original_win1last[self.SHIFT:]
            else:
                y[ sp0: int(sp0+ self.SHIFT)]= original_win1[self.SHIFT:self.N]  + original_win1[0:self.SHIFT]
                
        ax2.plot(x_timex2, y, color=color_list[0])
        ax2.plot(original_win1[self.SHIFT:self.N]  + original_win1[0:self.SHIFT], color=color_list[1] )
        
        
        ax1.grid(which='both', axis='both')
        plt.tight_layout()
        plt.show()
        plt.close()
        
    
    def read_wav(self, file_path ):
        try:
            sr, w = wavread( file_path)
        except:
            print ('error: wavread ', file_path)
            sys.exit()
        else:
            if w.dtype ==  np.int16:
                #print('np.int16')
                w= w / (2 ** 15)
            elif w.dtype ==  np.int32:
                #print('np.int32')
                w= w / (2 ** 31)
            #print ('sampling rate ', sr)
            #print ('size', w.shape) # [xxx,2]
        return w, sr


    def save_wav16(self,  file_path, data, sr=48000):
        amplitude = np.iinfo(np.int16).max
        try:
            wavwrite( file_path , sr, np.array( amplitude * data , dtype=np.int16))
        except:
            print ('error: wavwrite ', file_path)
            sys.exit()
        print ('wrote ', file_path)



if __name__ == '__main__':
    import datetime
    parser = argparse.ArgumentParser(description='WAV file convert sampling rate from 44.1KHz to 48KHz/96KHz')
    parser.add_argument('--input_wav', '-i', default='sample_wav/test_44100Hz.wav', help='specify input wav filename')
    parser.add_argument('--output_wav', '-o', default=None, help='specify output wav filename')
    parser.add_argument('--factor', '-f', type=int, default=1, help='specify 2 when convert to 44.1KHz to 96KHz (defualt 1)')
    parser.add_argument('--output_bit', '-b', type=int, default=16, help='output bit 16 or 24 (defualt 16bit)')
    parser.add_argument('--dir', '-d', default=None, help='specify input wav directory. This is alternative of --output_wav.')
    parser.add_argument('--method', '-m', type=str, default='COWM', help='specify method COWM or SDOM (default COWM) ')
    
    args = parser.parse_args()
    
    # record start time
    dt_now0 = datetime.datetime.now()
    
    if args.dir is not None  and os.path.exists(args.dir):
        flist= glob.glob( os.path.join(args.dir, '*.wav'))
        
        for i,file_path in enumerate(flist):
            # create instance
            conv1= convert441to480(file_path, output_bit=args.output_bit, factor=args.factor, method=args.method)
            # destruct instance
            del conv1
    else: # do once
        # create instance
        conv1= convert441to480(args.input_wav, args.output_wav, output_bit=args.output_bit, factor=args.factor, method=args.method )
    
    # record finish time
    dt_now1 = datetime.datetime.now()
    print ('time ', dt_now1-dt_now0)



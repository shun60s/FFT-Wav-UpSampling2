#coding:utf-8

#
#  stero WAV file convert to 2 times sampling rate 
#--------------------------------------------------------------
#  Using 
# Python 3.6.4, 64bit on Win32 (Windows 10)
# numpy 1.18.4
# scipy 1.4.1
# soundfile 0.10.3
#  ------------------------------------------------------------
# 2023/9/19  add: gain_adjust option: gain up 1,2,or,3 dB until non-clip

import sys
import os
import glob
import copy
import argparse
import numpy as np
from scipy.fftpack import fft, ifft
from scipy.io.wavfile import read as wavread
from scipy.io.wavfile import write as wavwrite




class convert2times(object):
    def __init__(self,path_input_wav, path_output_wav=None , output_bit=16, method="COWM", gain_adjust=False):
        # initalize
        self.wavfile= path_input_wav    # input wav file name
        if path_output_wav is None:
            new_dir= os.path.join(os.path.dirname(self.wavfile), method)
            if not os.path.exists( new_dir):
                os.mkdir( new_dir)
            sufix0='_fx2'
            self.wavfile2= os.path.join(new_dir ,os.path.splitext(os.path.basename(self.wavfile))[0] + sufix0 +  '.wav')
        else:
            self.wavfile2= path_output_wav  # output file name
        
        self.output_bit= output_bit
        
        # FFT point and every shift
        self.N = 4096
        self.SHIFT= int(self.N/2)  # shift must be N/2
        self.N2= int(self.N*2)      # output point is 2 times than input
        self.SHIFT2=int(self.SHIFT * 2)
        
        # read input wav file
        self.wdata, self.fs= self.read_wav( self.wavfile) 
        
        self.stmono= self.wdata.shape[1]
        self.size0= self.wdata.shape[0]
        
        # show WAV information
        print ("sampling rate ", self.fs)
        print ("points ", self.size0)
        
        if self.stmono != 2:
            print ("Sorry, only stereo wav file is available")
            sys.exit()
        
        # count shift number
        self.num0= int((self.size0 - self.N)/ self.SHIFT) + 1
        print ("number ", self.num0)
        
        # process
        self.method= method
        if self.method == "SDOM":
            print ("method", self.method)
            self.wavo= self.sub_main_SDOM()
        elif self.method == "COWM":
            print ("method", self.method)
            self.wavo= self.sub_main_COWM()
        else:
            print ("Error: there is no such method.", self.method )
            sys.exit()
        
        # gain adjustment
        MAX_ADJUST_GAIN=3
        if gain_adjust:
            peak0=np.max(np.abs(self.wavo))
            gain0=0
            for i in range(1,int(MAX_ADJUST_GAIN+1)):  # 1,2,3
                if peak0 * np.power(10, i /20.0) >= 1.0:  # when clip
                    break
                else:   # when non clip
                    gain0=gain0+1
                
            if gain0 > 0:
                self.wavo=self.wavo* np.power(10, gain0 /20.0)
                print("gain up ", gain0, " dB")
            else:
                print("gain no adjust")
        
        # write output wav
        if self.output_bit == 16:
            self.save_wav16(self.wavfile2, self.wavo, int(self.fs * 2))
        elif self.output_bit == 24:
            import soundfile as sf
            sf.write(self.wavfile2, self.wavo, int(self.fs * 2), 'PCM_24')
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
        
        # output data
        wavo=np.zeros( (int(self.size0 * 2), self.stmono) )
        
        for loop in range(self.num0):
            print (" " +  str(loop)+"/" + str(self.num0) +"\r",end="")
            
            sp0= int(self.SHIFT * loop)     # input point
            sp2= int(self.SHIFT * 2 * loop)  # output point is 2 times than input
            
            for ch0 in range( self.stmono ):
                
                # read N points via every SHIFT
                fw1= self.wdata[sp0: int(sp0 + self.N), ch0]
                
                # Fourier transform via FFT
                yf = fft(fw1)
                # 1/N ga kakarukara node *2baisuru,  center Value ha ryouhou ni huru
                yf2=np.concatenate([yf[0:1] , yf[1:N_2], yf[N_2:N_2P1]*0.5, np.zeros(N_M1), yf[N_2:N_2P1]*0.5, yf[N_2+1:N_0] ]) 
                iyf2= ifft(yf2 * 2).real
                
                
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
        
        # make Hann window
        original_win1= self.evenHANNwindow(self.N)
        original_win1st= np.concatenate( [np.ones( self.SHIFT), original_win1[self.SHIFT:] ])
        original_win1last= np.concatenate( [ original_win1[0:self.SHIFT], np.ones( self.SHIFT)])
        
        # output data
        wavo=np.zeros( (int(self.size0 * 2), self.stmono) )
        
        
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
                yf2=np.concatenate([yf[0:1] , yf[1:N_2], yf[N_2:N_2P1]*0.5, np.zeros(N_M1), yf[N_2:N_2P1]*0.5, yf[N_2+1:N_0] ]) 
                iyf2= ifft(yf2 * 2).real
                
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
        
        return window
    
    
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
    parser = argparse.ArgumentParser(description='stero WAV file convert to 2 times sampling rate ')
    parser.add_argument('--input_wav', '-i', default='sample_wav/test_44100Hz.wav', help='specify input wav filename')
    parser.add_argument('--output_wav', '-o', default=None, help='specify output wav filename')
    parser.add_argument('--output_bit', '-b', type=int, default=16, help='output bit 16 or 24 (defualt 16bit)')
    parser.add_argument('--dir', '-d', default=None, help='specify input wav directory. This is alternative of --output_wav')
    parser.add_argument('--method', '-m', type=str, default='COWM', help='specify method COWM or SDOM (default COWM) ')
    parser.add_argument('--gain_adjust', '-a', action='store_true', help='if set true, gain up 1,2, or 3 dB until non-clip')
    args = parser.parse_args()
    
    # record start time
    dt_now0 = datetime.datetime.now()
    #
    if args.dir is not None  and os.path.exists(args.dir):
        flist= glob.glob( os.path.join(args.dir, '*.wav'))
        
        for i,file_path in enumerate(flist):
            # create instance
            conv1= convert2times(file_path, output_bit=args.output_bit, method=args.method, gain_adjust=args.gain_adjust)
            # destruct instance
            del conv1
    else: # do once
    # create instance
        conv1= convert2times(args.input_wav, args.output_wav, output_bit=args.output_bit, method=args.method, gain_adjust=args.gain_adjust)
    
    # record finish time
    dt_now1 = datetime.datetime.now()
    print ('time ', dt_now1-dt_now0)



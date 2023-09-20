#coding:utf-8

#
# A GUI for convert44100to48000.py and convert_2times.py
# by tkinter
#
#--------------------------------------------------------------
#  Using 
# Python 3.10.4, 64bit on Win32 (Windows 10)
# numpy 1.22.3
# scipy 1.8.0
# soundfile 0.10.3
#  -----------
# 2023/9/19  add: gain_adjust option: gain up 1,2,or,3 dB until non-clip

import os
import sys
import glob
import re
import datetime
import argparse
import threading

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter.font import Font

from convert44100to48000 import *
from convert_2times import *


class GUI_App(ttk.Frame):
    def __init__(self, master=None):
        self.frame=ttk.Frame.__init__(self,master)
        #
        #
        self.open_file_init_dir=os.getcwd()
        self.save_file_init_dir=os.getcwd()
        self.open_dir_init_dir= os.getcwd()
        
        self.enable_print = False #True
        #
        self.create_widgets()
        
        # rediect piint out to Text 
        sys.stdout= self.StdoutRedirector(self.text)
    
    
    def create_widgets(self,):
        #######################################################################################
        self.frame1=ttk.Frame(self.frame)
        
        # Label
        gyou=0
        self.label0= ttk.Label(self.frame1, text='- This is a GUI for convert44100to48000.py and convert_2times.py. -',width=85)
        self.label0.grid(row=gyou, column=0)
        
        self.frame1.pack()
        
        #######################################################################################
        
        self.frame2=ttk.Frame(self.frame)
        # Combobox
        gyou=0
        self.label1= ttk.Label(self.frame2, text='converter',width=30)
        
        self.value0=['convert from 44.1kHz to 48kHz', 'conver from 44.1kHz to 96kHz', 'convert to 2 times sampling rate']
        self.combo_v0 = StringVar()
        self.cb0 = ttk.Combobox(self.frame2, textvariable=self.combo_v0, values=self.value0, width=30)
        self.cb0.set(self.value0[0])
        if self.enable_print:
            self.cb0.bind('<<ComboboxSelected>>', lambda e: print('converter=%s' % self.combo_v0.get()))
        
        self.label1.grid(row=gyou, column=0)
        self.cb0.grid(row=gyou, column=1)
        
        self.frame2.pack(fill = X)
        
        #######################################################################################
        
        self.frame3=ttk.Frame(self.frame)
        
        # open file/ dir
        
        gyou=0
        openfile_buttonb1 = ttk.Button(self.frame3, text='load wav file', width=20, command=self.open_file_button1_clicked)
        openfile_buttonb1.grid(row=gyou, column=0, sticky=(W))
        self.openfile1= StringVar()
        self.openfile1.set('')
        openfile_button1_l2 = ttk.Label(self.frame3, textvariable=self.openfile1)
        openfile_button1_l2.grid(row=gyou, column=1)
        
        gyou=gyou+1
        self.label22= ttk.Label(self.frame3, text="automatically assigned if save file name is empty.")
        self.label22.grid(row=gyou, column=0)
        gyou=gyou+1
        savefile_buttonb1 = ttk.Button(self.frame3, text='save file name', width=20, command=self.save_file_button1_clicked)
        savefile_buttonb1.grid(row=gyou, column=0, sticky=(W))
        self.savefile1= StringVar()
        self.savefile1.set('')
        savefile_button1_l2 = ttk.Label(self.frame3, textvariable=self.savefile1)
        savefile_button1_l2.grid(row=gyou, column=1)
        
        gyou=gyou+1
        self.label21= ttk.Label(self.frame3, text='load wav directory takes priority to load wav file.')
        self.label21.grid(row=gyou, column=0)
        
        gyou=gyou+1
        opendir_buttonb1 = ttk.Button(self.frame3, text='load wav directory', width=20, command=self.open_dir_button1_clicked)
        opendir_buttonb1.grid(row=gyou, column=0, sticky=(W))
        self.opendir1= StringVar()
        self.opendir1.set('')
        opendir_button1_l2 = ttk.Label(self.frame3, textvariable=self.opendir1)
        opendir_button1_l2.grid(row=gyou, column=1)
        
        self.frame3.pack(fill = X)
        #######################################################################################
        
        self.frame4=ttk.Frame(self.frame)
        # Radiobutton 1
        gyou=0
        self.label2= ttk.Label(self.frame4, text='output witdh bit',width=30)
        
        self.bit1 = StringVar()
        self.bit1_rb1 = ttk.Radiobutton(self.frame4, text='16',value='16', variable=self.bit1, width=10)
        self.bit1_rb2 = ttk.Radiobutton(self.frame4, text='24',value='24', variable=self.bit1, width=10)
        self.bit1.set('16')
        self.label2.grid(row=gyou, column=0)
        self.bit1_rb1.grid(row=gyou, column=1)
        self.bit1_rb2.grid(row=gyou, column=2)
        
        # Radiobutton 2
        gyou=gyou+1 
        self.label3= ttk.Label(self.frame4, text='method', width=30)
        
        self.method1 = StringVar()
        self.method1_rb1 = ttk.Radiobutton(self.frame4, text='COWM',value='COWM', variable=self.method1, width=10)
        self.method1_rb2 = ttk.Radiobutton(self.frame4, text='SDOM',value='SDOM', variable=self.method1, width=10)
        self.method1.set('COWM')
        self.label3.grid(row=gyou, column=0)
        self.method1_rb1.grid(row=gyou, column=1)
        self.method1_rb2.grid(row=gyou, column=2)
        
        # Radiobutton 3
        gyou=gyou+1
        self.label5= ttk.Label(self.frame4, text='gain adjust',width=30)
        
        self.gain1 = StringVar()
        self.gain1_rb1 = ttk.Radiobutton(self.frame4, text='OFF',value='OFF', variable=self.gain1, width=10)
        self.gain1_rb2 = ttk.Radiobutton(self.frame4, text='ON',value='ON', variable=self.gain1, width=10)
        self.gain1.set('OFF')
        self.label5.grid(row=gyou, column=0)
        self.gain1_rb1.grid(row=gyou, column=1)
        self.gain1_rb2.grid(row=gyou, column=2)
        
        self.frame4.pack(fill = X)
        #######################################################################################
        
        self.frame6=ttk.Frame(self.frame)
        # button
        gyou=0
        self.button1 = ttk.Button(self.frame6, text='start convert', width = 20, command=self.button1_clicked)
        self.button1.grid(row=gyou, column=0)
        #self.button1.pack(side=LEFT)
        self.frame6.pack(fill = X)
        
        
        #######################################################################################
        self.frame7=ttk.Frame(self.frame)
        # text
        gyou=0
        f = Font(family='Helvetica', size=8)
        tv1 = StringVar()
        self.text = Text(self.frame7, height=10, width=80)
        self.text.configure(font=f)
        self.text.grid(row=gyou, column=0, sticky=(N, W, S, E))
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame7, orient=VERTICAL, command=self.text.yview)
        self.text['yscrollcommand'] = scrollbar.set
        scrollbar.grid(row=gyou, column=1, sticky=(N, S))
        
        
        self.frame7.pack(side=LEFT)
        #######################################################################################
        
        
    def open_file_button1_clicked(self,):
        file_name = filedialog.askopenfilename(filetypes = [("WAV", ".wav")], initialdir=self.open_file_init_dir)
        if file_name:
            self.openfile1.set(file_name)
            self.open_file_init_dir= os.path.dirname(file_name)
            if self.enable_print:
                print ('openfile ', self.openfile1.get())
        
        
    def save_file_button1_clicked(self,):
        file_name = filedialog.asksaveasfilename(filetypes = [("WAV", ".wav")],initialdir=self.save_file_init_dir, defaultextension = "wav")
        if file_name:
            self.savefile1.set(file_name)
            self.save_file_init_dir= os.path.dirname(file_name)
            if self.enable_print:
                print ('savefile ', self.savefile1.get())

        
    def open_dir_button1_clicked(self,):
        file_dir = filedialog.askdirectory(initialdir=self.open_dir_init_dir)
        if file_dir:
            self.opendir1.set(file_dir)
            self.open_dir_init_dir= file_dir
            if self.enable_print:
                print ('opendir ', self.opendir1.get())
        
        
    def button1_clicked(self,):
        #
        self.button1['text']=('in process')
        self.button1.configure(state=DISABLED)
        self.text.delete('1.0','end') # clear TEXT BOX AT ONCE
        if self.enable_print:
            print ('button1 was clicked')
            print ('openfile', self.openfile1.get())
            print ('savefile', self.savefile1.get())
            print ('opendir', self.opendir1.get())
            print ('output witdth bit', self.bit1.get())
            print ('method', self.method1.get())
            print ('gain adjust', self.gain1.get())
        
        # call as a callback
        self.callback1()
        
        
    def process1(self,):
        #
        # check if gain adjust
        if self.gain1.get() == "ON":
            self.gain_adjust=True
        else:
            self.gain_adjust=False
        
        # record start time
        dt_now0 = datetime.datetime.now()
        if self.opendir1.get() != ""  and os.path.exists(self.opendir1.get()):
            flist= glob.glob( os.path.join(self.opendir1.get(), '*.wav'))
            
            for i,file_path in enumerate(flist):
                # create instance
                if self.combo_v0.get() == self.value0[0]:
                    conv1= convert441to480(file_path, factor=1, output_bit=int(self.bit1.get()), method=self.method1.get(), gain_adjust=self.gain_adjust)
                elif self.combo_v0.get() == self.value0[1]:
                    conv1= convert441to480(file_path, factor=2, output_bit=int(self.bit1.get()), method=self.method1.get(), gain_adjust=self.gain_adjust)
                elif self.combo_v0.get() == self.value0[2]:
                    conv1= convert2times(file_path, output_bit=int(self.bit1.get()), method=self.method1.get(),  gain_adjust=self.gain_adjust)
                # destruct instance
                del conv1
        
        else: # do once
            if self.openfile1.get() != "":
                if  self.savefile1.get() == "":
                    savefile0= None
                else:
                    savefile0=self.savefile1.get()
                    
                # create instance
                if self.combo_v0.get() == self.value0[0]:
                    conv1= convert441to480(self.openfile1.get(), savefile0, factor=1, output_bit=int(self.bit1.get()), method=self.method1.get(), gain_adjust=self.gain_adjust)
                elif self.combo_v0.get() == self.value0[1]:
                    conv1= convert441to480(self.openfile1.get(), savefile0, factor=2, output_bit=int(self.bit1.get()), method=self.method1.get(), gain_adjust=self.gain_adjust)
                elif self.combo_v0.get() == self.value0[2]:
                    conv1= convert2times(self.openfile1.get(), savefile0, output_bit=int(self.bit1.get()), method=self.method1.get(), gain_adjust=self.gain_adjust)
                del conv1
            
        # record finish time
        dt_now1 = datetime.datetime.now()
        print ('time ', dt_now1-dt_now0)
        
        self.button1.configure(state=NORMAL)
        self.button1['text']=('start convert')



    def callback1(self,):
        th = threading.Thread(target=self.process1, )
        th.start()




    class IORedirector(object):
        def __init__(self, text_area):
            self.text_area = text_area
            self.line_flag = False
            
    class StdoutRedirector(IORedirector):
        def write(self,st):
            if 1: # esc-r
                # check if there is num/num in st
                if re.search(r' \d+/\d+',st) is not None:
                    #
                    if not self.line_flag:  # start...
                        self.text_area.insert('end',  st)
                        self.text_area.insert('end', "\n") # make index up
                        self.line_flag=True
                    else:
                        # delete last 1 line 
                        self.text_area.delete("end-2l", "end-1l")
                        #
                        self.text_area.insert('end', st)
                        self.text_area.insert('end', "\n") # make index up
                else:
                    #self.text_area.insert('end', pos +'>' + st)
                    self.text_area.insert('end',  st )
                    if st != "":
                        self.line_flag = False  # reset line_flag
            else:
                self.text_area.insert('end',  st)
            
            self.text_area.see("end")
        
        
        def flush(self):
            pass



sys.stdout= sys.__stdout__


if __name__ == '__main__':
    #
    root = Tk()
    root.title('sampling rate converter')
    
    app=GUI_App(master=root)
    app.mainloop()
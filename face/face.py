#!/usr/bin/env python3
version = '1.5.0'
# python face.py
# Dec 4 2007
# Face G-Code Generator for LinuxCNC
"""
    Copyright (C) <2008>  <John Thornton>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    e-mail me any suggestions to "jet1024 at semo dot net"
    If you make money using this software
    you must donate $20 USD to a local food bank
    or the food police will get you! Think of others from time to time...
    To make it a menu item in Ubuntu use the Alacarte Menu Editor and add 
    the command python YourPathToThisFile/face.py
    make sure you have made the file execuatble by right
    clicking and selecting properties then Permissions and Execute

    To use with LinuxCNC see the instructions at: 
    https://github.com/linuxcnc/simple-gcode-generators

2008-02-24	Rick Calder "rick at llamatrails dot com"
	Added option/code to select X0-Y0 position: Left-Rear or Left-Front
	To change the default, change line 171: 4=Left-Rear, 5=Left-Front
	
2010-01-06	Brad Hanken "chembal at gmail dot com"
	Added option and code to change the lead in and lead out amount
	If nothing is entered, the old calculated value of tool radius + .1 is still used

2012-07-13 John Thornton
  Added graceful exit from face.py if opened in Axis

2018-12-30 Aglef Kaiser
	Added load and save preferences (all attributes). The default NC File directory
	is the home directory. After saving a gcode file, this directory is the new
	NC File directory and can be saved with save preferences.
	Added safe z hight.
"""
import os
import sys
import tkinter.messagebox
from configparser import *
from decimal import *
from math import *
from tkinter import *
from tkinter.filedialog import *
from tkinter.simpledialog import *

IN_AXIS = 'AXIS_PROGRESS_BAR' in os.environ

class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master, width=700, height=400, bd=1)
        self.grid()
        self.createMenu()
        self.createWidgets()
        self.LoadPrefs()


    def createMenu(self):
        #Create the Menu base
        self.menu = Menu(self)
        #Add the Menu
        self.master.config(menu=self.menu)
        #Create our File menu
        self.FileMenu = Menu(self.menu)
        #Add our Menu to the Base Menu
        self.menu.add_cascade(label='File', menu=self.FileMenu)
        #Add items to the menu
        self.FileMenu.add_command(label='New', command=self.ClearTextBox)
        self.FileMenu.add_command(label='Open', command=self.Simple)
        self.FileMenu.add_separator()
        self.FileMenu.add_command(label='Quit', command=self.quit)
        
        self.EditMenu = Menu(self.menu)
        self.menu.add_cascade(label='Edit', menu=self.EditMenu)
        self.EditMenu.add_command(label='Copy', command=self.CopyClpBd)
        self.EditMenu.add_command(label='Select All', command=self.SelectAllText)
        self.EditMenu.add_command(label='Delete All', command=self.ClearTextBox)
        self.EditMenu.add_separator()
        self.EditMenu.add_command(label='Save Preferences', command=self.SavePrefs)
        self.EditMenu.add_command(label='Load Preferences', command=self.LoadPrefs)
        
        self.HelpMenu = Menu(self.menu)
        self.menu.add_cascade(label='Help', menu=self.HelpMenu)
        self.HelpMenu.add_command(label='Help Info', command=self.HelpInfo)
        self.HelpMenu.add_command(label='About', command=self.HelpAbout)

    def createWidgets(self):
        row = 0
        column=0
 
        self.spacer1 = Label(self, text='')
        self.spacer1.grid(row=row, column=column)      
        column += 1
              
        self.st1 = Label(self, text='Part Length X * ')
        self.st1.grid(row=row, column=column, sticky=E)
        self.PartLengthVar = StringVar()
        self.PartLength = Entry(self, width=10, textvariable=self.PartLengthVar)
        self.PartLength.grid(row=row, column=column+1, sticky=W)
        self.PartLength.focus_set()
        column += 2

        self.spacer2 = Label(self, text='')
        self.spacer2.grid(row=row, column=column)      
        column += 1
              
        self.g_code = Text(self,width=30,height=30,bd=3)
        self.g_code.grid(row=row, column=column, sticky=E+W+N+S)
        self.tbscroll = Scrollbar(self,command = self.g_code.yview)
        self.tbscroll.grid(row=row, column=column+1, sticky=N+S+W)
        self.g_code.configure(yscrollcommand = self.tbscroll.set) 
        column += 2
        row += 1

        column=1
        self.st2 = Label(self, text='Part/Cut Width Y * ')
        self.st2.grid(row=row, column=column, sticky=E)
        self.PartWidthVar = StringVar()
        self.PartWidth = Entry(self, width=10, textvariable=self.PartWidthVar)
        self.PartWidth.grid(row=row, column=column+1, sticky=W)
        column += 2
        row += 1

        column=1
        self.st5 = Label(self, text='Total Z Depth * ')
        self.st5.grid(row=row, column=column, sticky=E)
        self.TotalToRemoveVar = StringVar()
        self.TotalToRemove = Entry(self, width=10, textvariable=self.TotalToRemoveVar)
        self.TotalToRemove.grid(row=row, column=column+1, sticky=W)
        column += 2
        row += 1

        column=1
        self.st3 = Label(self, text='Tool Diameter ')
        self.st3.grid(row=row, column=column, sticky=E)
        self.ToolDiameterVar = StringVar()
        self.ToolDiameter = Entry(self, width=10, textvariable=self.ToolDiameterVar)
        self.ToolDiameter.grid(row=row, column=column+1, sticky=W)
        column += 2       
        row += 1

        column=1
        self.st4 = Label(self, text='Feedrate ')    
        self.st4.grid(row=row, column=column, sticky=E)
        self.FeedrateVar = StringVar()
        self.Feedrate = Entry(self, width=10, textvariable=self.FeedrateVar)
        self.Feedrate.grid(row=row, column=column+1, sticky=W)
        column += 2
        row += 1

        column=1
        self.st6 = Label(self, text='Depth of Each Cut ')
        self.st6.grid(row=row, column=column, sticky=E)
        self.DepthOfCutVar = StringVar()
        self.DepthOfCut = Entry(self, width=10, textvariable=self.DepthOfCutVar)
        self.DepthOfCut.grid(row=row, column=column+1, sticky=W)
        column += 2
        row += 1
 
        column=1
        self.st4a = Label(self, text='M3 Spindle RPM ')
        self.st4a.grid(row=row, column=column, sticky=E)
        self.SpindleRPMVar = StringVar()
        self.SpindleRPM = Entry(self, width=10, textvariable=self.SpindleRPMVar)
        self.SpindleRPM.grid(row=row, column=column+1, sticky=W)
        column += 2
        row += 1

        column=1
        self.st7 = Label(self, text='Stepover (Value or %) ')
        self.st7.grid(row=row, column=column, sticky=E)
        self.StepOverVar = StringVar()
        self.StepOver = Entry(self, width=10, textvariable=self.StepOverVar)
        self.StepOver.grid(row=row, column=column+1, sticky=W)
        column += 2        
        row += 1

        column=1
        self.st10 = Label(self, text='Safe Z height ')
        self.st10.grid(row=row, column=column, sticky=E)
        self.SafeZVar = StringVar()
        self.Leadin = Entry(self, width=10, textvariable=self.SafeZVar)
        self.Leadin.grid(row=row, column=column+1, sticky=W)
        column += 2        
        row += 1

        column=1
        self.st8 = Label(self, text='Lead In / Lead Out ')
        self.st8.grid(row=row, column=column, sticky=E)
        self.LeadinVar = StringVar()
        self.Leadin = Entry(self, width=10, textvariable=self.LeadinVar)
        self.Leadin.grid(row=row, column=column+1, sticky=W)
        column += 2        
        row += 1

        column=1
        self.st8=Label(self,text='Units')
        self.st8.grid(row=row,column=column)
        UnitOptions=[('Inch',1),('MM',2)]
        self.UnitVar=StringVar()
        for text, y in UnitOptions:
            Radiobutton(self, text=text,value=text,
                variable=self.UnitVar,indicatoron=0,width=6,)\
                .grid(row=row+y, column=column)
        self.UnitVar.set('Inch')
        column += 1
           
        self.st12=Label(self,text='Cut Along')
        self.st12.grid(row=row,column=column)
        AxisOptions=[('X-Axis',1),('Y-Axis',2)]
        self.AxisVar=StringVar()
        for text, x in AxisOptions:
            Radiobutton(self, text=text,value=text,
                variable=self.AxisVar,indicatoron=0,width=11,)\
                .grid(row=row+x, column=column)
        self.AxisVar.set('X-Axis')
        column += 1
        row += 3

        column=1
        self.st11=Label(self,text='Mill Mode')
        self.st11.grid(row=row,column=column)
        MillOptions=[('Both',1),('Conventional',2),('Climb',3)]
        self.MillVar=StringVar()
        for text, y in MillOptions:
            Radiobutton(self, text=text,value=text,
                variable=self.MillVar,indicatoron=0,width=11,)\
                .grid(row=row+y, column=column)
        self.MillVar.set('Both')
        column += 1
              
        self.st13=Label(self,text='Finish Mode')
        self.st13.grid(row=row,column=column)
        FinishOptions=[('Exact',1),('Extra',2),('Spring',3)]
        self.FinishVar=StringVar()
        for text, y in FinishOptions:
            Radiobutton(self, text=text,value=text,
                variable=self.FinishVar,indicatoron=0,width=11,)\
                .grid(row=row+y, column=column)
        self.FinishVar.set('Exact')
        column += 1              
        row += 4

        column=1
        self.st9=Label(self,text='Start At X0-Y0')
        self.st9.grid(row=row,column=column,columnspan=2)
        HomeOptions=[('Left-Rear',0,1,E+S),('Left-Front',0,2,E+N),('Right-Rear',1,1,W+S),('Right-Front',1,2,W+N)]
        self.HomeVar=StringVar()
        for text, x, y, sticky in HomeOptions:
            Radiobutton(self, text=text,value=text,
                variable=self.HomeVar,indicatoron=0,width=11,)\
                .grid(row=row+y, column=column+x, sticky=sticky)
        self.HomeVar.set('Left-Rear')
        column += 1               
        row += 3

        column=1
        self.sp4 = Label(self)
        self.sp4.grid(row=row)        
        row += 1

        column=1
        self.GenButton = Button(self, text='Generate G-Code',command=self.GenCode)
        self.GenButton.grid(row=row, column=column)
        column += 1
        
        self.CopyButton = Button(self, text='Select All & Copy',command=self.SelectCopy)
        self.CopyButton.grid(row=row, column=column)
        column += 1        
        row += 1

        column=1
        self.WriteButton = Button(self, text='Write to File',command=self.WriteToFile)
        self.WriteButton.grid(row=row, column=column)
        column += 1

        self.ClearButton = Button(self, text='Clear',command=self.ClearCode)
        self.ClearButton.grid(row=row, column=column)
        column += 1
        row += 1

        column=1
        if IN_AXIS:
            self.toAxis = Button(self, text='Write to AXIS and Quit',\
                command=self.WriteToAxis)
            self.toAxis.grid(row=row, column=column)
            column += 1
        
            self.quitButton = Button(self, text='Quit', command=self.QuitFromAxis)
            self.quitButton.grid(row=row, column=column, sticky=E)
            column += 1
        else:

            self.quitButton = Button(self, text='Quit', command=self.quit)
            self.quitButton.grid(row=row, column=column, sticky=E)    
            column += 1
        self.g_code.grid(rowspan = row - self.g_code.grid_info()['row'] + 1)
        self.tbscroll.grid(rowspan = self.g_code.grid_info()['rowspan'])

    def QuitFromAxis(self):
        sys.stdout.write("M2 (Face.py Aborted)")
        self.quit()

    def WriteToAxis(self):
        sys.stdout.write(self.g_code.get(0.0, END))
        self.quit()

    def GenCode(self):
        """ Generate the G-Code for facing a part 
        assume that the part is at X0 to X+, Y0 to Y-"""
        D=Decimal
        z=float(self.SafeZVar.get())
        # Calculate the start position 1/2 the tool diameter + 0.100 in X and Stepover in Y
        self.ToolRadius = self.FToD(self.ToolDiameterVar.get())/2
        if len(self.LeadinVar.get())>0:
            self.LeadIn = self.FToD(self.LeadinVar.get())
        else:
            self.LeadIn = self.ToolRadius + D('0.1')
        self.Cut_Start = -(self.LeadIn)
        self.Cut_End = self.FToD(self.PartLengthVar.get()) + self.LeadIn
        self.DefaultMillMode = 'Climb'
        if ('Right' in self.HomeVar.get() and self.AxisVar.get() == 'X-Axis') or \
           ('Rear' in self.HomeVar.get() and self.AxisVar.get() == 'Y-Axis'):
           self.Cut_Dir = -1
        else:
           self.Cut_Dir = 1
        # real position, for use in Gcode
        self.Cut_Start_R = self.Cut_Start * self.Cut_Dir 
        self.Cut_End_R = self.Cut_End * self.Cut_Dir 
 
        if (self.HomeVar.get() in ['Right-Rear', 'Left-Front'] and self.AxisVar.get() == 'X-Axis') or \
           (self.HomeVar.get() in ['Left-Rear', 'Right-Front'] and self.AxisVar.get() == 'Y-Axis'):
           self.DefaultMillMode = 'Conventional'

        if len(self.StepOverVar.get())>0:
            if self.StepOverVar.get().endswith('%'):
                self.Step_Stepover = (self.FToD(self.ToolDiameterVar.get())\
                    * self.FToD(self.StepOverVar.get().rstrip('%'))/100)
            else:
                self.Step_Stepover = self.FToD(self.StepOverVar.get())
        else:
            self.Step_Stepover = self.FToD(self.ToolDiameterVar.get())*D('.5')
        
        self.NumOfSteps = int(ceil(self.FToD(self.PartWidthVar.get())/self.Step_Stepover))
        self.Step_Start = self.Step_Stepover - self.ToolRadius
        self.Step_End = self.FToD(self.PartWidthVar.get()) - self.ToolRadius
        if self.FinishVar.get() == 'Extra':
            self.Step_End += 0.1
        if ('Rear' in self.HomeVar.get() and self.AxisVar.get() == 'X-Axis') or \
           ('Right' in self.HomeVar.get() and self.AxisVar.get() == 'Y-Axis'):
            self.Step_Dir = -1
        else:
            self.Step_Dir = 1
        # real position, for use in Gcode
        self.Step_Start_R = self.Step_Start * self.Step_Dir 
        self.Step_End_R = self.Step_End * self.Step_Dir 
        
        self.Z_Total = self.FToD(self.TotalToRemoveVar.get())
        if len(self.DepthOfCutVar.get())>0:
            self.Z_Step = self.FToD(self.DepthOfCutVar.get())
            self.NumOfZSteps = int(self.FToD(self.TotalToRemoveVar.get()) / self.Z_Step)
            if self.Z_Total % self.Z_Step > 0:
                self.NumOfZSteps = self.NumOfZSteps + 1
        else:
            self.Z_Step = 0
            self.NumOfZSteps = 1
        self.Z_Position = 0
        if self.AxisVar.get() == 'X-Axis':
            self.Cut_Axis = 'X'
            self.Step_Axis = 'Y'
        else:
            self.Cut_Axis = 'Y'
            self.Step_Axis = 'X'

        # Generate the G-Codes
        if self.UnitVar.get()=="Inch":
            self.g_code.insert(END, 'G20 ')
        else:
            self.g_code.insert(END, 'G21 ')
        if len(self.SpindleRPMVar.get())>0:
            self.g_code.insert(END, 'S%i ' %(self.FToD(self.SpindleRPMVar.get())))
            self.g_code.insert(END, 'M3 ')
        if len(self.FeedrateVar.get())>0:
            self.g_code.insert(END, 'F%s\n' % (self.FeedrateVar.get()))
        for i in range(self.NumOfZSteps):
            self.g_code.insert(END, 'G0 %s%.4f %s%.4f\nZ%.4f\n' \
                %(self.Cut_Axis, self.Cut_Start_R, self.Step_Axis, self.Step_Start_R,z))
            # Make sure the Z position does not exceed the total depth
            if self.Z_Step>0 and (self.Z_Total+self.Z_Position) >= self.Z_Step:
                self.Z_Position = self.Z_Position - self.Z_Step
            else:
                self.Z_Position = -self.Z_Total
            
            self.g_code.insert(END, '(Pass %d)\n' % (i))
            self.g_code.insert(END, 'G1 Z%.4f\n' % (self.Z_Position))
            self.Cut_Position = self.Cut_Start
            self.Step_Position = self.Step_Start

            for j in range(self.NumOfSteps):
                self.g_code.insert(END, '(Step %d Y=%.4f)\n' % (j,self.Step_Position))
                # Insert rapids of we care about direction
                if self.MillVar.get() != 'Both':
                    if self.MillVar.get() != self.DefaultMillMode and self.Cut_Position == self.Cut_Start:
                        self.g_code.insert(END, 'G0 Z%.4f\n' % z)
                        self.g_code.insert(END, 'G0 %s%.4f\n' % (self.Cut_Axis, self.Cut_End_R))
                        self.g_code.insert(END, 'G1 Z%.4f\n' % self.Z_Position)
                        self.Cut_Position = self.Cut_End                        
                    elif self.MillVar.get() == self.DefaultMillMode and self.Cut_Position == self.Cut_End:
                        self.g_code.insert(END, 'G0 Z%.4f\n' % z)
                        self.g_code.insert(END, 'G0 %s%.4f\n' % (self.Cut_Axis, self.Cut_Start_R))
                        self.g_code.insert(END, 'G1 Z%.4f\n' % self.Z_Position)
                        self.Cut_Position = self.Cut_Start

                if self.Cut_Position == self.Cut_Start: 
                    self.g_code.insert(END, 'G1 %s%.4f\n' % (self.Cut_Axis, self.Cut_End_R))
                    self.Cut_Position = self.Cut_End
                else:
                    self.g_code.insert(END, 'G1 %s%.4f\n' % (self.Cut_Axis, self.Cut_Start_R))
                    self.Cut_Position = self.Cut_Start

                if self.Step_Position == self.Step_End:
                    break

                self.Step_Position += self.Step_Stepover

                if self.Step_Position > self.Step_End:
                    self.Step_Position = self.Step_End

                self.g_code.insert(END, 'G0 %s%.4f\n' % (self.Step_Axis, self.Step_Position * self.Step_Dir))
 
        # add a climb cut spring pass
        if self.FinishVar.get() == 'Spring':
            self.g_code.insert(END, '(Climbing Spring Pass)\n')
            # Get to the right end for a climb cut
            if self.DefaultMillMode == 'Conventional' and self.Cut_Position == self.Cut_Start:
                self.g_code.insert(END, 'G0 Z%.4f\n' % z)
                self.g_code.insert(END, 'G0 %s%.4f\n' % (self.Cut_Axis, self.Cut_End_R))
                self.g_code.insert(END, 'G1 Z%.4f\n' % self.Z_Position)
                self.Cut_Position = self.Cut_End                        
            elif self.DefaultMillMode == 'Climb' and self.Cut_Position == self.Cut_End:
                self.g_code.insert(END, 'G0 Z%.4f\n' % z)
                self.g_code.insert(END, 'G0 %s%.4f\n' % (self.Cut_Axis, self.Cut_Start_R))
                self.g_code.insert(END, 'G1 Z%.4f\n' % self.Z_Position)
                self.Cut_Position = self.Cut_Start
            if self.Cut_Position == self.Cut_Start: 
                self.g_code.insert(END, 'G1 %s%.4f\n' % (self.Cut_Axis, self.Cut_End_R))
                self.Cut_Position = self.Cut_End
            else:
                self.g_code.insert(END, 'G1 %s%.4f\n' % (self.Cut_Axis, self.Cut_Start_R))
                self.Cut_Position = self.Cut_Start

        self.g_code.insert(END, 'G0 Z%.4f\n'% z)
        if len(self.SpindleRPMVar.get())>0:
            self.g_code.insert(END, 'M5\n')
        self.g_code.insert(END, 'G0 X0.0000 Y0.0000\nM2 (End of File)\n')

    def ClearCode(self):
        """
        Clears the g_code box
        """
        self.g_code.delete(1.0, END)

    def FToD(self,s): # Float To Decimal
        """
        Returns a decimal with 4 place precision
        valid imputs are any fraction, whole number space fraction
        or decimal string. The input must be a string!
        """
        s=s.strip(' ') # remove any leading and trailing spaces
        D=Decimal # Save typing
        P=D('0.0001') # Set the precision wanted
        if ' ' in s: # if it is a whole number with a fraction
            w,f=s.split(' ',1)
            w=w.strip(' ') # make sure there are no extra spaces
            f=f.strip(' ')
            n,d=f.split('/',1)
            return D(D(n)/D(d)+D(w)).quantize(P)
        elif '/' in s: # if it is just a fraction
            n,d=s.split('/',1)
            return D(D(n)/D(d)).quantize(P)
        return D(s).quantize(P) # if it is a decimal number already
        
    def GetDirectory(self):
        self.DirName = askdirectory(initialdir='/home',title='Please select a directory')
        if len(self.DirName) > 0:
            return self.DirName 
       
    def CopyClpBd(self):
        self.g_code.clipboard_clear()
        self.g_code.clipboard_append(self.g_code.get(0.0, END))

    def WriteToFile(self):
        self.NewFileName = asksaveasfile(initialdir=self.NcDir,mode='w', \
		master=self.master,title='Create NC File',defaultextension='.ngc')
        self.NcDir=os.path.dirname(self.NewFileName.name)
        self.NewFileName.write(self.g_code.get(0.0, END))
        self.NewFileName.close()

    def LoadPrefs(self):
        self.cp=ConfigParser()
        self.cp.read('face.ini')
        self.NcDir=self.cp.get('Directories','NcFiles',fallback=os.path.expanduser("~"))
        self.FeedrateVar.set(self.cp.get('MillingPara','Feedrate',fallback='1000'))
        self.DepthOfCutVar.set(self.cp.get('MillingPara','DepthOfCut',fallback='3'))
        self.ToolDiameterVar.set(self.cp.get('MillingPara','ToolDiameter',fallback='10'))
        self.SpindleRPMVar.set(self.cp.get('MillingPara','SpindleRPM',fallback='9000'))
        self.StepOverVar.set(self.cp.get('MillingPara','StepOver',fallback='50%'))
        self.LeadinVar.set(self.cp.get('MillingPara','Leadin',fallback=''))
        self.UnitVar.set(self.cp.get('MillingPara','UnitVar',fallback='Inch'))
        self.HomeVar.set(self.cp.get('MillingPara','HomeVar',fallback='Left-Rear'))
        self.MillVar.set(self.cp.get('MillingPara','MillVar',fallback='Both'))
        self.AxisVar.set(self.cp.get('MillingPara','AxisVar',fallback='X-Axis'))
        self.FinishVar.set(self.cp.get('MillingPara','FinishVar',fallback='Exact'))
        self.SafeZVar.set(self.cp.get('MillingPara','SafeZ',fallback='1.0'))
        self.PartLengthVar.set(self.cp.get('Part','X',fallback=''))
        self.PartWidthVar.set(self.cp.get('Part','Y',fallback=''))
        self.TotalToRemoveVar.set(self.cp.get('Part','TotalToRemove',fallback=''))

    def SavePrefs(self):
        def set_pref(SectionName,OptionName,OptionData):
            self.cp[SectionName][OptionName] = OptionData

        set_pref('Directories','NcFiles',self.NcDir)
        set_pref('MillingPara','Feedrate',self.FeedrateVar.get())
        set_pref('MillingPara','DepthOfCut',self.DepthOfCutVar.get())
        set_pref('MillingPara','ToolDiameter',self.ToolDiameterVar.get())
        set_pref('MillingPara','SpindleRPM',self.SpindleRPMVar.get())
        set_pref('MillingPara','StepOver',self.StepOverVar.get().replace('%','%%'))
        set_pref('MillingPara','Leadin',self.LeadinVar.get())
        set_pref('MillingPara','UnitVar',self.UnitVar.get())
        set_pref('MillingPara','HomeVar',self.HomeVar.get())
        set_pref('MillingPara','MillVar',self.MillVar.get())
        set_pref('MillingPara','AxisVar',self.AxisVar.get())
        set_pref('MillingPara','FinishVar',self.FinishVar.get())
        set_pref('MillingPara','SafeZ',self.SafeZVar.get())
        set_pref('Part','X',self.PartLengthVar.get())
        set_pref('Part','Y',self.PartWidthVar.get())
        set_pref('Part','TotalToRemove',self.TotalToRemoveVar.get())
        self.cp.write(open('face.ini', 'w'))
 	
    def Simple(self):
        tkinter.messagebox.showinfo('Feature', 'Sorry this Feature has\nnot been programmed yet.')

    def ClearTextBox(self):
        self.g_code.delete(1.0,END)

    def SelectAllText(self):
        self.g_code.tag_add(SEL, '1.0', END)

    def SelectCopy(self):
        self.SelectAllText()
        self.CopyClpBd()

    def HelpInfo(self):
        tkinter.simpledialog(self,
            text='Required fields are:\n'
            'Part Width & Length,\n'
            'Amount to Remove,\n'
            'and Feedrate\n'
            'Fractions can be entered in most fields',
            buttons=['Ok'],
            default=0,
            title='User Info').go()
    def HelpAbout(self):
        tkinter.messagebox.showinfo('Help About', 'Programmed by\n'
            'Big John T (AKA John Thornton)\n'
            'Rick Calder\n'
            'Brad Hanken\n'
            'Aglef Kaiser\n'
            'Version ' + version)




app = Application()
app.master.title('Facing G-Code Generator Version ' + version)
app.mainloop()


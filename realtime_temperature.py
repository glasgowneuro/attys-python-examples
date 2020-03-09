#!/usr/bin/python3
"""
Plots both channels of the Attys in two different windows. Requires pyqtgraph.

"""

import threading
from time import sleep
import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

import numpy as np

import pyattyscomm as c

# create a global QT application object
app = QtGui.QApplication(sys.argv)

ch1 = c.AttysComm.INDEX_Analogue_channel_1
ch2 = c.AttysComm.INDEX_Analogue_channel_2

# Offset of channel 1 (thermocouple) in V
# This is the voltage measures if short circuited.
ch1Offset = 0.0006

# signals to all threads in endless loops that we'd like to run these
running = True

class QtTemperaturePlot:

    def __init__(self):
        self.lock = threading.Lock()
        self.hot = 20
        self.cold = 20
        self.bufferlen = 1000
        self.plt = pg.PlotWidget()
        self.plt.setYRange(0,1000)
        self.plt.setXRange(0,self.bufferlen/250)
        self.plt.setLabel('left',u"T/\u00b0C")
        self.plt.setLabel('bottom',u"t/sec")
        self.curve = self.plt.plot()
        self.data = []
        self.w = QtGui.QWidget()
        self.w.setStyleSheet("background: #191919;color: #DDDDDD; color: white;")
        self.label = QtGui.QLabel('Temperature')
        self.label.setStyleSheet("font-size:48px")
        self.temperatureThermo = QtGui.QLineEdit('20C')
        self.temperatureThermo.setStyleSheet("font-size:48px; color: yellow;")
        self.temperatureThermo.setFixedSize(300,70)
        self.temperatureThermo.setReadOnly(True);
        self.temperatureCold = QtGui.QLineEdit('20C')
        self.temperatureCold.setReadOnly(True);
        self.mainlayout = QtGui.QGridLayout()
        self.mainlayout.addWidget(self.label,0,0)
        self.mainlayout.addWidget(self.temperatureThermo,1,0)
        self.mainlayout.addWidget(self.temperatureCold,2,0)
        self.mainlayout.addWidget(self.plt, 0, 1, 4, 1)
        self.w.setLayout(self.mainlayout)
        self.w.show()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        
    def update(self):
        self.temperatureThermo.setText(u"{:10.1f}\u00b0C".format(self.hot))
        self.temperatureCold.setText(u"Cold junction = {:2.1f}\u00b0C".format(self.cold))
        self.data=self.data[-self.bufferlen:]
        if self.data:
            self.lock.acquire()
            self.curve.setData(np.linspace(0,self.bufferlen/250,len(self.data)),np.hstack(self.data))
            self.lock.release()

    def addData(self,hot,cold):
        self.hot = hot
        self.cold = cold
        self.lock.acquire()
        self.data.append(hot)
        self.lock.release()


def getDataThread(qtTemperaturePlot):
    while running:
        # loop as fast as we can to empty the kernel buffer
        while c.hasSampleAvailable():
            sample = c.getSampleFromBuffer()
            cold = c.phys2temperature(sample[ch2])
            hot = cold + (sample[ch1] - ch1Offset) / 39E-6
            qtTemperaturePlot.addData(hot,cold)
        # let Python do other stuff and sleep a bit
        sleep(0.1)

s = c.AttysScan()
s.scan()
c = s.getAttysComm(0)
if not c:
    print("No Attys connected and/or paired")
    sys.exit()
    
plot = QtTemperaturePlot()

c.setAdc1_mux_index(c.ADC_MUX_TEMPERATURE)
# start data acquisition
c.start()

# create a thread which gets the data from the USB-DUX
t = threading.Thread(target=getDataThread,args=(plot,))

# start the thread getting the data
t.start()

# showing all the windows
app.exec_()

# Signal the Thread to stop
running = False

c.quit()

# Waiting for the thread to stop
t.join()


print("finished")

import numpy
import paho.mqtt.client as mqtt
import sys,threading
import time
import struct
import os,json

sensorSSTopic3 = ""
sensorBuffer3 = []
sizeBuffer3 = 0

def on_connect3(client, userdata, flags, rc):
  client.subscribe(sensorSSTopic3)

def on_message3(client, userdata, msg):
    data = json.loads(msg)
    data = data['m'].split(',')
    for i in range(len(data)):
      data[i] = float(data[i])
    sensorBuffer3.append(data[0:sizeBuffer3])
  
class MyOVBox3(OVBox):

  def __init__(self):
    OVBox.__init__(self)
    self.channelCount = 0
    self.samplingFrequency = 0
    self.epochSampleCount = 0
    self.startTime = 0.
    self.endTime = 0.
    self.dimensionSizes = list()
    self.dimensionLabels = list()
    self.timeBuffer = list()
    self.signalBuffer = None
    self.signalHeader = None

# this time we also re-define the initialize method to directly prepare the header and the first data chunk
  def initialize(self):
    global sensorSSTopic3
    sensorSSTopic3 = 'cmd2dev'+str(self.setting['IMU Sensor Number'])
    self.mqttHostServer = str(self.setting['MQTT Server Host'])
    self.mqttGate = int(self.setting['MQTT Gate'])
    self.client = mqtt.Client() # Identificacao do Cliente
    # client.username_pw_set(username="minibike",password="minibike2021")  # Usuario e senha do broker
    self.client.on_connect = on_connect3
    self.client.on_message = on_message3
    # //client.subscribe(sensorTopic)
    self.client.connect(self.mqttHostServer,self.mqttGate) #se for o pendrive é '10.1.1.169' ou '10.1.1.191'(Conferir qual pendrive é)

    self.client.loop_start()
    print("Inicializou")
    # settings are retrieved in the dictionary
    self.channelCount = int(self.setting['Sensor Length'])
    self.samplingFrequency = int(self.setting['Sensor Sampling frequency'])
    self.epochSampleCount = int(self.setting['Generated epoch sample count'])
    global sizeBuffer3
    sizeBuffer3 = self.channelCount 

#creation of the signal header
    for i in range(self.channelCount):
      self.dimensionLabels.append( 'Sensor'+str(i) )
    self.dimensionLabels += self.epochSampleCount*['']
    self.dimensionSizes = [self.channelCount, self.epochSampleCount]
    self.signalHeader = OVSignalHeader(0., 0., self.dimensionSizes, self.dimensionLabels, self.samplingFrequency)
    self.output[0].append(self.signalHeader)

 #creation of the first signal chunk
    self.endTime = 1.*self.epochSampleCount/self.samplingFrequency
    self.signalBuffer = numpy.zeros((self.channelCount, self.epochSampleCount))
    self.updateTimeBuffer()
    self.updateSignalBuffer()

  def updateStartTime(self):
    self.startTime += 1.*self.epochSampleCount/self.samplingFrequency

  def updateEndTime(self):
    self.endTime = float(self.startTime + 1.*self.epochSampleCount/self.samplingFrequency)

  def updateTimeBuffer(self):
    self.timeBuffer = numpy.arange(self.startTime, self.endTime, 1./self.samplingFrequency)

  def updateSignalBuffer(self):
    if len(sensorBuffer3)>0:
      temp = sensorBuffer3.pop()
      if temp != []:
        print(temp)
        for rowIndex, row in enumerate(self.signalBuffer):
          if len(sensorBuffer3) > 0:
            self.signalBuffer[rowIndex,:] = temp[rowIndex]
          else:
            self.signalBuffer[rowIndex,:] = 0*self.signalBuffer[rowIndex-1,:]-1

  def sendSignalBufferToOpenvibe(self):
    start = self.timeBuffer[0]
    end = self.timeBuffer[-1] + 1./self.samplingFrequency
    bufferElements = self.signalBuffer.reshape(self.channelCount*self.epochSampleCount).tolist()
    self.output[0].append( OVSignalBuffer(start, end, bufferElements) )

  # the process is straightforward
  def process(self):
    #start = self.timeBuffer[0]
    end = self.timeBuffer[-1]
    if self.getCurrentTime() >= end:
      self.sendSignalBufferToOpenvibe()
      self.updateStartTime()
      self.updateEndTime()
      self.updateTimeBuffer()
      self.updateSignalBuffer()

  # this time we also re-define the uninitialize method to output the end chunk.
  def uninitialize(self):
    end = self.timeBuffer[-1]
    self.output[0].append(OVSignalEnd(end, end))
    # self.t1.join()
    if self.client:
      self.client.loop_stop()
      self.client.disconnect()

box = MyOVBox3()

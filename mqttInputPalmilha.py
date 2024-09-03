import numpy
import paho.mqtt.client as mqtt
import sys,threading
import time
import struct
import os,json
from collections import deque

sensorTopic1 = "" # alterar para o sensor que vai usar
sensorSSTopic1 = ""
sensorBuffer1 = deque()
sizeBuffer1 = 0
frequence1 = 0

def requestIMUStream1(client):
  msg2send = {'op':28}
  msg2send['timeout'] = str(9000)
  msg2send['frequency'] = frequence1
  print('request Insole Stream: ', sensorTopic1)
  client.publish(sensorTopic1,json.dumps(msg2send))

def stopIMUStream1(client):
  msg2send = {'op':29}
  client.publish(sensorTopic1,json.dumps(msg2send))

def on_connect1(client, userdata, flags, rc):
  requestIMUStream1(client)
  client.subscribe(sensorSSTopic1)

def on_message1(client, userdata, msg):
    global sensorBuffer1
    # print(msg.payload.decode('utf8'))
    data = msg.payload.decode('utf8').split('\n')
    # print(data)
    for line in data:
      if len(line) == 0:
        break
      sensorReading = line.replace(';','').replace('\r','').split(',')
      # print(sensorReading)
      for i in range(len(sensorReading)):
        sensorReading[i] = float(sensorReading[i])
      sensorBuffer1.append(sensorReading[0:sizeBuffer1])
  
class MyOVBox1(OVBox):

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
    global sensorTopic1
    global sensorSSTopic1
    sensorTopic1 = 'cmd2dev'+str(self.setting['IMU Sensor Number'])
    sensorSSTopic1 = 'dev'+str(self.setting['IMU Sensor Number'])+'ss'
    self.mqttHostServer = str(self.setting['MQTT Server Host'])
    self.mqttGate = int(self.setting['MQTT Gate'])
    self.client = mqtt.Client() # Identificacao do Cliente
    # client.username_pw_set(username="minibike",password="minibike2021")  # Usuario e senha do broker
    self.client.on_connect = on_connect1
    self.client.on_message = on_message1
    # //client.subscribe(sensorTopic)
    self.client.connect(self.mqttHostServer,self.mqttGate) #se for o pendrive é '10.1.1.169' ou '10.1.1.191'(Conferir qual pendrive é)
    self.client.loop_start()
    # self.t1 = threading.Thread(target = self.client.loop_forever)
    # self.t1.start()
    print("Inicializou")
    # settings are retrieved in the dictionary
    self.channelCount = int(self.setting['Sensor Length'])
    self.samplingFrequency = int(self.setting['Sensor Sampling frequency'])
    self.epochSampleCount = int(self.setting['Generated epoch sample count'])
    global sizeBuffer1
    sizeBuffer1 = self.channelCount 
    global frequence1
    frequence1 = self.samplingFrequency

#creation of the signal header
    for i in range(self.channelCount):
      self.dimensionLabels.append( 'Insole '+str(i) )
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
    if len(sensorBuffer1)>0:
      temp = sensorBuffer1.popleft()
      if temp != []:
        # print(len(sensorBuffer1))
        # print(temp)
        for rowIndex, row in enumerate(self.signalBuffer):
          if len(sensorBuffer1) > 0:
            self.signalBuffer[rowIndex,:] = temp[rowIndex]
          else:
            pass
            # print("Sem dados MQTT")

  def sendSignalBufferToOpenvibe(self):
    start = self.timeBuffer[0]
    end = self.timeBuffer[-1] + 1./self.samplingFrequency
    bufferElements = self.signalBuffer.reshape(self.channelCount*self.epochSampleCount).tolist()
    self.output[0].append( OVSignalBuffer(start, end, bufferElements) )

  # the process is straightforward
  def process(self):
    #start = self.timeBuffer[0]
    end = self.timeBuffer[-1]
    # if self.getCurrentTime() >= end:
    self.sendSignalBufferToOpenvibe()
    self.updateStartTime()
    self.updateEndTime()
    self.updateTimeBuffer()
    self.updateSignalBuffer()

  # this time we also re-define the uninitialize method to output the end chunk.
  def uninitialize(self):
    end = self.timeBuffer[-1]
    self.output[0].append(OVSignalEnd(end, end))
    stopIMUStream1(self.client) 
    # del self.client
    # self.t1.join()
    if self.client:
      self.client.loop_stop()
      self.client.disconnect()

box = MyOVBox1()

import numpy
import paho.mqtt.client as mqtt
import sys,threading
import time
import struct
import os,json,csv
from datetime import datetime
from collections import deque

sensorTopic = "" # alterar para o sensor que vai usar
sensorSSTopic = ""
sensorBuffer = deque()
sizeBuffer = 0
frequence = 120

def requestIMUStream2(client):
  # msg2send = {'op':28}
  # msg2send['timeout'] = 6000
  # msg2send['frequence'] = 10
  # print('requestIMUStream: ', sensorTopic)
  json_string = '{"op":38,"Stimtopics":"1488","Trigger":"300","Threshold":"300","Recoverytime":"3,6","Stimtime":1,"freq":'+str(frequence)+',"Stimfreq":60,"Stimpulsew":200,"Stimintensidade":"0,0,0,0","Tempenvio":'+str(1)+',"timeSimulation":9000}'

  client.publish(sensorTopic,json_string)

def stopIMUStream2(client):
  msg2send = {'op':22}
  client.publish(sensorTopic,json.dumps(msg2send))

def on_connect2(client, userdata, flags, rc):
  requestIMUStream2(client)
  client.subscribe(sensorSSTopic)
  print(sensorSSTopic)
  # print("Ei Eu me conectei")

def on_message2(client, userdata, msg):
   global sensorBuffer
   data = msg.payload.decode('utf8').split('\n')
   for line in data:
      if len(line) == 0:
        break
      sensorReading = line.replace(';','').replace('\r','').split(',')
      # print(sensorReading)
      for i in range(len(sensorReading)):
        sensorReading[i] = float(sensorReading[i])
      sensorBuffer.append(sensorReading[0:sizeBuffer])
    # print (msg.payload)
    # time.sleep(1)
    # now =datetime.now()
    # data_hora_formatada=now.strftime("%Y-%m-%d")
    # nome_arquivo=f'insole{data_hora_formatada}.csv'
    # sensorBuffer.append([0,0,0,0,0,0])
    # line = msg.payload.decode('utf8').split('\r\n')
    # print(line)
    # for  i in range (len(line)):
    #   data=line[i].split(',')
    #   print(data)
    #   for j in range(len(data)):
    #     try:
    #       data[j] = float(data[j])
    #     except:
    #       continue
    #   print(data)
    #   if all(not isinstance(item,str) for item in data):
  
    #     with open('C:\\Users\\'+nome_arquivo,'a',newline='') as file:

    #       writer = csv.writer(file)
    #       writer.writerow(data)

class MyOVBox2(OVBox):

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
    global sensorTopic
    global sensorSSTopic
    sensorTopic = 'cmd2dev'+str(self.setting['IMU Sensor Number'])
    sensorSSTopic = 'dev'+str(self.setting['IMU Sensor Number'])+'ss'

    print(sensorTopic)
    print(sensorSSTopic)

    self.mqttHostServer = str(self.setting['MQTT Server Host'])
    self.mqttGate = int(self.setting['MQTT Gate'])
    self.client = mqtt.Client() # Identificacao do Cliente
    # client.username_pw_set(username="minibike",password="minibike2021")  # Usuario e senha do broker
    self.client.on_connect = on_connect2
    self.client.on_message = on_message2
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
    global sizeBuffer
    sizeBuffer = self.channelCount 
    global frequence
    frequence = self.samplingFrequency

#creation of the signal header
    for i in range(self.channelCount):
      self.dimensionLabels.append( 'IMU'+str(i) )
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
    if len(sensorBuffer)>0:
      temp = sensorBuffer.popleft()
      if temp != []:
        # print(len(sensorBuffer))
        # print(temp)
        for rowIndex, row in enumerate(self.signalBuffer):
          if len(sensorBuffer) > 0:
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
    stopIMUStream2(self.client) 
    if self.client:
      self.client.loop_stop()
      self.client.disconnect()
    # self.t1.join()

box = MyOVBox2()

import paho.mqtt.client as mqtt
import json,threading

def on_connect(client, userdata, flags, rc):
	print('Connected')


client = mqtt.Client()    # Identificacao do Cliente
client.on_connect = on_connect
 

class MyOVBox(OVBox):
	def __init__(self):
		OVBox.__init__(self)


	def initialize(self):
		self.frequency = 100#int(self.setting['Clock frequency (Hz)'])
		self.mqttHost = str(self.setting['MQTTHost'])
		self.mqttPort = int(self.setting['MQTTPort'])
		self.topic = str(self.setting['topic'])
		self.triggerTime = float(self.setting['Time'])
		self.simulationTime = float(self.setting['Simulation Time'])
		self.TriggerActivated = False
		
		client.connect(self.mqttHost,self.mqttPort)
		self.t1 = threading.Thread(target = client.loop_forever)
		self.t1.start()
		print("Inicializou")
		return
	
	def requestIMUStream(self):
		msg2send = {'op':1}
		msg2send['simulationTime'] = str(self.simulationTime)
		msg2send['frequence'] = self.frequency
		msg2send['sensorType'] = ""
		print('requestIMUStream: ', self.topic)
		print(json.dumps(msg2send))
		client.publish(self.topic,json.dumps(msg2send))
		
	def process(self):
		# print(self.getCurrentTime())
		if self.triggerTime < self.getCurrentTime() and not self.TriggerActivated:
			self.TriggerActivated = True
			print(self.getCurrentTime())
			self.requestIMUStream()
            # self.sendData()
		# for chunkIdx in range( len(self.input[0]) ):
		# 	chunk = self.input[0].pop()
		# 	client.publish(self.topic,str(chunk).replace('[','').replace(']',''))
		return
		
	def uninitialize(self):
		# nop
		return

box = MyOVBox()

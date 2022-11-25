import paho.mqtt.client as mqtt
import json,threading

simulationTime = 99999
frequence = 20
sensorType = 2
start = False
m1d = "0,0,0,0"
m1e = "0,0,0,0"
m2d = "0,0,0,0"
m2e = "0,0,0,0"
m3d = "0,0,0,0"
m3e = "0,0,0,0"
m4d = "0,0,0,0"
m4e = "0,0,0,0"
deviceStim1 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":350,\"p\":20000}\n")
deviceStim2 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":350,\"p\":20000}\n")
sensorTopic = "dev3912ss"
cmdTopic = "cmd2dev3912"
stim1 = 'cmd2dev3632'
stim2 = 'cmd2dev4360'
lastInput = 0

def requestIMUStream(client):
	msg2send = {'op':1}
	msg2send['simulationTime'] = str(simulationTime)
	msg2send['frequence'] = frequence
	msg2send['sensorType'] = sensorType
	print('requestIMUStream: ', cmdTopic)
	client.publish(cmdTopic,json.dumps(msg2send))

def stopIMUStream(msg,client):
	msg2send = {'op':22}
	client.publish(cmdTopic,json.dumps(msg2send))

def startExperiment(msg):
	if '1' in msg.payload.decode('utf8'):
		print('Request Start')
		global start
		start = True
		requestIMUStream(client)

def stopExperiment(msg,client):
	if '0' in msg.payload.decode('utf8'):
		print('Request Stop')
		global start
		start = False
		stopIMUStream(msg,client)
		deviceStim1['m'] = '0,0,0,0'
		client.publish(stim1,json.dumps(deviceStim1))
		deviceStim2['m'] = '0,0,0,0'
		client.publish(stim2,json.dumps(deviceStim2)) 

def on_connect(client, userdata, flags, rc):
	print('Connected')
	client.subscribe(sensorTopic)
	client.subscribe('webCommand')
	client.subscribe('start')
	
def on_message(client, userdata, msg):
	if msg.topic == 'webCommand':
		msgDict = json.loads(msg.payload)
		# global m1d,m1e,m2d,m2e,m3d,m3e,m4d,m4e,deviceStim1,deviceStim2
		m1d = msgDict['m1'].split(';')[0]
		m1e = msgDict['m1'].split(';')[1]
		m2d = msgDict['m2'].split(';')[0]
		m2e = msgDict['m2'].split(';')[1]
		m3d = msgDict['m3'].split(';')[0]
		m3e = msgDict['m3'].split(';')[1]
		m4d = msgDict['m4'].split(';')[0]
		m4e = msgDict['m4'].split(';')[1]
		deviceStim1 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
		deviceStim2 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
	elif 'start' in msg.topic: 
		startExperiment(msg)
		stopExperiment(msg,client)



client = mqtt.Client()    # Identificacao do Cliente
client.on_connect = on_connect
client.on_message = on_message
 

class MyOVBox(OVBox):
	def __init__(self):
		OVBox.__init__(self)


	def initialize(self):
		client.connect('10.1.0.44',1883)
		self.t1 = threading.Thread(target = client.loop_forever)
		self.t1.start()
		print("Inicializou")
		# client.loop_forever()
		# nop
		return

	def process(self):
			#print(start)
		if start:
			for chunkIdx in range( len(self.input[0]) ):
				chunk = self.input[0].pop()
				#print('Entrou2')
				#print(chunk)
				if(len(chunk) > 0 ):
					stim=chunk.pop()
					global lastInput
					if stim != lastInput:
						
						if stim == 0:
							#PERNA DIREITA - CICLO 1
							#self.deviceStim1['m'] = '8,0,10,0' #1
							deviceStim1['m'] = m1d
							client.publish(stim1,json.dumps(deviceStim1))
							#PERNA ESQUERDA - CICLO 1
							#self.deviceStim2['m'] = '15,0,0,15'#3
							deviceStim2['m'] = m1e
							client.publish(stim2,json.dumps(deviceStim2))   
							print('Gate Phase: 0')

						elif stim == 1:
							#PERNA DIREITA - CICLO 2
							#self.deviceStim1['m'] = '0,12,0,12'#2
							deviceStim1['m'] = m2d
							client.publish(stim1,json.dumps(deviceStim1))
							#PERNA ESQUERDA - CICLO 2
							#self.deviceStim2['m'] = '15,0,0,0'#4
							deviceStim2['m'] = m2e          
							client.publish(stim2,json.dumps(deviceStim2))   
							print('Gate Phase: 1')

						elif stim == 2:               
							#PERNA DIREITA - CICLO 3
							#self.deviceStim1['m'] = '12,0,0,12'#3
							deviceStim1['m'] = m3d
							client.publish(stim1,json.dumps(deviceStim1))
							#PERNA ESQUERDA - CICLO 3
							#self.deviceStim2['m'] = '11,0,13,0'#1
							deviceStim2['m'] = m3e
							client.publish(stim2,json.dumps(deviceStim2))             
							print('Gate Phase: 2')

						elif stim == 3:
							#PERNA DIREITA - CICLO 4
							#self.deviceStim1['m'] = '12,0,0,0'#4
							deviceStim1['m'] = m4d
							client.publish(stim1,json.dumps(deviceStim1))
							#PERNA ESQUERDA - CICLO 4
							#self.deviceStim2['m'] = '0,15,0,15'#2
							deviceStim2['m'] = m4e
							client.publish(stim2,json.dumps(deviceStim2))     
							print('Gate Phase: 3')

					lastInput = stim
				#else:
				#	print 'Received chunk of type ', type(chunk), " looking for StimulationSet"
		return
		
	def uninitialize(self):
		# nop
		return

box = MyOVBox()

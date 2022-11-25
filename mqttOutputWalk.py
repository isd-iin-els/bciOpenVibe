import paho.mqtt.client as mqtt
import json,threading,time,sys

simulationTime = 99999
frequence = None
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
sensorTopic = ""
cmdTopic = ""
stim1 = ''
stim2 = ''
rpm = 0
rpmMin = 0
rpmMax = 0
fesMin = '0,0,0,0'
fesMax = '0,0,0,0'

def rpm2fes(rpm,devIndex,dev):
	fMin = fesMin.split(';')[devIndex]
	fMin = fMin.split(',')
	#print(fMin)
	fMax = fesMax.split(';')[devIndex]
	fMax = fMax.split(',')
	#print(fMax)
	fes = ''
	_dev = dev.split(',')
	for i in range(len(_dev)):
		if float(_dev[i]) > 0:
			fes += str((float(fMax[i])-float(fMin[i]))*((rpm-rpmMin)/(rpmMax-rpmMin)) + float(fMin[i]))+','
		else:
			fes += '0,'
	fes = fes[0:len(fes)-1]
	#print(fes)
	return fes

def gateCicle():
	while True:
		if stim1 != '' and rpm != 0:
			deviceStim1['m'] =  rpm2fes(rpm,0,m1d)
			client.publish(stim1,json.dumps(deviceStim1))
			deviceStim2['m'] = rpm2fes(rpm,1,m1e) 
			client.publish(stim2,json.dumps(deviceStim2))   
			print('Gate Phase: 0')
			time.sleep(1/(rpm*0.016666666666667)/4.0)

			deviceStim1['m'] = rpm2fes(rpm,0,m2d)
			client.publish(stim1,json.dumps(deviceStim1))
			deviceStim2['m'] = rpm2fes(rpm,1,m2e)           
			client.publish(stim2,json.dumps(deviceStim2))   
			print('Gate Phase: 1')
			time.sleep(1/(rpm*0.016666666666667)/4.0)
			
			deviceStim1['m'] = rpm2fes(rpm,0,m3d)
			client.publish(stim1,json.dumps(deviceStim1))
			deviceStim2['m'] = rpm2fes(rpm,1,m3e) 
			client.publish(stim2,json.dumps(deviceStim2))             
			print('Gate Phase: 2')
			time.sleep(1/(rpm*0.016666666666667)/4.0)

			deviceStim1['m'] = rpm2fes(rpm,0,m4d)
			client.publish(stim1,json.dumps(deviceStim1))
			deviceStim2['m'] = rpm2fes(rpm,1,m4e) 
			client.publish(stim2,json.dumps(deviceStim2))     
			print('Gate Phase: 3')
			time.sleep(1/(rpm*0.016666666666667)/4.0)

def requestIMUStream(client):
	msg2send = {'op':1}
	msg2send['simulationTime'] = str(simulationTime)
	msg2send['frequence'] = frequence
	msg2send['sensorType'] = sensorType
	#print('requestIMUStream: ', cmdTopic)
	client.publish(cmdTopic,json.dumps(msg2send))

def stopIMUStream(client):
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
		stopIMUStream(client)
		deviceStim1['m'] = '0,0,0,0'
		client.publish(stim1,json.dumps(deviceStim1))
		deviceStim2['m'] = '0,0,0,0'
		client.publish(stim2,json.dumps(deviceStim2)) 

def on_connect(client, userdata, flags, rc):
	print('Connected')
	client.subscribe('webCommand')
	client.subscribe('start')
	client.publish('requestStart','1')
	
	
def on_message(client, userdata, msg):
	if msg.topic == 'webCommand':
		msgDict = json.loads(msg.payload)
		global m1d
		global m1e
		global m2d
		global m2e
		global m3d
		global m3e
		global m4d
		global m4e
		global deviceStim1
		global deviceStim2
		global sensorTopic
		global cmdTopic
		global stim1
		global stim2
		global start
		global frequence
		frequence = msgDict['sensorFreq']
		m1d = msgDict['m1'].split(';')[0]
		m1e = msgDict['m1'].split(';')[1]
		m2d = msgDict['m2'].split(';')[0]
		m2e = msgDict['m2'].split(';')[1]
		m3d = msgDict['m3'].split(';')[0]
		m3e = msgDict['m3'].split(';')[1]
		m4d = msgDict['m4'].split(';')[0]
		m4e = msgDict['m4'].split(';')[1]
		#print(msgDict)
		sensorTopic = "dev"+str(msgDict['sensor'])+'ss'
		cmdTopic = "cmd2dev"+str(msgDict['sensor'])
		stim1 = "cmd2dev"+str(msgDict['stim1'])
		stim2 = "cmd2dev"+str(msgDict['stim2'])
		deviceStim1 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
		deviceStim2 = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
		client.subscribe(sensorTopic)
		start = True
		requestIMUStream(client)
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
		self.t2 = threading.Thread(target = gateCicle)
		self.t2.start()
		#global start
		
		print("Inicializou")
		return

	def process(self):
			#print(start)
		if start:
			for chunkIdx in range( len(self.input[0]) ):
				chunk = self.input[0].pop()
				#print('Entrou2')
				#print(chunk)
				if(len(chunk) > 0 ):
					global rpm
					rpm=chunk.pop()
					
				#else:
				#	print 'Received chunk of type ', type(chunk), " looking for StimulationSet"
		return
		
	def uninitialize(self):
		# nop
		del self.t1
		del self.t2
		print('Request Stop')
		global start
		start = False
		stopIMUStream(client)
		deviceStim1['m'] = '0,0,0,0'
		client.publish(stim1,json.dumps(deviceStim1))
		deviceStim2['m'] = '0,0,0,0'
		client.publish(stim2,json.dumps(deviceStim2)) 
		return

box = MyOVBox()

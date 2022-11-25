import paho.mqtt.client as mqtt
import json,threading

simulationTime = 99999
frequence = 20
sensorType = 2
start = False
p1 = "0,0,0,0"
p2 = "0,0,0,0"
deviceStim = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":350,\"p\":20000}\n")
sensorTopic = "dev3912ss"
cmdTopic = "cmd2dev3912"
stim1 = 'cmd2dev3632'
stim2 = 'cmd2dev4360'
lastInput1 = 0

def requestIMUStream(client1):
	msg2send = {'op':1}
	msg2send['simulationTime'] = str(simulationTime)
	msg2send['frequence'] = frequence
	msg2send['sensorType'] = sensorType
	print('requestIMUStream: ', cmdTopic)
	client1.publish(cmdTopic,json.dumps(msg2send))

def stopIMUStream(msg,client1):
	msg2send = {'op':22}
	client1.publish(cmdTopic,json.dumps(msg2send))

def startExperiment(msg):
	if '1' in msg.payload.decode('utf8'):
		print('Request Start')
		global start
		start = True
		requestIMUStream(client1)

def stopExperiment(msg,client1):
	if '0' in msg.payload.decode('utf8'):
		print('Request Stop')
		global start
		start = False
		stopIMUStream(msg,client1)
		deviceStim['m'] = '0,0,0,0'
		client1.publish(stim1,json.dumps(deviceStim))

def on_connect1(client1, userdata, flags, rc):
	print('Connected')
	client1.subscribe(sensorTopic)
	client1.subscribe('webCommand')
	client1.subscribe('start')
	
def on_message1(client1, userdata, msg):
    if msg.topic == 'webCommand':
        msgDict = json.loads(msg.payload)
        global p1
        global p2
        global deviceStim
        p1 = msgDict['p1']
        p2 = msgDict['p2']
        deviceStim = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
    elif 'start' in msg.topic: 
        startExperiment(msg)
        stopExperiment(msg,client1)



client1 = mqtt.Client()    # Identificacao do client1e
client1.on_connect = on_connect1
client1.on_message = on_message1
 

class MyOVBox(OVBox):
    def __init__(self):
        OVBox.__init__(self)

    def initialize(self):
        client1.connect('10.1.0.44',1883)
        self.t1 = threading.Thread(target = client1.loop_forever)
        self.t1.start()
        print("Inicializou")
        return
		
    def process(self):
		#print(start)
        if start:
            for chunkIdx in range( len(self.input[0]) ):
                chunk = self.input[0].pop()
                if(len(chunk) > 0 ):
                    stim=chunk.pop()
                    #print(stim)
                    global lastInput1
                    if stim != lastInput1:
                        if stim == 0:
                            deviceStim['m'] = p1
                            client1.publish(stim1,json.dumps(deviceStim))
                            print('Direita: ')

                        elif stim == 1:
                            deviceStim['m'] = p2
                            client1.publish(stim1,json.dumps(deviceStim))
                            print('Esquerda: ')
                    lastInput1 = stim
        return
		
    def uninitialize(self):
        # nop
        return

box = MyOVBox()

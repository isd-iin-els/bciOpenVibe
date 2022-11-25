import paho.mqtt.client as mqtt
import json,threading,time,sys

simulationTime = 99999
frequence = None
sensorType = 2
start = False
p1 = "0,0,0,0"
p2 = "0,0,0,0"
deviceStim = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":350,\"p\":20000}\n")
sensorTopic = ""
cmdTopic = ""
stim1 = ''
stim2 = ''
lastInput1 = 0
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

def bikeCicle():
    	while True:
            if stim1 != '' and rpm != 0:
                deviceStim['m'] = rpm2fes(rpm,0,p1)
                client1.publish(stim1,json.dumps(deviceStim))
                print('Direita: ')
                time.sleep(1/(rpm*0.016666666666667)/2.0)

                deviceStim['m'] = rpm2fes(rpm,0,p2)
                client1.publish(stim1,json.dumps(deviceStim))
                print('Esquerda: ')
                time.sleep(1/(rpm*0.016666666666667)/2.0)

def requestIMUStream(client1):
	msg2send = {'op':1}
	msg2send['simulationTime'] = str(simulationTime)
	msg2send['frequence'] = frequence
	msg2send['sensorType'] = sensorType
	#print('requestIMUStream: ', cmdTopic)
	client1.publish(cmdTopic,json.dumps(msg2send))

def stopIMUStream(client1):
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
		stopIMUStream(client1)
		deviceStim['m'] = '0,0,0,0'
		client1.publish(stim1,json.dumps(deviceStim))

def on_connect1(client1, userdata, flags, rc):
    print('Connected')
    client1.subscribe('webCommand')
    client1.subscribe('start')
    client1.publish('requestStart','1')
    
	
def on_message1(client1, userdata, msg):
    if msg.topic == 'webCommand':
        msgDict = json.loads(msg.payload)
        global p1
        global p2
        global deviceStim
        global sensorTopic
        global cmdTopic
        global stim1
        global start
        global rpmMin
        global rpmMax
        global fesMin
        global fesMax
        global frequence
        frequence = msgDict['sensorFreq']
        p1 = msgDict['p1']
        p2 = msgDict['p2']
        rpmMin = msgDict['rpmMin']
        rpmMax = msgDict['rpmMax']
        fesMin = msgDict['fesMin']
        fesMax = msgDict['fesMax']
        sensorTopic = "dev"+str(msgDict['sensor'])+'ss'
        cmdTopic = "cmd2dev"+str(msgDict['sensor'])
        stim1 = "cmd2dev"+str(msgDict['stim1'])
        deviceStim = json.loads("{\"op\":2,\"m\":\"Channel String Vector\",\"t\":"+str(msgDict['ton'])+",\"p\":"+str(msgDict['period'])+"}\n")
        client1.subscribe(sensorTopic)
        start = True
        requestIMUStream(client1)
       # print("webcommand")
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
        self.t2 = threading.Thread(target = bikeCicle)
        self.t2.start()
        print("Inicializou")
        return
		
    def process(self):
		#print(start)
        if start:
            for chunkIdx in range( len(self.input[0]) ):
                chunk = self.input[0].pop()
                if(len(chunk) > 0 ):
                    global rpm
                    rpm=chunk.pop()
                    
                    
        return
		
    def uninitialize(self):
        # nop
        del self.t1
        del self.t2
        print('Request Stop')
        global start
        #global deviceStim
        start = False
        stopIMUStream(client1)
        deviceStim['m'] = '0,0,0,0'
        client1.publish(stim1,json.dumps(deviceStim))
        return

box = MyOVBox()

import pylsl
import StimulationsCodes


class BoxMarkerLSL(OVBox):
    def __init__(self):
        OVBox.__init__(self)
        self.stimLabel = None
        self.stimCode = None

    def initialize(self):

        streams = pylsl.resolve_stream('type', 'Markers')

        if len(streams) > 0:
            self.inlet = pylsl.StreamInlet(streams[0])
            info = self.inlet.info()
            name = info.name()
            print('Fonte encontrada, ', name, ' ', info, ' ', self.getCurrentTime())

            #self.stimLabel = self.setting['Stimulation']
            #self.stimCode = OpenViBE_stimulation[self.stimLabel]
            self.output[0].append(OVStimulationHeader(0., 0.))

    def process(self):
        marker, timestamp = self.inlet.pull_sample(0)

        if marker != None:

            print('Marcador', marker[0], self.getCurrentTime())
            print('aqui 1')

            if marker[0] == 0:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_00']

            elif marker[0] == 1:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_01']

            elif marker[0] == 2:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_02']

            elif marker[0] == 3:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_03']

            elif marker[0] == 4:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_04']

            elif marker[0] == 5:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_05']

            elif marker[0] == 6:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_06']

            elif marker[0] == 7:
                self.stimCode = OpenViBE_stimulation['OVTK_StimulationId_Label_07']


            stimSet=OVStimulationSet(self.getCurrentTime(), self.getCurrentTime()+1./self.getClock())

            stimSet.append(OVStimulation(self.stimCode, self.getCurrentTime(), 0.))

            self.output[0].append(stimSet)

    def uninitialize(self):

        end=self.getCurrentTime()
        self.output[0].append(OVStimulationEnd(end, end))


box=BoxMarkerLSL()

from pyvisa import *

class MeasurementThread():
    def __init__(self):
        resources = ResourceManager()
        resourceList = resources.list_resources()

        self.connectionState = False # Is there a valid connection to an instrument and is it the expected instrument?
        self.initilisedState = False # Has the instrument completed initilisation and done so without error?

        # "Clean connection" method. Detects if "2450" is in the user resource. Often, Keithley instruments nicely identify themselves in the VISA resouce name.
        for resourceName in resourceList:
            if "2450" in resourceName:
                try:
                    self.instrument = resources.open_resource(resourceName)
                    identifyString = self.instrument.query("*IDN?")
                    
                    if "MODEL 2450" in identifyString:
                        self.connectionState = True

                except:
                    self.connectionState = False
                    # handle error in main GUI

        # "Brute force connection" method. Run through each detected instrument, attempt to connect and send identify query. A succesful identify query will return a string with the
        # instrument model, check if this is what we expect.
        if not self.connectionState:
            # communicate with event log
            for resourceName in resourceList:
                try:
                    self.instrument = resources.open_resource(resourceName)
                    identifyString = self.instrument.query("*IDN?")

                    if "MODEL 2450" in identifyString:
                        ConnectionSuccess = True
                except:
                    self.connectionState = False
                    # handle error in main GUI

        if self.connectionState:
            self.instrumentSetup()
        else:
            # No connection could be made with the brute force method either.
            # handle error in main GUI
            self.connectionState = False

    def instrumentSetup(self):

        # Reset Instrument:
        # Reset the instrument to default values and clear the reading buffer.
        self.instrument.write("*RST")

        # Configure the instrument's Standard Event Status Enable (ESE) register to monitor for the "Operation Complete" event. This event is logged in the Standard Event Status 
        # Register (ESR, the event log), when the instrument has finished processing all pending operations and is ready to accept new commands. Basically, write in the event log 
        # when all  operations are finished.
        self.instrument.write("*ESE 1")

        # Configure the Service Request Enable (SRE) register to generate a Service Request (SRQ) when the "Operation Complete" event is logged in the Standard Event Status Register 
        # (ESR). This instructs the instrument to signal the computer via SRQ for this specific event.
        self.instrument.write("*SRE 32")

        # ELI5
        # *ESE 1: "Hey instrument, put a checkmark in your log when you've finished what I asked you to do."
        # *SRE 32: "And when you put that checkmark, raise your hand so I know to look at your log and see what you've done."

        # Clears event registers and queues.
        self.instrument.write("*CLS")

        # Set read back on for voltage and current.
        # When sourcing the voltage, allow the value to be read back. Same logic for current.
        self.instrument.write(":SOUR:VOLT:READ:BACK ON;:SOUR:CURR:READ:BACK ON;")

        # Check for error
        errorCheck = self.instrument.query(":SYST:ERR?")
        if "No error" in errorCheck:
            self.initilisedState = True
        else:
            self.initilisedState = False
            # Handle initilisation error in the main GUI.

measurement = MeasurementThread()
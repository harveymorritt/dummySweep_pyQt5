# In the programs current state, you will need to change  the line "import instruments.dummyInstrument as inst" in measurement_handler.py to include your library name in place of "dummyInsturment"
 
import numpy as np

def initilise():
    """
    Instrument Initialisation

    Responsible for making the connection to the instrument and running the initial setup (e.g. default settings, screen brightness e.t.c.).

    Returns:
    _initilised: (bool), if the instrument has connected successfully and ran the setup without errors.
    _message: (string), the message to be printed to the main GUI console ("e.g. Kiethley 2450 Initilised Successfully" if _instrumentName = "Kiethley 2450")

    Insert the visa commands between "### INITIALISATION CODE HERE ###" and "### END ###". Edit _instrumentName to set the name of the measurement instrument.
    """

    ### INITIALISATION CODE HERE ###
    _instrumentName = "Dummy Instrument"
    _initilised = True
    ### END ###

    if _initilised:
        _message = _instrumentName + " Initilised Successfully"
        return True, _message
    else:
        _message = _instrumentName + " Initilisation Failed"
        return False, _message
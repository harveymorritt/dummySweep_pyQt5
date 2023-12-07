# Change the line "import instruments.dummyInstrument as inst" in measurement_handler.py to include your library name in place of "dummyInsturment"

import numpy as np
import time

def initilise():
    """
    Instrument Initialisation

    Responsible for making the connection to the instrument and running the initial setup (e.g. default settings, screen brightness e.t.c.).

    Returns:
    _initilised: (bool), if the instrument has connected successfully and ran the setup without errors.
    _message: (string), the message to be printed to the main GUI console ("e.g. Kiethley 2450 Initilised Successfully" if _instrumentName = "Kiethley 2450")

    Insert the VISA commands between "### INITIALISATION CODE HERE ###" and "### END ###". 
    Edit _instrumentName to set the name of the measurement instrument.
    The code should only set "_initilised = True" if the instrument has been connected to successfully. This is typically when all commands of the initial setup have been run without error.
    """

    _initilised = False

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

def measureVOC():
    _valueVOC = None

    """
    Measure the VOC of the cell

    Responsible for performing the measurement of the open circuit voltage, a single-point measurement of the cell at zero current.
    This function is the programatic equivalent of holding a multimeter to the photovoltaic cell.

    Returns:
    _valueVOC: (float) The measured value of the VOC.

    Insert the VISA commands between "### VOC CODE HERE ###" and "### END ###"
    _valueVOC is set to None by default and should only be set to a value once this value has been checked (i.e. the instrument did not return an error and gave a sensible float back).
    """

    ### VOC CODE HERE###
    _valueVOC = np.round(0.6+((1.05-0.6)*np.random.rand()), 3)
    ### END ###

    if _valueVOC:
        return _valueVOC

def measurePoint(voltagePoint = 0):
    _current = None
    
    """
    Measures the current at a given voltage.

    Responsible for performing the measurement of current at a voltage = voltagePoint.
    If no value is provided, voltagePoint = 0, which is used to measure the Voc of the photovoltaic cell, the programatic equivalent of holding a multimeter to the photovoltaic cell.

    Returns:
    _voltage: (float) The measured voltage value
    _current: (float) The measured current value

    The voltage is returned as some instruments allow the actual voltage point to be measured, since this will always be some (hopefully) small value off the requested voltage.
    If your instrument does not allow this, set _voltage = voltagePoint to return the requested voltage, but be aware of this in your error analysis!

    Insert the VISA commands for your instrument between "### VISA COMMANDS HERE ###" and "### END ###"
    _current is set to Nine by default and should only be set to a value once this value has been checked (i.e. the instrument did not return an error and gave a sensible float back).
    """

    ### SWEEP CODE HERE ###
    _n = 1.5
    _k = 1.38e-23
    _T = 300
    _I0 = 1e-12
    _q = 1.6e-19

    _sleepTime = 0.045+(0.055-0.045)*np.random.rand()
    time.sleep(_sleepTime)                                      # Wait some time to emulate instrument responce

    _voltage = voltagePoint
    _current = _I0*(np.exp((_q * voltagePoint)/(_n*_k*_T)) - 1) # Get current point using ideal diode equation
    _currentError = -0.005+(0.015+0.005)*np.random.rand()       # Add some error into the current
    
    _current = _current + _currentError - 0.2
    ### END ###

    if _current:
        return _voltage, _current


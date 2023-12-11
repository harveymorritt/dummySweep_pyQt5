# Change the line "import instruments.dummyInstrument as inst" in measurement_handler.py to include your library name in place of "dummyInsturment"

import numpy as np
import time
import yaml
import os

def getConfigData():
    """
    Creates or reads the configuration file for the instrument.

    If a configuration file does not exist it will save (and use) the default settings. Otherwise, it will read from a file.

    Returns:
    _dictionaryToReturn: (dict), the settings for the currently used instrument.

    Edit between "### CODE HERE ###" and "### END ###"

    Set _instrumentName to the name of the instrument. This will be used to name the configuration file. i.e. _instrumentName + "_ConfigurationFile".
    
    Set _configDefaultSettings to the default settings of the instrument. Any instrument variables (front or back connections, four or two wire, screen brightness, audio active, e.t.c.) should be set here.
    These are the default settings that will be used if no configuration file is found, or if the values inside the configuration file are invalid (user set them wrong).

    User inputs are checked to see if they are allowed. For example, a "terminal" settings could control if a two-wire of four-wire measurement is executed, depending on if this is set as "two" or "four".
    If the user sets anything other than "two" or "four" by mistake, the program would catch this and set the configuration file used to the default values to prevent issues in the instrument initialization.
    As such, it is extreamly important that the default values are tested extensively as these provide a saftey net.
    It is also important that the user knows if the default values are being used, if they typed "fuor" instead of "four", the default value of "two" would be taken (may be different for your code).
    Naturally, this could cause issues if the user did not know about it. Hence, the initilization values used are printed in the console (TO DO: raise a warning popup when an invalid value is detected).
    
    It would be possible and easier for the lab-user to configure the instrument settings from the GUI. However, for every instrument, a slightly different GUI would be needed.
    One of the core principles of the program is that to change the instrument used only one file (this one) should be edited.
    This is to allow the software to be downloaded and quickly edited to work with any VISA capable source-meter, so that no GUI code is needed to adapt the program to work with another instrument.
    Therefore, using a human readable .yaml file to edit the instrument settings was deemed an acceptable solution, as these variables don't need to be changed often.
    It would be possible to read from the .yaml file and build a GUI window dynamically to configure the instrument, depending on what variables are set in the .yaml - this is a planned feature.
    """
    _returnMessage = "" # The message that will be displayed to the console.

    ### CODE HERE ###
    _instrumentName = "Dummy-Instrument"

    # The default instrument settings. Loaded if no configuration file is found, or if the configuration file contains a value that is not valid.
    _configDefault = {
        "terminal": "two", # Options: "two", "four"
        "panel": "front"  # Options: "front", "rear"
    }

    # The allowed values for each setting.
    _configAllowedValues = {
        "terminal": ("two", "four"),
        "panel": ("front", "rear")
    }

    # Explain how to use the configuration file to the user. Clearly explain the valid options for each setting. Each line must start with "#"
    _configHeader = (
    "# \"terminal\" controls if the instrument executes a four or two wire wire measurement.\n" 
    "# The valid options are \"two\" and \"four\".\n\n"

    "# \"panel\" controls if the front or rear connections of the Keithley 2450 are used.\n" 
    "# The valid options are \"front\" and \"rear\".\n\n"
    
    "# You must type the setting EXACTLY as it is written in the valid options, without the quotation marks.\n"
    "# If an invalid setting is entered, the default values of \"two\" and \"front\" will be used. \n\n" 
    )
     ### END ###

    # Processing default values into savable yaml
    _yamlDataDefault = yaml.dump(_configDefault, default_flow_style=False)  # Convert to YAML format
    _yamlFullDefault = _configHeader + _yamlDataDefault                     # Combine with header
    _fileName = _instrumentName + "_Configuration-File.yaml"        # File name

    try:
        # Check if configuration file exists, if not, write the default configuration dictionary
        if not os.path.exists(_fileName):
            with open(_fileName, "w") as file:
                file.write(_yamlFullDefault)
                _returnMessage += "No instrument configuration file found. Default instrument configuration values loaded."
        else:
            _returnMessage += "Instrument configuration file found."

        # Load configuration file
        with open(_fileName, "r") as file:
            _configLoaded = yaml.safe_load(file)
    
        # Check all values are allowed, if not, set back to default
        _invalidValueFound = False
        for key in _configLoaded:
            _allowedValues = _configAllowedValues[key]
            _value = _configLoaded[key]

            if _value not in _allowedValues:
                # Save the default values to overwrite invalid setting
                _invalidValueFound = True

        if _invalidValueFound:
            with open(_fileName, "w") as file:
                file.write(_yamlFullDefault)
                _dictionaryToReturn = _configDefault # Return default configuration if contains not valid values
                _returnMessage += " WARNING: Invalid values found in configuration file. Check for typos! Default values have been set."
        else:
            _dictionaryToReturn = _configLoaded  # If all values are vaild, return loaded configuration
            _returnMessage += " All instrument configuration values are valid. Loaded successfully."

    except:
        _dictionaryToReturn = _configDefault         # If error occurs during loading, return default configuration
        _returnMessage += "Error occured while loading instrument configuration file. Default values have been loaded."
    
    return _dictionaryToReturn, _returnMessage

def initilise():
    """
    Instrument Initialisation

    Responsible for making the connection to the instrument and running the initial setup (e.g. default settings, screen brightness e.t.c.).

    Returns:
    _initialized: (bool), if the instrument has connected successfully and ran the setup without errors.
    _message: (string), the message to be printed to the main GUI console ("e.g. Keithley  2450 Initialized Successfully" if _instrumentName = "Keithley  2450")

    Insert the VISA commands between "### INITIALISATION CODE HERE ###" and "### END ###".
    
    Edit _instrumentName to set the name of the measurement instrument.
    The code should only set "_initialized = True" if the instrument has been connected to successfully. This is typically when all commands of the initial setup have been run without error.
    You can also run "sanity checks", i.e. measuring the voltage to check the instrument returns a sensible float value.

    If the _initialized returns as true, the main program will assume the instrument is functioning exactly as intended.
    _initialized must ONLY ever be set as true if the instrument is working. This is the one point in the code where you have the chance to catch errors with your hardware.
    If in doubt, DO NOT set _initialized = True. Returning _initialized = False is perfectly acceptable and the program can handled it, a measurement will not be attempted unless the initialization has worked.
    Set _failMessages to describe what has gone wrong to the user in the programs console.
    """

    _initialized = False

    ### INITIALISATION CODE HERE ###
    _instrumentName = "Dummy Instrument"
    _failMessages = ""
    _initialized = True
    ### END ###

    if _initialized:
        _message = _instrumentName + " Initialized Successfully"
    else:
        _message = _instrumentName + " Initialization Failed." + _failMessages
    
    return _initialized, _message

def measureVOC():
    """
    Measure the VOC of the cell

    Responsible for performing the measurement of the open circuit voltage, a single-point measurement of the cell at zero current.
    This function is the programmatic equivalent of holding a multimeter to the photovoltaic cell.

    Returns:
    _valueVOC: (float) The measured value of the VOC.

    Insert the VISA commands between "### VISA COMMANDS HERE ###" and "### END ###"
    
    _valueVOC is set to None by default and should only be set to a value once this value has been checked (i.e. the instrument did not return an error and gave a sensible float back).
    """

    _valueVOC = None

    ### VISA COMMANDS HERE ###
    _lowerLimit = 0.6
    _upperLimit = 1.05
    _valueVOC = _lowerLimit+((_upperLimit-_lowerLimit)*np.random.rand())
    _valueVOC = np.round(_valueVOC, 3)
    ### END ###

    if _valueVOC is not None:
        return _valueVOC

def measurePoint(voltagePoint = 0):    
    """
    Measures the current at a given voltage.

    Responsible for performing the measurement of current at a voltage = voltagePoint.

    Returns:
    _voltage: (float) The measured voltage value
    _current: (float) The measured current value

    Insert the VISA commands for your instrument between "### VISA COMMANDS HERE ###" and "### END ###"
    
    The voltage is returned as some instruments allow the actual voltage point to be measured, since this will always be some (hopefully) small value off the requested voltage.
    
    If your instrument does not allow this, set _voltage = voltagePoint to return the requested voltage, but be aware of this in your error analysis!
    _current is set to None by default and should only be set to a value once this value has been checked (i.e. the instrument did not return an error and gave a sensible float back).
    """

    _current = None

    ### VISA COMMANDS HERE ###
    _n = 1.5
    _k = 1.38e-23
    _T = 300
    _I0 = 1e-12
    _q = 1.6e-19

    _lowerLimit = 0.045
    _upperLimit = 0.055
    _sleepTime = _lowerLimit+(_upperLimit-_lowerLimit)*np.random.rand()
    time.sleep(_sleepTime)                                                  # Wait some time to emulate instrument response

    _voltage = voltagePoint
    _current = _I0*(np.exp((_q * voltagePoint)/(_n*_k*_T)) - 1)             # Get current point using ideal diode equation
    
    _lowerLimit = -0.005
    _upperLimit = 0.005
    _currentError = _lowerLimit+(_upperLimit-_lowerLimit)*np.random.rand()  # Add some error into the current
    
    _current = _current + _currentError - 0.2
    ### END ###

    if _current is not None:
        return _voltage, _current

print(getConfigData())
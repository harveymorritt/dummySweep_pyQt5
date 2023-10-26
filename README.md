# dummySweep_pyQt5
Test GUI for JV sweeps, set up with a "dummy sweep" function to emulate a source meter, so that no hardware needs to be programmed while I learn pyQt5.



# Naming Conventions

## Methods

### enforcer
enforcer[ClusterName]
e.g. enforcerSweepPropertyCluster

Watches to make sure values are sensible,  otherwise warns user. e.g. "Are you sure you want to run a 100 volt scan?" kind of thing.

## Variable names

### label

label[widgetName]
e.g. labelVoltageEnd

A label for wigets that don't have a means of inputting a prompt to the user, e.g. QDoubleSpinBox().

### input

input[widgetName]
e.g. inputVoltageEng

An input, for the user to enter values into


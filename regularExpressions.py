import os
import re

cellName = "testFile"

# cellName_SomeDigits_.anyExtension
pattern = re.compile(rf"{re.escape(cellName)}(?:_(\d+))?.*$")
currentPath = os.getcwd()

# Check if files saved with same name
highestNumFound = 0
for fileName in os.listdir(currentPath):
    match = pattern.match(fileName)
    
    # If files with same name, check for number
    if match:
        matchedNumber = match.group(1)      
        
        # If it has a number, keep track of the highest number found
        if matchedNumber:
            num = int(matchedNumber)
            highestNumFound = max(highestNumFound, num)

# If no number found, save file as "file number 1", otherwise increment
if highestNumFound == 0:
    cellName = cellName + "_1"
else:
    nextNum = highestNumFound+1
    cellName = cellName +"_" + str(nextNum)

print(cellName)
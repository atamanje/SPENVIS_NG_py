import sapi
import random
import string
import time
import sys

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

def is_running(ssn, myId):
    """Check if workflow execution is still running"""
    status = s.getExecutionStatus(ssn, myId)
    return True if hasattr(status,'state') and status.state == "RUNNING" else False

# Some variables must be defined by the user here.
## User name. Should be the same than the one in the config file.
username = 'stijn'

## Project name where the execution is to be saved. The project must already exists.
prjname = 'test'

## Path to the workflow to be executed. Can be public or private. The path can be checked using the HMI, in the "Workflow" menu.
workflow = '/common/workflows/GEO_AE8_SD2Q'

## Name of the execution. Here we use a fixed part and a random alphabetic section. This is done to produce unique names for each script execution and avoid collisions.
execname = 'GEO_AE8_SD2Q-' + randomword(10)

## VOTable containing the input data necessary for the execution.
votFile = 'geo_ae8_sd2q_input.vot'

## XML file containing the links between the required parameters to start 
## an execution and the associated resource in the input VOT.
## The text @path@ will be replaced by the actual path automatically.
datamodel = 'geo_ae8_sd2q_datamodel.xml'

# End of user-defined variables.

# Log in
print("Logging in the system.")
s = sapi.Session("global.conf", "")
s.readglobalconfig()
ssn = s.login()

# Create execution.
print "Creating the execution. "
myId=s.createExecution(ssn, username, prjname, execname, workflow, votFile, datamodel)

# Print the execution ID returned. Can be useful to check in the HMI.
print "Execution name: " + execname + " "
print "Execution ID: " + str(myId)

# Start execution
print "Starting the execution. "
sys.stdout.flush()
s.startExecution(ssn, myId)
sys.stdout.flush()
print "Execution started. "

# Check status until not in RUNNING state. It could be FINISHED or ERROR. It will be "WAITING_FOR_INPUTS" if the startExecution step didn't work. 
n = 0
while n < 100 : 
    n = n + 1
    status = s.getExecutionStatus(ssn, myId)
    if hasattr(status,'state'):
        if status.state == "RUNNING":
            print("Still in RUNNING state. ")
            time.sleep(5)
        else:
            print("New state: "+ status.state)
            break
    else:
        print "NO STATUS " + status
        break
print n

# Get VOTable for the whole output information
print("Getting output VOTable.")
outputvot = s.getVOT(ssn, username, prjname, execname)

# Save the VOT to disk. It will be a zip file with all the content.
target = open('output_votable.zip','wb')
target.write(outputvot)
target.close()


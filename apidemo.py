import sapi
from suds.sax.date import DateTime as XSdateTime
import datetime
import base64
import random
import string
import time

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

# Define some constants
username = 'username'
prjname = 'APIdemo'
workflow = '/' + username + '/workflows/geo_trep'
basepath = '/'+username+'/projects/APIdemo/data/'
execname = 'geotrep_' + randomword(10) # Random project name to avoid collisions
votFile = 'sd2q_test.vot'
votInstance = 'instance.vot'

# Define some web services and their URL.
WEMSS = "WorkflowExecutionManagementServiceService"
WEMS  = "WorkflowExecutionManagementService?wsdl"
RMSS  = "ResourceManagementServiceService"
RMS   = "ResourceManagementService?wsdl"

# Log in
print("Logging in the system")
s = sapi.Session("global.conf", "")
s.readglobalconfig()
ssn = s.login()

# Create execution
print("Creating execution "+execname)
paramlist = [("projectId", prjname), ("executionName", execname), ("workflowPath" ,workflow)]
result1 = s.executesingleoperationList(ssn, WEMSS, WEMS, "initializeExecution", "InitializeExecutionParam", paramlist)

print result1

# Create group to store VOTable.
# Some complex types has to be created as the 'createResource' service requires complex data types.
print("Creating group to store VOTable")
now = datetime.datetime.now()
# Create and fill the meta data.
meta = s.getComplexType(ssn, RMSS, RMS, 'XmlGroupResourceMetaDto')
meta.id = 0
meta.name = result1.id
meta.created = now
meta.createdBy = ""
meta.lastModified = now
meta.lastModifiedBy = ""
meta.sizeInBytes=0
# Create the Xml Group Resource DTO needed and copy here the meta data.
xrd = s.getComplexType(ssn, RMSS, RMS, 'XmlGroupResourceDto')
xrd.metadata=meta
xrd.value.childResources = []
xrd.parentPath = basepath
# crp contains the final variable required by the web service that contains the previously created data types.
crp = s.getComplexType(ssn, RMSS, RMS, 'CreateResourceParam')
crp.resource = xrd

result2 = s.executesingleoperationType(ssn, RMSS, RMS, 'createResource', crp)

# Upload VOTable in the created group
print("Uploading VOTable")
grouppath = basepath  + str(result1.id)
data = open(votFile).read()
# VOTable has to be uploaded in base64 encoding.
data64 = base64.standard_b64encode(data)
result3 = s.executesingleoperationList(ssn, RMSS, RMS, 'importVOTable', 'ImportVOTableParam', [('parentPath', grouppath), ('votable', data64)])


# Set the VOTable as the inputs for the workflow execution.
print("Setting execution inputs")
executionInputs = s.getComplexType(ssn, WEMSS, WEMS, 'SetExecutionInputParam')
executionInputs.executionId = result1.id
instanceData = open(votInstance).read()
# The string @path@ from the instance data file is replaced here by the instance data path used in the VOTable.
instanceData = instanceData.replace("@path@", basepath + str(result1.id) + "/spenvis/instancetable/instancedata/")
executionInputs.instanceData.append(base64.standard_b64encode(instanceData))
result4 = s.executesingleoperationType(ssn, WEMSS, WEMS, 'setExecutionInputs', executionInputs)


# Start execution
print("Starting the execution")
result5 = s.executesingleoperation(ssn, WEMSS, WEMS, 'startExecution', 'ExecutionDto', 'id', result1.id)

# Check status until not in RUNNING state. It could be FINISHED or ERROR.
while 1: 
    statustype = s.getComplexType(ssn, WEMSS, WEMS, 'ExecutionIDDto')
    statustype.id = result1.id
    status = s.executesingleoperationType(ssn, WEMSS, WEMS, 'getWorkflowExecutionStatus', statustype)
    if status.state == "RUNNING":
        print("Still in RUNNING state.")
        time.sleep(5)
    else:
        print("State: "+ status.state)
        break


# Get VOTable for the whole output information
print("Getting output VOTable")
path = '/' + username + '/projects/'+prjname+'/runs/'+execname + '/data'
outputvot = s.executesingleoperation(ssn, RMSS, RMS, 'exportVOTTable', 'ExportVOTableParam', 'resourcePath', path)
# Downloaded VOT comes as base64 zipped file. 
outputvot = base64.b64decode(outputvot.votable)
target = open('output_votable.zip','w')
target.write(outputvot)
target.close()
print("Output VOTable saved as output_votable.zip")

# Get VOTable for a single output group.
path = path+"/iterations/0001/sapreEarth_Trajectory"
outputvot = s.executesingleoperation(ssn, RMSS, RMS, 'exportVOTTable', 'ExportVOTableParam', 'resourcePath', path)
# Downloaded VOT comes as base64 zipped file. 
outputvot = base64.b64decode(outputvot.votable)
target = open('output_votable_traj.zip','w')
target.write(outputvot)
target.close()
print("Output VOTable for trajectory saved as output_votable_traj.zip")

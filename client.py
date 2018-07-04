import sapi

s = sapi.Session("global.conf","session_01getExecutionList.conf")
s.readglobalconfig()
ssn = s.login()
r = s.executeconfigfile(ssn)
print("---->",r)
for result in r[0].executionList:

    if result.name == "exec_api_01":
        result2 = s.executesingleoperation(ssn, "WorkflowExecutionManagementServiceService", "WorkflowExecutionManagementService?wsdl", "getWorkflowExecutionStatus", "ExecutionIDDto", "id", result.id)
        print(result2)
        result3 = s.executesingleoperation(ssn, "WorkflowExecutionManagementServiceService", "WorkflowExecutionManagementService?wsdl", "getExecutionOutputs", "ExecutionIDDto", "id", result.id)
        print(result3)


h = sapi.Hook(s)
afile = open("test.out","w")
afile.write(h.getResource(result3).__repr__())
afile.close()


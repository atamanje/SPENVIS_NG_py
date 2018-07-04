#!/usr/bin/env python

# Import section
import sys
import argparse
import base64
import datetime
import string
import time

from configobj import ConfigObj

from suds.client import Client
from suds import WebFault
from suds.sax.element import Element

class Hook:
	"""
	Human-friendly class that provides convenient hooks with same-name operations as those
found in the wsdl definition but that provide better output and work similar to macros.
	"""
	def __init__(self, session):
		self.session = session

	def getExecutionOutputs(self, resultlist):
		"""
		Hook function for getExecutionOutputs from webservice WorkflowExecutionManagementServiceService
		that receives GetExecutionList from a project as resultlist and returns a dictionary
		of the form {executionid: executionoutputs,}
		"""
		webservice = "WorkflowExecutionManagementServiceService"
		webservicefile = "WorkflowExecutionManagementService?wsdl"

		executionsdict = {}

		for result in resultlist.executionList:

			tempresult = self.session.executesingleoperation(self.session.ssn, webservice, webservicefile, "getExecutionOutputs", "ExecutionIDDto", "id", result.id)
				
			executionsdict[result.id] = tempresult
		return executionsdict


	def getResource(self, resultlist):
		"""
		Hook function for getResource from webservice "ResourceManagementServiceService
		that receives getExecutionOutputsList as resultlist adn returns a dictionary
		of the from {executionid: outputparampath}

		"""
		webservice = "ResourceManagementServiceService"
		webservicefile = "ResourceManagementService?wsdl"
		
		resourcesdict = {}

		for result in resultlist.outputParamPath:
			
			tempresult = self.session.executesingleoperation(Self.session.ssn, webservice, webservicefile, "getResource", "GetResourceParam", "resourcePath", result)
			if "XmlLinkResourceDto" in tempresult.__repr__():
				realresource = tempresult.resource.value.linkValue
				tempresult = self.session.executesingleoperation(self.session.ssn, webservice, webservicefile, "getResource", "GetResourceParam", "resourcePath", realresource)
			
			strtempresult = tempresult.__repr__()
			if "XmlStringResourceDto" in strtempresult:
				actualdata = tempresult.resource.value.stringValue

			elif "XmlArrayResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.array1D
				except:
					print("no 1D array found")
				try:
					actualdata = tempresult.resource.value.array2D
				except:
					print("no 2D array found")
				try:
					actualdata = tempresult.resource.value.array3D
				except:
					print("no 3D array found")

			elif "XmlFileResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.data
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlBooleanResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.isBoolValue
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlDateTimeResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.datetimeValue
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlDoubleResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.doubleValue
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlIntegerResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.intValue
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlLongResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.longValue
				except Exception as e:
					print("NOT TESTED YET",e)

			elif "XmlTokenResourceValueDto" in strtempresult:
				try:
					actualdata = tempresult.resource.value.tokenValue
				except Exception as e:
					print("NOT TESTED YET",e)

#            elif "XmlSequenceResourceValueDto" in strtempresult:
#                try:
#                    actualdata = tempresult.resource.value.FIXME
#                except Exception as e:
#                    print("NOT TESTED YET",e)


			else:
				print("ACTUALDATANOTSTRING",strtempresult)
				
			resourcesdict[result] = actualdata

		return resourcesdict

class Session:

	def __init__(self, globalconfigfile="global.conf", sessionconfigfile="session.conf"):
		self.globalconfigfile = globalconfigfile
		self.sessionconfigfile = sessionconfigfile
		self.globalconfig = {}
	
	def readglobalconfig(self):
		globalconfig = ConfigObj(self.globalconfigfile)
	
		serversection = globalconfig['Server']
		baseURL = serversection['baseURL']
	
		usersection = globalconfig['User']
		username = usersection['username']
		password = usersection['password']

		webservice = usersection['webservice']
		webservicefile = usersection['webservicefile']
	
		spenvissection = globalconfig['Spenvis']
		ns = spenvissection['ns']
		mainurl = spenvissection['mainurl']

		self.globalconfig = {
			"baseURL":baseURL,"username":username,
			"password":password,"webservice":webservice,"webservicefile":webservicefile,
			"spenvissection":spenvissection,"ns":ns,"mainurl":mainurl,
		}


	def login(self):

		url = "/".join([self.globalconfig["baseURL"],
						self.globalconfig["webservice"],self.globalconfig["webservicefile"]])
		clientlogin = Client(url)
		token = clientlogin.service.authenticate(username=self.globalconfig["username"],
											 password=self.globalconfig["password"])

		ssnns = (self.globalconfig["ns"], self.globalconfig["mainurl"])
		ssn = Element('SecureToken', ns=ssnns).setText(token)

		self.ssn = ssn                                        

		return ssn

	def executeconfigfile(self,ssn):
		"""
		This method reads the session configuration file and traverses the tree structure running the pertinent
		operations attached to webservices in order and using nesting as priority.
		"""

		sessionconfig = ConfigObj(self.sessionconfigfile)
		sessionresult = []
		referencedresults = {}

		for s in sessionconfig.sections:

			section = sessionconfig[s]
			url = "/".join([self.globalconfig["baseURL"],
							section["webservice"],section["webservicefile"]])
			client = Client(url)
			client.set_options(soapheaders=ssn)
                        
			for operation in section.sections:
				items = section[operation].items()
				hook = False
				extraPairs=[]
				print("items:", items)
				for key,values in items:
                                        #debug
                                        print("Processing k,v:", key, values)
					try:
						# First check if we already have a same-name referenced result
						referencedresult = referencedresults[values[2]]
						print("values",values[2])
					except:
						try:
							# i.e: Check 'myresult' under [[["getResource"]]]
							# [["getExecutionOutputs"]]
							#   myresult = 'id',"ExecutionIDDto",'113'
							#   [[["getResource"]]]
							#   param1 = 'resourcePath',"GetResourceParam", myresult

							referencedresult = values.values()[0][2]
							print("values2",values.values()[0][2])
						except:
							# i.e: Check normal situation, like '113' 
							# [["getExecutionOutputs"]]
							#   myresult = 'id',"ExecutionIDDto",'113'
							
							# Several options for the type
							extraPairs = [(values[0], values[2])]
							count = 3
							while len(values) > count:
								extraPairs.append((values[count],values[count+1]))
								count = count+2
							
							referencedresult = values[2]
							print("values3",values[2])

					# We check that out key has a hook attached and create the associated method
					if key in ["getResource", "getExecutionOutputs"]:
						hook = True
						h = Hook(self)
						h.operation = getattr(h, key)

					else:
						hook = False
						p = client.factory.create(values[1])
						print("Creating...", values[1])
						for pairs in extraPairs:
                                                        if pairs[1].startswith('sapi_read:'):
                                                                fileread = open(pairs[1][len('sapi_read:'):]).read()
                                                                pairs = [pairs[0], base64.standard_b64encode(fileread)]
							setattr(p,pairs[0],pairs[1])
						
					if hook:
						try:
							rresult = referencedresults[referencedresult]
						except KeyError:
							print("{0} referenced but no prior reference with that name exists, check your configuration file".format(referencedresult))
							raise

						# We run our hooks
						if "GetExecutionOutputsResp" in result.__repr__():
							hookresult = h.operation(rresult)
							referencedresults[key] = hookresult
							sessionresult.append(hookresult)
						elif "GetExecutionListResp" in result.__repr__():
							hookresult = h.operation(rresult)
							referencedresults[key] = hookresult
							sessionresult.append(hookresult)
					else:
						op = getattr(client.service, operation)
						try:
							result = op(p)
							referencedresults[key] = result
							sessionresult.append(result)
						except WebFault as w:
							error = w
							referencedresults[key] = error
							sessionresult.append(error)

		return sessionresult            

	
	def executesingleoperation(self, ssn, webservice, webservicefile, operation, complexdata, attribute, value):
		#print("execute single operation", complexdata, attribute, value)
		url = "/".join([self.globalconfig["baseURL"],
							webservice,webservicefile])
		"""
		This method is useful to perform a single operation through a specific webservice. Reuses the global configuration.
		"""
		client = Client(url)
		client.set_options(soapheaders=ssn)
		
		p = client.factory.create(complexdata)
		setattr(p, attribute, value)
		op = getattr(client.service, operation)
		
		try:
			result = op(p)
		except WebFault as w:
			result = w
 
		return result

	def executesingleoperationList(self, ssn, webservice, webservicefile, operation, complexdata, pairList):
		#print("execute single operation with several attributes", complexdata, pairList)
		url = "/".join([self.globalconfig["baseURL"],
							webservice,webservicefile])
		"""
		This method is useful to perform a single operation through a specific webservice. Reuses the global configuration.
		"""
		client = Client(url)
		client.set_options(soapheaders=ssn)
		
		p = client.factory.create(complexdata)

		for pair in pairList: 
			setattr(p, pair[0], pair[1])
		op = getattr(client.service, operation)

		
		try:
			result = op(p)
		except WebFault as w:
			result = w
 
		return result
        
        def getComplexType(self, ssn, webservice, webservicefile,complextype):
		"""
		This method returns a default object of the complextype requested.
		"""
		url = "/".join([self.globalconfig["baseURL"], webservice,webservicefile])
		client = Client(url)
		client.set_options(soapheaders=ssn)
		return client.factory.create(complextype)
	def executesingleoperationType(self, ssn, webservice, webservicefile, operation, complexdata):
		"""
		This method executes a single operation using the provided data as argument.
		"""
		url = "/".join([self.globalconfig["baseURL"], webservice,webservicefile])
		client = Client(url)
		client.set_options(soapheaders=ssn)
		
		op = getattr(client.service, operation)
		
		try:
			result = op(complexdata)
		except WebFault as w:
			result = w
 
		return result

        def createExecution(self, ssn, username,prjname, execname, workflow, votFile, votInstance):
                """
                This method creates an execution and all the necessary data related to it, leaving the execution ready to be started.
                """
                
                WEMSS = "WorkflowExecutionManagementServiceService"
                WEMS  = "WorkflowExecutionManagementService?wsdl"
                RMSS  = "ResourceManagementServiceService"
                RMS   = "ResourceManagementService?wsdl"
                basepath = '/'+username+'/projects/'+prjname+'/data/'

                # Create execution
                paramlist = [("projectId", prjname), ("executionName", execname), ("workflowPath" ,workflow)]
                result1 = self.executesingleoperationList(ssn, WEMSS, WEMS, "initializeExecution", "InitializeExecutionParam", paramlist)

                # Create group to store VOTable.
                # Some complex types has to be created as the 'createResource' service requires complex data types.
                now = datetime.datetime.now()
                # Create and fill the meta data.
                meta = self.getComplexType(ssn, RMSS, RMS, 'XmlGroupResourceMetaDto')
                meta.id = 0
                meta.name = result1.id
                meta.created = now
                meta.createdBy = ""
                meta.lastModified = now
                meta.lastModifiedBy = ""
                meta.sizeInBytes=0
                # Create the Xml Group Resource DTO needed and copy here the meta data.
                xrd = self.getComplexType(ssn, RMSS, RMS, 'XmlGroupResourceDto')
                xrd.metadata=meta
                xrd.value.childResources = []
                xrd.parentPath = basepath
                # crp contains the final variable required by the web service that contains the previously created data types.
                crp = self.getComplexType(ssn, RMSS, RMS, 'CreateResourceParam')
                crp.resource = xrd

                result2 = self.executesingleoperationType(ssn, RMSS, RMS, 'createResource', crp)

                # Upload VOTable in the created group
                grouppath = basepath  + str(result1.id)
                data = open(votFile).read()
                # VOTable has to be uploaded in base64 encoding.
                data64 = base64.standard_b64encode(data)
                result3 = self.executesingleoperationList(ssn, RMSS, RMS, 'importVOTable', 'ImportVOTableParam', [('parentPath', grouppath), ('votable', data64)])


                # Set the VOTable as the inputs for the workflow execution.
                executionInputs = self.getComplexType(ssn, WEMSS, WEMS, 'SetExecutionInputParam')
                executionInputs.executionId = result1.id
                instanceData = open(votInstance).read()
                # The string @path@ from the instance data file is replaced here by the instance data path used in the VOTable.
                instanceData = instanceData.replace("@path@", basepath + str(result1.id) + "/spenvis/instancetable/instancedata/")
                executionInputs.instanceData.append(base64.standard_b64encode(instanceData))
                result4 = self.executesingleoperationType(ssn, WEMSS, WEMS, 'setExecutionInputs', executionInputs)

                # Return the ID of the execution just created.
                return result1.id

        def startExecution(self, ssn, execId):
                WEMSS = "WorkflowExecutionManagementServiceService"
                WEMS  = "WorkflowExecutionManagementService?wsdl"

                result = self.executesingleoperation(ssn, WEMSS, WEMS, 'startExecution', 'ExecutionDto', 'id', execId)
                

        def getExecutionStatus(self, ssn, execId):
                WEMSS = "WorkflowExecutionManagementServiceService"
                WEMS  = "WorkflowExecutionManagementService?wsdl"
                statustype = self.getComplexType(ssn, WEMSS, WEMS, 'ExecutionIDDto')
                statustype.id = execId
                status = self.executesingleoperationType(ssn, WEMSS, WEMS, 'getWorkflowExecutionStatus', statustype)
                return status

        def getVOT(self, ssn, username, prjname, execname):
                RMSS  = "ResourceManagementServiceService"
                RMS   = "ResourceManagementService?wsdl"
                path = '/' + username + '/projects/'+prjname+'/runs/'+execname + '/data'
                outputvot = self.executesingleoperation(ssn, RMSS, RMS, 'exportVOTTable', 'ExportVOTableParam', 'resourcePath', path)
                # Downloaded VOT comes as base64 zipped file. 
                outputvot = base64.b64decode(outputvot.votable)
                return outputvot




#if __name__=="__main__":
#
#	parser = argparse.ArgumentParser(description='Manage SPENVIS through console')
#
#	parser.add_argument('--globalconfig', default='global.conf', help='Global configuration file')
#	parser.add_argument('--sessionconfig', default='session.conf', help='Session configuration file')
#	
#	args = vars(parser.parse_args())
#
#	globalconfig = ConfigObj(args['globalconfig'])
#
#	s = Session(args['globalconfig'],args['sessionconfig'])
#	s.readglobalconfig()
#	ssn = s.login()
#	r = s.executeconfigfile(ssn)
#
#	print(r)
#	sys.exit(0)

#!/usr/bin/env python3

from turtle import update
import requests
import sys
import json
from rich.console import Console
from rich.table import Table
from rich import inspect
from rich import print as rprint
from rich.prompt import Prompt
from rich.tree import Tree


# http GET https://portainer-url:9443/api/stacks X-API-Key:your_api_key_here

# global vars
access_token = '<add_access_token_here>'
base_url = '<provide_internal_portainer_URL_here>'
authHeader = {'X-API-Key': access_token, 'Connection': 'close'}
console = Console()

#################################################################################################
#     Functions                ##################################################################
#################################################################################################

def makeWebRequest(method, functionParms1, functionParms2=""):
#	request = f"{base_url}" + 
	if (functionParms2 != ""):
		rq = functionParms1 + ", body=" + functionParms2
	else:
		rq = functionParms1
		
	try:
		if method == 'get':
			r = requests.get(rq, headers=authHeader, timeout=6.0)
		elif method == 'post':
			r = requests.post(rq, headers=authHeader, timeout=30.0)
		r.raise_for_status()
	except requests.exceptions.HTTPError as errh:
		print("An Http Error occurred:\n", repr(errh))
		exit()
	except requests.exceptions.ConnectionError as errc:
		print("An Error Connecting to the API occurred:\n", repr(errc))
		exit()
	except requests.exceptions.Timeout as errt:
		print("A Timeout Error occurred:\n", repr(errt))
		exit()
	except requests.exceptions.RequestException as err:
		print("An Unknown Error occurred:\n", repr(err))
		exit()
		
	return r.json()

def getContainers(envId):

	response = makeWebRequest("get", f"{base_url}/endpoints/{envId}/docker/containers/json")

	containers = []
	for i in range(response.__len__()):
		dataSet = dict(response[i])
		container = dict(name=dataSet["Names"][0].replace("/", ""), id=dataSet["Id"], ImageID=dataSet["ImageID"])
		containers.append(container)

	return containers


def updateStack(stackId):
	
	response = makeWebRequest("post", f"{base_url}/stacks/{stackId}/stop")

	rprint(response)
	
	

	#get container image for delete
	#image = getContainerImage(f"{containerId}", 2)
	
	#delete image
		
#################################################################################################
#     user input                #################################################################
#################################################################################################
		

def setEnvironment():
	
			
	response = makeWebRequest("get", f"{base_url}/endpoints")
	
	environments = dict()
	for i in range(response.__len__()):
		name = response[i]["Name"]
		id = response[i]["Id"]
		environments[name] = id

	print("Please select the ID to pick the environment for use")
	print("ID : Environment")
	for value,key in environments.items():
		print(key, ':', value)
		
	valid = False
	while(valid == False):
		selection = input("Selection=")	
		for key,value in environments.items():
			#print(selection, "=", value)
			if int(selection) == int(value):
				valid = True
				return selection
		print("Invalid entry! Please select an ID Listed above...")


def setContainer(envId):

	containers = getContainers(envId)

	print("Please select the Container to upgrade")
	print("Select# : Container")
	for i in containers:
		print(containers.index(i) + 1, " : ", i["name"])
	valid = False
	while(valid == False):
		selection = int(input("Selection: "))
		if (selection > containers.__len__()) or (selection < 1):
			print("Please select a value in the range of 1 -", containers.__len__())
		else:
			valid = True
	selection = containers[selection-1]
	return selection


def setStack():
	
	response = makeWebRequest("get", f"{base_url}/stacks")
	environmentList = makeWebRequest("get", f"{base_url}/endpoints")

	environments = dict()
	for i in range(environmentList.__len__()):
		name = environmentList[i]["Name"]
		id = environmentList[i]["Id"]
		environments[id] = name

	tableDictionary = dict()

	table = Table(title="Stacks Available")
	table.add_column("Entry #", no_wrap=True, justify="center")
	table.add_column("Status", no_wrap=True, justify="center")
	table.add_column("Name", no_wrap=True, justify="center")
	table.add_column("Environment", no_wrap=True, justify="center")
	for i in range(response.__len__()):
		if (response[i]["Status"] == 1):
			table.add_row(str(i+1), "Online", response[i]["Name"], environments[response[i]["EndpointId"]], style="green")
		else:
			table.add_row(str(i+1), "Offline", response[i]["Name"], environments[response[i]["EndpointId"]], style="red")
		tableDictionary[i+1] = [response[i]["Name"], response[i]["Id"], response[i]["EndpointId"]]


	print("")
	console.print(table)

	print("")

	while True:
		try:
			stackNum = int(input('Please select a stack to update: '))
			if stackNum < 1 or stackNum > int(len(tableDictionary) + 1):
				raise ValueError
			break
		except ValueError:
			console.print("Invalid integer. The number must be between 1 and", len(tableDictionary) + 1, style="red")

	selection = {
		'stackNum': stackNum,
		'Name': tableDictionary[stackNum][0],
		'Id': tableDictionary[stackNum][1],
		'EnvironmentName': "",
		'EnvironmentId': tableDictionary[stackNum][2],
		'Containers': list()
	}

	selection["EnvironmentName"] = environments[selection["EnvironmentId"]]

	totalContainersEnv = getContainers(selection['EnvironmentId'])

	for i in range(totalContainersEnv.__len__()):
		if totalContainersEnv[i]["name"].startswith(selection["Name"]):
			selection["Containers"].append((totalContainersEnv[i]))

	#rprint(selection)
	del totalContainersEnv
	return selection
		
#Function for redeploying a container based on a git update in Gitea 
#http://10.29.29.11:3003
def gitRedeploy(stackId):
	
	body = {
		
	}
	
	response = makeWebRequest("get", f"{base_url}/stacks/{stackId}/git/redeploy", body)
	

	#def updateStack(stackId):
	

#################################################################################################
#################################################################################################
#################################################################################################


############
#   MAIN   #
############

valid = False
while (valid == False):
	rprint("[red]Do you want to update a stack or a standalone container?")
	stack_or_container = Prompt.ask("[green]1 : Stack\n2 : Container\nSelection")
	try:
		stack_or_container = int(stack_or_container)
	except:
		print("Not a number...")
	if stack_or_container == 1 or stack_or_container == 2:
		valid = True


# 1 is for Stacks
if stack_or_container == 1:
	stack = setStack()

	# visualization of selection
	stackTree = Tree(f'[green]{stack["EnvironmentName"]} Stack', style="bold")
	containerTree = stackTree.add(stack["Name"])
	for i in range(stack["Containers"].__len__()):
		containerTree.add(f'[blue]{stack["Containers"][i-1]["name"]}')
	rprint("\n", stackTree, "\n")

	rprint(f'[bold][red]Are you sure you wish to update the {stack["Name"]} stack?\nThis will stop the stack -> delete the image of each container -> start the stack again')

	answer = Prompt.ask("[Y]es  [N]o")
	if answer == ('n' or 'N' or 'No' or 'no'):
		exit()
	elif answer == ('y' or 'Y' or 'Yes' or 'yes'):
		updateStack(stack["Id"])

# 2 is for Containers
elif stack_or_container == 2:
	envSelection = setEnvironment()
	containerSelection = setContainer(envSelection)


exit()
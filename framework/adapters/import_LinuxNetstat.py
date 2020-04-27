import re
from arangoTools import *
import tools

def readFile(hostFile):

	#open switch list file for reading
	hF = open(hostFile, "r")
	output = dict()
	#read each host and perform actions, sequentially
	lines = hF.readlines()
	counter=1
	for i in range(0, len(lines)):
		proto = None
		localAddress = None
		localPort = None
		foreignAddress = None
		foreignPort = None
		process = None
		state = None
		processID=None
		line = lines[i]
		if("Internet connections" not in line and "PID/Program name" not in line):
			if(line!=None):
				proto = re.search(r'^[A-Za-z]{3,5}', line)
				if(proto): proto=proto.group(0).strip()
				localForeign = re.findall(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}:[\d*]{1,5})', line)
				localtemp = localForeign[0].strip()
				localtemp = re.findall(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}):([\d*]{1,5})',localtemp)[0]
				foreigntemp = localForeign[1].strip()
				foreigntemp = re.findall(r'(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}):([\d*]{1,5})',foreigntemp)[0]
				foreignAddress = foreigntemp[0]
				foreignPort = foreigntemp[1]
				localAddress = localtemp[0]
				localPort = localtemp[1]
				process = re.search(r'([\w\/.]+\s*)$', line)
				if process:
					process=process.group(0).strip()
					temp1 = re.findall(r'(\d+\/)(\w+)',process)
					temp2 = re.findall(r'(\d+)(\/..\/.+)', process)
					if (len(temp1) > 0):
						temp1 = temp1[0]
						processID = temp1[0].strip('/')
						processName = temp1[1]
					else:
						if (len(temp2) > 0):
							temp2 = temp2[0]
							processID = temp2[0]
							processName = temp2[1]
			if ("LISTEN" in line):
				state = "LISTEN"


			output[counter] = {"protocol": proto, "localIP": localAddress, 'localPort':localPort, "foreignIP":foreignAddress, 'foreignPort':foreignPort,"state":state, "name":processName, 'processID': processID}
			counter = counter+1
	hF.close()
	return output

#pprint(readFile("data\\new\\scada-a\\netstat.txt", "badabaa"))

def store(sourceName,scope, nodeip, nodeName, data, hash, date, client):
	checkStart = client['metaelement'].fetchByExample({'type': "startpoint", "label": "start"}, batchSize=100)
	if (len(checkStart) == 0):
		startKey = storeMetaelementArango('metaelement', 'startpoint', 'start', client)
	else:
		startKey = checkStart[0]._id
	checkTP = client['metaelement'].fetchByExample({'type': "timepoint","label": date}, batchSize = 100)
	if (len(checkTP) == 0):
		tpKey=storeMetaelementArango('metaelement','timepoint',date, client )
		storeAssocArango('metaelementAssoc', startKey, tpKey, 'startTimepoint', client)
	else:
		tpKey= checkTP[0]._id
	srcId = storeMetaelementArango('metaelement', 'source', str(sourceName)+'_'+str(nodeName), client)
	srcK = srcId.split('/')[1]
	tempsrc = client['metaelement'].fetchDocument(srcK)
	tempsrc['hash'] = hash
	tempsrc['scope'] = scope
	tempsrc.patch()
	storeAssocArango('metaelementAssoc', tpKey, srcId, 'timepointSource', client)
	#nodeKey = storeElementArango('element', 'node', 'general', str(nodeip)+';;'+str(nodeName), None, client)
	nodeKey = storeElementArango('element', 'node', 'general', str(nodeip), None, client)
	zoned=dict()
	zonedSrc=set()
	zonedIf = set()
	nodeIf = set()
	nodeZone = tools.returnNetworkZone2args(nodeip)
	netwzoneKey = storeElementArango('element', 'zone', 'network', nodeZone, None, client)
	zoned[nodeZone] = netwzoneKey
	nodeInterfaceKey = storeElementArango('element', 'interface', 'network', nodeip, None, client)
	# Connecting source with zone with interface
	storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceZone', client)
	zonedSrc.add((srcId, netwzoneKey))
	storeAssocArango('elementAssoc', netwzoneKey, nodeInterfaceKey, 'zoneInterface', client)
	zonedIf.add((netwzoneKey, nodeInterfaceKey))

	for val in data.values():
		serviceName=val.get('name').strip()
		localIP=val.get('localIP').strip()
		localPort=val.get('localPort').strip()
		foreignIP=val.get('foreignIP').strip()
		foreignPort=val.get('foreignPort').strip()
		protocol=val.get('protocol').strip()
		state=val.get('state')
		locZone=None
		if(localIP!='0.0.0.0' and localIP!='127.0.0.1'):
			locZone =tools.returnNetworkZone2args(localIP)

		else:
			locZone=nodeZone
		if(foreignIP!='0.0.0.0' and foreignIP!='127.0.0.1'):
			forZone = tools.returnNetworkZone2args(foreignIP)
		if(locZone not in zoned):
				netwzoneKey = storeElementArango('element', 'zone', 'network', locZone, None, client)
				storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceZone', client)
				zoned[locZone]=netwzoneKey
		else: netwzoneKey = zoned.get(locZone)
		#Creating the interfaces

		if(localIP!='0.0.0.0' and localIP!='127.0.0.1'):
			interfaceKey = getInterfaceByExample(nodeKey,localIP,'element',client)
			if(interfaceKey==None):
				interfaceKey = storeElementArango('element', 'interface', 'network', localIP, None, client)
		else:interfaceKey=nodeInterfaceKey

		#Connecting source with zone with interface
		if ((netwzoneKey, interfaceKey) not in zonedIf):
			storeAssocArango('elementAssoc', netwzoneKey, interfaceKey, 'zoneInterface', client)
			zonedIf.add((netwzoneKey, interfaceKey))

		#Reasoning over foreign interface
		#foreignInterfaceKey=getForeignInterfaceByExample(nodeKey,foreignIP,'element',client)
		#if(foreignInterfaceKey==None):
			#foreignInterfaceKey = storeElementArango('element', 'interface', 'network', foreignIP, None, client)
		#foreignZone=tools.create24Zone(foreignIP)
		#if (foreignZone not in zoned):
			#fnetwzoneKey = storeElementArango('element', 'zone', 'network', zone, None, client)
			#zoned[foreignZone] = fnetwzoneKey
		#else:
			#fnetwzoneKey = zoned.get(zone)
		#if(fnetwzoneKey!=None):
			#storeAssocArango('metaelementAssoc', srcId, fnetwzoneKey,'sourceZone', client)
			#storeAssocArango('elementAssoc', fnetwzoneKey, foreignInterfaceKey, 'zoneInterface', client)


		if((interfaceKey,nodeKey) not in nodeIf):
			storeAssocArango('elementAssoc', interfaceKey,nodeKey, 'interfaceNode', client)
			nodeIf.add((interfaceKey,nodeKey))

		if(tools.isEqual(state,'LISTEN')):
			serviceNameKey = storeElementArango('element', 'softwareInstance', 'server', serviceName, None, client)
			protocolKey = storeElementArango('element', 'property', 'protocol', protocol, None, client)
			# Properties for protocol
			protoDestPort = storeElementArango('element', 'property', 'destinationPort', foreignPort, None, client)
			protoLocalPort = storeElementArango('element', 'property', 'localPort', localPort, None, client)
			# Associations
			storeAssocArango('elementAssoc', protocolKey, protoDestPort, 'property', client)
			storeAssocArango('elementAssoc', protocolKey, protoLocalPort, 'property', client)
			storeAssocArango('elementAssoc', serviceNameKey, protocolKey, 'property', client)
			storeAssocArango('elementAssoc', nodeKey, serviceNameKey, 'nodeServer', client)

		if (tools.isEqual(state, 'ESTABLISHED')):
			flow=None
			#TODO:1. Add foregin interface 2. Create flow between the local and the foreign interface
			#Flow specific logic
			#serviceNameKey = storeElementArango('element', 'flow', 'data', serviceName, None, client)
			#protocolKey = storeElementArango('element', 'protocol', 'undefined', protocol, None, client)
			#Properties for protocol
			#protoDestPort = storeElementArango('element', 'property', 'destinationPort', foreignPort, None, client)
			#protoLocalPort = storeElementArango('element', 'property', 'localPort', localPort, None, client)
			#Associations
			#storeAssocArango('elementAssoc', protocolKey, protoDestPort, 'property', client)
			#storeAssocArango('elementAssoc', protocolKey, protoLocalPort, 'property', client)
			#storeAssocArango('elementAssoc', serviceNameKey, protocolKey, 'flowProtocol', client)
			#storeAssocArango('elementAssoc', nodeKey, serviceNameKey, 'flowProtocol', client)
			#storeAssocArango('elementAssoc', serviceNameKey, foreignInterfaceKey, 'flowProtocol', client)

def run(sourceName, scope, nodeip, nodeName, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"), dataFile)
		store(sourceName,scope, nodeip, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")

#pprint(readFile("..\\data\\scada-b\\netstat-b.txt"))
#run('netstat','system','192.168.109.20','bldas01', "..\\data\\scada-a\\netstat.txt", tools.creationDate("..\\data\\scada-a\\netstat.txt"), createConArango('claimOmania'))
#run('netstat','system','192.168.109.22','bldas02', "..\\data\\scada-b\\netstat-b.txt", tools.creationDate("..\\data\\scada-b\\netstat-b.txt"), createConArango('claimOmania'))

import re
import tools
from arangoTools import *


def readFile(hostFile):
	#open switch list file for reading
	hF = open(hostFile, "r")
	switchname=None
	output = dict()
	vlanDict = dict()
	#read each host and perform actions, sequentially
	lines = hF.readlines()
	for i in range(0, len(lines)):
		line = lines[i]
		if ("hostname" in line):
			switchname = (re.findall(r"(\".*\")", line))[0].replace("\"", "").replace("\"", "")
		elif "vlan" in line:
			vlan=line.strip()
			read=True
			j=i
			name=None
			untagged=None
			tagged=None
			ipAddress=None
			while(read):
				j=j+1
				if "name" in lines[j]:
					name = re.findall(r"(\".*\")", lines[j])[0].replace("\"", "").replace("\"", "").strip()
				elif "untagged" in lines[j] and "no untagged" not in lines[j]:
					untagged = re.findall(r"[0-9]{0,2}-[0-9]{0,2}|[0-9][^ \t\n\r\f\v\,]{0,2}", lines[j])
				elif "tagged" in lines[j] and "untagged" not in lines[j]:
					tagged = re.findall(r"[0-9]{0,2}-[0-9]{0,2}|[0-9][^ \t\n\r\f\v\,]{0,2}", lines[j])
				elif "ip address" in lines[j]:
					ipAddress = re.findall(r'\d+\.\d+\.\d+\.\d+', lines[j])
				elif "exit" in lines[j]:
					read=False
					i=j
			vlanDict[vlan]={"name":name, "untagged":untagged, "tagged":tagged,"ip":ipAddress}

	output[switchname]=  vlanDict
	hF.close()
	return output

####################################################################################################
###Writing the file
####################################################################################################



def store(sourceName, scope, data, hash, date, client):
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
	sname=next(iter(data.keys()))
	srcId = storeMetaelementArango('metaelement', 'source', str(sourceName)+'_'+str(sname), client)
	srcK = srcId.split('/')[1]
	tempsrc = client['metaelement'].fetchDocument(srcK)
	tempsrc['hash'] = hash
	tempsrc['scope'] = scope
	tempsrc.patch()
	storeAssocArango('metaelementAssoc', tpKey, srcId, 'timepointSource', client)
	for key, val in data.items():
		switchname = key
		nodeSet=set()
		for k, v in val.items():
			vlan = k
			vlanName = v.get("name")
			tagged = v.get("tagged")  # trunk port
			untagged = v.get("untagged")  # access port
			if ((tagged != None or untagged != None) and v.get("ip") != None):
				managementIP = v.get("ip")[0]
				managementMask = v.get("ip")[1]
				#zone = managementIP.split('.')
				#zone[3] = ('0')
				#zone = '.'.join(zone)
				zone=tools.returnNetworkZone2args(managementIP)
				if(switchname not in nodeSet):
					#nodeKey = storeElementArango('element', 'node', 'embedded', str(managementIP)+';;'+str(switchname), None, client)
					nodeKey = storeElementArango('element', 'node', 'embedded',
												 str(managementIP), None, client)
					nodeSet.add(switchname)
				netwKey = storeElementArango('element', 'interface', 'network', managementIP, None, client)
				netwzoneKey = storeElementArango('element', 'zone', 'network', zone, None, client)
				storeAssocArango('elementAssoc', netwKey, nodeKey, 'zoneNode', client)
				storeAssocArango('elementAssoc', netwzoneKey, netwKey, 'zoneNode', client)
				storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceNetwork', client)

				vlanIDArango = storeElementArango('element', 'property', 'vlanID', vlan, None, client)
				vlanArango = storeElementArango('element', 'property', 'vlanName', vlanName, None, client)
				untaggedArango = storeElementArango('element', 'property', 'accessPorts', untagged, None, client)
				taggedArango = storeElementArango('element', 'property', 'trunkPorts', tagged, None,
														client)
				storeAssocArango('elementAssoc', netwKey, vlanIDArango, 'Property', client)
				storeAssocArango('elementAssoc', netwKey, vlanArango, 'Property', client)
				storeAssocArango('elementAssoc', netwKey, untaggedArango, 'Property', client)
				storeAssocArango('elementAssoc', netwKey, taggedArango, 'Property', client)


def run(sourceName,scope, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName, scope, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


#run('HP-Procurve','system', "..\\data\\hp-procurve\\HP-Procurve_startup.txt", tools.creationDate("..\\data\\hp-procurve\\HP-Procurve_startup.txt"), createConArango('claimOmania'))

#print(tools.creationDate("..\\data\\hp-procurve\\HP-Procurve_startup.txt"))
#pprint(readFile("..\\data\\hp-procurve\\HP-Procurve_startup.txt"))
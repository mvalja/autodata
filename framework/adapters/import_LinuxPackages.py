import re
from arangoTools import *

def readFile(hostFile):

	#open switch list file for reading
	hF = open(hostFile, "r")
	output = dict()
	#read each host and perform actions, sequentially
	lines = hF.readlines()
	for i in range(0, len(lines)):
		package = None
		version = None
		source = None
		architecture = None
		line = re.findall(r'[\w.\-\/:]+',lines[i])
		if("Loaded plugins" not in line and "Installed Packages" not in line):
			if(line!=None and len(line)==3):
				package=line[0].strip(":").rstrip()
				if('x86_64' in package):
					architecture='x86_64'
					package=package.strip('.x86_64')
				if('i686' in package):
					architecture='i686'
					package=package.strip('.i686')
				if ('noarch' in package):
					package = package.strip('.noarch')
				version=line[1].strip(":").rstrip()
				source=line[2].strip(":").rstrip()
			if (len(line) == 1):
				package = line[0].strip(":").rstrip()
				if (len(lines[i+1]) == 2):
					version = lines[i+1].strip(":").rstrip()
					source = lines[i+1].strip(":").rstrip()

			if(package!=None):output[package] = {"version": version, "source": source, 'architecture': architecture}
	hF.close()
	return output

#termin= (readFile("..\\data\\scada-a\\installed.txt"))
#for k, v in termin.items():
	#print(k,v.get('version'), v.get('architecture'))



def store(sourceName,scope, sourceIP, nodeName, data, hash, date, client):
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
	#Get the zone
	zone = tools.returnNetworkZone2args(sourceIP)
	zoneID = storeElementArango('element', 'zone', 'network', zone, None, client)
	storeAssocArango('metaelementAssoc', srcId, zoneID, 'sourceInterface', client)

	# Get the node
	interfaceID = storeElementArango('element', 'interface', 'network', sourceIP, None, client)
	storeAssocArango('elementAssoc', zoneID, interfaceID, 'zoneInterface', client)
	#nodeID = storeElementArango('element', 'node', 'general', str(sourceIP)+';;'+str(nodeName), None, client)
	nodeID = storeElementArango('element', 'node', 'general', str(sourceIP), None, client)
	storeAssocArango('elementAssoc', interfaceID, nodeID, 'interfaceNode', client)
	for key, val in data.items():
			softname=key
			softsource=val.get("source")
			softvers=val.get("version")
			softArch=val.get("architecture")
			#Objects
			softInst = storeElementArango('element', 'softwareInstance', 'undefined', softname, None, client)
			softsource = storeElementArango('element', 'property', 'source', softsource, None, client)
			softPropertyVers = storeElementArango('element', 'property', 'version', softvers, None, client)

			#Associations
			storeAssocArango('elementAssoc', nodeID, softInst, 'nodeSoftware', client)
			storeAssocArango('elementAssoc', softInst, softsource, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyVers, 'softwareProperty', client)

			if(softArch!=None):
				softArch = storeElementArango('element', 'property', 'architecture', softArch, None, client)
				storeAssocArango('elementAssoc', softInst, softArch, 'softwareProperty', client)

#pprint(readFile("data\\new\\bldad01\\Software.xml"))
#store('Linux_Config', '192.168.109.21', readFile("data\\new\\scada-a\\installed.txt"), None, tools.creationDate("data\\new\\scada-a\\installed.txt"), createConArango('claimOmania'))

def run(sourceName,scope, sourceIP, nodeName, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName,scope, sourceIP, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


run('yum-list','system','192.168.109.20','blads01', "..\\data\\scada-a\\installed.txt", tools.creationDate("..\\data\\scada-a\\installed.txt"), createConArango('Lab'))
run('yum-list','system','192.168.109.22','blads02', "..\\data\\scada-b\\installed-b.txt", tools.creationDate("..\\data\\scada-b\\installed-b.txt"), createConArango('Lab'))
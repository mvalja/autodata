import re
from arangoTools import *
from ontology import paperRUN

def readFile(hostFile):
	#open switch list file for reading
	hF = open(hostFile, "r")
	output = dict()
	#read each host and perform actions, sequentially
	lines = hF.readlines()
	linesCounter=iter(range(0, len(lines)))
	for i in linesCounter:
		package = None
		version = None
		source = None
		architecture = None
		line = re.findall(r'[\w.\-\/:]+',lines[i])
		if("Loaded plugins" not in lines[i] and "Installed Packages" not in lines[i]):
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
			elif (line!=None and len(line) == 1):
				package = line[0].strip(":").strip('x86_64').rstrip()
				next(linesCounter)
				line2 = re.findall(r'[\w.\-\/:]+', lines[i+1])
				if (len(line2) == 2):
					version = line2[0].strip(":").rstrip()
					source = line2[1].strip(":").rstrip()
			elif (line!=None and len(line) == 2):
				package = line[0].strip(":").strip('x86_64').rstrip()
				version = line[1].strip(":").rstrip()
				line2 = re.findall(r'[\w.\-\/:]+', lines[i + 1])
				next(linesCounter)
				if (len(line2) == 1):
					source = line2[0].strip(":").rstrip()
			if(package!=None):
				#Apply ontology
				packageL=paperRUN.getLinStandard(package, version, paperRUN.linVerCutoff, [], paperRUN.coll, paperRUN.collAssoc, paperRUN.con)
				packageN=packageL[0]
				version=packageL[1]
				clss= paperRUN.getSoftwareClass(packageN, paperRUN.coll, paperRUN.con)
				group= paperRUN.getSoftwareGroupLin(packageN, clss, [])
				output[packageN] = {'oldpackage':package,"version": version, "source": source, 'architecture': architecture, 'class':clss, 'group':group}

	hF.close()
	return output

#termin= (readFile("..\\data\\scada-a\\installed.txt"))
#for k, v in termin.items():
	#print(k,v.get('version'), v.get('architecture'))

pprint(readFile("..\\data\\scada-a\\installed.txt"))

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
			softClass=val.get('class')
			softGrp = val.get('group')
			#Objects
			if(softClass!='unknown'):
				softInst = storeElementArango('element', 'softwareInstance', softClass, softname, None, client)
			else:
				softInst = storeElementArango('element', 'softwareInstance', 'undefined', softname, None, client)
			softsource = storeElementArango('element', 'property', 'source', softsource, None, client)
			softPropertyVers = storeElementArango('element', 'property', 'version', softvers, None, client)
			softPropertyGrp = storeElementArango('element', 'property', 'group', softGrp, None, client)
			#Associations
			storeAssocArango('elementAssoc', nodeID, softInst, 'nodeSoftware', client)
			storeAssocArango('elementAssoc', softInst, softsource, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyVers, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyGrp, 'softwareProperty', client)

			if(softArch!=None):
				softArch = storeElementArango('element', 'property', 'architecture', softArch, None, client)
				storeAssocArango('elementAssoc', softInst, softArch, 'softwareProperty', client)

#pprint(readFile("..\\data\\scada-a\\installed.txt"))
#store('Linux_Config', '192.168.109.21', readFile("data\\new\\scada-a\\installed.txt"), None, tools.creationDate("data\\new\\scada-a\\installed.txt"), createConArango('claimOmania'))

def run(sourceName,scope, sourceIP, nodeName, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName,scope, sourceIP, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


run('yum-list','system','192.168.109.20','blads01', "..\\data\\scada-a\\installed.txt", tools.creationDate("..\\data\\scada-a\\installed.txt"), createConArango('OntoLab'))
run('yum-list','system','192.168.109.22','blads02', "..\\data\\scada-b\\installed-b.txt", tools.creationDate("..\\data\\scada-b\\installed-b.txt"), createConArango('OntoLab'))
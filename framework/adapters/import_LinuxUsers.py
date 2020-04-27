import re
from arangoTools import *

def readFile(hostFile):

	#open switch list file for reading
	hF = open(hostFile, "r")
	output = dict()
	#read each host and perform actions, sequentially
	lines = hF.readlines()
	username = None
	userid = None
	groupid = None
	homedir = None
	usershell = None
	for i in range(0, len(lines)):
		line = re.findall(r':?:.+?\t|[^:]+?(?=:)|[^:]+|::',lines[i])
		if(line!=None):
			username=line[0].strip(":").rstrip()
			userid=line[2].strip(":").rstrip()
			groupid=line[3].strip(":").rstrip()
			homedir=line[5].strip(":").rstrip()
			usershell=line[6].strip(":").rstrip()

		output[username]={"userId":userid,"groupId":groupid,"homeDir":homedir,"userShellLoc":usershell}

	hF.close()
	return output

#pprint(readFile("data\\new\\scada-a\\users.txt", "badabaa"))

def store(sourceName,scope, mainIP, nodeName, data, hash, date, client):
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
	#nodeKey = storeElementArango('element', 'node', 'general', str(mainIP)+';;'+str(nodeName), None, client)
	nodeKey = storeElementArango('element', 'node', 'general', str(mainIP), None, client)
	#zone = mainIP.split('.')
	#zone[3] = ('0')
	#zone = '.'.join(zone)
	zone=tools.returnNetworkZone2args(mainIP)
	netwzoneKey = storeElementArango('element', 'zone', 'network', zone, None, client)
	interfaceKey = storeElementArango('element', 'interface', 'network', mainIP, None, client)
	aclKey = storeElementArango('element', 'accessControl', 'local', nodeName, None, client)
	storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceZone', client)
	storeAssocArango('elementAssoc', netwzoneKey, interfaceKey, 'zoneInterface', client)
	storeAssocArango('elementAssoc', interfaceKey, nodeKey, 'interfaceNode', client)
	storeAssocArango('elementAssoc', nodeKey,aclKey, 'interfaceNode', client)
	for key, val in data.items():
		gid=val.get('groupId')
		homeDir=val.get('homeDir')
		uid=val.get('userId')
		shellLoc=val.get('userShellLoc')
		uacKey = storeElementArango('element', 'userAccount', 'undefined', key, None, client)
		gidKey = storeElementArango('element', 'property', 'groupId', gid, None, client)
		homeDirKey = storeElementArango('element', 'property', 'homeDir', homeDir, None, client)
		uidKey = storeElementArango('element', 'property', 'userId', uid, None, client)
		shellLocKey = storeElementArango('element', 'property', 'shellLocation', shellLoc, None, client)

		#Associations
		storeAssocArango('elementAssoc', aclKey, uacKey, 'property', client)
		storeAssocArango('elementAssoc', uacKey, gidKey, 'property', client)
		storeAssocArango('elementAssoc', uacKey, homeDirKey, 'flowProtocol', client)
		storeAssocArango('elementAssoc', uacKey, uidKey, 'flowProtocol', client)
		storeAssocArango('elementAssoc', uacKey, shellLocKey, 'flowProtocol', client)

def run(sourceName,scope, ip, nodeName, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName,scope, ip, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


#run('etc-passwd','system', '192.168.109.20','bldas01',"..\\data\\scada-a\\users.txt", tools.creationDate("..\\data\\scada-a\\users.txt"), createConArango('claimOmania'))
#run('etc-passwd','system', '192.168.109.22','bldas02',"..\\data\\scada-b\\users-b.txt", tools.creationDate("..\\data\\scada-b\\users-b.txt"), createConArango('claimOmania'))

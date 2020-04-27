import xml.etree.ElementTree as ET
import tools
from arangoTools import *


def readFile(hostFile):
	ns= {'xmlns':"http://schemas.microsoft.com/powershell/2004/04"}
	#open switch list file for reading
	tree = ET.parse(hostFile)
	root = tree.getroot()
	output = dict()
	compName=None
	caption=None #Caption
	disabled=None #Disabled
	domain=None #Domain
	local= None #LocalAccount
	lockout = None #Lockout
	acName=None #Name
	passwordReq=None #PasswordRequired
	passwordExp=None #PasswordExpires
	sid=None #SID
	for i in root.findall("xmlns:Obj",ns):
		props = i.find("xmlns:Props", ns)
		ms = i.find("xmlns:MS/xmlns:S", ns)
		compName=ms.text
		for s in props:
			if ('Nil' not in s.tag):
				if (tools.isEqual(s.attrib.get('N') , "Name")):
					name=s.text
				if (tools.isEqual(s.attrib.get('N') , "LocalAccount")):
					local = s.text
				if (tools.isEqual(s.attrib.get('N') , "Domain")):
					domain = s.text
				if(tools.isEqual(s.attrib.get('N'), "PasswordRequired")):
					passwordReq = s.text
				if (tools.isEqual(s.attrib.get('N') , "SID")):
					sid = s.text
				if (tools.isEqual(s.attrib.get('N') , "PasswordExpires")):
					passwordExp = s.text
		if (sid != None):
				output[sid] = {"name": name, "localAccount": local, "domain": domain, "compName":compName,'passwordRequired':passwordReq, 'passwordExpires':passwordExp }
	return(output)

#pprint(readFile("..\\data\\bldde01\\UserAccounts.xml"))

def store(sourceName, scope, mainIP,nodeName, data, hash, date, client):
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
	zone = tools.create24Zone(mainIP)
	netwzoneKey = storeElementArango('element', 'zone', 'network', zone, None, client)
	interfaceKey = storeElementArango('element', 'interface', 'network', mainIP, None, client)
	#aclKey = storeElementArango('element', 'accessControl', 'local', sourceName, None, client)
	storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceZone', client)
	storeAssocArango('elementAssoc', netwzoneKey, interfaceKey, 'zoneInterface', client)
	storeAssocArango('elementAssoc', interfaceKey, nodeKey, 'interfaceNode', client)
	domainz=dict()


	for key, val in data.items():

		compName=val.get('compName')
		assert tools.isEqual(compName,nodeName)
		domain=val.get('domain')
		localA=val.get('localAccount')
		name=val.get('name')
		passwordExp=val.get('passwordExpires')
		passwordReq=val.get('passwordRequired')

		if(domain not in domainz and tools.isEqual(localA,'true')):
			aclKey = storeElementArango('element', 'accessControl', 'local', domain, None, client)
			storeAssocArango('elementAssoc', nodeKey, aclKey, 'NodeAC', client)
			domainz[domain] = aclKey
		elif (domain not in domainz and tools.isEqual(localA, 'false')):
			aclKey = storeElementArango('element', 'accessControl', 'domain', domain, None, client)
			storeAssocArango('elementAssoc', nodeKey, aclKey, 'NodeAC', client)
			domainz[domain] = aclKey
		else:
			aclKey=domainz.get(domain)
		sidKey = storeElementArango('element', 'property', 'SID', key, None, client)
		if(tools.isEqual(passwordReq,'true')):
			uacKey = storeElementArango('element', 'userAccount', 'password', name, None, client)
			oCKey = storeElementArango('element', 'property', 'passwordExpires', passwordExp, None, client)
		elif(tools.isEqual(passwordReq,'false')):
			uacKey = storeElementArango('element', 'userAccount', 'undefined', name, None, client)
			oCKey = storeElementArango('element', 'property', 'passwordExpires', passwordExp, None, client)
		if(tools.isEqual(passwordReq,'true') or tools.isEqual(passwordReq,'false')):
			# Associations
			storeAssocArango('elementAssoc', aclKey, uacKey, 'property', client)
			storeAssocArango('elementAssoc', uacKey, oCKey, 'property', client)
			storeAssocArango('elementAssoc', uacKey, sidKey, 'property', client)


def run(sourceName,scope, ip, nodeName,dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :',dataFile,' from ',sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName, scope, ip,nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


#run('Powershell-Get-UserAccounts','system', '192.168.109.21','bldad01',"..\\data\\bldad01\\UserAccounts.xml", tools.creationDate("..\\data\\bldad01\\ADDomainUsers.xml"), createConArango('claimOmania'))
#run('Powershell-Get-UserAccounts','system', '192.168.109.23','bldde01',"..\\data\\bldde01\\UserAccounts.xml", tools.creationDate("..\\data\\bldde01\\ADDomainUsers.xml"), createConArango('claimOmania'))
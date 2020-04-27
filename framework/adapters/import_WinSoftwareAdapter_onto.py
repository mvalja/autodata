import xml.etree.ElementTree as ET
import tools
from arangoTools import *
from ontology import paperRUN

def readFile(hostFile):
	ns= {'xmlns':"http://schemas.microsoft.com/powershell/2004/04"}
	#open switch list file for reading
	tree = ET.parse(hostFile)
	root = tree.getroot()
	output = dict()
	for i in root.findall("xmlns:Obj",ns):
		refid = i.get("RefId")
		pidentity = None
		pname = None
		pversion = None
		pvendor = None
		pinstallloc = None
		pinstalldate = None
		ppackagecode = None
		powner = None
		props=i.find("xmlns:Props", ns)
		for s in props:
			if(s.attrib.get('N') == "Name" and (s.tag!="xmlns:Nil",ns)):
				pname=s.text
			elif (s.attrib.get('N') == "InstallLocation" and (s.tag!="xmlns:Nil",ns)):
				pinstallloc = s.text
			elif (s.attrib.get('N') == "InstallDate" and (s.tag!="xmlns:Nil",ns)):
				pinstalldate = s.text
			elif (s.attrib.get('N') == "PackageCode" and (s.tag!="xmlns:Nil",ns)):
				ppackagecode = s.text
			elif (s.attrib.get('N') == "Vendor" and (s.tag!="xmlns:Nil",ns)):
				pvendor = s.text
			elif (s.attrib.get('N') == "Version" and (s.tag!="xmlns:Nil",ns)):
				pversion = s.text
			elif (s.attrib.get('N') == "RegOwner" and (s.tag!="xmlns:Nil",ns)):
				powner = s.text
			elif (s.attrib.get('N') == "IdentifyingNumber" and (s.tag!="xmlns:Nil",ns)):
				pidentity = s.text
		if(pidentity!=None):
			vendor=pvendor.split(' ')[0].replace(',','')
			pnameL=paperRUN.getWinStandard(pname, pversion,vendor , [], paperRUN.winBlckL, paperRUN.coll,paperRUN.collAssoc, paperRUN.con)
			pname=pnameL[0]
			pversion=pnameL[1]
			pclass=paperRUN.getSoftwareClass(pname, paperRUN.coll, paperRUN.con)
			pgroup=paperRUN.getSoftwareGroupWin(pname, paperRUN.groupList, pclass, paperRUN.exclssL)
			if(pgroup==None):pgroup=pname
			output[pidentity]={"name":pname, "version":pversion,"vendor":vendor, "installLocation": pinstallloc,
								   "lastChange": pinstalldate, "packageCode": ppackagecode, "regOwner": powner, 'class':pclass,'group':pgroup}

	return output

pprint(readFile("..\\data\\bldad01\\Software.xml"))

def store(sourceName, scope, sourceIP, nodeName,data, hash, date, client):
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
	#Get the node
	interfaceID = storeElementArango('element', 'interface', 'network', sourceIP, None, client)

	#nodeID = storeElementArango('element', 'node', 'general', str(sourceIP)+';;'+str(nodeName), None, client)
	nodeID = storeElementArango('element', 'node', 'general', str(sourceIP) , None, client)
	storeAssocArango('elementAssoc', interfaceID, nodeID, 'interfaceNode', client)
	netwzone=tools.create24Zone(sourceIP)
	zoneID = storeElementArango('element', 'zone', 'network', netwzone, None, client)
	storeAssocArango('metaelementAssoc', srcId, zoneID, 'sourceZone', client)
	storeAssocArango('elementAssoc', zoneID, interfaceID, 'zoneInterface', client)
	if (len(nodeID) != 0):
		for val in data.values():
			softname=val.get("name")
			softvendor=val.get("vendor")
			softvers=val.get("version")
			softChange=val.get("lastChange")
			softPackageId=val.get("packageCode")
			softClass=val.get("class")
			softGroup=val.get("group")
			#Objects
			if(softClass!=None and softClass!='unknown'):
				softInst = storeElementArango('element', 'softwareInstance', softClass, softname, None, client)
			else:
				softInst = storeElementArango('element', 'softwareInstance', 'undefined', softname, None, client)
			softPropertyVendor = storeElementArango('element', 'property', 'vendor', softvendor, None, client)
			softPropertyVers = storeElementArango('element', 'property', 'version', softvers, None, client)
			softPropertyChange = storeElementArango('element', 'property', 'lastChange', softChange, None, client)
			softPropertyPackId = storeElementArango('element', 'property', 'packageCode', softPackageId, None, client)
			if(softGroup!=None):
				softPropertyGroup = storeElementArango('element', 'property', 'group', softGroup, None, client)
				storeAssocArango('elementAssoc', softInst, softPropertyGroup, 'softwareProperty', client)
			#Associations
			storeAssocArango('elementAssoc', nodeID, softInst, 'nodeSoftware', client)
			storeAssocArango('elementAssoc', softInst, softPropertyVendor, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyVers, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyChange, 'softwareProperty', client)
			storeAssocArango('elementAssoc', softInst, softPropertyPackId, 'softwareProperty', client)

	else: print('No node to add data to')
"""
tektek=readFile("..\\data\\bldde01\\Software.xml")
for k, v in tektek.items():
	print(v.get('vendor')+','+v.get('name')+','+v.get('version'))
"""
#store('Windows_Config', '192.168.109.5', readFile("..\\data\\bldad01\\Software.xml"), None, tools.creationDate("..\\data\\bldad01\\Software.xml"), createConArango('claimOmania'))

def run(sourceName, scope, ip,nodeName, dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName,scope, ip, nodeName,hostsData, hash, date, con)
	else: print(dataFile + " already imported")


run('Powershell-Win32_Product','system', '192.168.109.21','bldad01',"..\\data\\bldad01\\Software.xml", tools.creationDate("..\\data\\bldad01\\Software.xml"), createConArango('OntoLab'))
run('Powershell-Win32_Product','system', '192.168.109.23','bldde01',"..\\data\\bldde01\\Software.xml", tools.creationDate("..\\data\\bldde01\\Software.xml"), createConArango('OntoLab'))
run('Powershell-Win32_Product','system', '192.168.109.110','winscanner',"..\\data\\winscanner\\Software.xml", tools.creationDate("..\\data\\winscanner\\Software.xml"), createConArango('OntoLab'))
import xml.etree.ElementTree as ET
import tools
from arangoTools import *

def readFile(hostFile):
	tree = ET.parse(hostFile)
	root = tree.getroot()
	output = dict()
	userList = []
	ifList = []
	system=root.find('system')
	interfaces=root.find('interfaces')
	filters = root.find('filter')
	vlans = root.find('vlans')
	#System
	hostname=system.find('hostname').text
	domain=system.find('domain').text
	dns=system.find('dnsserver').text
	users = system.findall('user')
	for u in users:
		name=u.find("name").text
		groupname=u.find("groupname").text
		uid=u.find("uid").text
		userList.append({'userName':name, 'groupName':groupname, "uid":uid})
	#Interfaces
	iftype=None
	ifname=None
	ifdescr=None
	ifsubnet=None
	for child in interfaces:
		iftype=name=child.tag
		ifname=child.find('if').text
		ifdescr=child.find('descr').text
		ifaddr=child.find('ipaddr').text
		if(child.find('subnet')!=None):
			ifsubnet=child.find('subnet').text

		ifList.append({"ifType":iftype,"ifName":ifname,"ifDescription":ifdescr,'ifAddress':ifaddr, "ifSubnet": ifsubnet})
	vlans = root.find('vlans')
	vlanList = []
	for v in vlans.findall('vlan'):
		vtag=v.find('tag').text
		vdescr=v.find('descr').text
		vlanif=v.find('vlanif').text
		vlanList.append({"vlanIf":vlanif,"vTags":vtag,"vDescription":vdescr})
	filterList = []
	ftype=None
	finterf=None
	fipprot=None
	fdirect=None
	fupdated=None
	for f in filters.findall('rule'):
		ftype=f.find('type').text
		finterf=f.find('interface').text
		fipprot=f.find('ipprotocol').text
		if(f.find('direction')!=None):
			fdirect=f.find('direction').text
		#ffloat=f.get('floating').text

		if(f.find('updated/time')!=None):
			fupdated=f.find('updated/time').text
		sources=f.find('source')
		sourceList = []
		for s in sources:
			if(s!='any'):
				sourceType=s.tag
				sourceLabel=s.text
				sourceList.append({'sourceType': sourceType, 'sourceLabel': sourceLabel})
			else:
				sourceList.append({'sourceType':'any','sourceLabel':None})
		destinations=f.find('destination')
		destinationList = []
		for d in destinations:
			if(d!='any'):
				destType=d.tag
				destLabel=d.text
				destinationList.append({'destType': destType, 'destLabel': destLabel})
			else:
				destType = 'any'
				destinationList.append({'destType': 'any', 'destLabel': None})
		filterList.append({"sources":sourceList,"destinations":destinationList,"filterType":ftype,"interfaces":finterf,"filterProtocol":fipprot, "filterDirection":fdirect,"updated":fupdated})

	output['pfSense']={"hostName": hostname,"domain":	domain, "dns": dns,"userList": userList,"ifList":ifList,"vlanList":vlanList,"filterList":filterList}

	return(output)



#pprint(readFile("..\\data\\pfsense\\config-fw-01_localdomain.xml"))

####################################################################################################
###Writing the file
####################################################################################################

def store(sourceName, scope, mainip ,data, hash, date, client):
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
	srcId = storeMetaelementArango('metaelement', 'source', str(sourceName)+'_'+str(mainip), client)
	srcK = srcId.split('/')[1]
	tempsrc = client['metaelement'].fetchDocument(srcK)
	tempsrc['hash'] = hash
	tempsrc['scope'] = scope
	tempsrc.patch()
	storeAssocArango('metaelementAssoc', tpKey, srcId, 'timepointSource', client)
	pf=data.get('pfSense')
	domain=pf.get('domain')
	filterL=pf.get('filterList')
	hostName=pf.get('hostName')
	interfaces=pf.get('ifList')
	users=pf.get('userList')
	vlans=pf.get('vlanList')
	#nodeKey = storeElementArango('element', 'node', 'embedded', str(mainip)+';;'+str(hostName), None, client)
	nodeKey = storeElementArango('element', 'node', 'embedded', str(mainip), None, client)
	aclKey = storeElementArango('element', 'accessControl', 'local', domain, None, client)
	storeAssocArango('elementAssoc', nodeKey, aclKey, 'zoneNode', client)
	for inf in interfaces:
			zone=None
			ifAddress=inf.get('ifAddress')
			ifDescr=inf.get('ifDescription')
			ifName=inf.get('ifName')
			ifSubn=inf.get('ifSubnet')
			if(tools.isEqual(ifSubn,'24')):
				zone=tools.create24Zone(ifAddress)
				netwKey = storeElementArango('element', 'interface', 'network', ifAddress, None, client)
				netwzoneKey = storeElementArango('element', 'zone', 'network', zone, None, client)
				storeAssocArango('elementAssoc', netwzoneKey, netwKey, 'zoneNode', client)
				storeAssocArango('elementAssoc', netwKey, nodeKey, 'zoneNode', client)
				storeAssocArango('metaelementAssoc', srcId, netwzoneKey, 'sourceNetwork', client)
				ifNameKey = storeElementArango('element', 'property', 'interfaceName', ifName, None, client)
				ifDescKey = storeElementArango('element', 'property', 'interfaceDescription', ifDescr, None, client)
				storeAssocArango('elementAssoc', netwKey, ifNameKey, 'property', client)
				storeAssocArango('elementAssoc', netwKey, ifDescKey, 'property', client)
	for us in users:
		groupName=us.get('groupName')
		userName=us.get('userName')
		uid=us.get('uid')
		userKey = storeElementArango('element', 'userAccount', 'local', userName, None, client)
		storeAssocArango('elementAssoc', aclKey, userKey, 'aclUA', client)
		uidKey = storeElementArango('element', 'property', 'uid', uid, None, client)
		storeAssocArango('elementAssoc', userKey, uidKey, 'property', client)
		groupKey = storeElementArango('element', 'property', 'userGroup', groupName, None, client)
		storeAssocArango('elementAssoc', userKey, groupKey, 'property', client)

def run(sourceName,scope,mainIP, nodename ,dataFile, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName, scope, mainIP, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


#run('pfSense_Config','system', "..\\data\\pfsense\\config-fw-01_localdomain.xml", tools.creationDate("..\\data\\pfsense\\config-fw-01_localdomain.xml"), createConArango('claimOmania'))
#run('pfSense_Config','system', '10.1.1.1',"..\\data\\pfsense\\config-fw-01.localdomain-20170502161728.xml", tools.creationDate("..\\data\\pfsense\\config-fw-01.localdomain-20170502161728.xml"), createConArango('claimOmania'))
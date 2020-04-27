from pprint import pprint
import xml.etree.ElementTree as ET
import tools
from arangoTools import *
from xml.etree.ElementTree import iterparse

def readFile(hostFile):
	#ns= {'xmlns':"http://schemas.microsoft.com/powershell/2004/04"}
	#open switch list file for reading
	tree = ET.parse(hostFile)
	root = tree.getroot()
	output = []
	structure=root.findall('structure/section')
	source=None
	destin=None
	protocol=None
	packet = root.findall('packet')
	for sec in packet:
		secelem=sec.findall('section')
		if (tools.isNotEqual('ARP',secelem[4].text) and  tools.isNotEqual('LLMNR',secelem[4].text) and tools.isNotEqual('DHCPv6',secelem[4].text) and tools.isNotEqual('ICMPv6',secelem[4].text)):
			output.append((secelem[2].text,secelem[3].text,secelem[4].text ))
	return output

#pprint(set(readFile("..\\data\\wireshark\\goteborg-test.xml")))
#pprint(set(readFile("..\\data\\wireshark\\summary-packets_fixed.xml")))


def parse_and_remove(filename, path):
	path_parts = path.split('/')
	doc = iterparse(filename, ('start', 'end'))
	# Skip the root element
	next(doc)

	tag_stack = []
	elem_stack = []
	loc=0
	for event, elem in doc:
		if event == 'start':
			tag_stack.append(elem.tag)
			elem_stack.append(elem)
		elif event == 'end':
			#print(tag_stack, path_parts)
			if tag_stack == path_parts:
				loc += 1
				if(loc==3):
					tempL=[]
					tempL.append(elem.text)
				if (loc == 4):
					tempL.append(elem.text)
				if (loc == 5):
					tempL.append(elem.text)
					yield(tempL)
				elem_stack[-2].remove(elem)
			elif(tag_stack != path_parts):
				loc = 0
			try:
				tag_stack.pop()
				elem_stack.pop()
			except IndexError:
				pass

#pprint(set(readFile("..\\data\\wireshark\\goteborg-test.xml")))
#pprint(set(readFile("..\\data\\wireshark\\summary-packets_fixed.xml")))

data=parse_and_remove("F:\\ongoingWork\\ModBusCaps\\unzipped\\converted\\packets_00001_20161115135616.xml", 'packet/section')

counter=0
newS=set()
for d in data:
	src=d[0]
	dst=d[1]
	proto=d[2]
	if (tools.isNotEqual('ARP', proto) and tools.isNotEqual('LLMNR', proto) and tools.isNotEqual(
		'DHCPv6', proto) and tools.isNotEqual('ICMPv6', proto)):
		newS.add(tuple(d))
		counter+=1
print(len(newS))
pprint(newS)
print('All',counter)

####################################################################################################
###Writing the file
####################################################################################################

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
	created = dict()
	zoned= dict()
	noded=dict()
	protod = set()
	flowed = dict()
	cliented = dict()
	servered = dict()
	nodeExist=False
	flowSet=set()
	for da in data:
		source=da[0]
		destin=da[1]
		proto = da[2]
		if(source not in created and source!=sourceIP):
			sourceKey = storeElementArango('element', 'interface', 'network', source, None, client)
			#snodeKey = storeElementArango('element', 'node', 'general', str(source)+';;unknown', None, client) # Alternativ name= source /destin
			snodeKey = storeElementArango('element', 'node', 'general', str(source), None,
										  client)  # Alternativ name= source /destin
			storeAssocArango('elementAssoc', sourceKey, snodeKey, 'interfaceNode', client)
			created[source]=sourceKey
			noded[source] = snodeKey

		if (destin not in created and destin!=sourceIP):
			destinKey = storeElementArango('element', 'interface', 'network', destin, None, client)
			#dnodeKey = storeElementArango('element', 'node', 'general', str(destin)+';;unknown', None, client)
			dnodeKey = storeElementArango('element', 'node', 'general', str(destin), None, client)
			storeAssocArango('elementAssoc', destinKey, dnodeKey, 'interfaceNode', client)
			created[destin] = destinKey
			noded[destin]=dnodeKey

		if(source not in created and source==sourceIP):
			if(nodeExist==False):
				#nodeKey = storeElementArango('element', 'node', 'general', str(source)+';;'+str(nodeName), None, client)
				nodeKey = storeElementArango('element', 'node', 'general', str(source), None,
											 client)
				nodeExist=True
			sourceKey = storeElementArango('element', 'interface', 'network', source, None, client)
			storeAssocArango('elementAssoc', sourceKey, nodeKey, 'interfaceNode', client)
			created[source]=sourceKey
			noded[source] = nodeKey

		if (destin not in created and destin==sourceIP):
			if(nodeExist==False):
				#nodeKey = storeElementArango('element', 'node', 'general', str(destin)+';;'+str(nodeName), None, client)
				nodeKey = storeElementArango('element', 'node', 'general', str(destin), None,
											 client)
				nodeExist=True
			destinKey = storeElementArango('element', 'interface', 'network', destin, None, client)
			storeAssocArango('elementAssoc', destinKey, nodeKey, 'interfaceNode', client)
			created[destin] = destinKey
			noded[destin] = nodeKey

		if(source !=None and destin !=None):
			flowKey = storeElementArango('element', 'flow', 'data', proto, None, client)
			if((destin,proto) not in servered):
				servSoft = storeElementArango('element', 'softwareInstance', 'server', proto, None, client)
				storeAssocArango('elementAssoc', noded.get(destin), servSoft, 'nodeSoftware', client)
				servered[(destin,proto)]=servSoft
			else:
				servSoft=servered.get((destin,proto))
			if((source,proto) not in cliented):
				cliSoft = storeElementArango('element', 'softwareInstance', 'client', proto, None, client)
				storeAssocArango('elementAssoc', noded.get(source), cliSoft, 'nodeSoftware', client)
				cliented[(source,proto)]=cliSoft
			else:
				cliSoft=cliented.get((source,proto))
			storeAssocArango('elementAssoc', cliSoft, flowKey, 'clientServer', client)
			storeAssocArango('elementAssoc', flowKey, servSoft, 'clientServer', client)
			flowed[(source, destin, proto)]=flowKey

		if(proto != None and  (source, destin, proto) not in protod):
			protoKey = storeElementArango('element', 'protocol', 'undefined', proto, None, client)
			storeAssocArango('elementAssoc', flowed.get((source,destin, proto)), protoKey, 'nodeSoftware', client)
			protod.add((source,destin, proto))

		szone=tools.create24Zone(source)
		dzone=tools.create24Zone(destin)
		if(szone not in zoned):
			sourceKey = created.get(source)
			sourcezoneKey = storeElementArango('element', 'zone', 'network', szone, None, client)
			storeAssocArango('elementAssoc',sourcezoneKey, sourceKey, 'zoneInterface', client)
			storeAssocArango('metaelementAssoc', srcId, sourcezoneKey, 'sourceNetwork', client)
			zoned[szone]=sourcezoneKey
		else:
			sourceKey = created.get(source)
			sourcezoneKey = zoned.get(szone)
			storeAssocArango('elementAssoc', sourcezoneKey, sourceKey, 'zoneInterface', client)

		if (dzone not in zoned):
			destinKey = created.get(destin)
			destinzoneKey = storeElementArango('element', 'zone', 'network', dzone, None, client)
			storeAssocArango('elementAssoc', destinzoneKey, destinKey, 'zoneInterface', client)
			storeAssocArango('metaelementAssoc', srcId, destinzoneKey, 'sourceNetwork', client)
			zoned[dzone] = destinzoneKey
		else:
			destinKey = created.get(destin)
			destinzoneKey = zoned.get(dzone)
			storeAssocArango('elementAssoc', destinzoneKey, destinKey, 'zoneInterface', client)

def run(sourceName,scope, sourceIP,nodeName, dataFiles, date, con):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName, scope, sourceIP, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")


#run('winscanner', '10.1.1.112',"..\\data\\p0f\\p0f_output", tools.creationDate("..\\data\\p0f\\p0f_output"), createConArango('Lab'))
#run('winscanner', 'subnet', '10.1.1.112','Winscanner',"..\\data\\p0f\\p0f_output_allLANs", tools.creationDate("..\\data\\wireshark\\summary-packets_fixed.xml"), createConArango('Lab'))
#run('Wireshark', 'subnet','10.1.1.112','Winscanner',"..\\data\\wireshark\\summary-packets_fixed.xml", tools.creationDate("..\\data\\wireshark\\summary-packets_fixed.xml"), createConArango('Lab'))
#run('Wireshark', 'subnet','10.1.1.112','Winscanner',"F:\\ongoingWork\\ModBusCaps\\unzipped\\converted\\packets_00001_20161115135616.xml", tools.creationDate("F:\\ongoingWork\\ModBusCaps\\unzipped\\converted\\packets_00001_20161115135616.xml"), createConArango('Lab'))

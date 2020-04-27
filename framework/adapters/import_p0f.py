import re
import tools
from arangoTools import *
import xml.etree.ElementTree as ET
from ontology import ontologyTools2

def nameSpaceFilter(recordName, data, ns):
    tempname=None
    if (data.find(recordName, ns) != None):
        tempname = data.find(recordName,ns).text
    return tempname

def getPortNames(hostFile):
#open switch list file for reading
	ns= {'xmlns':"http://www.iana.org/assignments", 'id':"service-names-port-numbers"}
	tree = ET.parse(hostFile)
	root = tree.getroot()
	output = dict()
	ports = root.findall('xmlns:record', ns)
	for p in ports:
		protocol=nameSpaceFilter('xmlns:protocol', p, ns)
		description = nameSpaceFilter('xmlns:description', p, ns)
		number=nameSpaceFilter('xmlns:number', p, ns)
		name=nameSpaceFilter('xmlns:name', p, ns)
		if(tools.isNotEqual(number,'0') and name!=None and number!=None):
			output[(number,protocol)]=name
	return output

def readFile(hostFile, portnames):
	#open switch list file for reading
	p0f = open(hostFile, "r")
	output = dict()
	#read each host and perform actions, sequentially
	lines = p0f.readlines()
	synAckSet = []
	for i in range(0, len(lines)):
		line = re.findall(r'\|([\w\d\.\=\/?:\+\s]+)',lines[i])
		if(line!=None):
			mod = re.search(r'mod=([\w\+]*)', lines[i]).group(1).strip()
			date = re.search(r'^\[(\d+\/\d+\/\d+)', lines[i]).group(1).strip()
			cli =line[0].strip('cli=').split('/')[0]
			#cliport=line[0].strip('cli=').split('/')[1]
			srv =line[1].strip('srv=').split('/')[0]
			srvport=line[1].strip('cli=').split('/')[1]
			#if(int(srvport)>10000):srvport='0'
			subj =line[2].partition('=')[2]
			portN=''
			if((srvport, 'tcp') in portnames):
				portN=portnames.get((srvport, 'tcp'))
			if (tools.isEqual(mod, 'syn') or tools.isEqual(mod,'syn+ack')):
				os=line[3].partition('=')[2]
				dist=line[4].partition('=')[2]
				param=line[5].partition('=')[2]
				if('NMap' not in os and 'scan' not in os and portN!=''):
					synAckSet.append((cli, srv, subj, os, dist, portN))

	output['p0f']=synAckSet
	p0f.close()
	return output
#pprint(readFile("..\\data\\p0f\\p0f_output",writeOntologyTrees.getPortNames('..\\ontology\\service-names-port-numbers.xml')))

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
	ozed = set()
	flowed = dict()
	protod = set()
	servered=dict()
	cliented=dict()
	synFormat=data.get('p0f')
	#nodeKey = storeElementArango('element', 'node', 'general', nodeName, None, client)
	nodeExist=False
	for syn in synFormat:
		sourceKey = None
		destinKey = None
		osKey = None
		flowKey = None
		sourcezoneKey = None
		destinzoneKey = None
		snodeKey = None
		dnodeKey = None
		source=syn[0]
		destin=syn[1]
		subj = syn[2] #shows which one is fingerprinted for OS
		os=syn[3]
		dist=syn[4]
		protName=syn[5]
		if(source not in created and source!=sourceIP):
			sourceKey = storeElementArango('element', 'interface', 'network', source, None, client)
			#snodeKey = storeElementArango('element', 'node', 'general', str(source)+';;unknown', None, client) # Alternativ name= source /destin
			snodeKey = storeElementArango('element', 'node', 'general', str(source), None, client)
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
				#nodeKey = storeElementArango('element', 'node', 'general', str(sourceIP)+';;'+str(nodeName), None, client)
				nodeKey = storeElementArango('element', 'node', 'general', str(sourceIP), None,
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

		sourceKey = created.get(source)
		destinKey=created.get(destin)

		if(subj == 'srv'  and os != '???' and (destin, os) not in ozed):
			softInst = storeElementArango('element', 'softwareInstance', 'operatingSystem', os, None, client)
			d=noded.get(destin)
			storeAssocArango('elementAssoc', d, softInst, 'nodeSoftware', client)
			ozed.add((destin, os))

		if (subj == 'cli' and os != '???' and (source, os) not in ozed):
			softInst = storeElementArango('element', 'softwareInstance', 'operatingSystem', os, None, client)
			storeAssocArango('elementAssoc', noded.get(source), softInst, 'nodeSoftware', client)
			ozed.add((source, os))
		if(source!=None and destin !=None):
			destNode =noded.get(destin)
			srcNode =noded.get(source)
			flowKey = storeElementArango('element', 'flow', 'data', protName, None, client)
			if((source,protName) not in cliented):
				cliSoft = storeElementArango('element', 'softwareInstance', 'client', protName, None, client)
				storeAssocArango('elementAssoc', srcNode, cliSoft, 'nodeSoftware', client)
				cliented[(source,protName)]=cliSoft
			else:
				cliSoft=cliented.get((source,protName))
			if ((destin,protName) not in servered):
				servSoft = storeElementArango('element', 'softwareInstance', 'server', protName, None, client)
				storeAssocArango('elementAssoc', destNode, servSoft, 'nodeSoftware', client)  # Could be problematic
				servered[(destin,protName)]=servSoft
			else:
				servSoft=servered.get((destin,protName))

			storeAssocArango('elementAssoc', cliSoft, flowKey, 'clientDfl', client)
			storeAssocArango('elementAssoc', flowKey, servSoft, 'dflServer', client)
			flowed[(source, destin, protName)]=flowKey
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

		if(protName != None and  (source, destin, protName) not in protod):
			protoKey = storeElementArango('element', 'protocol', 'undefined', protName, None, client)
			storeAssocArango('elementAssoc', flowed.get((source,destin, protName)), protoKey, 'nodeSoftware', client)
			protod.add((source,destin, protName))

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


def run(sourceName,scope, sourceIP,nodeName, dataFile, date,  portnames, con):#=getPortNames('adapters\\thirddata\\service-names-port-numbers.xml')):
	date=str(date)
	if(checkExists(dataFile, con)== False):
		print('Importing :', dataFile, ' from ', sourceName)
		hostsData = readFile(dataFile, portnames)
		hash=tools.hashfile(open(dataFile, "rb"),dataFile)
		store(sourceName, scope, sourceIP, nodeName, hostsData, hash, date, con)
	else: print(dataFile + " already imported")

###CHECK THE FIRST DATA! >> edge error

#run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\p0f_output", tools.creationDate("..\\data\\p0f\\p0f_output"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('Lab'))
#run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\nextScanOutput", tools.creationDate("..\\data\\p0f\\nextScanOutput"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('Lab'))
#run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\p0f_output_allLANs", tools.creationDate("..\\data\\p0f\\p0f_output_allLANs"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('Lab'))


#print(tools.creationDate("..\\data\\p0f\\nextScanOutput"))
#pprint(readFile("..\\data\\p0f\\\p0f_output", ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml')))

pprint(readFile("C:\\Temp\\foi\\pcaptxt_02.txt", ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml')))


#print(getSourceClasses('metaelement/4506083',createConArango('claimOmania')))


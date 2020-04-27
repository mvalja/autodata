import re
import tools
from arangoTools import *
import xml.etree.ElementTree as ET
from ontology import ontologyTools2
from ontology import paperRUN


def readFile(hostFile, portnames):
    #open switch list file for reading
    p0f = open(hostFile, "r")
    output = dict()
    #read each host and perform actions, sequentially
    lines = p0f.readlines()
    synAckSet = set()
    for i in range(0, len(lines)):
        osInfo=None
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
                if('and' in os):
                    os=os.split('and')[0]
                elif('or' in os):
                    os = os.split('or')[0]
                if('Microsoft' in os or 'Windows' in os):
                            platform='Windows'
                            duplicatesL = paperRUN.winDuplicatesL
                            versionL=paperRUN.winVersionL
                else:
                            platform='Linux'
                            duplicatesL = paperRUN.linDuplicatesL
                            versionL =[]
                if(os!=None and os!='' and os!='???'):
                    osInfo=paperRUN.getStandardOpsysName(os, platform, duplicatesL, versionL, paperRUN.coll,
                                                  paperRUN.collAssoc, paperRUN.con)
                    dist=line[4].partition('=')[2]
                    param=line[5].partition('=')[2]

                    if('NMap' not in os and 'scan' not in os and int(srvport)<49152):
                        synAckSet.add((cli, srv, subj, ' '.join(osInfo), dist, srvport))
    output['p0f']=synAckSet
    p0f.close()
    return output
#pprint(readFile("..\\data\\p0f\\p0f_output_allLANs",ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml')))

####################################################################################################
###Writing the file
####################################################################################################
"""
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


        if((source, destin, protName) not in flowed and source!=None and destin !=None):
            d =noded.get(destin)
            s =noded.get(source)
            flowKey = storeElementArango('element', 'flow', 'data', protName, None, client)
            if((source,protName) not in cliented):
                cliSoft = storeElementArango('element', 'softwareInstance', 'client', protName, None, client)
                cliented[(source,protName)]=cliSoft
            else:
                cliSoft=cliented.get((source,protName))
            if ((destin,protName) not in servered):
                servSoft = storeElementArango('element', 'softwareInstance', 'server', protName, None, client)
                servered[(destin,protName)]=servSoft
            else:
                servSoft=servered.get((destin,protName))
            storeAssocArango('elementAssoc', s, cliSoft, 'nodeSoftware', client)
            storeAssocArango('elementAssoc', d, servSoft, 'nodeSoftware', client) #Could be problematic
            storeAssocArango('elementAssoc', cliSoft, flowKey, 'clientServer', client)
            storeAssocArango('elementAssoc', flowKey, servSoft, 'clientServer', client)
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

"""
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
		#Creating interfaces and nodes - both are unique
		if(source not in created):
			sourceKey = storeElementArango('element', 'interface', 'network', source, None, client)
			#snodeKey = storeElementArango('element', 'node', 'general', str(source)+';;unknown', None, client) # Alternativ name= source /destin
			snodeKey = storeElementArango('element', 'node', 'general', str(source), None, client)
			storeAssocArango('elementAssoc', sourceKey, snodeKey, 'interfaceNode', client)
			created[source]=sourceKey
			noded[source] = snodeKey

		if (destin not in created):
			destinKey = storeElementArango('element', 'interface', 'network', destin, None, client)
			#dnodeKey = storeElementArango('element', 'node', 'general', str(destin)+';;unknown', None, client)
			dnodeKey = storeElementArango('element', 'node', 'general', str(destin), None, client)
			storeAssocArango('elementAssoc', destinKey, dnodeKey, 'interfaceNode', client)
			created[destin] = destinKey
			noded[destin]=dnodeKey

		sourceKey = created.get(source)
		destinKey=created.get(destin)
	#Creating operaint system
		if(subj == 'srv'  and os != '???' and (destin, os) not in ozed):
			softInst = storeElementArango('element', 'softwareInstance', 'operatingSystem', os, None, client)
			d=noded.get(destin)
			storeAssocArango('elementAssoc', d, softInst, 'nodeSoftware', client)
			ozed.add((destin, os))
		if (subj == 'cli' and os != '???' and (source, os) not in ozed):
			softInst = storeElementArango('element', 'softwareInstance', 'operatingSystem', os, None, client)
			storeAssocArango('elementAssoc', noded.get(source), softInst, 'nodeSoftware', client)
			ozed.add((source, os))

		if(source!=None and destin !=None and (source, destin, protName) not in flowed):
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
				storeAssocArango('elementAssoc', destNode, servSoft, 'nodeSoftware', client)
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

#run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\p0f_output", tools.creationDate("..\\data\\p0f\\p0f_output"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('OntoLab'))
#run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\nextScanOutput", tools.creationDate("..\\data\\p0f\\nextScanOutput"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('OntoLab'))
run('p0f', 'subnet','10.1.1.112','Winscanner',"..\\data\\p0f\\p0f_output_allLANs", tools.creationDate("..\\data\\p0f\\p0f_output_allLANs"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('OntoLab'))


#2#run('p0f', 'subnet','199.206.2.23','Winscanner',"C:\\Temp\\foi\\pcaptxt_00.txt", tools.creationDate("C:\\Temp\\foi\\pcaptxt_00.txt"), ontologyTools2.getPortNames('thirddata\\service-names-port-numbers.xml'), createConArango('OntoLab'))

#print(tools.creationDate("..\\data\\p0f\\nextScanOutput"))
#pprint(readFile("..\\data\\p0f\\\p0f_output_allLANs", writeOntologyTrees.getPortNames('..\\ontology\\service-names-port-numbers.xml')))
#print(getSourceClasses('metaelement/4506083',createConArango('claimOmania')))


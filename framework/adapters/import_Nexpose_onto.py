import xml.etree.ElementTree as ET
from itertools import count
import tools
from arangoTools import *
from ontology import paperRUN
from ontology import ontologyTools2

def generate_id(id_counter):
    id = next(id_counter)
    return id

def hosts(dataFile):
    tree = ET.parse(dataFile)
    root = tree.getroot()
    hostsDict = dict()

    #id_counter = count()
    for i in root.findall("nodes/node"):
        tempCVEL = []
        services = dict()
        opsys = dict()
        nodeName = i.find("names/name")
        if(nodeName is not None):nodeName = nodeName.text
        address = i.get("address")
        riskScore = i.get("risk-score")
        id_counter = count()
        for e in i.findall("endpoints/endpoint"):
            serviceProtocol = e.get("protocol").strip("?")
            servicePort = e.get("port")
            sn = e.find("services/service")
            serviceName = sn.get("name").strip("?")
            services[servicePort]={
            # 'servicePort': servicePort,
            'protocol': serviceProtocol,
            "serviceName": serviceName}
        collected=set()
        for o in i.findall("tests/test"):
                id = o.get("id")
                cveR=[]
                cve=None
                cveR=re.findall(r'cve-[0-9]{4}-[0-9]*',id)
                if(len(cveR)==1):
                    cve=cveR[0]
                if(cve!=None):
                    tempCVEL.append(cve)
        for o in i.findall("fingerprints/os"):
                osVendor = o.get("vendor")
                osFamily = o.get("family")
                osProduct = o.get("product")
                osVersion = o.get("version")
                osArch = o.get("arch")
                osCertainty = o.get("certainty")
                if(osVersion==None):
                    standardName=str(osVendor)+' '+str(osProduct)
                elif(osVersion!=None):
                    if(tools.isEqual(osVendor,osProduct)):
                        standardName=str(osProduct)+' '+str(osVersion)
                    else:
                        standardName=str(osVendor)+' '+str(osProduct)+' '+str(osVersion)
                #print(standardName)
                # Add host
                if(standardName not in collected):
                    if ('Microsoft' in standardName or 'Windows' in standardName):
                        platform = 'Windows'
                        duplicatesL = paperRUN.winDuplicatesL
                        versionL = paperRUN.winVersionL
                    else:
                        platform = 'Linux'
                        duplicatesL = paperRUN.linDuplicatesL
                        versionL = []
                    osInfo = paperRUN.getStandardOpsysName(standardName, platform, duplicatesL, versionL, paperRUN.coll,
                                                           paperRUN.collAssoc, paperRUN.con)
                    opsys[generate_id(id_counter)]={
                        'standardName':osInfo[0],
                        "osVendor":osVendor,
                        "osFamily":osFamily,
                        "osProduct":osProduct,
                        "osVersion":osInfo[1],
                        "osArch":osArch,
                        "osCertainty":osCertainty}
                    collected.add(standardName)
        hostsDict[address] = {
            'name': nodeName,
            "opsys": opsys,
            "services": services,
            'cve':tempCVEL}
    return hostsDict
pprint(hosts("..\data\\nexpose\\nexpose04_12.xml"))

def store(sourceName,scope, data, hash, date, client):
        checkStart = client['metaelement'].fetchByExample({'type': "startpoint", "label": "start"}, batchSize=100)
        if (len(checkStart) == 0):
            startKey = storeMetaelementArango('metaelement', 'startpoint', 'start', client)
        else:
            startKey = checkStart[0]._id
        checkTP = client['metaelement'].fetchByExample({'type': "timepoint","label": date}, batchSize = 100)
        if (len(checkTP) == 0):
            tpKey=storeMetaelementArango('metaelement','timepoint',date, client )
            storeAssocArango('metaelementAssoc', startKey, tpKey, 'startTimepoint', client)
        else: tpKey= checkTP[0]._id
        srcId = storeMetaelementArango('metaelement', 'source', sourceName, client)
        srcK = srcId.split('/')[1]
        tempsrc = client['metaelement'].fetchDocument(srcK)
        tempsrc['hash'] = hash
        tempsrc['scope'] = scope
        tempsrc.patch()
        storeAssocArango('metaelementAssoc', tpKey, srcId, 'timepointSource', client)
        zoneDict=dict()
        for key, val in data.items():
            address = key
            zone= address.split('.')
            zone[3]=('0')
            zone='.'.join(zone)
            if(zone not in zoneDict):
                netwKey=storeElementArango('element', 'zone', 'network', zone, None, client)
                zoneDict[zone] = netwKey
                storeAssocArango('metaelementAssoc', srcId, netwKey, 'sourceNetwork',client )

        for key,val in data.items():
            address = key
            name='unknown'
            if(val.get("name")!=None): name = val.get("name")
            services = val.get("services")
            opsys = val.get("opsys")
            vuln=val.get("cve")
            address = key
            zone= address.split('.')
            zoneShort=zone[0:3]
            zone[3]=('0')
            zone='.'.join(zone)
            services = val.get("services")
            netwKey=zoneDict.get(zone)
            interfaceKey = storeElementArango('element', 'interface', 'network', address, None, client)
            #nodeKey = storeElementArango('element', 'node', 'general', str(address)+';;'+str(name), None, client)
            nodeKey = storeElementArango('element', 'node', 'general', str(address) , None, client)
            storeAssocArango('elementAssoc', netwKey, interfaceKey, 'networkInterface', client)
            storeAssocArango('elementAssoc', interfaceKey, nodeKey, 'interfaceNode', client)

            for d in opsys.values():
                osCertainty = d.get("osCertainty")
                osVendor=d.get("osVendor", "")
                osFamily=d.get("osFamily", "")
                osProduct=d.get("osProduct", "")
                osVersion=d.get("osVersion", "")
                if(osVendor==None):osVendor=""
                if(osFamily==None):osFamily=""
                if(osProduct==None):osProduct=""
                if(osVersion==None):osVersion=""
                #tmpvlue=' '.join((osVendor,osFamily,osProduct,osVersion))
                standardName = d.get("standardName")
                #tmpvlue=(' '.join(OrderedDict.fromkeys(([d.get("osVendor", ""), d.get("osFamily", ""), d.get("osProduct", ""), (d.get("osVersion", "")or "")]))))
                #osName=" ".join(OrderedDict.fromkeys(tmpvlue.split())).strip()
                newName=' '.join((standardName, osVersion))
                spKey = storeElementArango('element', 'softwareInstance', 'operatingSystem', newName, osCertainty, client)
                storeAssocArango('elementAssoc', nodeKey, spKey, 'operatingsystemSoftwareproduct', client)

            for cve in vuln:
                attackName=paperRUN.getAttackName(cve, paperRUN.coll,
                                                           paperRUN.collAssoc, paperRUN.con)
                if(attackName!=None):
                    if(paperRUN.checkForAttack(attackName, nodeKey, 'elementAssoc', client)==False):
                        cveKey = storeElementArango('element', 'property', 'attack', attackName, None, client)
                        storeAssocArango('elementAssoc', nodeKey, cveKey, 'operatingsystemServer', client)

            for k,v in services.items():
                port = k
                protocol = v.get("protocol")
                serviceName = v.get("serviceName")
                serverName = ('-'.join((port,protocol,serviceName)))

                if (serviceName == "unknown"):
                    serviceName = ('-'.join((port, protocol)))
                else:
                    serviceName = ('-'.join((port, protocol, serviceName)))

                servKey = storeElementArango('element', 'softwareInstance', 'server', serviceName, None, client)
                storeAssocArango('elementAssoc', nodeKey, servKey, 'operatingsystemServer', client)

                if (protocol != None):
                    protKey = storeElementArango('element', 'property', 'protocol' ,protocol, None, client)
                    storeAssocArango('elementAssoc', servKey, protKey, 'ServerProtocol', client)

                #if (serverName != None):
                    #srvSpKey = storeElementArango('element', 'softwareInstance', serverName, None, client)
                    #storeAssocArango('elementAssoc', servKey, srvSpKey, 'serverSoftwareproduct', client)


def run(sourceName,scope, dataFile, date, con):
    if(checkExists(dataFile, con)== False):
        print('Importing :',dataFile,' from ',sourceName)
        hostsData = hosts(dataFile)
        #timestamp = str(datetime.date.today())
        hash=tools.hashfile(open(dataFile, "rb"),dataFile)
        #storeBasic(con)
        store(sourceName, scope, hostsData, hash, date, con)
    else: print(dataFile + " already imported")

###run('Nexpose', "..\data\\2014-03-28\\FullXMLReport_v2.xml", '2014-03-28', createConArango('claimOmania'))
#pprint(hosts("..\data\\nexpose\\nexpose04_12.xml"))

run('Nexpose','subnet', "..\data\\nexpose\\nexpose04_12.xml", tools.creationDate("..\data\\nexpose\\nexpose04_12.xml"), createConArango('OntoLab'))
#run('Nexpose','subnet', "..\data\\nexpose\\report.xml", tools.creationDate("..\data\\nexpose\\report.xml"), createConArango('OntoLab'))

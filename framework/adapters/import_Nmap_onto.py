import xml.etree.ElementTree as ET
from itertools import count
import tools
from arangoTools import *
from ontology import paperRUN

def generate_id(id_counter):
    id = next(id_counter)
    return id

def hosts(dataFile):
    nmapTree = ET.parse(dataFile)
    nmapRoot = nmapTree.getroot()
    hostsDict = dict()

    #id_counter = count()
    for i in nmapRoot.findall("host"):
        services = dict()
        opsys = dict()
        collected=set()
        state = i.find("status")
        if state.get("state") =="up":
            addrType = i.find("address")

            id_counter = count()

            if addrType.get("addrtype") == "ipv4":
                address = addrType.get('addr')
                if i.find('os/osmatch')!= None:
                    osName=i.find('os/osmatch').get('name').split('or')[0].split('-')[0]
                    osData=i.find("os/osmatch/osclass")
                    osVendor = osData.get("vendor")
                    osFamily = osData.get('osfamily')
                    osGen = osData.get('osgen')
                    osCertainty = None
                    if osData.get('accuracy') != None:
                        osCertainty = float(osData.get('accuracy'))/100
                    if(osName not in collected):
                        if('Microsoft' in osName or 'Windows' in osName):
                            platform='Windows'
                            duplicatesL = paperRUN.winDuplicatesL
                            versionL=paperRUN.winVersionL
                        else:
                            platform='Linux'
                            duplicatesL = paperRUN.linDuplicatesL
                            versionL =[]
                        osInfo = paperRUN.getStandardOpsysName(osName, platform, duplicatesL, versionL, paperRUN.coll,
                                                               paperRUN.collAssoc, paperRUN.con)
                        opsys[generate_id(id_counter)] = {
                            'osInfo':' '.join(osInfo),
                            "osName": osName,#.split('(')[0],
                            "osVendor": osVendor,
                            "osFamily": osFamily,
                            "osVersion": osGen,
                            "osCertainty": osCertainty}
                        #print(osName.split('(')[0])
                        collected.add(osName)
                for p in i.findall('ports/port'):
                    servicePort = p.get('portid')
                    serviceProtocol = p.get('protocol')
                    serviceName = p.find('service').get('name')
                    serviceSoftware = p.find('service').get('product')
                    serviceState = p.find('state').get('state')
                    services[servicePort] = {
                        # 'servicePort': servicePort,
                        'protocol': serviceProtocol,
                        "serviceName": serviceName,
                        "serviceSoftware": serviceSoftware,
                        "serviceState": serviceState}
                hostsDict[address] = {
                    "opsys": opsys,
                    "services": services}
        else:continue
    return hostsDict
#pprint(hosts('..\\data\\nmap\\04_25_nmap_scan.xml'))

def store(dataSource,scope, data, hash, date, client):
        checkStart = client['metaelement'].fetchByExample({'type': "startpoint","label": "start"}, batchSize = 100)
        if (len(checkStart) == 0):
            startKey=storeMetaelementArango('metaelement','startpoint','start', client )
        else: startKey= checkStart[0]._id

        checkTP = client['metaelement'].fetchByExample({'type': "timepoint","label": date}, batchSize = 100)
        if (len(checkTP) == 0):
            tpKey=storeMetaelementArango('metaelement','timepoint',date, client )
            storeAssocArango('metaelementAssoc', startKey, tpKey, 'startTimepoint', client)
        else: tpKey= checkTP[0]._id
        srcId=storeMetaelementArango('metaelement', 'source', dataSource, client)
        srcK=srcId.split('/')[1]
        tempsrc=client['metaelement'].fetchDocument(srcK)
        tempsrc['hash'] = hash
        tempsrc['scope'] = scope
        tempsrc.patch()
        storeAssocArango('metaelementAssoc', tpKey, srcId, 'timepointSource', client)
         #Source to Network
        zoneDict=dict()
        for key, val in data.items():
            address = key
            zone= address.split('.')
            zone[3]=('0')
            zone='.'.join(zone)
            if(zone not in zoneDict):
                netwKey=storeElementArango('element', 'zone', 'network', zone, None, client)
                zoneDict[zone]=netwKey
                storeAssocArango('metaelementAssoc', srcId, netwKey, 'sourceNetwork',client )

        #Network zone to Opsys
        for key, val in data.items():
            address = key
            zone= address.split('.')
            zone[3]=('0')
            zone='.'.join(zone)
            services = val.get("services")
            netwKey=zoneDict.get(zone)
            opsys = val.get("opsys")

            interfaceKey = storeElementArango('element', 'interface', 'network', address, None, client)
            nodeKey = storeElementArango('element', 'node', 'general', str(address), None, client)
            storeAssocArango('elementAssoc', netwKey, interfaceKey, 'networkInterface', client)
            storeAssocArango('elementAssoc', interfaceKey, nodeKey, 'interfaceNode', client)
            for d in opsys.values():
                osCertainty = d.get("osCertainty")
                osName=d.get("osName").strip()
                osInfo=d.get('osInfo')
                spKey=storeElementArango('element', 'softwareInstance','operatingSystem', osInfo, osCertainty , client)
                storeAssocArango('elementAssoc', nodeKey, spKey, 'nodeSoftware', client)

        #Operating system to Software Product
            for k,v in services.items():
                port = k
                protocol = v.get("protocol")
                serviceName = v.get("serviceName")
                serviceState=v.get('serviceState')
                if(tools.isEqual(serviceState,'open') or tools.isEqual(serviceState,'open|filtered')): #Add only open service ports
                    if(serviceName=="unknown"):
                        serviceName = ('-'.join((port, protocol)))
                    else:
                        serviceName = ('-'.join((port, protocol, serviceName)))
                    serverName = v.get("serviceSoftware")
                    servKey=storeElementArango('element','softwareInstance','server',serviceName, None, client)
                    storeAssocArango('elementAssoc', nodeKey, servKey,'nodeServer',client)
                    if(protocol!=None):
                        protKey = storeElementArango('element', 'property','protocol', protocol, None, client)
                        storeAssocArango('elementAssoc', servKey, protKey, 'property', client)

                    if(serverName!=None):
                        srvSpKey = storeElementArango('element', 'property','serverName', serverName, None, client)
                        storeAssocArango('elementAssoc', servKey, srvSpKey, 'serverSoftwareproduct', client)



def run(sourceName,scope, dataFile, date, con):
    if(checkExists(dataFile, con)== False):
        print('Importing :', dataFile, ' from ', sourceName)
        hostsData = hosts(dataFile)
        #timestamp = str(datetime.date.today())
        hash=tools.hashfile(open(dataFile, "rb"),dataFile)
        #storeBasic(con)
        store(sourceName,scope, hostsData, hash, date, con)
    else: print(dataFile + " already imported")

#store('Nmap', hosts("..\data\\2014-11-06\\nmap_20-10-2014.xml"), tools.hashfile(open("..\data\\2014-11-06\\nmap_20-10-2014.xml", "rb")), '2014-11-06', createConArango('claimOmania'))

run('Nmap','subnet', "..\\data\\nmap\\04_25_nmap_scan.xml", tools.creationDate("..\\data\\nmap\\04_25_nmap_scan.xml"), createConArango('OntoLab'))
#run('Nmap','subnet', "..\\data\\nmap\\all-subnets-SCADAscan.xml", tools.creationDate("..\\data\\nmap\\all-subnets-SCADAscan.xml"), createConArango('OntoLab'))


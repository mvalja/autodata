import xml.etree.ElementTree as ET
import re
from itertools import count
import tools
from arangoTools import *

def generate_id(id_counter):
    id = next(id_counter)
    return id

def hosts(dataFile):
    tree = ET.parse(dataFile)
    root = tree.getroot()
    hostsDict = dict()
    report=root.find("Report")
    #id_counter = count()
    for i in report.findall("ReportHost"):
        collected=set()
        services = dict()
        opsys = dict()
        osName=None
        cpe=None
        nodeName=None
        id_counter = count()
        address=i.get('name')
        for r in i.findall("ReportItem"):
            if ((r.get("port")) != 0):
                servicePort = r.get("port")
                serviceName = r.get("svc_name").replace('?','')
                serviceProtocol = r.get("protocol").replace('?','')
                services[servicePort]={
                'protocol': serviceProtocol,
                "serviceName": serviceName}
        for t in i.findall("HostProperties/tag"):
            #if ((t.get("name")) == "operating-system"): osName = t.text.replace('\n','').strip()
            if ((t.get("name")) == "operating-system"): osName = t.text.split('(')[0].split('\n')[0].strip() #Actually there are multiple options which could be broken down
            if ((t.get("name")) == "cpe-0"): cpe = t.text.split('->')[0].strip()
            if ((t.get("name")) == "netbios-name"): nodeName = t.text
            # Add host
        addedName=re.findall(r"on (.*)", osName)
        if(len(addedName)!=0):
            standardName=addedName[0].replace('release ', '')
        else:
            standardName=osName
        #print(standardName)
        if(standardName not in collected):
            opsys[generate_id(id_counter)]={
                    "osCPE":cpe,
                    "osProduct":osName,
                    "nodeName":nodeName,
                    'standardName':standardName
                }
            collected.add(standardName)
        hostsDict[address] = {
            'name': nodeName,
            "opsys": opsys,
            "services": services}
    return hostsDict

#pprint(hosts("..\data\\nessus\\Authenticated_SCADA_lab_scan_mj3yvv.xml"))



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
            zone=tools.returnNetworkZone2args(address)
            #zone= address.split('.')
            #zone[3]=('0')
            #zone='.'.join(zone)
            if(zone not in zoneDict):
                netwKey=storeElementArango('element', 'zone','network', zone, None, client)
                zoneDict[zone] = netwKey
                storeAssocArango('metaelementAssoc', srcId, netwKey, 'sourceNetwork',client )

        for key,val in data.items():
            if(val.get("name")!=None):
                name = val.get("name")
            else: name='unknown'
            opsys = val.get("opsys")
            address = key
            #zone= address.split('.')
            zone = tools.returnNetworkZone2args(address)
            #zoneShort=zone[0:3]
            #zone[3]=('0')
            #zone='.'.join(zone)
            services = val.get("services")
            netwKey=zoneDict.get(zone)
            interfaceKey = storeElementArango('element', 'interface', 'network', key, None, client)
            #nodeKey = storeElementArango('element', 'node', 'general', str(key)+';;'+str(name), None, client)
            nodeKey = storeElementArango('element', 'node', 'general', str(key), None, client)
            storeAssocArango('elementAssoc', netwKey, interfaceKey, 'networkInterface', client)
            storeAssocArango('elementAssoc', interfaceKey, nodeKey, 'interfaceNode', client)
            for d in opsys.values():
                osCertainty = d.get("osCertainty")
                osName = d.get("osProduct").split("->")[0].strip()
                standardName=d.get('standardName')
                osKey=storeElementArango('element', 'softwareInstance', 'operatingSystem', standardName, osCertainty , client)
                storeAssocArango('elementAssoc', nodeKey, osKey, 'operatingsystemSoftwareproduct', client)

            for k,v in services.items():
                port = k
                protocol = v.get("protocol")
                serviceName = v.get("serviceName")
                serverName = ('-'.join((port,protocol,serviceName)))

                if (serviceName == "unknown"):
                    serviceName = ('-'.join((port, protocol)))
                else:
                    serviceName = ('-'.join((port, protocol, serviceName)))

                servKey = storeElementArango('element', 'softwareInstance','server', serviceName, None, client)
                storeAssocArango('elementAssoc', nodeKey, servKey, 'operatingsystemServer', client)

                if (protocol != None):
                    protKey = storeElementArango('element', 'property','protocol', protocol, None, client)
                    storeAssocArango('elementAssoc', servKey, protKey, 'ServerProtocol', client)


def run(sourceName,scope, dataFile, date, con):
    if(checkExists(dataFile, con)== False):
        print('Importing :',dataFile,' from ',sourceName)
        hostsData = hosts(dataFile)
        #timestamp = str(datetime.date.today())
        hash=tools.hashfile(open(dataFile, "rb"),dataFile)
        #storeBasic(con)
        store(sourceName,scope, hostsData, hash, date, con)
    else: print(dataFile + " already imported")

run('Nessus','subnet', "..\data\\nessus\\Authenticated_SCADA_lab_scan_encn7b.xml", tools.creationDate("..\data\\nessus\\Authenticated_SCADA_lab_scan_encn7b.xml"), createConArango('Lab'))
#run('Nessus','subnet', "..\data\\nessus\\Authenticated_SCADA_lab_scan_mj3yvv.xml", tools.creationDate("..\data\\nessus\\Authenticated_SCADA_lab_scan_mj3yvv.xml"), createConArango('Lab'))




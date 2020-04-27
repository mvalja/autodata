import securiLangFullv2
from pprint import pprint
import tools
from arangoTools import *
from itertools import count
import collections
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput


def getDataOutbound(key, client):
    aql="FOR v IN 1 OUTBOUND '{}' metaelementAssoc, elementAssoc RETURN v".format(key)
    queryResult = client.AQLQuery(aql, rawResults=True)
    return queryResult

def getDataInbound(depth, key, client):
    aql="FOR v IN 1..{0} INBOUND '{1}' metaelementAssoc, elementAssoc RETURN v".format(depth, key)
    queryResult = client.AQLQuery(aql, rawResults=True)
    return queryResult

def getTimePointIds(client):
    aql="FOR u IN metaelement FILTER u.type=='timepoint' RETURN u"
    queryResult = client.AQLQuery(aql, rawResults=True)
    return queryResult

def getDataOutboundAll(key, client):
    aql="FOR v, e, p IN 1..1000 OUTBOUND '{}' metaelementAssoc, elementAssoc RETURN p".format(key)
    #print(aql)
    queryResult = client.AQLQuery(aql, rawResults=True)
    return queryResult

def getFrequency(output):
    for o in output:
        oCounter = set()
        oConValue=o.get('connectedValue')
        oConEntity=o.get('connected')
        if(oConEntity ==None and oConValue == None):
            oConId=o.get('connectedID')
            for r in output:
                oId = r.get('id')
                oValue = r.get('value')
                oEntity = r.get('entity')
                if(tools.isEqual(oConId, oId) and (oEntity !=None and oValue != None)):
                    oCounter.add((oId,oEntity,oValue))
                    print('success')
            print(collections.Counter(oCounter))
            print(oCounter)

#print(getElements('softwareInstance','server',createConArango('claimOmania') ))

#pprint(getSourceTimePoint('element/5068342', createConArango('claimOmania')))
####################################################
#Current getElement Output Format
#
#elementID
#label
#outgoing
#incoming
#
#connectedID
#connectedClass
#connectedType
#connectedLabel
####################################################



def getAccessControl(con):
    acLocal= getElements('accessControl','local',con)
    acDomain= getElements('accessControl','domain',con)
    ac=list(acLocal)+list(acDomain)
    output=[]
    for i in ac:
        elementID=i[0]
        elementLabel=i[1]
        elexistence=i[2]
        prevNodeG = getPreviousElements(elementID, 'node', 'general', 'in', con)
        prevServer = getPreviousElements(elementID, 'softwareInstance', 'server', 'in', con)
        newPrevList=[]
        propList=[]
        newAssocFromList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        for p in prevNodeG:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            #existence = p.get('existence')
            newPrevList.append({'targetClass':'Host', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Authorization'})
        for p in prevServer:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            #existence = p.get('existence')
            newPrevList.append({'targetClass':'Service', 'targetID':prevId, 'targetLabel':prevLabel,'type':'Authorization'})
        output.append(
                    {'source': source, 'sourceScope': scope,'entity': 'AccessControl', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': propList, 'associationsFrom':newAssocFromList, 'existence': elexistence })
    return output

def getClient(con):
    clients= getElements('softwareInstance','client',con)
    output=[]
    for i in clients:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeG = getPreviousElements(elementID, 'node', 'general', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevNodeG:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Host', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Client execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'Client', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

#pprint(getClient(createConArango('claimOmania')))

def getService(con):
    servers = getElements('softwareInstance', 'server', con)
    output=[]
    for i in servers:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeG = getPreviousElementsBoundary(elementID, 'node', 'general', 'in', '2',con)
        prevDataflow = getPreviousElementsBoundary(elementID, 'flow', 'undefined', 'in','2', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for g in prevDataflow:
            prevId =g.get('_key')
            prevLabel=g.get('label')
            existence = g.get('existence')
            newPrevList.append({'targetClass':'Dataflow', 'targetID':prevId, 'targetLabel':prevLabel,'type':'Communication execution'})
        for p in prevNodeG:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Host', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Application execution'})

        output.append(
                    {'source': source, 'sourceScope': scope,'entity': 'Service', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

#pprint(getService(createConArango('claimOmania')))

#print(len(getElements('softwareInstance', 'server',createConArango('claimOmania'))))

def getDataflow(con):
    dataflows = getElements('flow', 'data', con)
    output=[]
    for i in dataflows:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevClient = getPreviousElements(elementID, 'softwareInstance', 'client', 'in', con)
        prevRouter = getPreviousElements(elementID, 'node', 'embedded', 'in', con)
        assocFromL=getPreviousElements(elementID, 'softwareInstance', 'server', 'out', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        newAssocFromList = []
        propList= []
        newPropList= []
        for p in assocFromL:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newAssocFromList.append({'targetClass':'Service', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Communication'})
        for p in prevClient:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Client', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Communication'})
        for p in prevRouter:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Router', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Communication'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'Dataflow', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocFromList, 'existence': elexistence })
    return output

#pprint(getDataflow(createConArango('claimOmania')))

def getDatastore(con):
    datastores = getElements('softwareInstance', 'datastore', con)
    output = []
    for i in datastores:
        elementID = i[0]
        elementLabel = i[1]
        elexistence = i[2]
        prevNodeG = getPreviousElements(elementID, 'node', 'general', 'in', con)
        prevServer = getPreviousElements(elementID, 'softwareInstance', 'server', 'in', con)
        prevClient = getPreviousElements(elementID, 'softwareInstance', 'client', 'in', con)
        #prevDataflow = getPreviousElements(elementID, 'flow', 'unknown', 'in', con)
        newPrevList = []
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList = []
        newAssocList = []
        propList = getPreviousElements(elementID, 'property', 'version', 'in', con)
        newPropList = []
        for p in prevNodeG:
            prevId = p.get('_key')
            prevLabel = p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass': 'Host', 'targetID': prevId, 'targetLabel': prevLabel, 'type':'Database execution'})
        for p in prevServer:
            prevId = p.get('_key')
            prevLabel = p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass': 'Service', 'targetID': prevId, 'targetLabel': prevLabel, 'type':'Database execution'})
        for p in prevClient:
            prevId = p.get('_key')
            prevLabel = p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass': 'Client', 'targetID': prevId, 'targetLabel': prevLabel, 'type':'Database execution'})
        #for p in prevDataflow:
            #prevId = p.get('_key')
            #prevLabel = p.get('label')
            #newPrevList.append({'class': 'dataflow', 'id': prevId, 'label': prevLabel})
        output.append(
            {'source': source,'sourceScope': scope, 'entity': 'Datastore', 'value': elementLabel, 'id': elementID,
             'associationsTo': newPrevList, 'properties': newPropList, 'associationsFrom': newAssocList, 'existence': elexistence})
    return output
#pprint(getDatastore(createConArango('claimOmania')))

def getFirewall(con):
    firewalls = getElements('firewall', 'embedded', con)
    output=[]
    for i in firewalls:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeE = getPreviousElements(elementID, 'node', 'embedded', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevNodeE:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Router', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Firewall execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'Firewall', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

def getHost(con):
    nodeG = getElements('node', 'general', con)
    #nodeE = getElements('node', 'embedded', con)
    #node=list(nodeG)+list(nodeE)
    node=nodeG
    output=[]
    for i in node:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        assocToList= getPreviousElements(elementID,'zone','network','in',con)
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        propInterfList=getPreviousElements(elementID,'interface','network','in',con)
        propOPSysList=getPreviousElements(elementID,'softwareInstance','operatingSystem','out',con)
        newAssocToList = []
        newPropList=[]
        ipbasedname=''
        for a in propOPSysList:
            asId =a.get('_key')
            asLabel=a.get('label')
            existence = a.get('existence')
            newPropList.append({'type':'OperatingSystem', 'id':asId, 'label':asLabel, 'existence':existence})
        for a in propInterfList:
            asId =a.get('_key')
            asLabel=a.get('label')
            existence = a.get('existence')
            newPropList.append({'type':'Interface', 'id':asId, 'label':asLabel,'existence':existence})
            #if (ipbasedname!=''): ipbasedname = ipbasedname + '|' + str(asLabel)
            #if (ipbasedname == ''): ipbasedname = str(asLabel)
        for p in assocToList:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')

            if(prevLabel!='127.0.0.0' and prevLabel!='0.0.0.0'):
                newAssocToList.append({'type':'Connection','targetClass':'Network', 'targetID':prevId, 'targetLabel':prevLabel})

        if (elementLabel != '127.0.0.1' and elementLabel != '0.0.0.0'):
            output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'Host', 'value': str(elementLabel), 'id':elementID, 'properties': newPropList, 'associationsTo':newAssocToList, 'associationsFrom':[],'existence': elexistence})
    return output

#pprint(getHost(createConArango('claimOmania')))

def getIDS(con):
    idssE = getElements('ids', 'embedded', con)
    idssG = getElements('ids', 'general', con)
    output=[]
    for i in idssE:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeE = getPreviousElements(elementID, 'node', 'embedded', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevNodeE:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Router', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'HIDS execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'IDS', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })

    for i in idssG:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeG = getPreviousElements(elementID, 'node', 'general', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevNodeG:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Router', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'NIDS execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'IDS', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

#pprint(getHost(createConArango('claimOmania')))

def getIPS(con):
    ipss = getElements('ips', 'embedded', con)
    output=[]
    for i in ipss:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevNodeE = getPreviousElements(elementID, 'node', 'embedded', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevNodeE:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Router', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'IPS execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'IPS', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

def getNetwork(con):
    networks= getElements('zone','network',con)
    output=[]
    for n in networks:
        elementID=n[0]
        elementLabel=n[1]
        elexistence = n[2]
        sourceInfo=getSourceTimePoint(elementID, con)
        elsource=sourceInfo[0]
        scope=sourceInfo[1]
        newPrevList=[]
        newPropList=[]
        newAssocList=[]
        if (elementLabel != '127.0.0.0' and elementLabel != '0.0.0.0'):
            output.append(
                    {'source': elsource,'sourceScope': scope, 'entity': 'Network', 'value': elementLabel,  'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence})
    return output

def getPhysicalZone(con):
    zone= getElements('zone','physical',con)
    output=[]
    for n in zone:
        elementID=n[0]
        elementLabel=n[1]
        elexistence = n[2]
        sourceInfo=getSourceTimePoint(elementID, con)
        elsource=sourceInfo[0]
        scope=sourceInfo[1]
        newPrevList=[]
        newPropList=[]
        newAssocList=[]
        output.append(
                    {'source': elsource,'sourceScope': scope, 'entity': 'PhysicalZone', 'value': elementLabel,  'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence})
    return output

def getRouter(con):
    routers = getElements('node', 'embedded', con)
    output=[]
    for i in routers:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevZone = getPreviousElements(elementID, 'zone', 'network', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevZone:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Network', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Connection'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'Router', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

#pprint(getRouter(createConArango('claimOmania')))

def getProtocol(con):
    proto = getElements('protocol', 'undefined', con)
    output=[]
    for i in proto:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevDf = getPreviousElements(elementID, 'flow', 'data', 'in', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in prevDf:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Dataflow', 'targetID':prevId, 'targetLabel':prevLabel, 'type': 'Protocol status'})
        output.append(
                    {'source': source, 'sourceScope': scope, 'entity': 'Protocol', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output


#pprint(getProtocol(createConArango('claimOmania')))

def getUserAccount(con):
    useracc = getElements('userAccount', 'undefined', con)
    output=[]
    ac=[]
    for i in useracc:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        prevLoc = getPreviousElements(elementID, 'accessControl', 'local', 'in', con)
        prevDom = getPreviousElements(elementID, 'accessControl', 'domain', 'in', con)
        if(len(prevLoc)!=0 or len(prevDom)!=0):
            ac=list(prevLoc)+list(prevDom)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        for p in ac:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'AccessControl', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Authorization'})

        output.append(
                    {'source': source, 'sourceScope': scope, 'entity': 'UserAccount', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList,'existence': elexistence })
    return output

#pprint(getUserAccount(createConArango('claimOmania')))

def getVulnerabilityScanner(con):
    vulns = getElements('softwareInstance', 'networkScanner', con)
    output=[]
    for i in vulns:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        propList= []
        newPropList= []
        output.append(
                    {'source': source, 'sourceScope': scope, 'entity': 'VulnerabilityScanner', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList,'existence': elexistence })
    return output


#pprint(getVulnerabilityScanner(createConArango('claimOmania')))

def getWebApplication(con):
    wapp = getElements('softwareInstance', 'webApplication', con)
    output=[]
    for i in wapp:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        services = getPreviousElementsBoundary(elementID, 'softwareInstance', 'server', 'in', '2', con)
        newPrevList=[]
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        assocList=[]
        newAssocList=[]
        newPropList= []
        for p in services:
            prevId =p.get('_key')
            prevLabel=p.get('label')
            existence = p.get('existence')
            newPrevList.append({'targetClass':'Service', 'targetID':prevId, 'targetLabel':prevLabel, 'type':'Web server execution'})

        output.append(
                    {'source': source,'sourceScope': scope, 'entity': 'WebApplication', 'value': elementLabel, 'id':elementID, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList,'existence': elexistence })
    return output

def getWebApplicationFirewall(con):
    waf = getElements('softwareInstance', 'webApplication', con)
    output=[]
    for i in waf:
        elementID=i[0]
        elementLabel=i[1]
        elexistence = i[2]
        propList = getPreviousElements(elementID, 'property', 'WebApplicationFirewall', 'in', con)
        sourceInfo=getSourceTimePoint(elementID, con)
        source=sourceInfo[0]
        scope=sourceInfo[1]
        newPrevList=[]
        newPrevList.append({'type':'Firewall execution', 'targetID':elementID, 'targetLabel':asLabel, 'targetClass':'WebApplication'})
        newPropList= []
        newAssocList=[]
        if(len(propList)>0):
            asId =propList[0].get('_key')
            asLabel=propList[0].get('label')
            existence = propList[0].get('existence')
            output.append(
                        {'source': source,'sourceScope': scope, 'entity': 'WebApplicationFirewall', 'value': asLabel, 'id':asId, 'associationsTo':newPrevList, 'properties': newPropList, 'associationsFrom':newAssocList, 'existence': elexistence })
    return output

def getZoneManagement(con):
    aql=""
    queryResult = con.AQLQuery(aql, rawResults=True)
    output = dict() # describing objects, closest neighbours, properties
    return output


#print(getSourceTimePoint('element/5124477',createConArango('claimOmania')))
def generateSW(hosts, services, clients):
    swpoutput=[]
    newPrevList=[]
    for h in hosts:
        elementID=h.get('id')
        entity = h.get('entity')
        value = h.get('value')
        source = h.get('source')
        scope = h.get('sourceScope')
        properties = h.get('properties')
        for p in properties:
            swentity=p.get('type')
            if (tools.isEqual('operatingSystem', swentity)):
                swid = p.get('id')
                swlabel=p.get('label')
                swexistence=p.get('existence')
                swpoutput.append({'source': source, 'sourceScope': scope,'entity': 'SoftwareProduct','id': swid,'value': swlabel,'existence':swexistence, 'associationsTo':[{'targetClass':entity,'targetID':elementID,'targetLabel':value,'type':'Software status'}],'associationsFrom':[]})
        #Value should come from the property name, ID is the object id
        #newPrevList.append({'type':entity, 'id':elementID, 'label':value})
        #swpoutput.append({'source': source, 'entity': 'softwareProduct', 'value': asLabel, 'connectedList':newPrevList})
    #for s in services:
        #elementID = s.get('id')
        #swpid=str(elementID)+'SWP'
        #entity = s.get('entity')
        #value = s.get('value')
        #source = s.get('source')
        #scope = h.get('sourceScope')
        #existence = s.get('existence')
        #swpoutput.append({'source': source, 'sourceScope': scope,'entity': 'SoftwareProduct','id':swpid, 'value': value, 'existence': None,
                          #'associationsTo': [{'targetClass': entity, 'targetID': elementID, 'targetLabel': value,'existence': existence, 'type':'Software status'}],'associationsFrom':[]})
    #for c in clients:
        #elementID = c.get('id')
        #swpid = str(elementID) + 'SWP'
        #entity = c.get('entity')
        #value = c.get('value')
        #source = c.get('source')
        #scope = h.get('sourceScope')
        #existence = c.get('existence')
        #swpoutput.append({'source': source, 'sourceScope': scope,'entity': 'SoftwareProduct','id':swpid, 'value': value, 'existence': None,
         #                 'associationsTo': [{'targetClass': entity, 'targetID': elementID, 'targetLabel': value, 'existence': existence, 'type':'Software status'}],'associationsFrom':[]})

    return swpoutput

#################################
#BUILDING A securiCAD MODEL
#################################-
#--Get the networks
#--Get the hosts (general and embedded)
#--Get the software on the hosts
#--Get dataflows on the hosts
#--Get protocols for dataflows
#--Get added services on the hosts, software and dataflow like datastore
#--Get the added services on the hosts like HIDS, HIDS
#--Get added services on routers like firewall, IDS
#--Get manamgement of devices
#--Get Access control
#--Get users
#--Get physical space for users
#--SPECIAL CASES
#--Generate software products
#--Generate vulnerability scanner
#################################

#con=createConArango('claimOmania')

def mergeData(con):
    #--Get the networks
    networks = getNetwork(con)
    #--Get the hosts (general and embedded)
    hosts = getHost(con)

    #pprint(hosts)
    routers = getRouter(con)
    #--Get the software on the hosts
    clients=getClient(con)
    services=getService(con)
    #pprint(services)
    #pprint(generateSW(hosts,[],[]))
    webapps=getWebApplication(con)
    webappFWs=getWebApplicationFirewall(con)
    #--Get dataflows on the hosts
    dataflows=getDataflow(con)
    #--Get protocols for dataflows
    protocols=getProtocol(con)
    #--Get added services on the hosts, software and dataflow like datastore
    dataflows=getDataflow(con)
    datastores=getDatastore(con)
    #--Get the added services on the hosts like HIDS, HIDS
    idss=getIDS(con)
    ipss=getIPS(con)
    #--Get added services on routers like firewall, IDS
    firewalls=getFirewall(con)
    #--Get manamgement of devices
    #--Get Access control
    acs=getAccessControl(con)
    uacs=getUserAccount(con)
    #--Get users
    #getUser()
    #--Get physical space for users
    physical= getPhysicalZone(con)
    #--SPECIAL CASES
    #--Generate software products
    sw=generateSW(hosts, services, clients)
    #--Get vulnerability scanner
    vulnscanner=getVulnerabilityScanner(con)

    merged={'Network':networks, 'Host':hosts, 'Router':routers,'Client':clients, 'Service':services, 'WebApplication':webapps, 'WebApplicationFirewall':webappFWs,
                   'Dataflow':dataflows,'Datastore':datastores, 'IDS':idss,'IPS':ipss, 'Firewall':firewalls,'AccessControl':acs, 'UserAccount':uacs,'PhysicalZone': physical, 'SoftwareProduct':sw, 'Protocol':protocols}
    return merged


def modelData2DB(modelD, client):
    sourceDict=dict()
    netwAssoc=set()
    idKeyDict=dict()
    collection='collectedModel'
    collectionAssoc='collectedModelAssoc'
    checkStart = client[collection].fetchByExample({'type': "modelData", "label": "securiCAD"}, batchSize=100)
    if (len(checkStart) == 0):
        startKey = storeMetaelementArango(collection, 'modelData', 'securiCAD', client)
    else:
        startKey = checkStart[0]._id
    for key, val in modelD.items():
        for v in val:
            dbid=v.get('id')
            entity=v.get('entity')
            src=v.get('source')
            srcScp=v.get('sourceScope')
            elval=v.get('value')
            elex = v.get('existence')
            if(src not in sourceDict):
                srcKey=storeModelSourceArango(collection, 'source', src, srcScp, None, client)
                storeAssocArango(collectionAssoc, startKey, srcKey,  'start', client)
                sourceDict[src]=srcKey
            else:
                srcKey=sourceDict.get(src)
            #print(str(entity)+' '+str(dbid)+' '+str(elval))
            modelElKey=storeModelDataKeyArango(collection, dbid, entity, elval, elex, client)
            print('Storing class: ',entity, elval,dbid,' from ',src)
            idKeyDict[dbid]=modelElKey
            if(tools.isEqual(entity,'Network') and (srcKey,modelElKey) not in netwAssoc):
                storeAssocArango(collectionAssoc, srcKey, modelElKey, 'fromTo', client)
                netwAssoc.add((srcKey,modelElKey))
    conListAssoc=set()
    conListFromAssoc = set()
    for val in modelD.values():
        for v in val:
            key = v.get('id')
            anid=str(collection)+'/'+str(key)
            conList=v.get('associationsTo')
            conFromList = v.get('associationsFrom')
            for c in conList:
                clkey=c.get('targetID')
                clName=c.get('type')
                clid = str(collection) + '/' + str(clkey)
                if((clid, anid) not in conListAssoc):
                    conListAssoc.add((clid, anid))
                    storeAssocArango(collectionAssoc, clid, anid, clName, client)
            for c in conFromList:
                clkey=c.get('targetID')
                clName=c.get('type')
                clid = str(collection) + '/' + str(clkey)
                if((anid, clid) not in conListFromAssoc):
                    conListFromAssoc.add((anid, clid))
                    storeAssocArango(collectionAssoc, anid, clid , clName, client)

#pprint(mergeData(createConArango('claimOmania')))


def measure():
    graphviz = GraphvizOutput()
    graphviz.output_file = 'secAdapter3.png'
    with PyCallGraph(output=graphviz):

        modelData2DB(mergeData(createConArango('claimOmania')),createConArango('claimOmania'))

#measure()


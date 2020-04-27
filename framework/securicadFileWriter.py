import hashlib
import xml.etree.ElementTree as ET
from arangoTools import *
from itertools import count
import uuid as UUID
from xml.dom import minidom

data = dict()

titleText="Autodata generated model"



def generate_id():
    return "id-"+str(UUID.uuid4().hex)

def getStartPoint(client):
    checkStart = client['modelData'].fetchByExample({'type': "startpoint", "label": "modelStart"}, batchSize=100)
    if (len(checkStart) != 0):
        return checkStart[0]._id

def getDataOutbound(depth, key, client):
    #aql="FOR v, e, p IN 1..{0} OUTBOUND '{1}' modelDataAssoc RETURN p".format(depth, key)
    aql ="FOR v, e, p IN 1..1000 OUTBOUND 'metaelement/5066844' metaelementAssoc, elementAssoc RETURN p"
    queryResult = client.AQLQuery(aql, rawResults=True)
    return queryResult

def getDataAndLevels(con):
    K=0
    id_counter = count()
    next(id_counter)
    data = dict()
    classes = dict()
    startPoint=getStartPoint(con)
    claims = []
    layeredData=getDataOutbound(1000,startPoint, con)
    for ld in layeredData:
        vertices = ld.get('vertices')
        levels = len(vertices)-1
        level = 1
        superList = []
        for vr in vertices:
            clss = vr.get('class')
            typ=vr.get('type')
            value=vr.get('label')
            credibility=vr.get('existence')
            id="id-"+vr.get('_key')
            if(credibility!=None): credibility= float(credibility)
            if(typ!='startpoint'):
                if(level<levels):
                    superList.append({"superDistance":levels-level, "superName": value, "superClass": clss,'superType':typ, "id":id})
                    level=level+1

                else:
                    claims.append({"class": clss, "value": value, "credibility": credibility,
                                               "superList": superList, "id":id, 'type':typ})

    return claims
###############################################################################################
##MODEL CREATION FUNCTIONS
###############################################################################################


def newSoftwareProduct(link, id, name, hasvendorsupport,nopatchablevulnerability,nounpatchablevulnerability,safelanguages, scrutinized, secretbinary,secretsource,staticcodeanalysis): #10
    swp=ET.SubElement(link, "softwareproduct", {"id":id})
    ET.SubElement(swp, "name").text=name
    ET.SubElement(swp, "hasvendorsupport").text = hasvendorsupport
    ET.SubElement(swp, "nopatchablevulnerability").text = nopatchablevulnerability
    ET.SubElement(swp, "nounpatchablevulnerability").text = nounpatchablevulnerability
    ET.SubElement(swp, "safelanguages").text = safelanguages
    ET.SubElement(swp, "scrutinized").text = scrutinized
    ET.SubElement(swp, "secretbinary").text = secretbinary
    ET.SubElement(swp, "secretsource").text = secretsource
    ET.SubElement(swp, "staticcodeanalysis").text = staticcodeanalysis
    return swp

def newAccessControl(link, id, name, backoff, enabled, hashedpasswordrepository, nodefaultpasswords, passwordpolicyenforcement, salting, useraccountids):
    rt=ET.SubElement(link, "accesscontrol", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "backoff").text = backoff
    ET.SubElement(rt, "enabled").text = enabled
    ET.SubElement(rt, "hashedpasswordrepository").text = hashedpasswordrepository
    ET.SubElement(rt, "nodefaultpasswords").text = nodefaultpasswords
    ET.SubElement(rt, "passwordpolicyenforcement").text = passwordpolicyenforcement
    ET.SubElement(rt, "salting").text = salting
    if(len(useraccountids)>0 and useraccountids!= None):
        uas= ET.SubElement(rt, "useraccounts")
        for u in useraccountids:
            ua=ET.SubElement(uas, "useraccount")
            ET.SubElement(ua, "id").text=u
    return rt

def newUserAccount(link, id, name, keystoreid):
    rt=ET.SubElement(link, "useraccount", {"id":id})
    ET.SubElement(rt, "name").text=name
    if(keystoreid!=None):
        ET.SubElement(rt, "keystoreid").text = keystoreid
    return rt

def newKeystore(link, id, name, encrypted):
    rt=ET.SubElement(link, "keystore", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "encrypted").text = encrypted
    return rt

def newUser(link, id, name, securityaware, useraccountids):
    rt=ET.SubElement(link, "user", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "securityaware").text = securityaware
    if(len(useraccountids)>0 and useraccountids!=None):
        uas= ET.SubElement(rt, "useraccounts")
        for u in useraccountids:
            ua=ET.SubElement(uas, "useraccount")
            ET.SubElement(ua, "useraccountid").text=u
    return rt

def newDatastore(link, id, name, encrypted):
    rt=ET.SubElement(link, "datastore", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "encrypted").text = encrypted
    return rt

def newHost(link, id, name,aslr, antimalware, dep, hardened, hostfirewall, patched, staticarptables, softwareproductid, accesscontrolid, hostdatastoreid, services, clients):
    rt=ET.SubElement(link, "host", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "aslr").text = aslr
    ET.SubElement(rt, "antimalware").text = antimalware
    ET.SubElement(rt, "dep").text = dep
    ET.SubElement(rt, "hardened").text = hardened
    ET.SubElement(rt, "hostfirewall").text = hostfirewall
    ET.SubElement(rt, "patched").text = patched
    ET.SubElement(rt, "staticarptables").text = staticarptables
    if(softwareproductid!=None):
        ET.SubElement(rt, "softwareproductid").text = softwareproductid
    if(accesscontrolid!=None):
        ET.SubElement(rt, "accesscontrolid").text = accesscontrolid
    if(hostdatastoreid!=None):
        ET.SubElement(rt, "hostdatastoreid").text = hostdatastoreid
    if(len(services)>0 and services!=None):
        ser= ET.SubElement(rt, "services")
        for u in services:
            ua=ET.SubElement(ser, "service")
            ET.SubElement(ua, "serviceid").text=u[0]
            ET.SubElement(ua, "root").text = u[1]
            ET.SubElement(ua, "shellorapplication").text = u[2]
    if (len(clients)>0 and clients !=None):
        ser = ET.SubElement(rt, "clients")
        for u in clients:
            ua = ET.SubElement(ser, "client")
            ET.SubElement(ua, "clientid").text = u[0]
            ET.SubElement(ua, "root").text = u[1]
    return rt

def newWebApplicationFW(link, id, name, blackboxtuned, enabled, experttuned, monitored, tuningeffort):
    rt=ET.SubElement(link, "webapplicationfirewall", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "blackboxtuned").text = blackboxtuned
    ET.SubElement(rt, "enabled").text = enabled
    ET.SubElement(rt, "experttuned").text = experttuned
    ET.SubElement(rt, "monitored").text = monitored
    ET.SubElement(rt, "tuningeffort").text = tuningeffort
    return rt


def newClient(link, id, name, patched, softwareproductid,datastoreid,keystoreid):
    rt=ET.SubElement(link, "client", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "patched").text = patched
    if(softwareproductid!=None):
        ET.SubElement(rt, "softwareproductid").text = softwareproductid
    if(datastoreid!=None):
        ET.SubElement(rt, "datastoreid").text = datastoreid
    if(keystoreid!=None):
        ET.SubElement(rt, "keystoreid").text = keystoreid
    return rt


def newService(link, id, name, patched, shellorapplication, softwareproductid, accesscontrolid, datastoreid, keystoreid, exposedonnetworks):
    rt=ET.SubElement(link, "service", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "patched").text = patched
    ET.SubElement(rt, "shellorapplication").text = shellorapplication
    if(softwareproductid!=None):
        ET.SubElement(rt, "softwareproductid").text = softwareproductid
    if(accesscontrolid!=None):
        ET.SubElement(rt, "accesscontrolid").text = accesscontrolid
    if(datastoreid!=None):
        ET.SubElement(rt, "datastoreid").text = datastoreid
    if(keystoreid!=None):
        ET.SubElement(rt, "keystoreid").text = keystoreid
    if(len(exposedonnetworks)>0 and exposedonnetworks!=None):
        exs= ET.SubElement(rt, "exposedonnetworks")
        for en in exposedonnetworks:
            ex=ET.SubElement(exs, "network")
            ET.SubElement(ex, "networkid").text=en
    return rt

def newWebApplication(link, id, name, blackboxtesting,nopubliccivulnerabilities,nopublicrfivulnerabilities,nopublicxssvulnerabilities, securityawaredevelopers, staticcodeanalysis, typesafeapi, accesscontrolid, datastoreid, webapplicationfirewallid):
    rt=ET.SubElement(link, "webapplication", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "blackboxtesting").text = blackboxtesting
    ET.SubElement(rt, "nopubliccivulnerabilities").text = nopubliccivulnerabilities
    ET.SubElement(rt, "nopublicrfivulnerabilities").text = nopublicrfivulnerabilities
    ET.SubElement(rt, "nopublicxssvulnerabilities").text = nopublicxssvulnerabilities
    ET.SubElement(rt, "securityawaredevelopers").text = securityawaredevelopers
    ET.SubElement(rt, "staticcodeanalysis").text = staticcodeanalysis
    ET.SubElement(rt, "typesafeapi").text = typesafeapi
    if(webapplicationfirewallid!=None):
        ET.SubElement(rt, "webapplicationfirewallid").text = webapplicationfirewallid
    if(accesscontrolid!=None):
        ET.SubElement(rt, "accesscontrolid").text = accesscontrolid
    if(datastoreid!=None):
        ET.SubElement(rt, "datastoreid").text = datastoreid
    return rt

def newNetwork(link, id, name, dnssec, portsecurity, staticarptables, hostids):
    rt=ET.SubElement(link, "network", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "dnssec").text = dnssec
    ET.SubElement(rt, "portsecurity").text = portsecurity
    ET.SubElement(rt, "staticarptables").text = staticarptables
    if(len(hostids)>0 and hostids!=None):
        mhs= ET.SubElement(rt, "memberhosts")
        for m in hostids:
            mh=ET.SubElement(mhs, "host")
            ET.SubElement(mh, "hostid").text=m
    return rt

def newRouter(link, id, name, firewallid, networkids):
    rt=ET.SubElement(link, "router", {"id":id})
    ET.SubElement(rt, "name").text=name
    if(firewallid!=None):
        ET.SubElement(rt, "firewallid").text = firewallid
    if(len(networkids)>0 and networkids!=None):
        nws= ET.SubElement(rt, "networks")
        for n in networkids:
            nw=ET.SubElement(nws, "network")
            ET.SubElement(nw, "networkid").text=n[0]
            ET.SubElement(nw, "connectionoradministration").text = n[1]
    return rt

def newFirewall(link, id, name, enabled, knownruleset):
    rt=ET.SubElement(link, "firewall",{"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "enabled").text = enabled
    ET.SubElement(rt, "knownruleset").text = knownruleset
    return rt

def newProtocol(link, id, name, authenticated, encrypted, nonce):
    rt=ET.SubElement(link, "protocol",{"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "authenticated").text = authenticated
    ET.SubElement(rt, "encrypted").text = encrypted
    ET.SubElement(rt, "nonce").text = nonce
    return rt

def newDataflow(link, id, name, protocolid, dataflowkeystoreid,routerid, clientid, serviceid, datastoreid, idsid, ipsid, firewallid):
    rt=ET.SubElement(link, "dataflow", {"id":id})
    ET.SubElement(rt, "name").text=name
    if(protocolid!=None):
        ET.SubElement(rt, "protocolid").text = protocolid
    if(dataflowkeystoreid!=None):
        ET.SubElement(rt, "dataflowkeystoreid").text = dataflowkeystoreid
    if(routerid!=None):
        rts1= ET.SubElement(rt, "routers")
        rts2=ET.SubElement(rts1, "router")
        ET.SubElement(rts2, "routerid").text = routerid
    if(clientid!=None):
        rts1= ET.SubElement(rt, "clients")
        rts2=ET.SubElement(rts1, "client")
        ET.SubElement(rts2, "clientid").text = clientid
    if(serviceid!=None):
        rts1= ET.SubElement(rt, "services")
        rts2=ET.SubElement(rts1, "service")
        ET.SubElement(rts2, "serviceid").text = serviceid
    if(datastoreid!=None):
        rts1= ET.SubElement(rt, "datastores")
        rts2=ET.SubElement(rts1, "datastore")
        ET.SubElement(rts2, "datastoreid").text = datastoreid
    if(idsid!=None):
        rts1= ET.SubElement(rt, "idss")
        rts2=ET.SubElement(rts1, "ids")
        ET.SubElement(rts2, "idsid").text = idsid
    if(ipsid!=None):
        rts1= ET.SubElement(rt, "ipss")
        rts2=ET.SubElement(rts1, "ips")
        ET.SubElement(rts2, "ipsid").text = ipsid
    if(firewallid!=None):
        rts1= ET.SubElement(rt, "firewalls")
        rts2=ET.SubElement(rts1, "firewall")
        ET.SubElement(rts2, "firewallid").text = firewallid

    return rt

def newVulnerabilityscanner(link, id, name, enabled, networkids, hostids):
    rt=ET.SubElement(link, "vulnerabilityscanner", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "enabled").text=enabled
    if(len(networkids)>0 and networkids!=None):
        nws= ET.SubElement(rt, "networks")
        for n in networkids:
            nw=ET.SubElement(nws, "network")
            ET.SubElement(nw, "networkid").text=n[0]
            ET.SubElement(nw, "scantype").text = n[1]
    if (len(hostids)>0 and hostids != None):
            hosts = ET.SubElement(rt, "hosts")
            for h in hostids:
                hst=ET.SubElement(hosts, "host")
                ET.SubElement(hst, "hostid").text=h[0]
                ET.SubElement(hst, "scantype").text = h[1]
    return rt

def newIDS(link, id, name, enabled, tuned, updated, hostid, routerid):
    rt=ET.SubElement(link, "ids", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "enabled").text = enabled
    ET.SubElement(rt, "tuned").text = tuned
    ET.SubElement(rt, "updated").text = updated
    if(hostid!=None):
        ET.SubElement(rt, "hostid").text = hostid
    if(routerid!=None):
        ET.SubElement(rt, "routerid").text = routerid
    return rt

def newIPS(link, id, name, enabled, dataflowids, routerid):
    rt=ET.SubElement(link, "ips", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "enabled").text = enabled
    if(len(dataflowids)>0 and dataflowids!=None):
        nws= ET.SubElement(rt, "dataflows")
        for n in dataflowids:
            nw=ET.SubElement(nws, "dataflow")
            ET.SubElement(nw, "dataflowid").text=n
    if(routerid!=None):
        rts1= ET.SubElement(rt, "routers")
        rts2=ET.SubElement(rts1, "router")
        ET.SubElement(rts2, "routerid").text = routerid
    return rt

def newZoneManagement(link, id, name, antimalwarepolicy, changecontrol, hostfirewall, hosthardening, patchmanagement, networkids):
    rt=ET.SubElement(link, "zonemanagement", {"id":id})
    ET.SubElement(rt, "name").text=name
    ET.SubElement(rt, "antimalwarepolicy").text = antimalwarepolicy
    ET.SubElement(rt, "changecontrol").text = changecontrol
    ET.SubElement(rt, "hostfirewall").text = hostfirewall
    ET.SubElement(rt, "hosthardening").text = hosthardening
    ET.SubElement(rt, "patchmanagement").text = patchmanagement
    if(len(networkids)>0 and networkids!=None):
        mhs= ET.SubElement(rt, "networks")
        for m in networkids:
            mh=ET.SubElement(mhs, "network")
            ET.SubElement(mh, "networkid").text=m
    return rt

def newPhysicalZone(link, id, name, networkids, hostids):
    rt=ET.SubElement(link, "physicalzone", {"id":id})
    ET.SubElement(rt, "name").text=name
    if(len(networkids)>0 and networkids!=None):
        uas= ET.SubElement(rt, "networks")
        for u in networkids:
            ua=ET.SubElement(uas, "network")
            ET.SubElement(ua, "networkid").text=u
    if(len(hostids)>0 and hostids!=None):
        uas= ET.SubElement(rt, "hosts")
        for u in hostids:
            ua=ET.SubElement(uas, "host")
            ET.SubElement(ua, "hostid").text=u
    return rt

def getSecuriCADElements(elName, dateID, con):
    if (elName != None):
        aql = "FOR e in 1..10 outbound '{0}' securiCADModelAssoc FILTER e.class=='{1}'  RETURN DISTINCT e".format(
            dateID, elName)
        query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
        return query

def getSecuriCADAssocElemIDs(elementID, elName, con):
    if (elName != None and elementID!=None):
        aql = "FOR e in 1..2 outbound 'securiCADModel/{0}' securiCADModelAssoc FILTER e.class=='{1}'  RETURN DISTINCT e._key".format(
            elementID, elName)
        query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
        return query

def getSecuriCADAssocElemIDsReverse(elementID, elName, con):
    if (elName != None and elementID!=None):
        aql = "FOR e in 1..2 inbound 'securiCADModel/{0}' securiCADModelAssoc FILTER e.class=='{1}'  RETURN DISTINCT e._key".format(
            elementID, elName)
        query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
        return query

def prepareXML(fileName, date, con):
    created=dict()
    generateSWP=dict()
    dateID=con['securiCADModel'].fetchByExample({'type': 'timepoint','label':date}, batchSize=100)
    if(len(dateID)==0):
        print('No data in DB.')
        return None
    else: dateID=dateID[0]._id
    root = ET.Element('architecture')
    #Network
    networkL=getSecuriCADElements('Network', dateID, con)
    if(len(networkL)>0):
        networks = ET.SubElement(root, "networks")
        for n in networkL:
            eid=n.get('_key')
            elabel=n.get('label')
            eclass=n.get('class')
            #existen=n.get('existence')
            hostL = getSecuriCADAssocElemIDs(eid, 'Host', con)
            network = newNetwork(networks, eid, elabel, '0.0', '0.0', '0.0', hostL)
            created[eid]=network

    #AccessControl
    accesscontrolL = getSecuriCADElements('AccessControl', dateID, con)
    if (len(accesscontrolL) > 0):
        accesscontrols = ET.SubElement(root, "accesscontrols")
        for n in accesscontrolL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            useraccountidL = getSecuriCADAssocElemIDs(eid, 'UserAccount', con)
            acl = newAccessControl(accesscontrols, eid, elabel, '0.0', '0.0', '0.0','0.0', '0.0', '0.0', useraccountidL)
            created[eid] = acl

    #Client
    clientL = getSecuriCADElements('Client', dateID, con)
    if (len(clientL) > 0):
        clients = ET.SubElement(root, "clients")
        for n in clientL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            softwareproductid = getSecuriCADAssocElemIDs(eid, 'SoftwareProduct', con)
            if (len(softwareproductid) > 0):
                softwareproductid = softwareproductid[0]
            else:
                softwareproductid = None
            datastoreid = getSecuriCADAssocElemIDs(eid, 'Datastore', con)
            if (len(datastoreid) > 0):
                datastoreid = datastoreid[0]
            else:
                datastoreid = None
            keystoreid = getSecuriCADAssocElemIDs(eid, 'Keystore', con)
            if (len(keystoreid) > 0):
                keystoreid = keystoreid[0]
            else:
                keystoreid = None
            if (softwareproductid == None):
                softwareproduct = elabel
                generateSWP[eid + '-SWP'] = softwareproduct
                softwareproductid = eid + '-SWP'

            client = newClient(clients, eid, elabel, '0.0', softwareproductid, datastoreid, keystoreid)
            created[eid] = client

    #Service
    serviceL = getSecuriCADElements('Service', dateID, con)
    if (len(serviceL) > 0):
        services = ET.SubElement(root, "services")
        for n in serviceL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            softwareproductid = getSecuriCADAssocElemIDs(eid, 'SoftwareProduct', con)
            if (len(softwareproductid) > 0):
                softwareproductid = softwareproductid[0]
            else:
                softwareproductid = None
            accesscontroid = getSecuriCADAssocElemIDs(eid, 'AccessControl', con)
            if (len(accesscontroid) > 0):
                accesscontroid = accesscontroid[0]
            else:
                accesscontroid= None
            datastoreid = getSecuriCADAssocElemIDs(eid, 'Datastore', con)
            if (len(datastoreid) > 0):
                datastoreid = datastoreid[0]
            else:
                datastoreid = None
            keystoreid = getSecuriCADAssocElemIDs(eid, 'Keystore', con)
            if (len(keystoreid) > 0):
                keystoreid = keystoreid[0]
            else:
                keystoreid = None

            if(softwareproductid==None):
                softwareproduct = elabel
                generateSWP[eid+'-SWP'] = softwareproduct
                softwareproductid=eid+'-SWP'
            networkL = getSecuriCADAssocElemIDs(eid, 'Network', con)
            service = newService(services, eid, elabel, '0.0', 'application', softwareproductid, accesscontroid, datastoreid,
                                 keystoreid, networkL)
            created[eid] = service

    #UserAccount
    useraccountL = getSecuriCADElements('UserAccount', dateID, con)
    if (len(useraccountL) > 0):
        useraccounts = ET.SubElement(root, "useraccounts")
        for n in useraccountL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            keystoreid = getSecuriCADAssocElemIDs(eid, 'Keystore', con)
            if (len(keystoreid) > 0):
                keystoreid = keystoreid[0]
            else:
                keystoreid = None
            useraccount = newUserAccount(useraccounts, eid, elabel, keystoreid)
            created[eid] = useraccount

    #KeyStore
    keystoreL = getSecuriCADElements('KeyStore', dateID, con)
    if (len(keystoreL) > 0):
        keystores = ET.SubElement(root, "keystores")
        for n in keystoreL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            keystore = newKeystore(keystores, eid, elabel, None)
            created[eid] = keystore

    #Host
    hostL = getSecuriCADElements('Host', dateID, con)
    if (len(hostL) > 0):
        hosts = ET.SubElement(root, "hosts")
        for n in hostL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            softwareproductid = getSecuriCADAssocElemIDs(eid, 'SoftwareProduct', con)
            if(len(softwareproductid)>0):
                softwareproductid = softwareproductid[0]
            else: softwareproductid = None
            accesscontrolid = getSecuriCADAssocElemIDs(eid, 'AccessControl', con)
            if(len(accesscontrolid)>0):
                accesscontrolid = accesscontrolid[0]
            else: accesscontrolid = None
            hostdatastoreid = getSecuriCADAssocElemIDs(eid, 'Datastore', con)
            if(len(hostdatastoreid)>0):
                hostdatastoreid = hostdatastoreid [0]
            else: hostdatastoreid = None
            serviceL = getSecuriCADAssocElemIDs(eid, 'Service', con)
            clientL = getSecuriCADAssocElemIDs(eid, 'Client', con)
            #Temporary fix
            ##############
            newServiceL=[]
            for s in serviceL:
                newServiceL.append((s, 'true','shell'))
            newClientL=[]
            for c in clientL:
                newClientL.append((c, 'false'))
            if (softwareproductid == None):
                softwareproduct = 'Unknown'
                generateSWP[eid + '-SWP'] = softwareproduct
                softwareproductid = eid + '-SWP'
            host = newHost(hosts, eid, elabel, '0.0', '0.0', '0.0', '0.0', '0.0', '0.0', '0.0',
                           softwareproductid, accesscontrolid, hostdatastoreid, newServiceL, newClientL)
            created[eid] = host

    #User
    userL = getSecuriCADElements('User', dateID, con)
    if (len(userL) > 0):
        users = ET.SubElement(root, "users")
        for n in userL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            useraccountL = getSecuriCADAssocElemIDs(eid, 'UserAccount', con)
            user = newUser(users, eid, elabel, None, useraccountL)
            created[eid] = useraccount

    #Datastore
    datastoreL = getSecuriCADElements('Datastore', dateID, con)
    if (len(datastoreL) > 0):
        datastores = ET.SubElement(root, "datastores")
        for n in datastoreL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            datastore = newDatastore(datastores, eid, elabel, None)
            created[eid] = datastore


    #Router
    routerL = getSecuriCADElements('Router', dateID, con)
    if (len(routerL) > 0):
        routers = ET.SubElement(root, "routers")
        for n in routerL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            firewallid = getSecuriCADAssocElemIDs(eid, 'Firewall', con)
            if(len(firewallid)>0):
                firewallid = firewallid[0]
            else: firewallid = None
            networkidL = getSecuriCADAssocElemIDsReverse(eid, 'Network', con)
            newNetworkidL=[]
            for n in networkidL:
                newNetworkidL.append((n, 'connection'))
            router = newRouter(routers, eid, elabel, firewallid, newNetworkidL)
            created[eid] = router

    #WebApplication Firewall
    webapplicationfirewallL = getSecuriCADElements('WebApplicationFirewall', dateID, con)
    if (len(webapplicationfirewallL) > 0):
        webapplicationfirewalls = ET.SubElement(root, "webapplicationfirewalls")
        for n in webapplicationfirewallL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            webapplicationfirewall = newWebApplicationFW(webapplicationfirewalls, eid, elabel, None, None, None, None, None)
            created[eid] = webapplicationfirewall

    #WebApplication
    webapplicationL = getSecuriCADElements('WebApplication', dateID, con)
    if (len(webapplicationL) > 0):
        webapplications = ET.SubElement(root, "webapplications")
        for n in webapplicationL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            accesscontrolid = getSecuriCADAssocElemIDs(eid, 'AccessControl', con)
            if(len(accesscontrolid)>0):
                accesscontrolid = accesscontrolid[0]
            else: accesscontrolid = None
            datastoreid = getSecuriCADAssocElemIDs(eid, 'Datastore', con)
            if(len(datastoreid)>0):
                datastoreid = datastoreid[0]
            else: datastoreid = None
            webapplicationfirewallid = getSecuriCADAssocElemIDs(eid, 'WebApplicationFirewall', con)
            if(len(webapplicationfirewallid)>0):
                webapplicationfirewallid =  webapplicationfirewallid[0]
            else: webapplicationfirewallid = None
            webapplication = newWebApplication(webapplications, eid, elabel, None, None, None, None, None, None, None,
                                               accesscontrolid, datastoreid, webapplicationfirewallid)
            created[eid] = webapplication

    #Firewall
    firewallL = getSecuriCADElements('Firewall', dateID, con)
    if (len(firewallL) > 0):
        firewalls = ET.SubElement(root, "firewalls")
        for n in firewallL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            firewall = newFirewall(firewalls, eid, elabel, None, None)
            created[eid] = firewall


    #Protocol
    protocolL = getSecuriCADElements('Protocol', dateID, con)
    if (len(protocolL) > 0):
        protocols = ET.SubElement(root, "protocols")
        for n in protocolL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            protocol = newProtocol(protocols, eid, elabel, '0.0', '0.0', '0.0')
            created[eid] = protocol

    #Dataflow
    dataflowL = getSecuriCADElements('Dataflow', dateID, con)
    if (len(dataflowL) > 0):
        dataflows = ET.SubElement(root, "dataflows")
        for n in dataflowL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            protocolid = getSecuriCADAssocElemIDs(eid, 'Protocol', con)
            if(len(protocolid)>0):
                protocolid = protocolid[0]
            else: protocolid = None
            dataflowkeystoreid = getSecuriCADAssocElemIDs(eid, 'Keystore', con)
            if(len(dataflowkeystoreid)>0):
                dataflowkeystoreid = dataflowkeystoreid[0]
            else: dataflowkeystoreid = None
            routerid = getSecuriCADAssocElemIDs(eid, 'Router', con)
            if(len(routerid)>0):
                routerid = routerid[0]
            else: routerid = None
            clientid = getSecuriCADAssocElemIDsReverse(eid, 'Client', con)
            if(len(clientid)>0):
                clientid = clientid[0]
            else: clientid = None
            serviceid = getSecuriCADAssocElemIDs(eid, 'Service', con)
            if(len(serviceid)>0):
                serviceid = serviceid[0]
            else: serviceid = None
            datastoreid = getSecuriCADAssocElemIDs(eid, 'Datastore', con)
            if(len(datastoreid)>0):
                datastoreid = datastoreid[0]
            else: datastoreid = None
            idsid = getSecuriCADAssocElemIDs(eid, 'IDS', con)
            if(len(idsid)>0):
                idsid = idsid[0]
            else: idsid = None
            ipsid = getSecuriCADAssocElemIDs(eid, 'IPS', con)
            if(len(ipsid)>0):
                ipsid = ipsid[0]
            else: ipsid = None
            firewallid = getSecuriCADAssocElemIDs(eid, 'Firewall', con)
            if(len(firewallid)>0):
                firewallid = firewallid[0]
            else: firewallid = None
            if(clientid !=None and serviceid !=None):
                dataflow = newDataflow(dataflows, eid, elabel, protocolid, dataflowkeystoreid, routerid, clientid, serviceid,
                                       datastoreid, idsid, ipsid, firewallid)
                created[eid] = dataflow

    #VulnerabilityScanner
    vulnerabilityscannerL = getSecuriCADElements('VulnerabilityScanner', dateID, con)
    if (len(vulnerabilityscannerL) > 0):
        vulnerabilityscanners = ET.SubElement(root, "vulnerabilityscanners")
        for n in vulnerabilityscannerL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            networkidL = getSecuriCADAssocElemIDs(eid, 'Network', con)
            hostidsL = getSecuriCADAssocElemIDs(eid, 'Host', con)
            vulnerabilityscanner = newVulnerabilityscanner(vulnerabilityscanners, eid, elabel, None, networkidL, hostidsL)
            created[eid] = vulnerabilityscanner

    #IDS
    idsL = getSecuriCADElements('IDS', dateID, con)
    if (len(idsL) > 0):
        idss = ET.SubElement(root, "idss")
        for n in idsL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            hostid = getSecuriCADAssocElemIDs(eid, 'Host', con)
            if(len(hostid)>0):
                hostid = hostid[0]
            else: hostid = None
            routerid = getSecuriCADAssocElemIDs(eid, 'Router', con)
            if(len(routerid)>0):
                routerid = routerid[0]
            else: routerid = None
            ids = newIDS(idss, eid, elabel, None, None, None, hostid, routerid)
            created[eid] = ids

    #IPS
    ipsL = getSecuriCADElements('IPS', dateID, con)
    if (len(ipsL) > 0):
        ipss = ET.SubElement(root, "ipss")
        for n in ipsL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            dataflowids = getSecuriCADAssocElemIDs(eid, 'Dataflow', con)
            routerid = getSecuriCADAssocElemIDs(eid, 'Router', con)
            if(len(routerid)>0):
                routerid = routerid[0]
            else: routerid = None
            ips = newIPS(ipss, eid, elabel, None, dataflowids, routerid)
            created[eid] = ips

    #ZoneManagement
    zonemanagementL = getSecuriCADElements('ZoneManagement', dateID, con)
    if (len(zonemanagementL) > 0):
        zonemanagements = ET.SubElement(root, "zonemanagements")
        for n in zonemanagementL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            networkidL = getSecuriCADAssocElemIDs(eid, 'Network', con)
            zonemanagement = newZoneManagement(zonemanagements, eid, elabel, None, None, None, None, None, networkidL)
            created[eid] = zonemanagement

    #PhysicalZone
    physicalzoneL = getSecuriCADElements('PhysicalZone', dateID, con)
    if (len(physicalzoneL) > 0):
        physicalzones = ET.SubElement(root, "physicalzones")
        for n in physicalzoneL:
            eid = n.get('_key')
            elabel = n.get('label')
            eclass = n.get('class')
            # existen=n.get('existence')
            useraccountidL = getSecuriCADAssocElemIDs(eid, 'UserAccount', con)
            physicalzone = newPhysicalZone(physicalzones, eid, elabel, None, useraccountidL)
            created[eid] = physicalzone

    #SoftwareProduct
    softwareproductL = getSecuriCADElements('SoftwareProduct', dateID, con)
    if (len(softwareproductL) > 0):
        softwareproducts = ET.SubElement(root, "softwareproducts")
        for n in softwareproductL:
                    eid = n.get('_key')
                    elabel = n.get('label')
                    eclass = n.get('class')
                    # existen=n.get('existence')
                    softwareproduct = newSoftwareProduct(softwareproducts,eid, elabel, '0.0', '0.0', '0.0', '0.0','0.0', '0.0',
                                                         '0.0', '0.0')
                    created[eid] = softwareproduct
        if (len(generateSWP) > 0):
            for k, v in generateSWP.items():
                softwareproduct = newSoftwareProduct(softwareproducts, k, v, '0.0', '0.0', '0.0', '0.0', '0.0',
                                                     '0.0',
                                                     '0.0', '0.0')
                created[eid] = softwareproduct
    #Check if all clients and services have a software product


    #tree = ET.ElementTree(root)
    #tree.write(fileName , encoding="UTF-8", xml_declaration=True)

    xmlstr = minidom.parseString(ET.tostring(root), ).toprettyxml(indent="   ")
    with open(fileName, "w") as f: f.write(xmlstr)

#prepareXML('securicadF51.xml','07/09/2017', createConArango('claimOmania'))



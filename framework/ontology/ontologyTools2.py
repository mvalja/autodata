from pyArango.connection import *
import re
import tools
import xml.etree.ElementTree as ET

def createConArango(dbname):
    conn = Connection(username="root", password="P4lju4ndm3id")
    #conn.createDatabase(name="Ontology")
    return conn[dbname]


#Create a node linked to a node

def storeElementArango(clss, name, coll, client):
    collection = client[coll]
    first = collection.createDocument()
    first['type']=clss
    first["name"] = name
    first.save()
    return first._id

def storeAssocArango(startTT, startNT,endK,edgeName, coll, collAssoc, client):
    startK = client[coll].fetchByExample({'type': startTT, 'name': startNT}, batchSize=100)
    startK = startK[0]._id
    edge = client[collAssoc].createEdge()
    edge.links(startK, endK)
    edge['name']=edgeName
    edge.patch()

def storeAssocArangoSimple(startK, endK, edgeName, collAssoc, client):
    edge = client[collAssoc].createEdge()
    edge.links(startK, endK)
    edge['name']=edgeName
    edge.patch()


def storeElementList(elementList, superElKey, coll,collAssoc, client, created=dict()):
    prevK = None
    firstK= None
    for el in elementList:
        type=el.get('type')
        name=el.get('name')
        if((type, name) not in created):
            elK=storeElementArango(type, name, coll, client)
            if(prevK==None):
                firstK=elK
            created[(type,name)]=elK
        else:
            elK=created.get((type, name))
        if(prevK!=None):
            edge = client[collAssoc].createEdge()
            edge.links(prevK, elK)
        prevK=elK
    if (superElKey != None and firstK!=None):
        edge = client[collAssoc].createEdge()
        edge.links(superElKey, firstK)
    return created



def createSchema():
    coll='software'
    collAssoc=coll+'Assoc'
    con=createConArango('Ontology')
    super = storeElementArango('class', 'Ontology', coll, con)
    list1=[{'type':'class','name':'Software'},{'type':'class','name':'Linux'}]
    list2=[{'type':'class','name':'Software'},{'type':'class','name':'Windows'}]
    list3=[{'type':'class','name':'Dataflow'}]
    list4=[{'type':'class','name':'Vulnerability'}]
    created = storeElementList(list1, super, coll, collAssoc, con)
    created2 = storeElementList(list2, super, coll, collAssoc, con, created)
    created3 = storeElementList(list3, super, coll, collAssoc, con, created2)
    created4 = storeElementList(list4, super, coll, collAssoc, con, created3)


def findProductArchitecture(ontNode, collAssoc, prodName,prodVersion,prodArch, client):
    if(prodName!=None and prodVersion !=None and prodArch!=None):
        aql='''FOR v, e, p IN 0..10 OUTBOUND '{0}' {1} FILTER p.edges[2].name == 'runs_apps' AND p.edges[3].name == 'has_version' FILTER p.vertices[3].type == 'product' AND LOWER(p.vertices[3].name) == "{2}" AND p.vertices[4].type == 'version' AND  LOWER(p.vertices[4].name) == '{3}' AND p.vertices[5].type == 'architecture' AND LOWER(p.vertices[5].name) == '{4}' RETURN p.vertices[5]._id'''.format(ontNode, collAssoc, prodName.lower(), prodVersion.lower(), prodArch.lower())
        result = client.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return result

def extractMainVersion(oldversion, verblacklist=None):
    checkDot = re.findall(r"^\.|^\_", oldversion)
    if(len(checkDot)==0 and oldversion!=None):
        newVerL = re.findall(r"[a-zA-Z0-9]+", oldversion)
        if(verblacklist!=None):
            for ver in verblacklist:
                if(ver in newVerL):
                    newVerL.remove(ver)
        if(len(newVerL)>0):
            return newVerL[0]

def checkVer(prodID, verString, collAssoc, con):
    mainver = extractMainVersion(verString)
    if (mainver == None): mainver = '*'
    if(prodID!=None and verString!=None):
        aql_mainv = '''FOR v,e,p in 0..3 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'mainVersion' AND p.vertices[1].name == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(prodID, collAssoc, mainver)
        aql_ver='''FOR v,e,p in 0..3 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'mainVersion' AND p.vertices[1].name == '{2}' AND p.vertices[2].type == 'version' AND p.vertices[2].name == '{3}' RETURN DISTINCT p.vertices[2]._id'''.format(prodID,collAssoc,mainver, verString)
        result_main = con.AQLQuery(aql_mainv, rawResults=True)
        if(len(result_main) > 0):
            result_ver = con.AQLQuery(aql_ver, rawResults=True)
        else: return
        if (len(result_ver) > 0):
            return {'version':result_ver[0]}
        else:
            return {'main': result_main[0]}

#print(checkVer('software/25846645','1.7-45.el7','softwareAssoc', con))


def checkDesc(prodID, descString, collAssoc, con):
    if(prodID!=None and descString!=None):
        descString=descString.replace('"', "'")
        aql = '''FOR v,e,p in 0..3 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'description' AND LOWER(p.vertices[1].name) == "{2}" RETURN DISTINCT p.vertices[1]._id'''.format(prodID, collAssoc, descString.lower())
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True

def checkProd(prodID, collAssoc, con):
    if(prodID!=None):
        aql = '''FOR v,e,p in 0..3 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'sw_class' RETURN DISTINCT p.vertices[1]._id'''.format(prodID, collAssoc)
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True
        else: return False

def isEqual(a, b):
    try:
        return a.upper() == b.upper()
    except AttributeError:
        return a == b

def isNotEqual(a, b):
    try:
        return a.upper() != b.upper()
    except AttributeError:
        return a != b

def containsNumber(string):
    if(re.search('\d', string)!=None):
       return True
    else: return False


def checkOpsys(platformID, opsysN,collAssoc, con):
    if(platformID!=None):
        aql = '''FOR v,e,p in 0..1 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'opsys' AND p.vertices[1].name == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(platformID, collAssoc, opsysN)
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True
        else: return False

def checkOpsysMainVer(opsysID,version,collAssoc, con):
    if(opsysID!=None and version!=None):
        aql = '''FOR v,e,p in 0..1 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'mainVersion' AND LOWER(p.vertices[1].name) == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(opsysID, collAssoc, version.lower())
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True
        else: return False

def checkOpsysVer(opsysID,version,collAssoc, con):
    if(opsysID!=None and version!=None):
        aql = '''FOR v,e,p in 0..2 OUTBOUND '{0}' {1} FILTER p.vertices[2].type == 'version' AND LOWER(p.vertices[2].name) == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(opsysID, collAssoc, version.lower())
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True
        else: return False

def getOpsysMainVerK(opsysID,version,collAssoc, con):
    if(opsysID!=None and version!=None):
        aql = '''FOR v,e,p in 0..1 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'mainVersion' AND LOWER(p.vertices[1].name) == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(opsysID, collAssoc, version.lower())
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return result[0]

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


def checkAttackCVE(attackNodeK,cve,collAssoc, con):
    if(attackNodeK!=None and cve!=None):
        aql = '''FOR v,e,p in 0..1 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'cve' AND p.vertices[1].name == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(attackNodeK, collAssoc, cve)
        result = con.AQLQuery(aql, rawResults=True)
        return result



"""

coll='software'
collAssoc=coll+'Assoc'
con=createConArango('Ontology')
super=storeElementArango('class','Start',coll, con)
branch1=[{'type':'class','name':'Software'},{'type':'class','name':'OperatingSystem'},{'type':'class','name':'Linux'},{'type':'class','name':'LinuxApplication'}]
branch2=[{'type':'class','name':'Software'},{'type':'class','name':'OperatingSystem'},{'type':'class','name':'Windows'},{'type':'class','name':'WindowsApplication'}]
branch3=[{'type':'class','name':'LinuxApplication'},{'type':'data','name':'StandardName'}]
created=storeElementList(branch1,super ,coll, collAssoc,con)
created2=storeElementList(branch2, super,coll, collAssoc,con, created)
#storeElementList(branch3, None,coll, collAssoc,con, created2)

"""
metamodel = dict()
from pprint import pprint

def createModel():
    #AccessControl
    acDefences=["noDefaultPasswords", "passwordPolicyEnforcement", "salting", "enabled", "backoff",
                                  "hashedPasswordRepository"]
    acAssociations = dict()
    acAssociations["1"]={"name":"Authorization","target":"Host","multiplicity":"many"}
    acAssociations["2"]={"name":"Authorization","target":"Service","multiplicity":"many"}
    acAssociations["3"] = {"name": "Authorization", "target": "UserAccount", "multiplicity": "many"}
    metamodel["AccessControl"] = {"defences": acDefences, "associations": acAssociations}

    #Client
    clDefences=["patched"]
    clAssociations = dict()
    clAssociations["1"]={"name":"Client execution","target":"Host","multiplicity":"one"}
    clAssociations["2"]={"name":"Communication","target":"Dataflow","multiplicity":"many"}
    clAssociations["3"]={"name":"Database execution","target":"Datastore","multiplicity":"one"}
    clAssociations["4"]={"name":"Software status","target":"SoftwareProduct","multiplicity":"one"}
    metamodel["Client"] ={"defences":clDefences,"associations":clAssociations}
    #Service
    svDefences=["patched"]
    svAssociations = dict()
    svAssociations["1"]={"name":"Authorization","target":"AccessControl","multiplicity":"one"}
    svAssociations["2"]={"name":"Communication","target":"Dataflow","multiplicity":"one"}
    svAssociations["3"]={"name":"Application execution","target":"Host","multiplicity":"one"}
    svAssociations["4"]={"name":"Shell execution","target":"Host","multiplicity":"one"}
    svAssociations["5"]={"name":"Web server execution","target":"WebApplication","multiplicity":"many"}
    svAssociations["6"]={"name":"Database execution","target":"Datastore","multiplicity":"one"}
    svAssociations["7"]={"name":"Software status","target":"SoftwareProduct","multiplicity":"one"}
    svAssociations["8"]={"name":"Fake","target":"Protocol","multiplicity":"one"} #FAKE for testing purposes
    metamodel["Service"] = {"defences":svDefences,"associations":svAssociations}

    #Dataflow
    dfAssociations = dict()
    dfAssociations["1"]={"name":"Communication","target":"Client","multiplicity":"one"}
    dfAssociations["2"]={"name":"Communication","target":"Datastore","multiplicity":"many"}
    dfAssociations["3"]={"name":"Communication","target":"Network","multiplicity":"many"}
    dfAssociations["4"]={"name":"Protocol status","target":"Protocol","multiplicity":"one"}
    dfAssociations["5"]={"name":"Communication","target":"Router","multiplicity":"many"}
    dfAssociations["6"]={"name":"Communication","target":"Service","multiplicity":"one"}
    metamodel["Dataflow"] = {"defences":None,"associations":dfAssociations}

    #Datastore
    dsDefences= ["encrypted"]
    dsAssociations = dict()
    dsAssociations["1"]={"name":"Database execution","target":"Host","multiplicity":"one"}
    dsAssociations["2"]={"name":"Database execution","target":"Client","multiplicity":"one"}
    dsAssociations["3"]={"name":"Database execution","target":"Service","multiplicity":"one"}
    metamodel["Datastore"] = {"defences":dsDefences,"associations":dsAssociations}

    #Firewall
    rtDefences= ["knownRuleSet", "enabled"]
    rtAssociations = dict()
    dsAssociations["1"]={"name":"Firewall execution","target":"Router","multiplicity":"one"}
    metamodel["Firewall"] = {"defences":rtDefences,"associations":rtAssociations}

    #Host
    opDefences= ["aSLR", "dEP", "staticARPTables", "patched", "antiMalware", "hostFirewall"]
    opAssociations = dict()
    opAssociations["1"]={"name":"Authorization","target":"AccessControl","multiplicity":"one"}
    opAssociations["2"]={"name":"Application execution","target":"Service","multiplicity":"many"}
    opAssociations["3"]={"name":"Shell execution","target":"Service","multiplicity":"many"}
    opAssociations["4"]={"name":"Database execution","target":"Datastore","multiplicity":"one"}
    opAssociations["5"]={"name":"HIDS execution","target":"IDS","multiplicity":"one"}
    opAssociations["6"]={"name":"Authenticated scan","target":"VulnerabilityScanner","multiplicity":"many"}
    opAssociations["7"]={"name":"Excluded from scan","target":"VulnerabilityScanner","multiplicity":"many"}
    opAssociations["8"]={"name":"Unauthenticated scan","target":"VulnerabilityScanner","multiplicity":"many"}
    opAssociations["9"]={"name":"Client execution","target":"Client","multiplicity":"many"}
    opAssociations["10"]={"name":"IPS execution","target":"IPS","multiplicity":"one"}
    opAssociations["11"]={"name":"Connection","target":"Network","multiplicity":"many"}
    opAssociations["12"]={"name":"Physical access","target":"PhysicalZone","multiplicity":"one"}
    opAssociations["13"]={"name":"Software status","target":"SoftwareProduct","multiplicity":"one"}
    metamodel["Host"] = {"defences":opDefences,"associations":opAssociations}

    #IDS
    idsDefences = ["updated", "enabled", "tuned"]
    idsAssociations= dict()
    idsAssociations["1"]={"name":"HIDS execution","target":"Host","multiplicity":"one"}
    idsAssociations["2"]={"name":"NDIS execution","target":"Router","multiplicity":"one"}
    metamodel["IDS"] = {"defences":idsDefences,"associations":idsAssociations}

    #IPS
    ipsDefences = ["enabled"]
    ipsAssociations = dict()
    ipsAssociations["1"]={"name":"IPS execution","target":"Host","multiplicity":"many"}
    metamodel["IPS"] = {"defences":ipsDefences,"associations":ipsAssociations}

    #Network
    nzDefences = ["portSecurity", "dNSSec"]
    nzAssociations = dict()
    nzAssociations["1"]={"name":"Connection","target":"Host","multiplicity":"many"}
    nzAssociations["2"]={"name":"Authenticated scan","target":"VulnerabilityScanner","multiplicity":"many"}
    nzAssociations["3"]={"name":"Unauthenticated scan","target":"VulnerabilityScanner","multiplicity":"many"}
    nzAssociations["4"]={"name":"Communication","target":"Dataflow","multiplicity":"many"}
    nzAssociations["5"]={"name":"Physical access","target":"PhysicalZone","multiplicity":"many"}
    nzAssociations["6"]={"name":"Connection","target":"Router","multiplicity":"many"}
    nzAssociations["7"]={"name":"Management status","target":"ZoneManagement","multiplicity":"one"}
    metamodel["Network"] = {"defences":nzDefences,"associations":nzAssociations}

    #PhysicalZone
    pzAssociations = dict()
    pzAssociations["1"]={"name":"Physical access","target":"Host","multiplicity":"many"}
    pzAssociations["2"]={"name":"Physical access","target":"Network","multiplicity":"many"}
    metamodel["PhysicalZone"] = {"defences":None,"associations":pzAssociations}

    #Router
    rtDefences = ["staticARPTables"]
    rtAssociations = dict()
    rtAssociations["1"]={"name":"Connection","target":"Network","multiplicity":"many"}
    rtAssociations["2"]={"name":"Firewall execution","target":"Firewall","multiplicity":"one"}
    rtAssociations["3"]={"name":"NIDS execution","target":"IDS","multiplicity":"one"}
    metamodel["Router"] = {"defences":rtDefences,"associations":rtAssociations}

    #Protocol
    prDefences = ["nonce", "encrypted", "authenticated"]
    prAssociations = dict()
    prAssociations ["1"]={"name":"Protocol status","target":"Dataflow","multiplicity":"many"}
    metamodel["Protocol"] = {"defences":prDefences,"associations":prAssociations}

    #SoftwareProduct
    swpDefences =["staticCodeAnalysis", "scrutinized", "noUnpatchableVulnerability",
                                    "noPatchableVulnerability", "secretBinary", "secretSource", "hasVendorSupport",
                                    "safeLanguages"]
    swpAssociations = dict()
    swpAssociations ["1"]={"name":"Software status","target":"Host","multiplicity":"many"}
    swpAssociations ["2"]={"name":"Software status","target":"Service","multiplicity":"many"}
    swpAssociations ["3"]={"name":"Software status","target":"Client","multiplicity":"many"}
    metamodel["SoftwareProduct"] = {"defences":swpDefences,"associations":swpAssociations}

    #User
    usDefences = ["securityAware"]
    usAssociations = dict()
    usAssociations ["1"]={"name":"Authentication","target":"UserAccount","multiplicity":"many"}
    metamodel["User"] = {"defences":usDefences,"associations":usAssociations}

    #UserAccount
    #usaDefences = None
    usaAssociations = dict()
    usaAssociations ["1"]={"name":"Authentication","target":"User","multiplicity":"one"}
    metamodel["UserAccount"] = {"defences":None,"associations":usaAssociations}

    #VulnerabilityScanner
    vsDefences = ["enabled"]
    vsAssociations = dict()
    vsAssociations ["1"]={"name":"Authenticated scan","target":"Network","multiplicity":"many"}
    vsAssociations ["2"]={"name":"Unauthenticated scan","target":"Network","multiplicity":"many"}
    vsAssociations ["3"]={"name":"Authenticated scan","target":"Host","multiplicity":"many"}
    vsAssociations ["4"]={"name":"Unauthenticated scan","target":"Host","multiplicity":"many"}
    vsAssociations ["5"]={"name":"Excluded from scan","target":"Host","multiplicity":"many"}
    metamodel["VulnerabilityScanner"] = {"defences":vsDefences,"associations":vsAssociations}

    #WebApplication
    waDefences= ["noPublicXSSVulnerabilities", "typeSafeAPI", "securityAwareDevelopers",
                                   "blackBoxTesting", "noPublicCIVulnerabilities", "noPublicRFIVulnerabilities",
                                   "noPublicSQLIVulnerabilities", "staticCodeAnalysis"]
    waAssociations = dict()
    waAssociations ["1"]={"name":"Web server execution","target":"Service","multiplicity":"one"}
    waAssociations ["2"]={"name":"WebApplication","target":"Datastore","multiplicity":"many"}
    waAssociations ["3"]={"name":"Firewall execution","target":"WebApplicationFirewall","multiplicity":"many"}
    metamodel["WebApplication"] = {"defences":waDefences,"associations":waAssociations}

    #WebApplicationFirewall
    wafDefences= ["expertTuned", "blackBoxTuned", "monitored", "tuningEffort"]
    wafAssociations = dict()
    wafAssociations["1"]={"name":"Firewall execution","target":"WebApplication","multiplicity":"many"}
    metamodel["WebApplicationFirewall"] = {"defences":wafDefences,"associations":wafAssociations}

    #ZoneManagement
    zmDefences = ["patchManagement", "hostHardening", "antiMalwarePolicy", "changeControl", "hostFirewall"]
    zmAssociations = dict()
    zmAssociations["1"]={"name":"Management status","target":"Network","multiplicity":"many"}
    metamodel["ZoneManagement"] = {"defences":zmDefences,"associations":zmAssociations}

    return metamodel

def returnDependencies():
    dependencies=set()

    dependencies=(
    ('Network',
     'Host'),

    ('Network',
    'Host',
    'Service'),

    ('Network',
     'Host',
     'Client'),

    ('Network',
     'Host',
     'Client',
     'Dataflow'),

    ('Network',
    'Host',
    'Client',
    'Dataflow',
    'Protocol'),

    ('Network',
    'Host',
    'AccessControl',
    'UserAccount'),

    ('Network',
    'Host',
    'Service',
    'AccessControl'),

    ('Network',
    'Router',
    'AccessControl'),

    ('Network',
    'Host',
    'Client',
    'SoftwareProduct'),

    ('Network',
    'Host',
    'Client',
    'Datastore'),

    ('Network',
    'Host',
    'Service',
    'SoftwareProduct'),

    ('Network',
    'Host',
    'SoftwareProduct'),

    ('Network',
    'Host',
    'Router',
    'Firewall'),


    ('Network',
    'Host',
    'Client',
    'Dataflow',
    'Datastore'),

    ('Network',
    'Host',
    'Datastore'),

    ('Network',
    'Host',
    'Router',
    'IDS'),

    ('Network',
    'Host',
    'IDS'),

    ('Network',
    'Host',
    'IPS'),

    ('Network',
    'Host',
    'PhysicalZone'),

    ('Network',
    'PhysicalZone'),

    ('Network',
    'Host',
    'AccessControl',
    'UserAccount',
    'User'),

    ('Network',
    'Host',
    'VulnerabilityScanner'),

    ('Network',
    'VulnerabilityScanner'),

    ('Network',
    'Host',
    'WebApplication',
    'AccessControl'),

    ('Network',
    'Host',
    'WebApplication',
    'WebApplicationFirewall'),

    ('Network',
    'Host',
    'WebApplication',
    'Datastore'),

    ('Network',
    'ZoneManagement'),

    ('PhysicalZone',
    'ZoneManagement'),

    ('PhysicalZone',
    'Host'),

    ('Network',)
    ,
    ('Network',
     'Host',
     'AccessControl'),


    ('Network',
     'Router')
    )

    return dependencies

def getPreviousValue(el, depSet):
    immediate=set()
    for d in depSet:
        if(el in d):
            indx=d.index(el)
            if(indx!=0):
                immediate.add((d[indx-1], d[indx]))
    return(immediate)

def getAllPreviousValues(el, depSet):
    immediate=set()

    for d in depSet:
        if(el in d):
            indx=d.index(el)
            if(indx!=0):
                temp = []
                for i in range(indx+1):
                    temp.append(d[i])
                immediate.add(tuple(temp))
    return(immediate)


def getValueWithIndex(index, depSet):
    immediate=set()
    index=int(index)
    for d in depSet:
            temp = []
            if(index<=(len(d))):
                for i in range(index):
                    temp.append(d[i])
                immediate.add(tuple(temp))
    return(immediate)

def getBiggestValue(depSet):
    tempcount=0
    for d in depSet:
            if(tempcount<(len(d))):
                tempcount=len(d)
    return tempcount

#print(getAllPreviousValues('SoftwareProduct', returnDependencies()))
#print(getValueWithIndex('1', returnDependencies()))
#print(returnDependencies())
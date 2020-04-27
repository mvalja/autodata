import hashlib
import xml.etree.ElementTree as ET
import os
import platform
import datetime
import pickle
import uuid as UUID
import re, math
from collections import Counter
import ipaddress

def hashfile(afile, filepath, blocksize=65536):
    date=creationDate(filepath).encode('utf-8')
    hasher = hashlib.sha512()
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    hasher.update(date)
    return hasher.hexdigest()


def configParser(fileName):
    tempDb = []
    configTree = ET.parse(fileName)
    configRoot = configTree.getroot()
    importCfg = configRoot.find("Import")
    dbCfg = configRoot.find("Database")
    dbHostName = dbCfg.find("Hostname").text
    dbPort = dbCfg.find("Port").text
    dbName = dbCfg.find("Database").text
    dbUser = dbCfg.find("Username").text
    dbPw = dbCfg.find("Password").text

    tempDb.append({
       "host": dbHostName,
       "port": dbPort,
       "database": dbName,
       "user": dbUser,
       "password":dbPw
        })

    config = {"database": tempDb}
    return config

def sourceCfgParser(fileName):
    tempLoc = []
    tempAdap = []
    configTree = ET.parse(fileName)
    configRoot = configTree.getroot()
    importCfg = configRoot.find("Import")
    for s in importCfg.findall("Source"):
        sourceName= s.get("name")
        coverage = s.get("coverage")
        for f in s:
            location = f.text
            mainip = f.get("mainip")
            nodename = f.get("nodename")
            tempLoc.append( {
                "sourceName": sourceName,
                "mainip": mainip,
                "nodename": nodename,
                "coverage": coverage,
                "location": location
            })
    adapterCfg = configRoot.find("Adapters")
    for adap in adapterCfg.findall("Adapter"):
        adapterName = adap.get("name")
        adapterFile = (adap.find("File")).text
        tempAdap.append({
            "name": adapterName,
            "file": adapterFile
        })
    config = {"imports": tempLoc,
              "adapters": tempAdap}
    return config

def getAdapter(sourceN, adapterList):
    for a in adapterList:
        temp = a.get("name")
        if(sourceN == temp):
            return a.get("file")

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

def creationDate(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    """
    if platform.system() == 'Windows':
        return str(datetime.date.fromtimestamp(os.path.getmtime(path_to_file))) #getctime,getatime,getmtime
    else:
        stat = os.stat(path_to_file)
        return str(datetime.date.fromtimestamp(stat.st_mtime))

def create24Zone(inputIP):
    if(inputIP!=None):
        zone = inputIP.split('.')
        zone[3] = ('0')
        zone = '.'.join(zone)
        return zone


def returnNetworkZone(inputIP): #Input should be 192.168.0.1/24
    if(isinstance(inputIP, str)):
        ip=ipaddress.IPv4Interface(inputIP)
        output=str(ip.network)
        return output

def returnNetworkZone2args(inputIP,inputBits='24'): #Input should be 192.168.0.1/24
    if(isinstance(inputIP, str)):
        inputIP=inputIP+'/'+inputBits
        ip=ipaddress.IPv4Interface(inputIP)
        output=str(ip.network)
        return output

#print(returnNetworkZone2args('192.168.0.1'))

def sortDictList(input):
    seen = set()
    newList = []
    for d in input:
        t = tuple(sorted(d.items()))
        if t not in seen:
            seen.add(t)
            newList.append(d)
    return newList

def hashATuple(inputT):
    tempT = list()
    for i in inputT:
        tempT.append(i.casefold())
    pickledh=pickle.dumps(tempT)
    return hashlib.md5(pickledh).hexdigest()[:10]

def generate_id():
    return "id-"+str(UUID.uuid4().hex)[:10]

def matchDataSources(oldSource,newSource):
    #question - what other data sources can make similar claims as the source in question
    oldSource=re.findall(r"\d{4}\-\d{2}\-\d{2}\_(\w+)", oldSource)[-1].split('_')[0]
    newSource=re.findall(r"\d{4}\-\d{2}\-\d{2}\_(\w+)", newSource)[-1].split('_')[0]
    output=False
    matches=dict()
    matches['etc_passwd']= ()
    matches['hp_procurve'] = ('nessus', 'nexpose', 'nmap')
    matches['nessus'] = ('nexpose', 'nmap')
    matches['nexpose'] = ('nessus', 'nmap')
    matches['nmap'] = ('nessus', 'nexpose')
    matches['p0f'] = ('wireshark', 'netstat')
    matches['powershell-get-user'] = ()
    matches['powershell-win32_product'] = ('nessus', 'nexpose', 'nmap')
    matches['wireshark'] = ('netstat')
    matches['netstat'] = ('wireshark')
    matches['yum-list'] = ('nessus', 'nexpose', 'nmap')
    if(oldSource.lower() in matches):
        oldSet=matches.get(oldSource.lower())
        if(len(oldSet)>0):
            if(newSource.lower() in oldSet):
                output=True
    return output


def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    WORD = re.compile(r'\w+')
    words = WORD.findall(text)
    return Counter(words)

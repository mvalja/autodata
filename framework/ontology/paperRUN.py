import csv
from ontology import ontologyTools2
from pprint import pprint
from sklearn import metrics
from sklearn.feature_extraction.text import HashingVectorizer
import xml.etree.ElementTree as ET
import re
from collections import Counter
from collections import OrderedDict
import xml.etree.ElementTree as ET
import tools
import datetime

coll='software'
collAssoc=coll+'Assoc'
con=ontologyTools2.createConArango('Ontology')
winBlckL=['x86','x64','(ENU)', '(32bit)','(x64)', 'x86_64', 'ENU']
architectureL=['x86', 'x64','(32bit)','(x64)','(x86)', 'x86_64']
linVerCutoff = ['el4','el5','el6','el7']
winVersionL=['XP','Vista', 'Embedded']
linDuplicatesL={'CentOS Linux':'CentOS','Linux Kernel':'Linux','Red Hat Enterprise Linux Server':'Red Hat Enterprise Linux','Ubuntu Linux':'Ubuntu'}
winDuplicatesL={'Standard Edition':'Standard'}
exclssL=['opsys', 'internal']
groupList={'.Net Framework 4.6.1':'.Net Framework  4.6.1','Office 2016':'Office 2016','Access 2016':'Office 2016','Excel 2016':'Office 2016','MUI (English) 2016':'Office 2016'}

def cleanString(instring, blacklist):
    outstring=instring
    outstringL=outstring.split()
    if(blacklist!=None):
        for b in blacklist:
            if(b in outstringL):
                outstringL.remove(b)
        outstring=' '.join(outstringL)
        return outstring.strip()

def readMyCSV(filename, delimiter, skipFirst):
    merged=[]
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        if(skipFirst):
            next(reader, None)
        for row in reader:
            tempL=[]
            for r in row:
                tempL.append(r)
            merged.append(tempL)
    return merged

def addIndivToDBWin(inlist, coll,collAssoc, client):
    for i in inlist:
        pro=i.get('product')
        ven=i.get('vendor')
        ver=i.get('version')
        arch=i.get('architecture')
        mainver=ontologyTools2.extractMainVersion(ver)
        if(mainver==None): mainver='*'
        checkP = client[coll].fetchByExample({'type': 'product', 'name': pro}, batchSize=100)
        checkV = None
        if (len(checkP) > 0):
            prodID = checkP[0]._id
            checkV = ontologyTools2.checkVer(prodID, ver, collAssoc, con)
        if (len(checkP) == 0):
            proKey = ontologyTools2.storeElementArango('product', pro, coll, client)
            ontologyTools2.storeAssocArango('class', 'Windows', proKey, 'runs_apps',coll, collAssoc, client)
            #add vendor
            vkey=ontologyTools2.storeElementArango('vendor', ven, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, vkey,'has_vendor', collAssoc, client)
            #add version
            mverKey = ontologyTools2.storeElementArango('mainVersion', mainver, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, mverKey, 'has_version', collAssoc, client)
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if(arch!=None):
                archKey=ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)
        elif(checkV==None):
            proKey=checkP[0]._id
            mverKey = ontologyTools2.storeElementArango('mainVersion', mainver, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, mverKey, 'has_version', collAssoc, client)
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if (arch != None):
                archKey = ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)
        elif(checkV.get('main') != None and checkV.get('version')==None):
            mverKey = checkV.get('main')
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if (arch != None):
                archKey = ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)

#Import Windows software
def importWinSoft(filename, delimiter, skipFirst, blkL, architectureL):
    output=[]
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for ret in retrieved:
        arch=None
        for ar in architectureL:
            if(ar in ret[6]):
                arch=ar.replace('(','').replace(')','')
        prodN=cleanString(ret[3], blkL)
        vendLong=ret[6].replace(',','')
        vendShort=' '.join(vendLong.split()[0:1])
        if(vendShort in prodN):
            prodN=prodN.replace(vendShort,'').strip()
        vers=ret[7]
        #longProd=prodN+'-'+vers
        if(vers in prodN):
            prodN=prodN.replace(vers,'').replace('-','').replace('  ',' ').strip()
        longProd=prodN+'-'+vers
        output.append({'product':prodN,'vendorLong':vendLong,'vendor': vendShort,'version':vers, 'architecture':arch})
    return output

def importWinClasses(filename, delimiter, skipFirst, blkL, architectureL):
    output=dict()
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for ret in retrieved:
        prodN=cleanString(ret[0], blkL)
        vendLong=ret[1].replace(',','')
        vendShort=' '.join(vendLong.split()[0:1])
        if(vendShort in prodN):
            prodN=prodN.replace(vendShort,'').strip()
        vers=ret[2]
        clss=ret[3]
        #longProd=prodN+'-'+vers
        if(vers in prodN):
            prodN=prodN.replace(vers,'').replace('-','').replace('  ',' ').strip()
        output[prodN]={'vendorLong':vendLong,'vendor': vendShort,'class':clss}
    return output

def importWinOpsys(filename, delimiter, skipFirst, versionL):
    winSet=set()
    output=[]
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for ret in retrieved:
        ret=ret[0].replace('Microsoft', '').strip()
        if(ret not in winSet):
            winSet.add(ret)
            retL = re.findall(r"[a-zA-Z0-9\.]+", ret)
            newNameL=[]
            newVersionL=[]
            indx=0
            for r in retL:
                if(ontologyTools2.containsNumber(r)==False and r not in versionL and r!='Microsoft'):
                    newNameL.append(r)
                    indx+=1
                elif(ontologyTools2.containsNumber(r) or r in versionL): break
            newName =' '.join(newNameL)
            mainversion=None
            if(len(retL)>indx):mainversion = retL[indx]
            newVersion = ' '.join(retL[indx:])
            output.append((newName,mainversion, newVersion))
    return output

def writeOpsysToDB(opsysL, platform, coll, con):
    platfR=con[coll].fetchByExample({'type': 'class', 'name':platform}, batchSize=100)
    platfK=platfR[0]._id
    count=0
    for op in opsysL:
        mainop=op[0]
        mainver=op[1]
        fullver=op[2]
        existCheck=ontologyTools2.checkOpsys(platfK, mainop,collAssoc, con)
        if(existCheck==False):
            opsysK=ontologyTools2.storeElementArango('opsys', mainop, coll, con)
            ontologyTools2.storeAssocArangoSimple(platfK, opsysK, 'is', collAssoc, con)
            if(ontologyTools2.checkOpsysMainVer(opsysK, mainver, collAssoc, con)==False and mainver!=None):
                mainvK = ontologyTools2.storeElementArango('mainVersion', mainver, coll, con)
                ontologyTools2.storeAssocArangoSimple(opsysK, mainvK, 'has_mainVersion', collAssoc, con)
                if (ontologyTools2.checkOpsysVer(opsysK, fullver, collAssoc, con) == False):
                    verK = ontologyTools2.storeElementArango('version', fullver, coll, con)
                    ontologyTools2.storeAssocArangoSimple(mainvK, verK, 'has_version', collAssoc, con)
            elif(mainver!=None):
                if (ontologyTools2.checkOpsysVer(opsysK, fullver, collAssoc, con) == False):
                    verK = ontologyTools2.storeElementArango('version', fullver, coll, con)
                    mainvK=ontologyTools2.getOpsysMainVerK(opsysK, mainver, collAssoc, con)
                    ontologyTools2.storeAssocArangoSimple(mainvK, verK, 'has_version', collAssoc, con)

def importLinOpsys(filename, delimiter, skipFirst, duplicatesL):
    winSet=set()
    output=[]
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for ret in retrieved:
        ret=ret[0]
        for k, v in duplicatesL.items():
            if(k in ret):
                ret=ret.replace(k, v)
        if(ret not in winSet):
            winSet.add(ret)
            retL = re.findall(r"[a-zA-Z0-9\.\-]+", ret)
            newNameL=[]
            newVersionL=[]
            indx=0
            for r in retL:
                if(ontologyTools2.containsNumber(r)==False):
                    newNameL.append(r)
                    indx+=1
                elif(ontologyTools2.containsNumber(r)): break
            newName =' '.join(newNameL)
            mainversion=None
            if(len(retL)>indx):
                mainversion = re.findall(r"[a-zA-Z0-9]+", retL[indx])[0]
            newVersion = ' '.join(retL[indx:])
            output.append((newName,mainversion, newVersion))
    return output

def getStandardOpsysName(inputN, platform, duplicatesL, versionL, coll, collAssoc, con):
    #1. Remove duplicates if any (Lin, Windows)
    for k, v in duplicatesL.items():
        if (k in inputN):
            inputN = inputN.replace(k, v)
    #2. Break into version if Windows
    if(ontologyTools2.isEqual(platform,'Windows')):
        inputN = inputN.replace('Microsoft', '').strip()
        newNameL = []
        mainversion = None
        indx = 0
        nameL = re.findall(r"[a-zA-Z0-9\.\-]+", inputN)
        for r in nameL:
            if (ontologyTools2.containsNumber(r) == False and r not in versionL):
                newNameL.append(r)
                indx += 1
            elif (ontologyTools2.containsNumber(r) or r in versionL):
                break
        inputN = ' '.join(newNameL)
        if(len(nameL)>indx):
            mainversion = nameL[indx]
        newVersion = ' '.join(nameL[indx:])
    else:
        newNameL = []
        mainversion = None
        indx = 0
        nameL = re.findall(r"[a-zA-Z0-9\.\-]+", inputN)
        for r in nameL:
            if (ontologyTools2.containsNumber(r) == False):
                newNameL.append(r)
                indx += 1
            elif (ontologyTools2.containsNumber(r)):
                break
        inputN = ' '.join(newNameL)
        if(len(nameL)>indx):
            mainversion = re.findall(r"[a-zA-Z0-9]+", nameL[indx])[0]
        newVersion = ' '.join(nameL[indx:])
    #for vb in versionCut:
        #if(vb in newVersion):
            #newVersion=newVersion.split('.'+vb)[0]
            #break
    newOpsysLength=len(newNameL)
    #3. Check for a token based match from DB
    aql_start='''FOR opsys in {0} FILTER opsys.type=='opsys' FILTER LENGTH(SPLIT(opsys.name, ' '))=={1} AND'''.format(coll, newOpsysLength)
    aql_series='('
    for pn in newNameL:
        tempaql='CONTAINS(LOWER(opsys.name), "{}") AND '.format(pn.lower())
        aql_series+=tempaql
    aql_series=aql_series.strip().rsplit(' ', 1)[0]
    aql_series+=') RETURN opsys.name'
    aql=aql_start+aql_series
    #print(aql)
    result = con.AQLQuery(aql, rawResults=True)
    if(len(result)>0):
        return [result[0], newVersion]
    else: return [inputN, newVersion]
    #3.1 Opsys
    #3.2 MainVersion
    #3.3 Subversion

def readDebianClass(filename, delimiter,skipFirst):
    output=[]
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for r in retrieved:
        prodn=r[0].split('(')[0]
        if('(' in r[0]):
            vers = r[0].split('(')[1].replace('(','').replace(')','').strip()
        else:
            vers = None
        clss=r[1]
        output.append({'product':prodn,'version':vers,'class':clss})
    return output

#Read CPE info
def importCPExml(filename):
    output=[]
    count=0
    archicount=0
    ns = {'xml':"http://www.w3.org/XML/1998/namespace",'xmlns': "http://cpe.mitre.org/dictionary/2.0","cpe-23":"http://scap.nist.gov/schema/cpe-extension/2.3"}
    # open switch list file for reading
    tree = ET.parse(filename)
    root = tree.getroot()
    for i in root.findall("xmlns:cpe-item", ns):
        release=None
        title=i.find('xmlns:title',ns).text
        lang=i.find('xmlns:title',ns).attrib.values()#
        if(list(lang)[0]=="en-US"):
            cpe23=i.find('cpe-23:cpe23-item', ns).get('name')
            cpeL=re.findall(r"[^:]+", cpe23)
            #cpeL=re.findall(r"([\w\.\-\_\*\+\&\/]+)", cpe23)
            if(cpeL[2]=='a' and '\:' not in cpe23):
                product=cpeL[4].replace('\\','').replace('_',' ')
                vendor=cpeL[3]
                version=cpeL[5]
                archi=cpeL[11]
                if(archi!='*' and archi !='-'):
                    archicount+=1
                if (cpeL[9] != '*' and cpeL[9] != None and cpeL[9] != '-' ):
                    release = cpeL[9].replace('_',' ')
                output.append({'title':title,'cpe23':cpe23, 'product':product, 'vendor':vendor,'version':version, 'release':release, 'architecture':archi})
                count+=1
    print('CPEs',count, 'Archi-count', archicount)
    return output

#Import Linux software
def addIndivToDBLin(inlist, coll,collAssoc, client):
    for i in inlist:
        pro=i.get('product')
        desc=i.get('description')
        desc=desc.replace('"', "'")
        ver=i.get('version')
        arch=i.get('architecture')
        mainver=ontologyTools2.extractMainVersion(ver)
        if(mainver==None): mainver='*'
        checkP = client[coll].fetchByExample({'type': 'product', 'name': pro}, batchSize=100)
        checkV = None
        checkD = None
        if(len(checkP)>0):
            prodID=checkP[0]._id
            checkV = ontologyTools2.checkVer(prodID,ver,collAssoc,con)
            checkD = ontologyTools2.checkDesc(prodID,desc,collAssoc,con)
        if(len(checkP)==0):
            proKey=ontologyTools2.storeElementArango('product', pro, coll, client)
            ontologyTools2.storeAssocArango('class', 'Linux',proKey,'runs_apps', coll, collAssoc, client)
            #add description
            dkey=ontologyTools2.storeElementArango('description', desc, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, dkey, 'has_description', collAssoc, client)
            #add version
            mverKey = ontologyTools2.storeElementArango('mainVersion', mainver, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, mverKey, 'has_version', collAssoc, client)
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if(arch!=None):
                archKey=ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)
        elif(checkV==None):
            #add version
            proKey = checkP[0]._id
            mverKey = ontologyTools2.storeElementArango('mainVersion', mainver, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, mverKey, 'has_version', collAssoc, client)
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if(arch!=None):
                archKey=ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)
            if (checkD == None):
                dkey = ontologyTools2.storeElementArango('description', desc, coll, client)
                ontologyTools2.storeAssocArangoSimple(proKey, dkey, 'has_description', collAssoc, client)
        elif (checkV.get('main') != None and checkV.get('version')==None):
            # add version
            mverKey = checkV.get('main')
            proKey = checkP[0]._id
            verKey = ontologyTools2.storeElementArango('version', ver, coll, client)
            ontologyTools2.storeAssocArangoSimple(mverKey, verKey, 'has_exactversion', collAssoc, client)
            if (arch != None):
                archKey = ontologyTools2.storeElementArango('architecture', arch, coll, client)
                ontologyTools2.storeAssocArangoSimple(verKey, archKey, 'has_architecture', collAssoc, client)
            if (checkD == None):
                dkey = ontologyTools2.storeElementArango('description', desc, coll, client)
                ontologyTools2.storeAssocArangoSimple(proKey, dkey, 'has_description', collAssoc, client)
        elif(checkD==None):
            proKey = checkP[0]._id
            dkey=ontologyTools2.storeElementArango('description', desc, coll, client)
            ontologyTools2.storeAssocArangoSimple(proKey, dkey, 'has_description', collAssoc, client)

def importLinuxSoft(filename, delimiter, skipFirst):
    output=[]
    retrieved = readMyCSV(filename, delimiter,skipFirst)
    for ret in retrieved:
        prodN=ret[1]
        arch=ret[4]
        vers=ret[3]
        descr=ret[6]
        longProd=prodN+'-'+vers
        output.append({'product':prodN,'architecture':arch,'version':vers, 'description':descr, 'productLong':longProd})
    return output

def returnUnique(instring):
    if(instring!=None and len(instring)>0):
        wordSet=set(instring.split())
        return ' '.join(wordSet)

def returnCosine(instring1,instring2):
    string1=returnUnique(instring1)
    string2=returnUnique(instring2)
    if(string1 != None and string2!=None):
        vectorizer = HashingVectorizer()
        vectors = vectorizer.transform([string1, string2])
        score=metrics.pairwise.cosine_similarity(vectors, dense_output=True)
        return score[0,1]
    else: print('ERROR: ',instring1,instring2)

def simpleCosine(a_in, b_in):
    # count word occurrences
    a_set=set(a_in.upper().split())#ignore multiplicity
    b_set=set(b_in.upper().split())#ignore multiplicity
    a_vals = Counter(a_set)
    b_vals = Counter(b_set)
    # convert to word-vectors
    words  = list(a_vals.keys() | b_vals.keys())
    a_vect = [a_vals.get(word, 0) for word in words]
    b_vect = [b_vals.get(word, 0) for word in words]
    # find cosine
    len_a  = sum(av*av for av in a_vect) ** 0.5
    len_b  = sum(bv*bv for bv in b_vect) ** 0.5
    dot = sum(av*bv for av,bv in zip(a_vect, b_vect))
    cosine = dot / (len_a * len_b)
    #print(a_in,b_in,cosine)
    assert cosine >=0 and cosine <= 1.001
    return round(cosine, 3)

def compareLinCPECosine(mylist, cpelist):
    output=[]
    for my in mylist:
        prod=my.get('product')
        vers=my.get('version')
        for cpe in cpelist:
            cpeprod=cpe.get('product')
            cpevend=cpe.get('vendor')
            cpever=cpe.get('version')
            if(len(prod)>1 and len(cpeprod)>1):
                cosine=simpleCosine(prod, cpeprod)
                if(cosine>0.8):
                    output.append((prod,vers,cpeprod,cpevend,cpever, cosine))
            else:print('SHORT names', prod, vers, cpeprod,cpevend, cpever)
    return output

def compareLinCPE(mylist, cpelist):
    output=[]
    counter=0
    matchcounter=0
    for my in mylist:
        prod=my.get('product')
        vers=my.get('version')
        counter+=1
        for cpe in cpelist:
            cpeprod=cpe.get('product')
            cpevend=cpe.get('vendor')
            cpever=cpe.get('version')
            if(len(prod)>1 and len(cpeprod)>1):
                if(cpeprod.upper()==prod.upper()):
                    output.append((prod,vers,cpeprod,cpevend,cpever))
                    matchcounter += 1
            else:print('SHORT names', prod, vers, cpeprod,cpevend, cpever)
    print(counter,matchcounter)
    print(len(output))
    return output

def compareWinCPE(mylist, cpelist, blackL):
    output=[]
    for my in mylist:
        vend=my.get('vendor')
        prod=cleanString(my.get('product'), blackL)
        vers=my.get('version')
        for cpe in cpelist:
            cpeprod=cleanString(cpe.get('product'), blackL)
            cpevend=cpe.get('vendor')
            cpever=cpe.get('version')
            if(len(prod)>1 and len(cpeprod)>1):
                if(cpevend.upper()==vend.upper()):
                    simpcos=simpleCosine(prod.replace(vend,''), cpeprod.replace(cpevend,''))
                    if(simpcos>0.8):
                        output.append((prod,cpeprod,simpcos))
            else:print('SHORT names', prod, vers, cpeprod,cpevend, cpever)
    return output


#print(checkDesc('software/25845020', 'Common files for the SSSD', 'softwareAssoc', con))

##################################################################
###################RUN THIS##########################################

#1. Create schema
#ontologyTools2.createSchema()

#2. Add Windows data
#bldad=importWinSoft('data\\bldad01.txt', ';', True, winBlckL, architectureL)
#pprint(bldad)
#bldde01=importWinSoft('data\\bldde01.txt', ';', True, winBlckL,architectureL)
#pprint(bldde01)
#winscanner=importWinSoft('data\\winscanner.txt', ';', True, winBlckL,architectureL)
#pprint(winscanner)

#pprint(importWinCl)
#addIndivToDBWin(winscanner, coll,collAssoc, con)
#addIndivToDBWin(bldad, coll,collAssoc, con)
#addIndivToDBWin(bldde01, coll,collAssoc, con)

#3. Add Linux data
#scadaA = importLinuxSoft('data\\installed-a_N.txt', ';', True)
#scadaB = importLinuxSoft('data\\installed-b_N.txt', ';', True)
#addIndivToDBLin(scadaA, coll, collAssoc, con)
#addIndivToDBLin(scadaB, coll, collAssoc, con)

#4. Add operating system data
#winOpsys = importWinOpsys('data\\opsystemWindows.csv', ';', True, winVersionL)
#linOpsys = importLinOpsys('data\\opsystemLinux.csv', ';', True, linDuplicatesL)

#pprint(linOpsys)
#writeOpsysToDB(winOpsys,'Windows', coll, con)
#writeOpsysToDB(linOpsys,'Linux', coll, con)
#5. Get standard opsys name

#print(getStandardOpsysName('FreeBSD 10.3-RELEASE-p5', 'Linux', linDuplicatesL, winVersionL, coll, collAssoc, con))

#cpelist=importCPExml("data\\official-cpe-dictionary_v2.3.xml")
#findProductArchitecture

def addCPEtoDBproduct(cpeL, coll, collAssoc, client):
    ontNode=client[coll].fetchByExample({'type': 'class', 'name':'Ontology'}, batchSize=100)
    ontNodeId=ontNode[0]._id
    count=0
    for cpe in cpeL:
        prod=cpe.get('product').replace('"','')
        ver=cpe.get('version')
        arch=cpe.get('architecture')
        #if(arch!='*' and arch !='-'):
            #print(prod, ver, arch)
        print(ontologyTools2.extractMainVersion(ver), ver)
        dbarchid=None#ontologyTools2.findProductArchitecture(ontNodeId, collAssoc, prod, ver, arch, client)
        if(dbarchid!=None):
            cpe23 = cpe.get('cpe23')
            cpekey=ontologyTools2.storeElementArango('cpe23', cpe23, coll, client)
            ontologyTools2.storeAssocArangoSimple(dbarchid, cpekey, 'has_cpe', collAssoc, client)
            count+=1
    print(count)

#addCPEtoDBproduct(cpelist, coll, collAssoc, con)

#pprint(cpelist)


#

#pprint(importWinSoft('data\\bldde01.txt', ';', True))
#pprint(importWinSoft('data\\winscanner.txt', ';', True))

#def compareWinCPE():

#def compareLinDebian():


#clssDef=readDebianClass('data\\debian-combined-comma.csv', ';',False)
#pprint(compareWinCPE(winscanner, cpelist))
#pprint(compareLinCPE(scadaA, cpelist))
#pprint(bldde01)
#pprint(winscanner)

#pprint(importLinuxSoft('data\\installed-a_N.txt', ';', True))
#pprint(importLinuxSoft('data\\installed-b_N.txt', ';', True))


#print(simpleCosine(a,b))

#scadaA=importLinuxSoft('data\\installed-a_N.txt', ';', True)

#pprint(scadaA)
#addIndivToDBLin(scadaA, coll,collAssoc, con)

#scadaB=importLinuxSoft('data\\installed-b_N.txt', ';', True)
#addIndivToDBLin(scadaB, coll,collAssoc, con)

# word-lists to compare
#a = 'bla bla blad'
#b = 'bla blad'

#Import Windows operating systems
#Import Linux operating systems
#Import/generate a list of non-interesing words for Windows
#Import/generate a list of non-interesing words for Linux
#Import/generate a list of acronyms for Windows
#-probably not needed--Import/generate a list acronyms for Linux

#string1= 'bla bla bla3'
#string2= 'blal bla'
#print(returnCosine(string1, string2))


#Get the words that are different function (long-short)
##Get the product name that is different or same?



#Token comparison

#N-gram comparison

#Store all known names and pick one in an interative manner

#A rule to generate a standard name

def getLinStandardDB(inProd, inVer, blackL, coll, collAssoc, con):
    if(inProd!=None and inVer!=None):
        aqlO =con[coll].fetchByExample({'type': 'class', 'name': 'Ontology'}, batchSize=100)
        resultO = con.AQLQuery(aqlO, rawResults=True)
        ontoId=resultO[0]._id
        aqlP = '''FOR v, e, p in 0..3 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'product' AND LOWER(p.vertices[1].name) == "{2}" AND p.vertices[3].type == 'mainVersion' AND LOWER(p.vertices[3].name) == "{2}" RETURN DISTINCT p.vertices[1]._id'''.format(ontoId, collAssoc, inProd.lower(), inVer)
        resultP = con.AQLQuery(aqlP, rawResults=True)
        if (len(resultP) > 0):
            return True

def getLinStandard_old(inProd, inVer, verCutOff, nmBlackL=[]):
    newVerL = re.findall(r"[a-zA-Z0-9]+", inVer)
    newVer=inVer
    for vb in verCutOff:
        if(vb in newVerL):
            newVer=inVer.split('.'+vb)[0]
            break
    newPrL = re.findall(r"[a-zA-Z0-9]+", inProd)
    for nb in nmBlackL:
        if (nb in newPrL):
            newPrL.remove(nb)
    newPr='-'.join(newPrL)
    return newPr, newVer

#FOR pro in software FILTER pro.type=='product' AND (CONTAINS(pro.name, 'rhn') AND CONTAINS(pro.name, 'check')) AND LENGTH(SPLIT(pro.name, '-'))==1 RETURN pro.name
def getLinStandard(inProd, inVer, verCutOffL, nmBlackL, coll, collAssoc, con):
    assert (inProd != None and inVer != None)
    platform = 'Linux'
    newVerL = re.findall(r"[a-zA-Z0-9]+", inVer)
    newVer=inVer
    for vb in verCutOffL:
        if(vb in newVerL):
            newVer=inVer.split('.'+vb)[0]
            break
    newPrL = re.findall(r"[a-zA-Z0-9\_]+", inProd.lower())
    for nb in nmBlackL:
        if (nb in newPrL):
            newPrL.remove(nb)
    #newPr='-'.join(newPrL)
    newPrLength=len(newPrL)
    aql_start='''FOR pro in {0} FILTER pro.type=='product' FILTER LENGTH(SPLIT(pro.name, '-'))=={1} AND'''.format(coll, newPrLength)
    aql_series='('
    assert newPrL!=None
    for pn in newPrL:
        tempaql='CONTAINS(LOWER(pro.name), "{}") AND '.format(pn)
        aql_series+=tempaql
    aql_series=aql_series.strip().rsplit(' ', 1)[0]
    aql_series+=") FOR proassoc in {0} FILTER pro._id==proassoc._to FOR platf in software FILTER platf.name=='{1}' AND platf._id==proassoc._from RETURN pro.name".format(collAssoc,platform)
    aql=aql_start+aql_series
    result = con.AQLQuery(aql, rawResults=True)
    if(len(result)>0):
        return [result[0], newVer]
    else:
        return ['-'.join(newPrL),newVer]

def getSoftwareClass(inProd, coll, con):
    ontoID = con[coll].fetchByExample({'type': 'class', 'name': 'Ontology'}, batchSize=10)
    aql = '''FOR v, e, p in 0..4 OUTBOUND '{0}' {1} FILTER p.vertices[3].type == 'product' AND LOWER(p.vertices[3].name) == "{2}" AND p.vertices[4].type == 'sw_class' RETURN DISTINCT p.vertices[4].name'''.format(ontoID[0]._id, collAssoc, inProd.lower())
    result = con.AQLQuery(aql, rawResults=True)
    if (len(result) > 0):
        return result[0]
    else: return 'unknown'

#print(getSoftwareClass('Office 64-bit Components 2016', coll, con))

def getSoftwareGroupLin(inProd, clss,exclssL ):
    for ex in exclssL:
        if(ontologyTools2.isEqual(ex,clss)):
            return None
    inProdL = re.findall(r"[a-zA-Z0-9]+", inProd)
    groupN=inProdL[0]
    return groupN


def getSoftwareGroupWin(inProd, groupList, clss, exclssL ):
    for ex in exclssL:
        if(ontologyTools2.isEqual(ex,clss)):
            return None
    inProdL = re.findall(r"[a-zA-Z0-9\-\.]+", inProd)
    for gk, gv in groupList.items():
        keyws=re.findall(r"[a-zA-Z0-9\-\.]+", gk)
        keywslen=len(keyws)
        tempcount=0
        for k in keyws:
            for i in inProdL:
                if (ontologyTools2.isEqual(k,i)):
                    tempcount += 1
        if(tempcount==keywslen):
            return gv

#print(getSoftwareGroupLin('xorg-x11-evdev-drv','client',exclssL))
#print(getSoftwareGroupWin('Microsoft .NET Framework 4.6.1 SDK',groupList,'client',exclssL))

#print(getLinStandard('NM_CyberSecurity',' 9.0.0-25', linVerCutoff, [], coll, con))
#FOR pro in software FILTER pro.type=='product' FILTER LENGTH(SPLIT(pro.name, ' '))==1 AND(CONTAINS(LOWER(pro.name), "putty")) FOR proassoc in softwareAssoc FILTER pro._id==proassoc._to FOR platf in software FILTER platf.name=='Windows'AND platf._id==proassoc._from RETURN pro.name

def getWinStandard(inProd, inVer, vendor, verCutOffL, nmBlackL, coll, collAssoc, con):
    platform='Windows'
    if(vendor in inProd):
        inProd=inProd.replace(vendor,'').strip()
    if(inVer in inProd):
            inProd=inProd.replace(inVer,'').replace('-','').replace('  ',' ').strip()
    newVerL = re.findall(r"[a-zA-Z0-9]+", inVer)
    newVer=inVer
    for vb in verCutOffL:
        if(vb in newVerL):
            newVer=inVer.split('.'+vb)[0]
            break
    newPrL = re.findall(r"[a-zA-Z0-9\-\.\+]+", inProd.split('-')[0].strip())
    for nb in nmBlackL:
        if (nb in newPrL):
            newPrL.remove(nb)
    #print(newPrL)
    newPrLength=len(newPrL)
    aql_start='''FOR pro in {0} FILTER pro.type=='product' FILTER LENGTH(SPLIT(pro.name, ' '))=={1} AND'''.format(coll, newPrLength)
    aql_series='('
    for pn in newPrL:
        tempaql='CONTAINS(LOWER(pro.name), "{}") AND '.format(pn.lower())
        aql_series+=tempaql
    aql_series=aql_series.strip().rsplit(' ', 1)[0]
    aql_series+=") FOR proassoc in {0} FILTER pro._id==proassoc._to FOR platf in software FILTER platf.name=='{1}' AND platf._id==proassoc._from RETURN pro.name".format(collAssoc,platform)
    aql=aql_start+aql_series
    #print(aql)
    result = con.AQLQuery(aql, rawResults=True)
    if(len(result)>0):
        return [result[0], newVer]
    else: return [' '.join(newPrL),newVer]

#print(getWinStandard('Office 64-bit Components 2016','16.0.4266.1001', [], winBlckL, coll, con))

def tokenMatchLin(inProd, coll, con):
    aql='''FOR pro in {0} FILTER pro.type == 'product' RETURN DISTINCT pro.name'''.format(coll)
    result = con.AQLQuery(aql, rawResults=True, batchSize=100000)
    outName=''
    linProd=inProd.replace('-',' ')
    if (len(result) > 0):
        bestMatch=[0,None]
        for r in result:
            rr=r.replace('-',' ')
            if(linProd==rr):
                outName=rr
                break
        if(outName==''):
            print('test')
            for r in result:
                rr=r.replace('-', ' ')
                temp=simpleCosine(linProd, rr)
                if(temp>bestMatch[0]):
                    bestMatch[0]=temp
                    bestMatch[1]=r
    if(bestMatch[0]>=1):
        return bestMatch[1]
    else: return inProd

def tokenMatchWin(inProd, coll, con):
    aql='''FOR pro in {0} FILTER pro.type == 'product' RETURN DISTINCT pro.name'''.format(coll)
    result = con.AQLQuery(aql, rawResults=True, batchSize=100000)
    print(type(result), result)
    outName=''
    if (len(result) > 0):
        bestMatch=[0,None]
        for r in result:
            if(inProd==r):
                outName=r
                break
        if(outName==''):
            print('test')
            for r in result:
                temp=simpleCosine(inProd, r)
                if(temp>bestMatch[0]):
                    bestMatch[0]=temp
                    bestMatch[1]=r
    if(bestMatch[0]>=1):
        return bestMatch[1]
    else: return inProd

def getLinDesc(coll, collAssoc, con):
    #aql='''FOR pro in {0} FILTER pro.type == 'description' RETURN [pro._id, pro.name]'''.format(coll)
    aql = '''FOR pro in {0} FILTER pro.type=='product' FOR proassoc in {1} FILTER pro._id==proassoc._from AND proassoc.name=='has_description' FOR descr in {0} FILTER proassoc._to==descr._id RETURN DISTINCT [pro.name,pro._id, descr.name]'''.format(coll, collAssoc)
    result = con.AQLQuery(aql, rawResults=True, batchSize=100000)
    if(len(result)>0):
        return list(result)


#print(descl)

def findDescrKeywordsLin(keywords, descL):
    output=[]
    kw=keywords.split()
    for d in descL:
        if all(x in d[2] for x in kw):
            output.append(d)
    for o in output:
        descL.remove(o)
    return descL, output

def findDescrKeywordsSequenceLin(keywords, clss, descL):
    output=[]
    templist=[]
    for d in descL:
        if (keywords.lower() in d[2].lower()):
            output.append((d[0], d[1], d[2], clss))
            templist.append(d)
    for o in templist:
        descL.remove(o)
    return descL, output


def findNameLin(name, clss, descL):
    output=[]
    templist=[]
    for d in descL:
        if (name.lower() in d[0].lower()):
            output.append((d[0], d[1], d[2], clss))
            templist.append(d)
    for o in templist:
        descL.remove(o)
    return descL, output


#print(newK)

#readMyCSV('data\\client.csv', ',', False)

def importKeywords(filename, clssN):
    tempL=[]
    importF=readMyCSV(filename, ',', False)
    for i in importF:
        tempL.append((clssN,i[0].strip()))
    return tempL

def importNames(filename):
    tempL=[]
    importF=readMyCSV(filename, ';', False)
    for i in importF:
        tempL.append((i[0].strip(), i[1].strip()))
    return tempL
"""
keywords_client=importKeywords('data\\client.csv','client')
keywords_server=importKeywords('data\\server.csv','server')
keywords_firewall=importKeywords('data\\firewall.csv','firewall')
keywords_datastore=importKeywords('data\\datastore.csv','datastore')
keywords_remove=importKeywords('data\\remove.csv','internal')
names_all=importNames('data\\names.csv')

keywords=keywords_client+ keywords_server+ keywords_firewall+ keywords_datastore + keywords_remove
descl=getLinDesc(coll, collAssoc, con)
#pprint(descl)
#pprint(keywords)

"""

def findRemovebasedonNames(descL, nameL):
    outputL=[]
    for nm in nameL:
        descL, outtemp=findNameLin(nm[1],nm[0] ,descL)
        outputL=outputL+outtemp
    return descL, outputL

def findRemovebasedonNamesAndOrder(descL, nameL, keywordsL):
        outputL=[]
        for nm in nameL:
            descL, outtemp = findNameLin(nm[1], nm[0], descL)
            outputL = outputL + outtemp
        keywordsL.sort(key=lambda x: len(x[1].split()), reverse=True)
        for keyw in keywordsL:
            descL, outtemp=findDescrKeywordsSequenceLin(keyw[1],keyw[0] ,descL)
            outputL=outputL+outtemp
        return descL, outputL
    #Output: [key, class, description]

def writeClassesLinDB(clssdL,coll, collAssoc, con):
    for cl in clssdL:
        productN=cl[0]
        productK=cl[1]
        clssN=cl[3]
        checkCl=ontologyTools2.checkProd(productK, collAssoc, con)
        if(checkCl==False):
            clkey = ontologyTools2.storeElementArango('sw_class', clssN, coll, con)
            ontologyTools2.storeAssocArangoSimple(productK, clkey, 'is_of_class', collAssoc, con)

def writeClassesWinDB(clssdL,coll, collAssoc, con):
    for kc, cv in clssdL.items():
        productN=kc
        productC=cv.get('class').lower()
        if(productC=='local'):productC='client'
        checkProd = con[coll].fetchByExample({'type': 'product', 'name': productN}, batchSize=100)
        if(len(checkProd)>0):
            checkCl = ontologyTools2.checkProd(checkProd[0]._id, collAssoc, con)
        if(checkCl==False):
            clkey = ontologyTools2.storeElementArango('sw_class', productC, coll, con)
            ontologyTools2.storeAssocArangoSimple(checkProd[0]._id, clkey, 'is_of_class', collAssoc, con)



########
##CVE
#######
cwe_rfi=['CWE-434', 'CWE-78','CWE-95','CWE-98', 'CWE-714']
cwe_xss=['CWE-79','CWE-712', 'CWE-931']
cwe_ci=['CWE-77', 'CWE-78', 'CWE-88','CWE-90', 'CWE-91','CWE-93', 'CWE-713','CWE-929']
cwe_sqli=['CWE-89']

def csvCVEparser(filename):
    cveset = set()
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            cveset.add(row[0].strip())
    return cveset


def findCVEData(xmlfile, cweSet):
    ns = {'xmlns':"http://scap.nist.gov/schema/feed/vulnerability/2.0",
          "scap-core":"http://scap.nist.gov/schema/scap-core/0.1",
          "cvss":"http://scap.nist.gov/schema/cvss-v2/0.2",
          "vuln":"http://scap.nist.gov/schema/vulnerability/0.4",
          "xsi":"http://www.w3.org/2001/XMLSchema-instance",
          "nil":"http://scap.nist.gov/schema/patch/0.1",
          "cpe-lang":"http://cpe.mitre.org/language/2.0"}
    tree = ET.parse(xmlfile)
    assert tree!=None
    root = tree.getroot()
    fullData=dict()
    for cs in cweSet:
        myCWE=cs
        for c in root.findall("xmlns:entry", ns):
            newCVE=(c.find("vuln:cve-id", ns)).text
            newCVE=newCVE.strip()
            tempCWE=[]
            tempCPE = []
            for w in c.findall("vuln:cwe", ns):
                cwe = w.get("id")
                tempCWE.append(cwe)
            if(myCWE in tempCWE):
                #tempCVE.append(newCVE)
                for sw in c.findall("vuln:vulnerable-software-list/vuln:product", ns):
                    cpe=sw.text
                    tempCPE.append(cpe)
                if(myCWE not in fullData.keys()):
                    fullData[myCWE]=dict()
                    if('cveL' not in fullData[myCWE].keys()):
                        fullData[myCWE]['cpeL'] = tempCPE
                        fullData[myCWE]['cveL']=[]
                        fullData[myCWE]['cveL'].append(newCVE)
                    else:
                        fullData[myCWE]['cpeL'] += tempCPE
                        fullData[myCWE]['cveL'].append(newCVE)
                else:
                    if('cveL' not in fullData[myCWE].keys()):
                        fullData[myCWE]['cpeL'] = tempCPE
                        fullData[myCWE]['cveL']=[]
                        fullData[myCWE]['cveL'].append(newCVE)
                    else:
                        fullData[myCWE]['cpeL'] += tempCPE
                        fullData[myCWE]['cveL'].append(newCVE)
    return fullData

def mergeDicts(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                mergeDicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            elif(isinstance(a[key], list)):
                    # lists can be only appended
                    if isinstance(b[key], list):
                        # merge lists
                        a[key].extend(b[key])
                    else:
                        # append to list
                        a[key].append(b)
                #raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def getAllCVEfeeds(cweL, start=2010, stop=2018):
    comboCVEs = dict()
    for f in range(start,stop):
        tempDict=dict()
        query='findCVEData("data\\\\nvdcve-2.0-{0}.xml",cweL)'.format(f)
        tempDict=eval(query)
        if(tempDict!=None):
            mergeDicts(comboCVEs,tempDict)
    return comboCVEs


#cwecve_ci=getAllCVEfeeds(cwe_ci)
#cwecve_rfi=getAllCVEfeeds(cwe_rfi)
#cwecve_sqli=getAllCVEfeeds(cwe_sqli)
#cwecve_xss=getAllCVEfeeds(cwe_xss)

def writeCWECVE2DB(modelWeakn, cveDict, coll, collAssoc, con):
    vulnNode = con[coll].fetchByExample({'type': 'class', 'name': 'Vulnerability'}, batchSize=100)
    vulnK=vulnNode[0]._id
    assert modelWeakn != None
    attackNode = con[coll].fetchByExample({'type': 'attackMethod', 'name': modelWeakn}, batchSize=100)
    if(len(attackNode)==0):
        attackNodeK = ontologyTools2.storeElementArango('attackMethod', modelWeakn, coll, con)
        ontologyTools2.storeAssocArangoSimple(vulnK, attackNodeK, 'has_attack', collAssoc, con)
    else:
        attackNodeK=attackNode[0]._id
    for cv in cveDict.values():
        #cpeL=cv.get('cpeL')
        cveL = cv.get('cveL')
        for cve in cveL:
            checkCVE=ontologyTools2.checkAttackCVE(attackNodeK,cve, collAssoc, con)
            if(len(checkCVE)==0):
                cveK = ontologyTools2.storeElementArango('cve', cve, coll, con)
                ontologyTools2.storeAssocArangoSimple(attackNodeK, cveK, 'has_cve', collAssoc, con)

#writeCWECVE2DB('CommandInjection', cwecve_ci, coll, collAssoc, con)
#writeCWECVE2DB('RemoteFileInjection', cwecve_rfi, coll, collAssoc, con)
#writeCWECVE2DB('SQLInjection', cwecve_sqli, coll, collAssoc, con)
#writeCWECVE2DB('XSS', cwecve_xss, coll, collAssoc, con)


def getAttackName(cveN, coll, collAssoc, con):
    aql = '''FOR pro in {0} FILTER pro.type=='cve' AND LOWER(pro.name) =='{1}' FOR proassoc in softwareAssoc FILTER pro._id==proassoc._to AND proassoc.name=='has_cve' FOR descr in {0} FILTER proassoc._from==descr._id RETURN DISTINCT descr.name'''.format(coll, cveN.lower(),  collAssoc)
    result = con.AQLQuery(aql, rawResults=True, batchSize=100000)
    if(len(result)>0):
        return result[0]

def checkForAttack(attackName, nodeKey,collAssoc, con):
    if(attackName!=None and nodeKey!=None):
        aql = '''FOR v,e,p in 0..1 OUTBOUND '{0}' {1} FILTER p.vertices[1].type == 'attack' AND p.vertices[1].label == '{2}' RETURN DISTINCT p.vertices[1]._id'''.format(nodeKey, collAssoc, attackName)
        #print(aql)
        result = con.AQLQuery(aql, rawResults=True)
        if (len(result) > 0):
            return True
        else: return False

#print(getAttackName('cve-2013-0464',coll, collAssoc, con))

############




#list4 = [{'type': 'class', 'name': 'Vulnerability'}]


###list, classed = findRemovebasedonNamesAndOrder(descl, names_all, keywords)
#pprint(classed)
#print('----')
#pprint(list)

###writeClassesLinDB(classed,coll,collAssoc,con)

##importWinCl=importWinClasses('data\\windows-combined2.csv', ';', True, winBlckL,architectureL)
##writeClassesWinDB(importWinCl,coll,collAssoc,con)

#Write to DB


#print(getLinStandard('xorg-x11-drv-evdev','2.8.2-5.el7', linVerCutoff))
#print(tokenMatchLin('xorg-x11-evdev-drv',coll, con))
#print(addClassesKWLin('server','',coll, collAssoc, con))
######################
#TEST standardization
#####################

#Test 1 - Linux
#python-setuptools 0.9.8-4.el7 noarch Python Distutils Enhancements
# xorg-x11-drv-evdev  2.8.2-5.el7 x86_64 Xorg X11 evdev input driver

# INPUT name, version, architecture
# RETURN name, version, architecture


#Test 2 - Windows
# Tenable Nessus (x64) 6.9.0.20070  Tenable Network Security, Inc.
# Adobe Acrobat Reader DC Adobe Systems Incorporated 15.020.20039

######################
#TEST classification
#####################

#TODO:Write query to get products class by matching standard name (tokens)
#getLinStandard('xorg-x11-drv-evdev','2.8.2-5.el7', linVerCutoff)
#-Windows
#-Linux

######################
#TEST grouping
#####################

#TODO: Write query to evaluate if to exclude if 1. Class == internal 2. Name contains keywords 3. Keep only 1st part if name not in inclusion list


"""
def compareWinCPE(mylist, cpelist):
    output=[]
    for my in mylist:
        vend=my.get('vendor')
        prod=my.get('product')
        vers=my.get('version')
        for cpe in cpelist:
            simpcos=0
            newcpeprod=[]
            cpeprod=cpe.get('product').split()
            cpevend=cpe.get('vendor')
            cpevendL=cpevend.split()
            cpever=cpe.get('version')
            templist = cpevendL + cpeprod
            for t in templist:
                if(t not in newcpeprod):
                    newcpeprod.append(t)
            newcpeprod=' '.join(newcpeprod)
            if(len(prod)>1 and len(newcpeprod)>1):
                if(cpevend.upper()==vend.upper()):
                    simpcos=simpleCosine(prod.replace(''), newcpeprod)
                    if(simpcos>0.8):
                        output.append((prod,newcpeprod,simpcos))
            else:print('SHORT names', prod, vers, cpeprod,cpevend, cpever)
    return output

def getLinStandard(inProd, inVer, verBlackL, nmBlackL=[]):
    newVerL = re.findall(r"[a-zA-Z0-9]+", inVer)
    verPunct = re.findall(r"[^a-zA-Z0-9]+", inVer)

    for vb in verBlackL:
        if(vb in newVerL):
            newVerL.remove(vb)
    newPrL = re.findall(r"[a-zA-Z0-9]+", inProd)
    for nb in nmBlackL:
        if (nb in newPrL):
            newPrL.remove(nb)

    newVer='.'.join(newVerL)
    newPr='-'.join(newPrL)

    return newPr, newVer

"""
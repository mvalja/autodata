import securiLangFullv2
from arangoTools import *
import copy
import datetime
import re

###################
##Defined variables
###################





###################
##Support functions
###################

def getAdapterSources(adapterData):
    sources=set()
    for ad in adapterData.values():
        for a in ad:
            source = a.get('source')
            sources.add(source)
    return sources


def getObjectMultiplicity(object, target, fullModel):
    for fMk, fMv in fullModel.items():
        if(tools.isEqual(fMk,object)):
            assList = fMv.get("associations")
            for a in assList.values():
                tar = a.get("target")
                if(tools.isEqual(tar,target)):
                    mul = a.get("multiplicity")
                    return mul

# print(getObjectMultiplicity('Network','Host',securiLangFullv2.createModel()))
def checkTimeSourceClassValueData(flatDict, iTimesrc, ifullV):
    returnValue=False
    for key, val in flatDict.items():
        cld=val.get('claimData')
        for c1 in cld:
            fullN=c1.get('fullName')
            src = c1.get('source')
            if(tools.isEqual(src,iTimesrc)):
                if(tools.isEqual(ifullV,fullN)):
                    returnValue=True
    return returnValue

def checkSubnetExists(flatDict, iTimesrc, isubnet):
    returnValue=False
    for key, val in flatDict.items():
        cld=val.get('claimData')
        for c1 in cld:
            fullN=c1.get('fullName')
            src = c1.get('source')
            if(tools.isEqual(src,iTimesrc)):
                sbnet = (re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN)[0]).replace('<<Network>>', '').strip()
                if(tools.isEqual(sbnet,isubnet)):
                    returnValue=True
    return returnValue

def getMatch(src, ifullN, claims):
    output=False
    for c in claims:
        csrc=c.get('source')
        if(tools.isEqual(src,csrc)):
            cfN=c.get('fullName')
            if (tools.isEqual(ifullN, cfN)):
                output=True
                break
    return output

def getMatchScope(src, scope, fullN, claims):
    output = False
    breakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN)
    subnet = breakup[0].replace('<<Network>>', '')
    host=None
    if(len(breakup)>1):
        breakhost=re.findall(r"<<Host>>([^<]*)", fullN)
        if (len(breakhost) > 0):
            host = re.findall(r"<<Host>>([^<]*)", fullN)[0]
        else:
            #print(fullN)
            host= re.findall(r"<<Router>>([^<]*)", fullN)[0]
    for c in claims:
        csrc = c.get('source')
        if (tools.isEqual(src, csrc)):
            cscope=c.get('scope')
            cfN = c.get('fullName')
            cbreakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", cfN)
            if(tools.isEqual(cscope,'subnet')):
                csubnet = re.findall(r"<<Network>>([^<]*)", cfN)[0]
                if(tools.isEqual(csubnet,subnet)):
                    output=True
                    break
            if(tools.isEqual(cscope,'system') and (len(cbreakup)>1)):
                cbreakhost = re.findall(r"<<Host>>([^<]*)", cfN)
                if (len(cbreakhost) > 0):
                    chost = re.findall(r"<<Host>>([^<]*)", cfN)[0]
                else:
                    chost = re.findall(r"<<Router>>([^<]*)", cfN)[0]
                if(tools.isEqual(host,chost)):
                    output=True
                    break
    return output

def getMatchBase(src, base, claims):
    output = False
    for c in claims:
        csrc = c.get('source')
        if (tools.isEqual(src, csrc)):
            cfN = c.get('fullName')
            breakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", cfN)
            if (len(breakup) > 1):
                cbase = ''.join(breakup[0:-1])
            else:
                cbase = breakup[0]
            if(tools.isEqual(base, cbase)):
                output=True
                break
    return output

def reverseGroupDict(inDict,search_list):
    return [name for name, claim in inDict.items() if claim == search_list]

def getAssocType(elID, con):
    if (elID != None):
        aql = "FOR v, p in inbound '{0}' collectedModelAssoc RETURN DISTINCT p.label".format(
            elID)
    query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
    if(len(query)>0):
        return query[0]

def getLastAssoc(elID, clss, defAssoc, con):
    if (elID != None):
        aql = "FOR e in outbound '{0}' collectedModelAssoc RETURN DISTINCT e".format(
            elID)
        query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
        assocList=[]
        for q in query:
            target=q.get('class')
            id=q.get('_id')
            label=q.get('label')
            doNotuseValue=False
            for da in defAssoc:
                if(len(da)>1):
                    last=da[-1]
                    prelast=da[-2]
                    if(tools.isEqual(prelast,clss) and tools.isEqual(last,target)):
                        doNotuseValue=True
            if(doNotuseValue==False):
                type=getAssocType(id, con)
                assocList.append({"type": type, "class": 'Association', 'targetClass':target, 'targetValue':label, 'targetID':id})
        return assocList

#def getLastProp(elID, clss, con):

def getDFTargetID(dfID, con):
    if (dfID != None):
        targetID=None
        aql = "FOR e in outbound '{0}' collectedModelAssoc FILTER e.class=='Service' RETURN DISTINCT e".format(
            dfID)
        query = con.AQLQuery(aql, rawResults=True)
        assert len(query)==1
        for q in query:
            targetID=q.get('_id')
        return targetID

def round_down(num, digits=4):
    factor = 10.0 ** digits
    return int(num * factor) / factor

def normalizeCredibility(allList, inentity, insource, incred):
    templist= []
    sumcred = 0
    count = 0
    if(incred!=None):
        for nl in allList:
            entity = nl[0]
            attrbute = nl[1]
            source=nl[2]
            cred=nl[3]
            if(tools.isEqual(entity, inentity) and tools.isEqual(source, insource)):
                if(cred!=None):
                    sumcred = sumcred + float(cred)
                else:
                    return None
        assert (sumcred != 0 and isinstance(sumcred, (int, float)))
        retval=(float(incred)/float(sumcred))
        return (retval)

###################
##Main functions
###################

def flattenConData(inputD, con):
    collection='collectedModel'
    flatDict=dict()
    tempList=[]
    shorttempList=[]
    tempDict=dict()
    assocLList=[]
    propList = []
    for key, val in inputD.items():
        if(len(key)>1 or ('Association' in key or 'Property' in key)):
            if('Property' in key or 'Association' in key):
                multipl='one'
            else:
                target=key[-1]
                object=key[-2]
                multipl = getObjectMultiplicity(object, target, securiLangFullv2.createModel())
                #assert multipl != None
                if(multipl==None): print(key)
            tempList = []
            for vs in val:
                fullName=''
                idL=[]
                for v in vs:
                    clss=v.get('class')
                    if(tools.isNotEqual(clss,'Association') and tools.isNotEqual(clss,'AssociationLast') and tools.isNotEqual(clss,'Dataflow')):
                        label=v.get('label')
                        fullName = fullName + '<<' + str(clss) + '>>' + str(label)
                        exist = v.get('existence')
                        srcInfo = v.get('source')
                        id1=v.get('id')
                        assert id !=None
                        idL.append(id1)
                    if(tools.isEqual(clss,'AssociationLast')):
                        astarget=v.get('target')
                        astarID=v.get('targetID')
                        hashedid=checkHashwithID(astarID,groupIDvalues(inputD))
                        astarV=v.get('targetValue')
                        label=v.get('type')
                        fullName = fullName + '<<' + str(clss) +'='+str(hashedid)+'>>'+str(label)
                        #exist = v.get('existence')
                        idL.append(astarID)
                    if(tools.isEqual(clss,'Dataflow')):
                        label = v.get('label')
                        exist = v.get('existence')
                        srcInfo = v.get('source')
                        did=v.get('id')
                        assert did != None
                        targetID=getDFTargetID(did, con)
                        hashedid=checkHashwithID(targetID,groupIDvalues(inputD))
                        fullName = fullName + '<<' + str(clss) + '>>' +str(label) +'='+ str(hashedid)
                        idL.append(did)
                if(fullName!=''):
                    #id=idL[-1]
                    #sourceInfo = getSourceFromCollected(id,'20',collection, con)
                    #if (sourceInfo == None): print(fid, fsrcInfo, fullName)
                    tempList.append({"fullName":fullName, "class":clss,"existence":exist, "id":idL,"source":srcInfo[0],"scope":srcInfo[1],"label":label})
                    print('Created: ',fullName)
        elif (len(key) == 1 and ('Association' not in key or 'Property' not in key)):
            multipl='many'
            tempList = []
            for fs in val:
                fullName=''
                fidL = []
                for f in fs:
                    fclss=f.get('class')
                    if (tools.isNotEqual(fclss, 'Association')):
                        flabel=f.get('label')
                        ffullName = '<<' + str(fclss) + '>>' + str(flabel)
                        fexist = f.get('existence')
                        fsrcInfo = f.get('source')
                        fid1=f.get('id')
                        assert fid1!= None
                        fidL.append(fid1)
                if(ffullName!=''):
                    fid2 = fidL[-1]
                    #fsourceInfo = getSourceFromCollected(fid2,'20',collection, con)
                    #if(fsourceInfo==None):print(fid2, fsrcInfo, fullName)
                    tempList.append({"fullName":ffullName, "class":fclss,"existence":fexist, "id":fidL,"source":fsrcInfo[0],"scope":fsrcInfo[1],"label":flabel})
                    print('Created: ', fullName)
        if(val!=[]):tempDict[key]={"claimData":tempList, "multiplicity":multipl}
    return tempDict


def getSingleData(flatD):
    tempDict=dict()
    for key, val in flatD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        if(tools.isEqual('one',multipl)):
            tempDict[key] = {"claimData": cld, "multiplicity": multipl}
    return tempDict

def getMultiData(flatD):
    tempDict=dict()
    for key, val in flatD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        if(tools.isEqual('many',multipl)):
            tempDict[key] = {"claimData": cld, "multiplicity": multipl}
    return tempDict


def generateMultiExistence(inputD):
    negativeCount = 0
    outDict=dict()
    #Take a class
    for key, val in inputD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        # Take an element of a class
        for c1 in cld:
            matchBase=False
            matchScope=False
            matchOldNewSource=False
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            scp1 = c1.get('scope')
            breakup1=re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN1)
            subnet1 = (breakup1[0]).replace('<<Network>>','')
            #Check if TRUE already created for a source
            if((key,src1,fullN1.lower(),True) not in checkSet):
                confList.append({'class':clss1,'fullName':fullN1,'id':id1,'label':True,'source':src1})
                checkSet.add((key,src1,fullN1.lower(),True))
            for c2 in cld:
                src2 = c2.get('source')
                id2=c2.get('id')
                scope2 = c2.get('scope')
                if(tools.isNotEqual(src1,src2)): #and src2 not in visitedS):
                    matchOldNewSource = tools.matchDataSources(src1, src2)
                    #if(matchOldNewSource):print('ons',matchOldNewSource, src1, src2)
                    if(len(breakup1) != 1):
                        match = getMatch(src2,fullN1,cld)
                        if(match==False):
                            matchScope = getMatchScope(src2, scope2, fullN1, cld) #Check for the other source for the same subnet or ip
                            #matchBase = getMatchBase(src2, base1, cld) #Check for other sources for same class/base
                            if(matchOldNewSource and matchScope and (key, src2, fullN1.lower(),False) not in checkSet): # Do not need to add matchBase or matchClass as the claim list is already limited to a particular identity
                                confList.append({'class': clss1, 'fullName': fullN1, 'id': 'generated', 'label': False, 'source': src2})
                                checkSet.add((key, src2, fullN1.lower(),False))
                                print('Generated negative for: ', fullN1, ' ,source: ',src2)
                                negativeCount += 1
                    if(len(breakup1)==1 and (tools.isNotEqual(key,'Association')) and (tools.isNotEqual(key,'Property')) and tools.isEqual(scope2,'subnet')):
                        match = getMatch(src2, fullN1, cld)
                        if (matchOldNewSource and match == False and (key, src2, fullN1.lower(),False) not in checkSet):
                            confList.append({'class': clss1, 'fullName': fullN1, 'id': 'generated', 'label': False, 'source': src2})
                            checkSet.add((key, src2, fullN1.lower(),False))
                            print('Generated negative for: ', fullN1, ' ,source: ', src2)
                            negativeCount += 1
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    print('-------------------------------------------')
    print('Negative claims generated for NON-exclusive set:', negativeCount)
    return outDict

def generateSingleExistence(singleD):
    negativeCount=0
    outDict=dict()
    #Take a class
    for key, val in singleD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        # Take an element of a class
        for c1 in cld:
            visitedS=set()
            matchScope=False
            matchBase=False
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            scp1 = c1.get('scope')
            breakup1=re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN1)
            #subnet1 = (breakup1[0]).replace('<<Network>>','')
            if(len(breakup1)>1):
                base1=''.join(breakup1[0:-1])
            else:
                base1=breakup1[0]
            lastclass=re.findall(r"<<([a-zA-Z0-9\=]*)>>", breakup1[-1])[0]
            #Check if TRUE already created for a source
            #Check for other sources for same class
            #Generate a FALSE if same class and subnet/ip
            if((key,src1,fullN1.lower()) not in checkSet):
                confList.append({'class':clss1,'fullName':fullN1,'id':id1,'label':lbl1,'source':src1, 'existence':exist1})
                checkSet.add((key,src1,fullN1.lower()))
            for c2 in cld:
                src2 = c2.get('source')
                id2 = c2.get('id')
                exist2 = c2.get('existence')
                fullN2=c2.get('fullName')
                if(tools.isNotEqual(src1,src2)): #and src2 not in visitedS):
                    #visitedS.add(src2)
                    scope2=c2.get('scope')
                    match = getMatch(src2,fullN1,cld)
                    if(match==False):
                        matchOldNewSource = tools.matchDataSources(src1, src2)
                        matchScope = getMatchScope(src2, scope2, fullN1, cld) #Check for the other source for the same subnet or ip
                        matchBase = getMatchBase(src2, base1, cld) #Check for other sources for same class/base
                        newfN = str(base1) + '<<' + str(lastclass) + '>>' + 'False'
                        if(matchBase==False and matchScope and matchOldNewSource and (key, src2, newfN.lower()) not in checkSet):
                            confList.append({'class': clss1, 'fullName': newfN, 'id': 'generated', 'label': False, 'source': src2, 'existence':None})
                            checkSet.add((key, src2, newfN.lower()))
                            print('Generated negative for: ', newfN, ' ,source: ', src2)
                            negativeCount+=1
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    print('Negative claims generated for exclusive set:', negativeCount)
    return outDict

def getSingleConflicting(singleD):
    outDict=dict()
    for key, val in singleD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        for c1 in cld:
            counter=0
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            scope1=c1.get('scope')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            basis1 = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN1)[0:-1])
            for c2 in cld:
                lbl2 = c2.get('label')
                fullN2 = c2.get('fullName')
                basis2 = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN2)[0:-1])
                if(tools.isNotEqual(lbl2, lbl1) and tools.isEqual(basis1,basis2)):
                    counter=counter + 1
            #print(counter)
            if(counter>=1 and (fullN1.lower(),str(lbl1).lower(),src1) not in checkSet):
                confList.append({"fullName":fullN1, "class":clss1,"existence":exist1, "id":id1,"source":src1, "label":lbl1})
                checkSet.add((fullN1.lower(),str(lbl1).lower(),src1))
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    return outDict


def getSingleNonConflicting(singleD):
    outDict=dict()
    for key, val in singleD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        for c1 in cld:
            counter=0
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            scope1=c1.get('scope')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            basis1 = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN1)[0:-1]).strip()
            for c2 in cld:
                lbl2 = c2.get('label')
                fullN2 = c2.get('fullName')
                basis2 = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN2)[0:-1]).strip()
                if(tools.isNotEqual(lbl1, lbl2) and tools.isEqual(basis1,basis2)):
                    counter=counter + 1
            if(counter==0 and (fullN1.lower(),str(lbl1).lower(),src1) not in checkSet):
                confList.append({"fullName":fullN1, "class":clss1,"existence":exist1, "id":id1,"source":src1, "label":lbl1})
                checkSet.add((fullN1.lower(),str(lbl1).lower(),src1))
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    return outDict

def getMultiConflicting(multiD):
    outDict=dict()
    for key, val in multiD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        for c1 in cld:
            counter=0
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            for c2 in cld:
                    lbl2 = c2.get('label')
                    fullN2 = c2.get('fullName')
                    if(tools.isNotEqual(lbl2, lbl1) and tools.isEqual(fullN1,fullN2)):
                        counter=counter + 1
            if(counter>=1 and (fullN1.lower(),str(lbl1).lower(),src1) not in checkSet):
                confList.append({"fullName":fullN1, "class":clss1,"existence":exist1, "id":id1,"source":src1, "label":lbl1})
                checkSet.add((fullN1.lower(),str(lbl1).lower(),src1))
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    return outDict


def getMultiNonConflicting(multiD):
    outDict=dict()
    for key, val in multiD.items():
        cld=val.get('claimData')
        multipl=val.get('multiplicity')
        confList=[]
        checkSet=set()
        for c1 in cld:
            counter=0
            lbl1 = c1.get('label')
            exist1=c1.get('existence')
            id1=c1.get('id')
            clss1=c1.get('class')
            fullN1=c1.get('fullName')
            src1 = c1.get('source')
            #basis1 = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN1)[0:-1])
            for c2 in cld:
                lbl2 = c2.get('label')
                fullN2 = c2.get('fullName')
                if(tools.isNotEqual(lbl2, lbl1) and tools.isEqual(fullN1,fullN2)):
                    counter=counter + 1
            if(counter==0 and (fullN1.lower(),str(lbl1).lower(),src1) not in checkSet):
                confList.append({"fullName":fullN1, "class":clss1,"existence":exist1, "id":id1,"source":src1, "label":lbl1})
                checkSet.add((fullN1.lower(),str(lbl1).lower(),src1))
        outDict[key] = {"claimData": confList, "multiplicity": multipl}
    return outDict
#getModelElements(clss, coll, con)
#getPreviousModelElemWBoundary(sourceID, previousClass, previousType, direction, boundary, collection,con)



def getDataInbound(con):
    collection='collectedModel'
    modelDep = securiLangFullv2.returnDependencies()
    modelDepth = securiLangFullv2.getBiggestValue(modelDep)+1
    SequenceDict=dict()
    assocList = []
    propList = []
    for r in range(modelDepth):
        if(r>=1):
            iterationElements = securiLangFullv2.getValueWithIndex(r, modelDep)
            for it in iterationElements:
                if(len(it)==5):
                    tempEls=get5modelElements(it[0], it[1], it[2], it[3], it[4], collection, con)
                elif(len(it)==4):
                    tempEls =get4modelElements(it[0], it[1], it[2], it[3], collection,con)
                elif(len(it)==3):
                    tempEls =get3modelElements(it[0], it[1], it[2], collection,con)
                elif(len(it)==2):
                    tempEls =get2modelElements(it[0], it[1], collection,con)
                elif(len(it)==1):
                    tempEls=getmodelElements(it[0], collection,con)
                procsList=[]
                if(len(tempEls)>0):
                    for te in tempEls:
                        tempList=[]
                        assocTempList=[]
                        propTempList=[]
                        for t in te:
                            if(isinstance(t, dict)):
                                label=t.get('label')
                                idd=t.get('_id')
                                clss=t.get('class')
                                exist=t.get('existence')
                                source=getSourceFromCollected(idd,'20',collection, con)
                                tempList.append({"id":idd,"class":clss,"label":label,'source':source,"existence":exist})
                            elif((isinstance(t, str))):
                                tempList.append({"type": t, "class": 'Association', 'target':te[te.index(t)+1].get('class')})
                        # Add last association
                        lastAssocL=getLastAssoc(idd, clss, modelDep,con)
                        #if(len(lastAssocL)>0):print(clss,lastAssocL)
                        if(len(lastAssocL)>0):
                            for la in lastAssocL:
                                lcls=la.get('class')
                                ltc=la.get('targetClass')
                                ltid=la.get('targetID')
                                ltv=la.get('targetValue')
                                ltp=la.get('type')
                                #tempList.append({"type": ltp, "class":'AssociationLast', 'targetID':ltid,'target':ltc,'targetValue':ltv })
                                assocTempList=copy.deepcopy(tempList)
                                assocTempList.append({"type": ltp, "class":'AssociationLast', 'targetID':ltid,'target':ltc,'targetValue':ltv })
                        # Add properties
                        procsList.append(tempList)
                        if(len(assocTempList)>0):assocList.append(assocTempList)
                        if(len(propTempList)>0):propList.append(propTempList)
                if (len(procsList) > 0):SequenceDict[it]=procsList
            if (len(assocList) > 0):SequenceDict[('Association',)] = assocList
            if (len(propList) > 0):SequenceDict[('Property',)] = propList
    return SequenceDict


def mergeSingleMultiForLCA(singleData, multiData):
    newDataList = []
    newerDataList = []
    if(singleData != None):
        for md in singleData.values():
            claims=md.get("claimData")
            for c in claims:
                source = c.get("source")
                clss = c.get("class")
                label = c.get("label")
                fulN = c.get("fullName")
                exist = c.get("existence")
                idn= c.get('id')
                assert ((len(re.findall(r"(<<[a-zA-Z0-9\=]*>>)", fulN))) >= 2)
                newEntity = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fulN)[0:-1])
                newnewEntity=newEntity+'||'+clss
                #newAttribute = "".join(re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fulN)[0:])
                newDataList.append([newnewEntity, label, source, exist, idn])
    if(multiData != None):
        for md in multiData.values():
            claims=md.get("claimData")
            for c in claims:
                source = c.get("source")
                idn = c.get('id')
                clss = c.get("class")
                fulE = c.get("fullName")
                exist = c.get("existence")
                attribute = c.get("label")
                newDataList.append([fulE, attribute, source, exist, idn])
   #Recalculate credibility values
    for nd in newDataList:
        exist=normalizeCredibility(newDataList, nd[0],nd[2],nd[3]) #if exist == None => exist is assumed 1
        newerDataList.append([nd[0], nd[1], nd[2], exist, None, nd[4]]) #NOT REMOVED FOR LTM
    return newerDataList

def transformTruthfToFlat(truthResult):
    output = []
    maxValues = truthResult.get("maxValues")
    for m in maxValues:
        if isinstance((m.get("value")),bool):
            if m.get("value")== True:
                fe = m.get("entity")
                fe = fe.split('||')[0]
                credibility = m.get("Cv")
                clss = re.findall(r"<<([a-zA-Z0-9\=]*)>>", fe)[-1]
                #assert credibility <= 1
                output.append({"calculated":True, "class":clss, "credibility":credibility, "value":fe})
        else:
            fe = m.get("value")
            credibility = m.get("Cv")
            clss = re.findall(r"<<([a-zA-Z0-9\=]*)>>", fe)[-1]
            #assert credibility <= 1
            output.append({"calculated": True, "class": clss, "credibility": credibility, "value": fe})
    return output


def groupIDvalues(inData):
    outDict=dict()
    newClaims = dict()
    for key, claims in inData.items():
        if('Property' not in key and 'Association' not in key):
            for claim1 in claims:
                claimLen=len(claim1)
                i1 = 0
                newClaim = []
                while i1 < len(claim1):
                    cclass1 = claim1[i1].get('class')
                    if (tools.isNotEqual(cclass1, 'Association')):
                        cexistence1 = claim1[i1].get('existence')
                        cid1 = claim1[i1].get('id')
                        clabel1 = claim1[i1].get('label')
                        #csource1 = claim1[i1].get('source')
                        newClaim.append({"class": cclass1, "label": clabel1,
                             "existence": cexistence1})
                    if (tools.isEqual(cclass1, 'Association')):
                        ctype1 = claim1[i1].get('type')
                        ctarget1 = claim1[i1].get('target')
                        newClaim.append(
                            {"type": ctype1, "class": cclass1, 'target': ctarget1})
                    i1+=1
                newClaims[cid1]=newClaim
    for g,f in newClaims.items():
        group=reverseGroupDict(newClaims, f)
        if(isinstance(group, list) and group !=[]):
            group=tuple(group)
            hashedV=tools.hashATuple(group)
        outDict[hashedV]=group
        #print('Added: ','new key:',hashedV,'old keys:',group)
    return outDict


def checkHashwithID(idIN,inDict):
    for k, v in inDict.items():
        if(idIN in v):
            return k

def mergeAll(singleNonConf, multiNonConf,truthD):
    outputDict=dict()
    if(truthD!=None and len(truthD)!=0):
        maxVal=truthD.get('maxValues')
        for mv in maxVal:
            newKeyList=[]
            newKey=None
            tvalue=mv.get('value')
            if(tools.isNotEqual(tvalue,'False') and tvalue!=False):
                tcv = mv.get('Cv')
                tentity = mv.get('entity')
                tid=mv.get('id')
                #assert float(tcv) <=1
                breakupEntity=re.findall(r"<<[a-zA-Z0-9\=]*>>([^<]*)", tentity)
                if(len(breakupEntity)>1):
                    checkType=re.findall(r"\|\|(\w+)", breakupEntity[-1])
                    if(len(checkType)>0): #Means single type
                        clss=re.findall(r"\|\|(\w+)", breakupEntity[-1])[0]
                        newEntity=tentity.split('||')[0]+'<<'+str(clss)+'>>'+str(tvalue)
                        newKeyList=re.findall(r"<<([a-zA-Z0-9\=]*)>>", newEntity)
                        newKey=tuple(newKeyList)
                        if(newKey not in outputDict):
                            outputDict[newKey]={}
                            outputDict[newKey]['claimData']=[]
                            outputDict[newKey]['claimData'].append(
                                {"fullName": newEntity, "class": clss, "existence": tcv, "id": tid, "label": tvalue})
                        else:
                            outputDict[newKey]['claimData'].append({"fullName":newEntity, "class":clss,"existence":tcv, "id":tid, "label":tvalue})
                    else: #Means multi type
                        newKeyList=re.findall(r"<<([a-zA-Z0-9\=]*)>>", tentity)
                        clss=newKeyList[-1]
                        newKey=tuple(newKeyList)
                        if (newKey not in outputDict):
                            outputDict[newKey] = {}
                            outputDict[newKey]['claimData'] = []
                            outputDict[newKey]['claimData'].append(
                                {"fullName": tentity, "class": clss, "existence": tcv, "id": tid, "label": tvalue})
                        else:
                            outputDict[newKey]['claimData'].append({"fullName":tentity, "class":clss,"existence":tcv, "id":tid, "label":tvalue})
                elif (len(breakupEntity) == 1): #Means can be still both
                    checkType = re.findall(r"\|\|(\w+)", breakupEntity[-1])
                    if (len(checkType) > 0):
                        clss=re.findall(r"\|\|(\w+)", breakupEntity[-1])[0]
                        newEntity=tentity.split('||')[0]+'<<'+str(clss)+'>>'+str(tvalue)
                        newKeyList=re.findall(r"<<([a-zA-Z0-9\=]*)>>", newEntity)
                        newKey=tuple(newKeyList)
                        if(newKey not in outputDict):
                            outputDict[newKey]={}
                            outputDict[newKey]['claimData']=[]
                            outputDict[newKey]['claimData'].append(
                                {"fullName": newEntity, "class": clss, "existence": tcv, "id": tid, "label": tvalue})
                        else:
                            outputDict[newKey]['claimData'].append({"fullName":newEntity, "class":clss,"existence":tcv, "id":tid, "label":tvalue})
                    else:
                        newKey = re.findall(r"<<([a-zA-Z0-9\=]*)>>", tentity)
                        clss = newKey[0]
                        newKey = (clss,)
                        if (newKey not in outputDict):
                            outputDict[newKey] = {}
                            outputDict[newKey]['claimData'] = []
                            outputDict[newKey]['claimData'].append(
                            {"fullName": tentity, "class": clss, "existence": tcv, "id": tid, "label": tvalue})
                        else:
                            outputDict[newKey]['claimData'].append(
                            {"fullName": tentity, "class": clss, "existence": tcv, "id": tid, "label": tvalue})

    if(singleNonConf!=None and len(singleNonConf)!=0):
        for snk,snv in singleNonConf.items():
            if (snv != []):
                newie = snv.get('claimData')
                if(snk in outputDict):
                    oldie=outputDict.get(snk).get('claimData')
                    outputDict[snk]['claimData'] = oldie + newie

                else:
                    outputDict[snk]={}
                    outputDict[snk]['claimData'] = newie

    if(multiNonConf!=None and len(multiNonConf)!=0):
        for mnk, mnv in multiNonConf.items():
            if (mnv != []):
                newie = mnv.get('claimData')
                if (mnk in outputDict):
                    oldie = outputDict.get(mnk).get('claimData')
                    outputDict[mnk]['claimData'] = oldie + newie

                else:
                    outputDict[mnk] = {}
                    outputDict[mnk]['claimData'] = newie
    return outputDict

def analyzed2DB(mergedD, hashedGroups, client):
    collection='securiCADModel'
    collectionAssoc='securiCADModelAssoc'
    dateStr=datetime.date.today().strftime("%d/%m/%Y")
    #dateStr='15/06/2015'
    checkStart = client[collection].fetchByExample({'type': "modelData", "label": "securiCAD"}, batchSize=100)
    if (len(checkStart) == 0):
        startKey = storeMetaelementArango(collection, 'modelData', 'securiCAD', client)
    else:
        startKey = checkStart[0]._id
    checkDate = client[collection].fetchByExample({'type': "timepoint", "label": dateStr}, batchSize=100)
    if (len(checkDate) == 0):
        dateKey = storeMetaelementArango(collection, 'timepoint', dateStr, client)
        storeAssocArango(collectionAssoc, startKey, dateKey, 'fromTo', client)
    else:
        print('Data already imported! Doing nothing.')
        return None
    storedKeys=dict()
    for dkey in sorted(mergedD, key=len): #done in sorted manner for connection purposes
        if('Association' not in dkey and 'Property' not in dkey):
            vals=mergedD.get(dkey)
            if(len(vals)>0):
                clmD=vals.get('claimData')
                for c in clmD:
                    value=None
                    fN=c.get('fullName')
                    idList=c.get('id')
                    clss=c.get('class')
                    if(tools.isEqual(clss,'Dataflow')):
                        fN=fN.split('=')[0]
                    exist=c.get('existence')
                    newIdHash=checkHashwithID(idList[-1],hashedGroups)
                    label=c.get('label')
                    if(tools.isEqual(label,'True') or label==True):
                        value = re.findall(r"<<\w+>>([^<]*)", fN)[-1]
                    else:
                        value=label
                    prevKey=None
                    if(newIdHash not in storedKeys):
                        if(len(dkey)==1):
                            elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                            storeAssocArango(collectionAssoc, dateKey, elementID, 'fromTo', client)
                            storedKeys[newIdHash]=elementID
                        elif(len(dkey)>1):
                            # check if anything to connect to, if not do not create
                            prevIdHash = checkHashwithID(idList[-2], hashedGroups)
                            prevKey=storedKeys.get(prevIdHash)
                            if(prevKey!=None):
                                elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                                storeAssocArango(collectionAssoc, prevKey, elementID, 'fromTo', client)
                                storedKeys[newIdHash]=elementID
    #Connect properties and associations
    storedAssoc=set()
    for ka, va in mergedD.items():
        if('Association' in ka):
            if (len(va) > 0):
                clmD = va.get('claimData')
                for c in clmD:
                    fN=c.get('fullName')
                    idList=c.get('id')
                    clss=c.get('class')
                    exist=c.get('existence')
                    newIdHash=checkHashwithID(idList[-2],hashedGroups)
                    label=c.get('label')
                    #nextHash = re.findall(r"<<\w+>>([^<]*)", fN)[-1]
                    nextHash = checkHashwithID(idList[-1], hashedGroups)
                    conType=label
                    #prevIdHash = checkHashwithID(idList[-2], hashedGroups)
                    prevKey=storedKeys.get(newIdHash)
                    nextKey=storedKeys.get(nextHash)
                    if(prevKey!=None and nextKey!=None and (prevKey, nextKey) not in storedAssoc):
                        #elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                        storeAssocArango(collectionAssoc, prevKey, nextKey, conType, client)
                        storedAssoc.add((prevKey,nextKey))


#data=getDataInbound(createConArango('claimOmania'))

#pprint(groupIDvalues(data))

#pprint(checkHashwithID('collectedModel/297971',groupIDvalues(data)))


#pprint(data)
#fdata= flattenConData(getDataInbound(createConArango('claimOmania')),createConArango('claimOmania'))
#pprint(fdata)
#print(getmodelElements('Network', createConArango('claimOmania'))[0][0])
#hashedGroups= groupIDvalues(data)
#pprint(hashedGroups)

#multiDT=(getMultiData(fdata))
#pprint(multiDT)

#single=(getSingleData(fdata))
#pprint(single)
#print('####################')
#singleED=generateSingleExistence(single)
#pprint(singleED)
#pprint(getNonConflicting(fdata))
#multiED=(generateMultiExistence(multiDT))
#pprint(multiED)


#cMD=getMultiConflicting(multiED)
#nonCMD=getMultiNonConflicting(multiED)

#cSD=getSingleConflicting(singleED)
#nonCSD=getSingleNonConflicting(singleED)
#pprint(cMD)
#pprint(nonCMD)
#print('#####')
#pprint(nonCSD)
#pprint(cSD)
#mergedConflictSet=mergeSingleMultiForLCA(cSD,cMD)
#pprint(mergedConflictSet)
#print('Starting truth analysis')
#pprint(mergedConflictSet)
#truthData=LCA3_quick.run(mergedConflictSet)
#pprint(truthData)

#mergeAllD = mergeAll(nonCSD, nonCMD, truthData)
#pprint(mergeAllD)
#analyzed2DB(mergeAllD, hashedGroups, createConArango('claimOmania'))

#result=transformTruthfToFlat(truthData)
#pprint(mergedSet)


#pprint(multiDT)

""""""
#pprint(nonCSD)
#truthData2DB(truthData, createConArango('claimOmania'))
###########################################
###Troubleshooting
###########################################

def countSortConflictsGenerated(mergedConflicts):
    checkset=set()
    newMergedSet=[]
    output=dict()
    for m1 in mergedConflicts:
        count=0
        idrepeat=0
        for m2 in mergedConflicts:
            if(tools.isEqual(m1[0],m2[0]) and tools.isEqual(m1[1],m2[1])): #count if entity, value equal?
                count+=1
            if(tools.isEqual(m1[5],m2[5]) and m1[5]!='generated'): #id?
                idrepeat+=1
        if(idrepeat>1):print('IDrepeat',idrepeat,m1[5])
        newMergedSet.append([m1[0],m1[1],m1[2],m1[3],m1[4], count]) #dropping id nrs
    #newMergedSet.sort(key=lambda x: x[6])
    print(newMergedSet)
    for nm1 in newMergedSet:
        templist=[]
        tempmaxval=0
        tempminval=len(newMergedSet)
        sum=0
        #sourcesum=0
        for nm2 in newMergedSet: #0.entity fN 1.value 2. data source 3. DS existance 4. prior trust value of DS 5. equal count
            if(tools.isEqual(nm1[0],nm2[0])):
                templist.append([nm2[1], nm2[2],nm2[3],nm2[4],nm2[5]])
                sum += nm2[5]
                if(tempmaxval<nm2[5]):
                    tempmaxval=nm2[5]
                    biggest = nm2[1]
                if(tempminval>nm2[5]):
                    tempminval=nm2[5]
                #if(tools.isEqual(nm1[2],nm2[2])):#source
                    #sourcesum+=nm2[3]
        #if(sourcesum!=1):print('WARNING',sourcesum,nm2[0])
        size=len(templist)
        assert size > 1
        if(size == 2 and (tempmaxval != tempminval)):
            print('F*cked up')
            return None
        if ((sum / size) == 1):
            biggest = 'NA'
        entity=nm1[0]
        if(entity.lower() not in checkset):
            output[entity]={'setSize':float(size),'maximumCount':float(tempmaxval), 'maximumLabel':biggest, 'minimumCount':float(tempminval), 'claims':templist}
            checkset.add(entity.lower())
    return output

def countSortConflictsOriginal(flatData):
    output=dict()
    sourceCount=dict()
    for key, val in flatData.items():
        claimD=val.get('claimData')
        multip=val.get('multiplicity')
        newClaims=[]
        if(tools.isEqual(multip, 'one')):
            for c1 in claimD:
                fullN=c1.get('fullName')
                lbl=c1.get('label')
                src=c1.get('source')
                clss = c1.get('class')
                exist=c1.get('existence')
                id=c1.get('id')
                breakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN)
                if(len(breakup)<2):
                    base=breakup[0]
                    conflicts=False
                else:
                    base=''.join(breakup[0:-1])
                    conflicts=True
                confCount=0
                matchCount=0
                sameSource=dict()
                for c2 in claimD:
                    src2=c2.get('source')
                    clss2 = c2.get('class')
                    fullN2 = c2.get('fullName')
                    lbl2=c2.get('label')
                    #if(tools.isNotEqual(src,src2)):
                    if(tools.isEqual(clss,clss2)):
                            breakup2 = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN2)
                            if(len(breakup2)<2):
                                base2=breakup2[0]
                            else:
                                base2=''.join(breakup2[0:-1])
                            #print(fullN,base,base2)
                            if(tools.isEqual(base,base2)):
                                if (tools.isEqual(src, src2)):
                                    if (src in sameSource):
                                        scount = sameSource[src]
                                        scount += 1
                                        sameSource[src] = scount
                                    else:
                                        sameSource[src] = 1
                                if(tools.isEqual(lbl,lbl2)): #match
                                    matchCount+=1
                                    if (src not in sourceCount):
                                        sourceCount[src] = dict()
                                        sourceCount[src]['claimMatch']=1
                                    elif('claimMatch' not in sourceCount[src]):
                                        sourceCount[src]['claimMatch'] = 1
                                    else:
                                        count = sourceCount[src]['claimMatch']
                                        count += 1
                                        sourceCount[src]['claimMatch'] = count
                                elif(conflicts): #conflicting
                                    confCount += 1
                                    if (src not in sourceCount):
                                        sourceCount[src] = dict()
                                        sourceCount[src]['claimConflict']=1
                                    elif('claimConflict' not in sourceCount[src]):
                                        sourceCount[src]['claimConflict'] = 1
                                    else:
                                        count = sourceCount[src]['claimConflict']
                                        count += 1
                                        sourceCount[src]['claimConflict'] = count
                sameSourceV=sameSource.get(src)
                newClaims.append({"fullName":fullN, "class":clss,"existence":exist, "source":src,"label":lbl,'conflictCount':confCount,'maxUnique':matchCount, 'id':id, 'maxSameSourceClaims':sameSourceV})
            output[key]={'claims':newClaims, 'multiplicity':multip}
    return output, sourceCount

#origdata, sourceCount=countSortConflictsOriginal(fdata)

def prepareOrigDataframe(origD):
    output = dict()
    for key, val in origD.items():
        #if ('Association' not in key or 'Property' in key):
            claimD=val.get('claims')
            multip=val.get('multiplicity')
            for v1 in claimD:
                tempList = []
                fullN = v1.get('fullName')
                breakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN)
                lastbreakup= re.findall(r"(<<[a-zA-Z0-9\=]*>>)[^<]*", breakup[-1])[0]
                newfullN=''.join(breakup[0:-1])+str(lastbreakup)
                #print(newfullN, lastbreakup,breakup,fullN)

                if (newfullN not in output):
                    for v2 in claimD:
                        fullN2 = v2.get('fullName')
                        breakup2 = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN2)
                        lastbreakup2 = re.findall(r"(<<[a-zA-Z0-9\=]*>>)[^<]*", breakup2[-1])[0]
                        newfullN2 = ''.join(breakup2[0:-1]) + str(lastbreakup2)
                        lbl2 = v2.get('label')
                        src2 = v2.get('source')
                        conflicC = v2.get('conflictCount')
                        matchC = v2.get('maxUnique')
                        exist2 = v2.get('existence')
                        maxSSC = v2.get('maxSameSourceClaims')
                        if (tools.isEqual(newfullN, newfullN2)):
                            tempList.append({'source': src2, 'label': lbl2, 'existence': exist2, 'conflictCount': conflicC,
                                             'maxUnique': matchC, 'maxSameSourceClaims':maxSSC})
                    output[newfullN] = tempList
    newClaim = dict()
    newList=[]
    for ok, ov in output.items():

        for o1 in ov:
            olbl1=o1.get('label')
            temp=0
            size = len(ov)
            sumConf=0
            sumMatch=0
            bigConf=0
            bigMatch=0
            maxSame=0
            tempVal=None
            for o2 in ov:
                olbl2 =o2.get('label')
                osrc2 =o2.get('source')
                omatchC2=o2.get('maxUnique')
                oconfC2=o2.get('conflictCount')
                maxSSC = o2.get('maxSameSourceClaims')
                if(bigMatch<omatchC2):
                    bigMatch=omatchC2
                    tempVal=olbl2
                if(bigConf<oconfC2):
                    bigConf=oconfC2
                sumConf+=oconfC2
                sumMatch+=omatchC2
                if(maxSame<maxSSC):
                    maxSame=maxSSC
            if((size/sumMatch)==1):tempVal='NA'
        newList.append({'Claim':ok,'biggestConflicts':bigConf, 'biggestUnique': bigMatch ,'bestValue':tempVal, 'setSize':size, 'claims':ov, 'maxSameSourceClaims': maxSame})
        #newClaim[ok]=newList
    return newList


#origdata, sourceCount=countSortConflictsOriginal(fdata)
#pprint(sourceCount)
#pprint(origdata)
#pprint(prepareOrigDataframe(origdata))

#(column='biggestConflicts', 'biggestUnique','bestValue', 'claims', 'setSize')
#oreo=prepareOrigDataframe(origdata)
#originalConflicts = pandas.DataFrame(oreo)
#originalConflicts=originalConflicts.set_index('Claim')
#originalConflictsD = pandas.DataFrame.from_records(oreo)
#pprint(originalConflictsD)
#pprint(originalConflicts.describe())
#originalConflicts=originalConflicts.sort_values('setSize')
#originalConflicts=originalConflicts.rename(columns={'setSize': 'Subset_Size', 'biggestConflicts': 'Biggest_Conflicts','biggestUnique':'Biggest_Single_Repeat','maxSameSourceClaims':'Max_Same_Source_Claims'})
#originalConflicts=originalConflicts[originalConflicts.Subset_Size > 1]
#originalConflicts=originalConflicts[originalConflicts.Biggest_Conflicts > 0]
#originalConflicts.set_index('index')
#pprint(originalConflicts)
#orgPlot=originalConflicts.plot(x=originalConflicts.index, y=['Subset_Size','Biggest_Conflicts','Biggest_Single_Repeat', 'Max_Same_Source_Claims'], kind='bar', title='securiCAD claims')
#orgPlot.axes.get_xaxis().set_visible(False)
#fig_org1 = orgPlot.get_figure()
#fig_org1.savefig("secCAD1-org-conf.png", dpi=300)
#originalConflicts.to_csv(r'c:\temp\orgSecConfl.txt', sep=';')

"""

"""

#Counting unique matches, excluding generated values
def countDataSourcesMatching(mCF):
    sourceCount=dict()
    for k, m1 in mCF.items():
            cl=m1.get('claims')
            for c1 in cl:
                source1=c1[1]
                label1=c1[0]
                for c2 in cl:
                    source2 = c2[1]
                    label2= c2[0]
                    if(tools.isNotEqual(source1,source2)):
                        if(tools.isEqual(label1,label2) and tools.isNotEqual(label1,False) and tools.isNotEqual(label1,'false')):
                            if(c1[1] not in sourceCount):
                                sourceCount[c1[1]]=1
                            else:
                                count=sourceCount[c1[1]]
                                count+=1
                                sourceCount[c1[1]]=count
    return sourceCount


def countDataSourcesFalse(mCF):
    sourceCount=dict()
    for k, m1 in mCF.items():
            cl=m1.get('claims')
            for c1 in cl:
                label1=c1[0]
                if((tools.isEqual(label1,False) or tools.isEqual(label1,'false'))):
                            if(c1[1] not in sourceCount):
                                sourceCount[c1[1]]=1
                            else:
                                count=sourceCount[c1[1]]
                                count+=1
                                sourceCount[c1[1]]=count
    return sourceCount

def countDataSourcesNotFalse(mCF):
    sourceCount=dict()
    for k, m1 in mCF.items():
            cl=m1.get('claims')
            for c1 in cl:
                label1=c1[0]
                if((tools.isNotEqual(label1,False) and tools.isNotEqual(label1,'false'))):
                            if(c1[1] not in sourceCount):
                                sourceCount[c1[1]]=1
                            else:
                                count=sourceCount[c1[1]]
                                count+=1
                                sourceCount[c1[1]]=count
    return sourceCount









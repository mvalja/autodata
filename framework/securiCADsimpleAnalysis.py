#TODO:
#1. Get flat single data (including associations and properties)
#Use newProcessLCA flatData function
#2. Divide into subsets based on entity full value
#Input: single flat Output: entity based single flat with groups
#3. Find most frequent values for all
#Input: entity based single flat with groups Output: groups with most frequent values on higher level
#4. Find data source with most frequent postive outcomes
#Input: Previous output Output: a separate set of sources with frequency values
#5. Assign rest of the values using a randomization method - build pool, assign ids, then pick one
#Input 4 and 5 outputs Output: new set that will be written to the DB
"""
import random
foo = ['battery', 'correct', 'horse', 'staple']
secure_random = random.SystemRandom()
print(secure_random.choice(foo))
"""


#import newPreprocessLCA5_forImport as secPrep
import tools
#from arangoTools import *
import re
import datetime
import random

#1. Get flat single data (including associations and properties)
#Use newProcessLCA flatData function





#2. Divide into subsets based on entity full value
#Input: single flat Output: entity based single flat with groups

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



#3. Find most frequent values for all
#Input: entity based single flat with groups Output: groups with most frequent values on higher level

def getHighestScoringSource(sourceL, sourceCount):
    srcMetric=None
    newDict=dict()
    if(sourceL!=None and len(sourceL)>1):
        for src in sourceL:
            srcD=sourceCount.get(src)
            clmM =srcD.get('claimMatch')
            clmC =srcD.get('claimConflict')
            if(clmM==None):clmM=0
            if (clmC == None): clmC = 0
            srcMetric=clmM/clmC
            newDict[src]=srcMetric
        outputMax=max(newDict, key=newDict.get)
        outputMin=min(newDict, key=newDict.get)
        if(tools.isNotEqual(outputMax,outputMin)): #Checking that there is difference in values
            return outputMax

def getSourceScores(sourceCount):
    srcMetric=None
    newDict=dict()
    for k, v in sourceCount.items():
        clmM = v.get('claimMatch')
        clmC = v.get('claimConflict')
        if(clmM==None):clmM=0
        if (clmC == None): clmC = 0
        srcMetric=clmM/clmC
        newDict[k]=srcMetric
    return newDict


def groupBasedOnEntity(origD):
    output = dict()
    for key, val in origD.items():
        #if ('Association' not in key or 'Property' in key):
            claimD=val.get('claims')
            for v1 in claimD:
                tempList = []
                fullN = v1.get('fullName')
                breakup = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN)
                lastbreakup= re.findall(r"(<<[a-zA-Z0-9\=]*>>)[^<]*", breakup[-1])[0]
                newfullN=''.join(breakup[0:-1])+str(lastbreakup)
                if (newfullN not in output):
                    for v2 in claimD:
                        fullN2 = v2.get('fullName')
                        breakup2 = re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", fullN2)
                        lastbreakup2 = re.findall(r"(<<[a-zA-Z0-9\=]*>>)[^<]*", breakup2[-1])[0]
                        newfullN2 = ''.join(breakup2[0:-1]) + str(lastbreakup2)
                        lbl2 = v2.get('label')
                        id2 = v2.get('id')
                        src2 = v2.get('source')
                        conflicC = v2.get('conflictCount')
                        matchC = v2.get('maxUnique')
                        exist2 = v2.get('existence')
                        maxSSC = v2.get('maxSameSourceClaims')
                        if (tools.isEqual(newfullN, newfullN2)):
                            tempList.append({'source': src2, 'label': lbl2, 'existence': exist2, 'conflictCount': conflicC,
                                             'maxUnique': matchC, 'maxSameSourceClaims':maxSSC, 'id':id2})
                    output[newfullN] = tempList
    newList=dict()
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
        newList[ok]={'bestValue':tempVal,  'claims':ov}
        #newClaim[ok]=newList
    return newList

#3. Find most frequent values for all
#Input: entity based single flat with groups Output: groups with most frequent values on higher level


def getEntityBestValue(oreo, sourceCount): #This function needs to be optimized for better perfomance
    newDict=dict()
    for key, val in oreo.items():
        bestValue = val.get('bestValue')
        claimD=val.get('claims')
        if(tools.isNotEqual(bestValue,'NA')):
            for c in claimD:
                lbl=c.get('label')
                if(tools.isEqual(lbl,bestValue)):
                    src=c.get('source')
                    ex=c.get('existence')
                    id=c.get('id')
                    newDict[key]={'source':src,'existence':ex,'label':lbl,'id':id,'reason':'bestValue'}
        if (tools.isEqual(bestValue, 'NA')):
            srcS=set()
            for c in claimD:
                src=c.get('source')
                srcS.add(src)
            trustedSource=getHighestScoringSource(srcS, sourceCount)
            tempLL=[]
            if(trustedSource!=None):
                tempD=dict()
                for c in claimD:
                    src = c.get('source')
                    if(tools.isEqual(src,trustedSource)):
                       ex = c.get('existence')
                       lbl = c.get('label')
                       if(ex==None):ex=0
                       tempD[lbl]=ex
                #print(tempD)
                maxLbl = max(tempD, key=tempD.get)
                for c in claimD:
                    lbl = c.get('label')
                    if (tools.isEqual(lbl, maxLbl)):
                        src = c.get('source')
                        ex = c.get('existence')
                        id = c.get('id')
                        newDict[key] = {'source': src, 'existence': ex, 'label': lbl, 'id': id,'reason':'source'}
            else:
                for c in claimD:
                    lbl = c.get('label')
                    tempLL.append(lbl)
                secure_random = random.SystemRandom()
                randomV=secure_random.choice(tempLL)
                for c in claimD:
                    lbl = c.get('label')
                    if (tools.isEqual(lbl, randomV)):
                        src = c.get('source')
                        ex = c.get('existence')
                        id = c.get('id')
                        newDict[key] = {'source': src, 'existence': ex, 'label': lbl, 'id': id, 'reason':'random'}

    return newDict

def mergeAllAnalyzed(singleNonConf, multiNonConf, analyzed):
    outputDict=dict()
    if(analyzed!=None and len(analyzed)!=0):
        for ak, av in analyzed.items():
            aex=av.get('existence')
            aid=av.get('id')
            albl=av.get('label')
            breakupClasses =re.findall(r"<<([a-zA-Z0-9\=]*)>>", ak)
            breakupAll= re.findall(r"(<<[a-zA-Z0-9\=]*>>[^<]*)", ak)
            if(len(breakupClasses)>1):
                lastClass=breakupClasses[-1]
                if('AssociationLast' not in lastClass):
                    newKey = tuple(breakupClasses)
                    if (newKey not in outputDict):
                        outputDict[newKey] = {}
                        outputDict[newKey]['claimData'] = []
                        outputDict[newKey]['claimData'].append(
                            {"fullName": ak+albl, "class": lastClass, "existence": aex, "id": aid, "label": albl})
                    else:
                        outputDict[newKey]['claimData'].append(
                            {"fullName": ak+albl, "class": lastClass, "existence": aex, "id": aid, "label": albl})
                elif('AssociationLast' in lastClass):
                    newKey = ('Association',)
                    shortEntity=breakupAll[0:-2]
                    shortEntity=''.join(shortEntity)
                    if (newKey not in outputDict):
                        outputDict[newKey] = {}
                        outputDict[newKey]['claimData'] = []
                        outputDict[newKey]['claimData'].append(
                            {"fullName": shortEntity+'<<AssociationLast>>'+albl, "class": 'AssociationLast', "existence": aex, "id": aid, "label": albl})
                    else:
                        outputDict[newKey]['claimData'].append(
                            {"fullName": shortEntity+'<<AssociationLast>>'+albl, "class": 'AssociationLast', "existence": aex, "id": aid, "label": albl})
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


def saveAnalyzed2DB(mergedD, hashedGroups, client):
    collection = 'securiCADModelOriginal'
    collectionAssoc = 'securiCADModelOriginalAssoc'
    dateStr = datetime.date.today().strftime("%d/%m/%Y")
    # dateStr='15/06/2015'
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
    storedKeys = dict()
    for dkey in sorted(mergedD, key=len):  # done in sorted manner for connection purposes
        if ('Association' not in dkey and 'Property' not in dkey):
            vals = mergedD.get(dkey)
            if (len(vals) > 0):
                clmD = vals.get('claimData')
                for c in clmD:
                    value = None
                    fN = c.get('fullName')
                    idList = c.get('id')
                    clss = c.get('class')
                    if (tools.isEqual(clss, 'Dataflow')):
                        fN = fN.split('=')[0]
                    exist = c.get('existence')
                    newIdHash = secPrep.checkHashwithID(idList[-1], hashedGroups)
                    label = c.get('label')
                    if (tools.isEqual(label, 'True') or label == True):
                        value = re.findall(r"<<\w+>>([^<]*)", fN)[-1]
                    else:
                        value = label
                    prevKey = None
                    if (newIdHash not in storedKeys):
                        if (len(dkey) == 1):
                            elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                            storeAssocArango(collectionAssoc, dateKey, elementID, 'fromTo', client)
                            storedKeys[newIdHash] = elementID
                        elif (len(dkey) > 1):
                            # check if anything to connect to, if not do not create
                            prevIdHash = secPrep.checkHashwithID(idList[-2], hashedGroups)
                            prevKey = storedKeys.get(prevIdHash)
                            if (prevKey != None):
                                elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                                storeAssocArango(collectionAssoc, prevKey, elementID, 'fromTo', client)
                                storedKeys[newIdHash] = elementID
    # Connect properties and associations
    storedAssoc = set()
    for ka, va in mergedD.items():
        if ('Association' in ka):
            if (len(va) > 0):
                clmD = va.get('claimData')
                for c in clmD:
                    fN = c.get('fullName')
                    idList = c.get('id')
                    clss = c.get('class')
                    exist = c.get('existence')
                    newIdHash = secPrep.checkHashwithID(idList[-2], hashedGroups)
                    label = c.get('label')
                    #nextHash = re.findall(r"<<\w+>>([^<]*)", fN)[-1]
                    nextHash = secPrep.checkHashwithID(idList[-1], hashedGroups)
                    conType = label
                    # prevIdHash = checkHashwithID(idList[-2], hashedGroups)
                    prevKey = storedKeys.get(newIdHash)
                    nextKey = storedKeys.get(nextHash)
                    if (prevKey != None and nextKey != None and (prevKey, nextKey) not in storedAssoc):
                        # elementID = storeModelDataKeyArango(collection, newIdHash, clss, value, exist, client)
                        storeAssocArango(collectionAssoc, prevKey, nextKey, conType, client)
                        storedAssoc.add((prevKey, nextKey))

"""
#############################
#Run the function
#
#############################

con = createConArango('claimOmania')
data = secPrep.getDataInbound(createConArango('claimOmania'))
fdata = secPrep.flattenConData(data,con)
singleD = secPrep.getSingleData(fdata)
multiD = secPrep.getMultiData(fdata)
fdataConflicting = secPrep.getSingleConflicting(singleD)
fdataNonConflicting = secPrep.getSingleNonConflicting(singleD)
print('counting starts')
origdata, sourceCount=countSortConflictsOriginal(fdataConflicting)
groupedOrigD=groupBasedOnEntity(origdata)
#print(groupedOrigD)
fdataConflictsSolved = getEntityBestValue(groupedOrigD, sourceCount)
pprint(getSourceScores(sourceCount))
#pprint(fdataConflictsSolved)
pprint(sourceCount)
#pprint(fdataConflictsSolved)

hashedGroups= secPrep.groupIDvalues(data)

mergedAll = mergeAllAnalyzed(fdataNonConflicting, multiD, fdataConflictsSolved)
#pprint(mergedAll)
#saveAnalyzed2DB(mergedAll, hashedGroups, con)

"""


"""
#6. Counters
"""

"""

#Data counter
claimcounter=0
for key, val in data.items():
	#if ('Association' not in key or 'Property' in key):
		for v in val:
			claimcounter+=1
print('Claimcounter',claimcounter)


#Flattened claim counter
fcounter=0
for key, val in fdata.items():
	#if ('Association' not in key or 'Property' in key):
		cld=val.get('claimData')
		for c in cld:
			fcounter+=1
print('Flatcounter',fcounter)

#Single NonConflicting claim counter
counter=0
for key, val in fdataNonConflicting.items():
	#if ('Association' not in key or 'Property' in key):
		cld=val.get('claimData')
		for c in cld:
			counter+=1
print('Single nonconflicting claim',counter)

#Multi NonConflicting claim counter
counter=0
for key, val in multiD.items():
	#if ('Association' not in key or 'Property' in key):
		cld=val.get('claimData')
		for c in cld:
			counter+=1
print('Multi nonconflicting counter',counter)


#Single Conflicting claim counter
counter=0
for key, val in fdataConflicting.items():
	#if ('Association' not in key or 'Property' in key):
		cld=val.get('claimData')
		for c in cld:
			counter+=1
print('Single conflicting claim',counter)



#Multi Conflicting claim counter
counter=0
for key in groupedOrigD.keys():
	#if ('Association' not in key or 'Property' in key):
			counter+=1
print('Conflicts claims counter grouped by entity',counter)


#Multi Conflicting claim counter
counter=0
for key in fdataConflictsSolved.keys():
	#if ('Association' not in key or 'Property' in key):
			counter+=1
print('Conflicts solved claims counter',counter)


counter=0
for key, val in mergedAll.items():
	#if ('Association' not in key or 'Property' in key):
		cld=val.get('claimData')
		for c in cld:
			counter+=1
print('MergedAll claims',counter)

"""
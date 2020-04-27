import random
import tools
from pprint import pprint

sources = []
entities = []
facts = {}
claims = []
factTruth = dict()
maxValues = dict()

"""""""""""""""""""""""""""
##Input format of data
##
##List of list: entity,attribute,source,trust
"""""""""""""""""""""""""""


"""
Variables
"""
uniformPriorTrust = 0.8
K = 2
# Characteristics of the ...
beta1 = 0.5


"""
Functions
"""
def randomTruth():
    tempRan = random.random()
    return tempRan


def countValues(claimD, entity):
    i=0
    for c in claimD:
        if(tools.isEqual(c.get("entity"),entity)):
            i=i+1
    return i

def getCv(factsD, entity, value):
    for k,v in factsD.items():
        if(tools.isEqual(v.get('entity'),entity) and tools.isEqual(v.get('value'),value)):
            return v.get("Cv")


def setCv(factsD, entity, value, nV):
    for k, v in factsD.items():
        if(tools.isEqual(v.get("entity"),entity) and tools.isEqual(v.get("value"),value)):
            v["Cv"]=nV

def setTs(sourcesD , source, nV):
    for s in sourcesD:
        if(tools.isEqual(s.get("source"),source)):
            s["trust"]=nV

def prepTruthFacts(rawData):
    fid = 0
    visited = set()
    factTruth = dict()
    for i in rawData:
        entity = i[0]
        assert isinstance(entity,str)
        value = str(i[1])
        id = i[5]
        if ((entity.lower(), value.lower()) not in visited):
            fid = fid + 1
            visited.add((entity.lower(), value.lower()))
            factTruth[fid] = {'entity': entity, 'value': value, 'Cv': 0, 'id':id}
    return factTruth

def prepTruthSources(rawData):
    # Create source dataset (that will be updated)
    srcs = set()
    sources = []
    for r in (rawData):
        src = r[2]
        trst = r[4]
        if trst == None: trst = uniformPriorTrust
        if trst == 0: trst = float(0.001)
        if trst >= 1: trst = float(0.99)
        if (src.lower() not in srcs):
            sources.append({"source": src, "trust": trst})
            srcs.add(src.lower())
    print (sources)
    return sources


def prepEntities(rawData):
    # Create entities list
    entities = set()
    for r in (rawData):
        entity = r[0]
        if (entity.lower() not in entities):
            entities.add(entity.lower())
    return entities


def prepNoDuplClaims(rawData):
    claims = []
    visited = set()
    for r in rawData:
        #assert float(r[3]) >= 0 and float(r[3]) <= 1 #wsd value check
        value=str(r[1])
        if(r[3]==None):
            prior=beta1
        else:
            prior=float(r[3])
        if ((r[0].lower(), value.lower(), r[2].lower()) not in visited):
            # claims.append({"entity":r[0], "value":r[1], "source":r[2], "wsd":r[3]})
            claims.append({"entity": r[0], "value": value, "source": r[2], "wsd": 0.8, 'id':r[4], 'prior':prior})
            visited.add((r[0].lower(), value.lower(), r[2].lower()))
    return claims


def run(rawData):
    returnDict= dict()
    """
    Preprocessing
    """
    factTruth=prepTruthFacts(rawData)
    entities=prepEntities(rawData)
    sources=prepTruthSources(rawData)
    claims=prepNoDuplClaims(rawData)
    """
Calculations
    """
    #Cdsum = 0
    #Cv = 0
    #Ts = 0
    cntr=0
    while cntr<=K:
        for e in entities:
            Cdsum = 0
            for k, v in factTruth.items():
                vvalue=str(v.get("value"))
                CvPart1 = 1
                CvPart2 = 1
                if(tools.isEqual(v.get("entity"),e)):
                    betaCounter=0
                    beta=0
                    for s in sources:
                        for c in claims:
                            cvalue=str(c.get("value"))
                            if(tools.isEqual(c.get("source") , s.get("source")) and tools.isEqual(c.get("entity"), e) and tools.isEqual(cvalue,vvalue)):
                                wsd=c.get("wsd")
                                prior=c.get('prior')
                                assert isinstance(wsd, (int, float))
                                trust=s.get("trust")
                                assert isinstance(trust, (int, float))
                                CvPart1=CvPart1*((trust)**wsd)
                                beta+=float(prior)
                                betaCounter+=1
                            if(tools.isEqual(c.get("source"), s.get("source")) and (tools.isEqual(cvalue, vvalue)==False) and tools.isEqual(c.get("entity"), e)):
                                wsd=c.get("wsd")
                                assert isinstance(wsd, (int, float))
                                assert wsd>=0 and wsd <=1
                                trust=s.get("trust")
                                assert trust >=0 and trust <= 1
                                assert isinstance(trust, (int, float))
                                CvPart2=CvPart2*(((1-trust)/(countValues(claims, e) - 1))**wsd)
                                assert (countValues(claims, e) - 1)!=0
                                assert isinstance(countValues(claims, e), (int, float))
                    #print(e, v, vvalue, cvalue, type(vvalue), type(cvalue))
                    #print(beta, betaCounter, prior)
                    if(beta!=0 and betaCounter !=0):
                        beta=beta/betaCounter
                    assert beta<=1 and beta >0
                    Cv = beta * CvPart1 * CvPart2
                    assert isinstance(CvPart1, (int, float))
                    assert isinstance(CvPart2, (int, float))
                    assert isinstance(Cv, (int, float))
                    setCv(factTruth, e, v.get("value"), Cv)
                    Cdsum = Cdsum + Cv

            for k, v in factTruth.items():
                if (tools.isEqual(v.get("entity"), e)):
                    assert Cdsum!=0
                    Cv1 = v.get("Cv")
                    Cvv = (Cv1/Cdsum)

                    assert isinstance(Cvv, (int, float))
                    setCv(factTruth, e , v.get("value"),Cvv)
                    assert Cvv <= 1
        for s in sources:
            sumPart1 = 0
            sumPart2 = 0
            source = s.get("source")
            for k, v in factTruth.items():
                ent=v.get("entity")
                val= str(v.get("value"))
                for c in claims:
                    cvalu=str(c.get("value"))
                    if(tools.isEqual(c.get("source"), source) and tools.isEqual(c.get("entity"), ent) and tools.isEqual(cvalu, val)):
                        sumPart1 = sumPart1 + ((getCv(factTruth,ent,val))*(c.get("wsd")))
            assert isinstance(sumPart1, (int, float))
            for cl in claims:
                if(tools.isEqual(cl.get("source"), source)):
                    sumPart2=sumPart2+(cl.get("wsd"))
            assert isinstance(sumPart2, (int, float))
            Ts= sumPart1/sumPart2
            assert sumPart2 != 0
            assert isinstance(Ts, (int, float))
            setTs(sources,source,Ts)
        cntr=cntr+1
        print('Truth calculation iteration number:',cntr)

    #Find maximum values with Cv
    for e in entities:
        templist = []
        max = 0
        for f in factTruth.values():
            if(tools.isEqual(f.get("entity"), e)):
                templist.append(f)
        for tmp in templist:
            if tmp.get("Cv") > max:
                max = tmp.get("Cv")
                maxValues[e] = tmp

    returnDict["maxValues"]= list(maxValues.values())
    returnDict["factTruth"]= factTruth
    returnDict["sources"]= sources

    return returnDict

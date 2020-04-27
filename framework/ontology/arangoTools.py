import re
import tools
from pprint import pprint
from pyArango.connection import *


def createConArango(dbname):
	conn = Connection(username="claimer", password="c14imer1")
	return conn[dbname]

def storeAssocArango(collAssc, firstid, secondid, asscLabel, client):
    if (firstid != 0 and secondid != 0):
        tps = client[collAssc].createEdge()
        tps['label'] = asscLabel
        tps.links(firstid, secondid)

def storeElementArango(coll, clss, type, name, existence, client):
	collection = client[coll]
	first = collection.createDocument()
	first['class']=clss
	first["type"] = type
	first["label"]= name
	first["existence"]= existence
	first.save()
	return first._id

def storeMetaelementArango(coll, type, value, client):
	collection = client[coll]
	first = collection.createDocument()
	first["type"] = type
	first["label"] = value
	first.save()
	return first._id

def checkExists(dataF,con):
    hash=tools.hashfile(open(dataF, "rb"), dataF)
    result= None
    if con:
        result=con['metaelement'].fetchByExample({'hash': hash}, batchSize=100)
    if (len(result) !=0):
        return True
    else:
        return False

def returnDoc(docid, collection, client):
	doc= client[collection].fetchByExample({'_id': docid}, batchSize=100)
	try:
		return doc[0]
	except IndexError:
		return None

def getNodeFromInterface(nodeIntfIP, collection, client):
    interf = client[collection].fetchByExample({'label': nodeIntfIP, 'class': 'interface'}, batchSize=100)
    if(len(interf) != 0):
        interfId = interf[0]._id
        aql = "FOR v IN 1..2 OUTBOUND '{0}' {1}Assoc FILTER v.class == 'node' RETURN v".format(interfId, collection)
        queryResult = client.AQLQuery(aql, rawResults=True)
        if (len(queryResult) != 0):
            return queryResult[0].get("_id")

def getInterfaceByExample(nodeId, example, coll, client):
        aql= "FOR v IN 1..2 INBOUND '{0}' {1}Assoc FILTER v.label == '{2}' && v.class == 'interface' RETURN v".format(nodeId, coll, example)
        intid = client.AQLQuery(aql, rawResults=True)
        if(len(intid)>0):
            return intid[0].get('_id')

def getForeignInterfaceByExample(nodeId, example, coll, client):
    aql = "FOR inter IN 1..2 INBOUND '{0}' {1}Assoc FILTER inter.class == 'interface' RETURN  (FOR v IN 2..2 OUTBOUND inter elementAssoc FILTER v.class == 'interface' && v.label == '{2}' RETURN v)".format(
        nodeId, coll, example)
    intid = client.AQLQuery(aql, rawResults=True)
    if (len(intid) > 0):
        first=intid[0][0]
        return first.get('_id')


def getSourceClasses(source, client):
    aql = "FOR p IN 1..10000 OUTBOUND '{}' elementAssoc, metaelementAssoc RETURN DISTINCT p.class".format(source)
    result = client.AQLQuery(aql, rawResults=True)
    if (len(result) > 0):
        return result


def getSourceTimePoint(elementid, client):
    source=None
    aql="for s in 1..1000 inbound 'element/{}' elementAssoc, metaelementAssoc FILTER s.type=='timepoint' || s.type =='source' RETURN DISTINCT s".format(elementid)
    #aql="for s in 1..1000 inbound '{}' elementAssoc, metaelementAssoc FILTER s.type=='timepoint' || s.type =='source' RETURN DISTINCT s.label".format(elementid)
    #print(aql)
    queryResult = client.AQLQuery(aql, rawResults=True)
    if(len(queryResult)==2):
        source=str(queryResult[1].get('label'))+'_'+str(queryResult[0].get('label'))
        scope =queryResult[0].get('scope')
        return [source, scope]

def getSourceFromCollected(elementid, maxdistance,collection, client):
    source=None
    aql="for s in 1..{0} inbound '{1}' {2}Assoc FILTER s.class=='source' RETURN DISTINCT s".format(maxdistance,elementid,collection)
    queryResult = client.AQLQuery(aql, rawResults=True)
    if(len(queryResult)==1):
        source= queryResult[0].get('label')
        scope = queryResult[0].get('scope')
        return [source, scope]

def getSourceArchi(elementid, maxdistance,collection, client):
    source=None
    aql="for v,e,p in 1..{0} inbound '{1}' {2}Assoc FILTER p.vertices[*].class ALL!='CommunicationPath' FILTER v.class=='source' RETURN DISTINCT v".format(maxdistance,elementid,collection)
    queryResult = client.AQLQuery(aql, rawResults=True)
    if(len(queryResult)==0):
        aql = "for v,e,p in 1..{0} inbound '{1}' {2}Assoc FILTER v.class=='source' RETURN DISTINCT v".format(
            maxdistance, elementid, collection)
        queryResult = client.AQLQuery(aql, rawResults=True)
    if(len(queryResult)==1):
        source= queryResult[0].get('label')
        scope = queryResult[0].get('scope')
        return [source, scope]
#print(getSourceFromCollected(collectedModel/6367013, con))
#print(getSourceTimePoint('element/6062045',createConArango('claimOmania')))

def getElements(clss, tpe, con):
    if(clss!=None and tpe !=None):
        aql = "FOR e in element FILTER e.class=='{0}' && e.type=='{1}' RETURN DISTINCT [e._key, e.label, e.existence]".format(clss, tpe)
    if(clss!=None and tpe == None):
        aql = "FOR e in element FILTER e.class=='{}' && e.type== null RETURN DISTINCT [e._key, e.label, e.existence]".format(clss)
    if(aql!=None):
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def getPreviousElements(sourceID, previousClass, previousType, direction, con):
    if(previousType==None):previousType='null'
    if(tools.isEqual(direction,'in')):
        aql = "FOR v IN 1..3 INBOUND 'element/{0}' elementAssoc FILTER v.class == '{1}' && v.type=='{2}' RETURN DISTINCT v".format(
        sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'out')):
        aql = "FOR v IN 1..3 OUTBOUND 'element/{0}' elementAssoc FILTER v.class == '{1}' && v.type=='{2}' RETURN DISTINCT v".format(
        sourceID,  previousClass, previousType)
    query = con.AQLQuery(aql, rawResults=True)
    return query

def getPreviousElementsOutIn(sourceID, previousClass, previousType, con):
    aql = "FOR e in element FOR a in elementAssoc FILTER (e._id=='element/{0}') && (e._id ==a._from) FOR pe in element FILTER  (a._to==pe._id) FOR pa in elementAssoc FILTER  (pe._id ==pa._to) FOR ppe in element FILTER (ppe.class=='{1}') && (ppe.type=='{2}') && (ppe._id==pa._from) RETURN DISTINCT ppe".format(sourceID,  previousClass, previousType)
    query = con.AQLQuery(aql, rawResults=True)
    return query

def getPreviousElementsBoundary(sourceID, previousClass, previousType, direction,boundary, con):
    #if(previousType==None):
       #aql = "FOR v IN 1..2 INBOUND '{0}' elementAssoc FILTER v.class == '{1}' && v.type==null RETURN DISTINCT v".format(
        #sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'in') and previousType!=None):
        aql = "FOR v IN 1..{0} INBOUND 'element/{1}' elementAssoc FILTER v.class == '{2}' && v.type=='{3}' RETURN DISTINCT v".format(
        boundary, sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'out') and previousType!=None):
        aql = "FOR v IN 1..{0} OUTBOUND 'element/{1}' elementAssoc FILTER v.class == '{2}' && v.type=='{3}' RETURN DISTINCT v".format(
        boundary, sourceID,  previousClass, previousType)
    query = con.AQLQuery(aql, rawResults=True)
    return query

def getAllPreviousElements(sourceID, previousClass, previousType, direction, con):
    if(previousType==None):previousType='null'
    if(tools.isEqual(direction,'in')):
        aql = "FOR v IN 1..3 INBOUND 'element/{0}' elementAssoc FILTER v.class == '{1}' && v.type=='{2}' RETURN DISTINCT v".format(
        sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'out')):
        aql = "FOR v IN 1..3 OUTBOUND 'element/{0}' elementAssoc FILTER v.class == '{1}' && v.type=='{2}' RETURN DISTINCT v".format(
        sourceID,  previousClass, previousType)
    query = con.AQLQuery(aql, rawResults=True)
    return query

def storeModelDataKeyArango(coll, key, clss, name, existence, client):
	collection = client[coll]
	first = collection.createDocument()
	first['_key']=key
	first["class"] = clss
	first["label"]= name
	first["existence"]= existence
	first.save()
	return first._id


def storeModelDataArango(coll, clss, name, existence, client):
	collection = client[coll]
	first = collection.createDocument()
	first["class"] = clss
	first["label"]= name
	first["existence"]= existence
	first.save()
	return first._id

def storeModelSourceArango(coll, clss, name, scope, existence, client):
	collection = client[coll]
	first = collection.createDocument()
	first['scope']=scope
	first["class"] = clss
	first["label"]= name
	first["existence"]= existence
	first.save()
	return first._id


def getPreviousModelElemWBoundary(sourceID, previousClass, previousType, direction, boundary, collection,con):
    #if(previousType==None):
       #aql = "FOR v IN 1..2 INBOUND '{0}' elementAssoc FILTER v.class == '{1}' && v.type==null RETURN DISTINCT v".format(
        #sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'in') and previousType!=None):
        aql = "FOR v IN 1..{0} INBOUND '{1}/{2}' {1}Assoc FILTER v.class == '{3}' && v.type=='{4}' RETURN DISTINCT v".format(
        boundary,collection, sourceID,  previousClass, previousType)
    if(tools.isEqual(direction,'out') and previousType!=None):
        aql = "FOR v IN 1..{0} OUTBOUND '{1}/{2}' {1}Assoc FILTER v.class == '{3}' && v.type=='{4}' RETURN DISTINCT v".format(
        boundary, collection, sourceID,  previousClass, previousType)
    query = con.AQLQuery(aql, rawResults=True)
    return query


def getModelElements(clss, coll, con):
    if(clss!=None):
        aql = "FOR e in {0} FILTER e.class=='{1}' RETURN DISTINCT [e._key, e.label, e.existence]".format(coll, clss)
    if(aql!=None):
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query
#print(hashATuple(('Test', 'kalA', 'koer')))


def get5modelElements(first, second, third, fourth, fifth,collection, con):
    if(first != None and second != None and third != None and fourth != None and fifth!=None):
        aql ="FOR e in {0} FOR a in {0}Assoc FILTER (e.class=='{1}') && (e._id ==a._to) FOR pe in {0} FILTER (pe.class=='{2}') && (a._from==pe._id) FOR pa in {0}Assoc FILTER  (pe._id ==pa._to) FOR ppe in {0} FILTER (ppe.class=='{3}') && (pa._from==ppe._id) FOR ppa in {0}Assoc FILTER  (ppe._id ==ppa._to) FOR pppe in {0} FILTER (pppe.class=='{4}') && (ppa._from==pppe._id) FOR pppa in {0}Assoc FILTER  (pppe._id ==pppa._to) FOR ppppe in {0} FILTER (ppppe.class=='{5}') && (pppa._from==ppppe._id) RETURN DISTINCT [ppppe, pppa.label, pppe, ppa.label, ppe, pa.label,pe,a.label,e]".format(collection,fifth, fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get4modelElements(first, second, third, fourth,collection, con):
    if (first != None and second != None and third != None and fourth != None):
        aql = "FOR e in {0} FOR a in {0}Assoc FILTER (e.class=='{1}') && (e._id ==a._to) FOR pe in {0} FILTER (pe.class=='{2}') && (a._from==pe._id) FOR pa in {0}Assoc FILTER  (pe._id ==pa._to) FOR ppe in {0} FILTER (ppe.class=='{3}') && (pa._from==ppe._id) FOR ppa in {0}Assoc FILTER  (ppe._id ==ppa._to) FOR pppe in {0} FILTER (pppe.class=='{4}') && (ppa._from==pppe._id) RETURN DISTINCT [pppe, ppa.label, ppe, pa.label,pe,a.label,e]".format(collection, fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get3modelElements(first, second, third, collection, con):
    if (first != None and second != None and third != None):
        aql = "FOR e in {0} FOR a in {0}Assoc FILTER (e.class=='{1}') && (e._id ==a._to) FOR pe in {0} FILTER (pe.class=='{2}') && (a._from==pe._id) FOR pa in {0}Assoc FILTER  (pe._id ==pa._to) FOR ppe in {0} FILTER (ppe.class=='{3}') && (pa._from==ppe._id) RETURN DISTINCT [ppe, pa.label,pe,a.label,e]".format(collection, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get2modelElements(first, second, collection, con):
    if (first != None and second != None):
        aql = "FOR e in {0} FOR a in {0}Assoc FILTER (e.class=='{1}') && (e._id ==a._to) FOR pe in {0} FILTER (pe.class=='{2}') && (a._from==pe._id) RETURN DISTINCT [pe,a.label, e]".format(collection,second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def getmodelElements(first, collection, con):
        if (first != None):
            aql = "FOR e in {0} FILTER (e.class=='{1}') RETURN DISTINCT [e]".format(
                collection, first)
            query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
            return query

#print((get4modelElements('Network','Host','Client', 'Dataflow',createConArango('claimOmania'))))
"""
def getElements(clss, tpe, con):
    if(clss!=None and tpe !=None):
        aql='FOR e in element FOR a in elementAssoc FILTER (e.class=="{0}" && e.type=="{1}") && (e._id ==a._to ||e._id==a._from) FOR oe in element FILTER (a._to==oe._id || a._from==oe._id) RETURN DISTINCT {{"elementID":e._id, "incoming": a._to, "outgoing": a._from, "label": e.label, "connectedClass": oe.class, "connectedType":oe.type, "connectedLabel": oe.label, "connectedID": oe._id, "existence":e.existence, "connectedExistence": oe.existence}}'.format(clss, tpe)
    if(clss!=None and tpe == None):
        aql = 'FOR e in element FOR a in elementAssoc FILTER (e.class=="{0}" && e.type==null) && (e._id ==a._to ||e._id==a._from) FOR oe in element FILTER (a._to==oe._id || a._from==oe._id) RETURN DISTINCT {{"elementID":e._id, "incoming": a._to, "outgoing": a._from, "label": e.label, "connectedClass": oe.class, "connectedType":oe.type, "connectedLabel": oe.label, "connectedID": oe._id, "existence":e.existence, "connectedExistence": oe.existence}}'.format(clss)
    if(aql!=None):
        query = con.AQLQuery(aql, rawResults=True)
        return query


def getInterfaceByExample(sourceId, example, coll, clss, type, name, existence, client):
    aql1 = "FOR v IN 1..2 OUTBOUND '{0}' {1}Assoc FILTER v.class == 'node' RETURN v".format(sourceId, coll)
    queryResult = client.AQLQuery(aql1, rawResults=True)
    if (len(queryResult) != 0):
        nid=queryResult[0].get("_id")
        aql2= "FOR v IN 1..2 INBOUND '{0}' {1}Assoc FILTER v.label == '{2}' && v.class == 'interface' RETURN v".format(nid, coll, example)
        intid = client.AQLQuery(aql2, rawResults=True)
        return intid[0].get('_id')



def get5modelElements(first, second, third, fourth, fifth, con):
    if(first != None and second != None and third != None and fourth != None and fifth!=None):
        aql ="FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) FOR ppa in collectedModelAssoc FILTER  (ppe._id ==ppa._to) FOR pppe in collectedModel FILTER (pppe.class=='{3}') && (ppa._from==pppe._id) FOR pppa in collectedModelAssoc FILTER  (ppe._id ==pppa._to) FOR ppppe in collectedModel FILTER (ppppe.class=='{4}') && (pppa._from==ppppe._id) RETURN DISTINCT [ppppe,pppe,ppe,pe,e]".format(fifth, fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get4modelElements(first, second, third, fourth, con):
    if (first != None and second != None and third != None and fourth != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) FOR ppa in collectedModelAssoc FILTER  (ppe._id ==ppa._to) FOR pppe in collectedModel FILTER (pppe.class=='{3}') && (ppa._from==pppe._id) RETURN DISTINCT [pppe,ppe,pe,e]".format(fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get3modelElements(first, second, third, con):
    if (first != None and second != None and third != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) RETURN DISTINCT [ppe,pe,e]".format(third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get2modelElements(first, second, con):
    if (first != None and second != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) RETURN DISTINCT [pe,a.label, e]".format(second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def getmodelElements(first, con):
        if (first != None):
            aql = "FOR e in collectedModel FILTER (e.class=='{}') RETURN DISTINCT [e]".format(
                first)
            query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
            return query

#Newest down
def get5modelElements(first, second, third, fourth, fifth, con):
    if(first != None and second != None and third != None and fourth != None and fifth!=None):
        aql ="FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) FOR ppa in collectedModelAssoc FILTER  (ppe._id ==ppa._to) FOR pppe in collectedModel FILTER (pppe.class=='{3}') && (ppa._from==pppe._id) FOR pppa in collectedModelAssoc FILTER  (pppe._id ==pppa._to) FOR ppppe in collectedModel FILTER (ppppe.class=='{4}') && (pppa._from==ppppe._id) RETURN DISTINCT [ppppe, pppa.label, pppe, ppa.label, ppe, pa.label,pe,a.label,e]".format(fifth, fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get4modelElements(first, second, third, fourth, con):
    if (first != None and second != None and third != None and fourth != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) FOR ppa in collectedModelAssoc FILTER  (ppe._id ==ppa._to) FOR pppe in collectedModel FILTER (pppe.class=='{3}') && (ppa._from==pppe._id) RETURN DISTINCT [pppe, ppa.label, ppe, pa.label,pe,a.label,e]".format(fourth, third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get3modelElements(first, second, third, con):
    if (first != None and second != None and third != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) FOR pa in collectedModelAssoc FILTER  (pe._id ==pa._to) FOR ppe in collectedModel FILTER (ppe.class=='{2}') && (pa._from==ppe._id) RETURN DISTINCT [ppe, pa.label,pe,a.label,e]".format(third, second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def get2modelElements(first, second, con):
    if (first != None and second != None):
        aql = "FOR e in collectedModel FOR a in collectedModelAssoc FILTER (e.class=='{0}') && (e._id ==a._to) FOR pe in collectedModel FILTER (pe.class=='{1}') && (a._from==pe._id) RETURN DISTINCT [pe,a.label, e]".format(second, first)
        query = con.AQLQuery(aql, rawResults=True, batchSize = 100000000)
        return query

def getmodelElements(first, con):
        if (first != None):
            aql = "FOR e in collectedModel FILTER (e.class=='{}') RETURN DISTINCT [e]".format(
                first)
            query = con.AQLQuery(aql, rawResults=True, batchSize=100000000)
            return query


"""
#print(getNodeFromInterface('192.168.109.5', 'element', createConArango('claimOmania')))
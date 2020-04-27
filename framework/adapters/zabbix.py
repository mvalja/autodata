# -*- coding: utf-8 -*-


from pyzabbix import ZabbixAPI
import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def parseZabbix(db, config):
    zapi = connect_to_zabbix(config)

    datadict = retrieve_zabbix_data(zapi, config)

    import_zabbixdata_into_arangodb(datadict, db)


def connect_to_zabbix(config):
    """Tries to connect to Zabbix and returns an API object to interact with
    the Zabbix API.
    """
    try:
        ZABBIX_SERVER = config['zabbix']['host']
        zapi = ZabbixAPI(ZABBIX_SERVER)
        zapi.login(config['zabbix']['username'], config['zabbix']['password'])
        logger.info('Connected to Zabbix on %s', config['zabbix']['host'])
        return zapi
    except Exception:
        logger.error('Connection to Zabbix failed. Are you sure the Web API is accessible on %s ?', config['zabbix']['host'], exc_info=Exception)


def retrieve_zabbix_data(zapi, config):
    """Iterate over a dict with all the zabbix get methods we want (as keys), and
    optional parameters for each get method (as value).
    """
    # Create a time range for the history retrieval
    time_till = time.mktime(datetime.now().timetuple())
    time_from = time_till - 60 * 60 * config['zabbix']['historyrange'] # config is in hours

    print('\nRetrieving data from Zabbix', flush=True)
    methoddict = { 'item':'', 'host':'', 'hostgroup':'', 'graph':'', \
                  'history':'time_from=time_from, time_till=time_till', 'application':'', 'hostinterface':'' }

    datadict = {}

    for data, params in methoddict.items():
        try:
            datadict[data] = eval('zapi.' + data + '.get(' + params + ')')
            logger.info('Retrieved %s items for %s', len(datadict[data]), data)
        except Exception:
            logger.error('Failed retrieving items for %s', data, exc_info=Exception)
            pass

    if len(datadict) == 0:
        try:
            raise ValueError('Could not retrieve anything from Zabbix')
        except Exception:
            logger.error('Could not retrieve anything from Zabbix', exc_info=Exception)
    else:
        return datadict


def import_zabbixdata_into_arangodb(datadict, db):
    """Import data that is extracted using the Zabbix API.
    """
    print('\nImporting Zabbix data into ArangoDB', flush=True)
    
	checkStart = client['metaelement'].fetchByExample({'type': "startpoint","label": "start"}, batchSize = 100)
    if (len(checkStart) == 0):
            startKey=storeMetaelementArango('metaelement','startpoint','start', client )
    else: startKey= checkStart[0]._id

    checkTP = client['metaelement'].fetchByExample({'type': "timepoint","label": date}, batchSize = 100)
    if (len(checkTP) == 0):
            tpKey=storeMetaelementArango('metaelement','timepoint',date, client )
            storeAssocArango('metaelementAssoc', startKey, tpKey, 'startTimepoint', client)
    else: tpKey= checkTP[0]._id
    srcId=storeMetaelementArango('metaelement', 'source', dataSource, client)
	
	for collection, data in datadict.items():
		
		#network zone
		#network interface
		#host (or router)
		#application instances (servers, clients, data stores, operating systems, antimalware, vulnscanner, web application, host firewall, host ids)
		#ports
		#access control
		
		
		
		logger.info('Going to import %s items of type %s', len(data), collection)

        jsonarray = ''
        for item in data:
            jsonarray += json.dumps(item) + '\n'

        try:
            r = db.bulk_arangodb(jsonarray, 'zabbix_' + collection)
        except Exception:
            logger.error('Unable to input data into ArangoDB', exc_info=Exception)
            break

        try:
            resptext = json.loads(r.text)
            logger.info('Imported %s items into ArangoDB with %s errors', resptext['created'], resptext['errors'])
        except:
            logger.info('Raw import response: %s', r.text)
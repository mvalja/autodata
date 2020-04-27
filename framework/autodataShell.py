"""
The purpose of this file is to run the framework's shell in an interactive way
"""
import os.path
import tools
from cmd import Cmd
import arangoTools
import importlib.util
import sys
import securicadAdapter
import preprocess
import LCA3_quick
import securiCADsimpleAnalysis as naive
from pprint import pprint
import securicadFileWriter

#Read the database and data source configuration
currentdir = os.path.dirname(os.path.realpath(__file__))
configFile = currentdir + '/config/default.xml'
dataSourceFile = currentdir + '/config/dataSource.xml'
# The values calculated and checked during the analysis

if (os.path.isfile(configFile)):
    cfgparser = tools.configParser(configFile)
else:
    print(configFile + ' not found, please create it!' ,flush=True)
if (os.path.isfile(dataSourceFile)):
    sourceparser = tools.sourceCfgParser(dataSourceFile)
else:
    print(configFile + ' not found, please create it!' ,flush=True)

adapterList = sourceparser.get("adapters")
imports = sourceparser.get("imports")
database = cfgparser.get("database")

#Creating connection to DB, assuming localhost
dbName = database[0].get("database")
dbUser = database[0].get("user")
dbPw = database[0].get("password")

con=arangoTools.createConArango(dbName,dbUser,dbPw)

class SubInterpreter(Cmd):
    prompt = "(level2) "

    def do_subcommand_1(self, args):
        pass

    def do_subcommand_2(self, args):
        pass

    def do_quit(self, args):
        return True
    do_EOF = do_quit


class autodataPrompt(Cmd):

    def __init__(self):
        self.data = None
        self.fdata = None
        self.single = None
        self.multiDT = None
        self.singleED = None
        self.multiED = None
        self.mergedConflictSet = None
        self.nonCSD = None
        self.nonCMD = None
        self.hashedGroups = None
        super(autodataPrompt, self).__init__()

    intro = '''
         ___  __  ____________  ___  ___ _________
        / _ |/ / / /_  __/ __ \/ _ \/ _ /_  __/ _ |
       / __ / /_/ / / / / /_/ / // / __ |/ / / __ |
      /_/_|_\____/_/_/__\____/____/_/ |_/_/_/_/ |_|  __ __
      / __/ _ \/ _ | /  |/  / __/ | /| / / __ \/ _ \/ //_/
     / _// , _/ __ |/ /|_/ / _/ | |/ |/ / /_/ / , _/ ,<
    /_/ /_/|_/_/ |_/_/  /_/___/ |__/|__/\____/_/|_/_/|_|

    |||||||||||||||||||||||||||||||||||||||||||||||||||||\n
    Please use the following commands to operate the framework.\n
    dataimport          -   Import data using info from config files
    convertmodel        -   Convert collected data to securiLANG
    getstringdata       -   Transform data structures into long strings
    generateids         -   Generate new data source independent ids
    sortassoc           -   Sort data according to associations
    gennegative         -   Generate negative values for some data
    sortconflicting     -   Sort data into conflicting and non-conflicting
    runtruth            -   Run truth analysis
    runnaive            -   Run naive analysis (only getstringdata required)
    genseccadfile       -   Write a securicad file

    ------------------------------------------
    truncatecommon      -   Delete common lang. data from DB
    truncatemodel       -   Delete securiCAD data from multiple sources from DB

    '''

    def do_dataimport(self, args):
        """Imports data from source files using data source specific adapters. The location of source files and appropriate adapters are defined in the configuration file - "dataSources.xml")."""
        importedAdapter=dict()
        for i in imports:
            sourceName = i.get("sourceName")
            if ((tools.getAdapter(sourceName, adapterList)) != None):
                dataLoc = i.get("location")
                coverage = i.get("coverage")
                mainip = i.get("mainip")
                nodename = i.get("nodename")
                adapter = tools.getAdapter(sourceName, adapterList)
                ts=tools.creationDate(dataLoc)
                # Importing adapters from adapters
                if(sourceName not in importedAdapter):
                    spec = importlib.util.spec_from_file_location('run', 'adapters\\{}.py'.format(adapter))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    #print('Importing adapters ',mod)
                    importedAdapter[sourceName]=mod
                else:
                    mod=importedAdapter[sourceName]
                if(mainip!=None and nodename!=None):
                    query = ("mod.run('{0}', '{1}', '{2}','{3}','{4}','{5}',con )").format(sourceName, coverage, mainip, nodename, dataLoc, ts)
                elif(mainip==None and nodename==None):
                    query = ("mod.run('{0}', '{1}', '{2}','{3}',con)").format(sourceName, coverage, dataLoc, ts)

                exec(query)

    def do_convertmodel(self, args):
        """Converts data from common language to securiLANG and writes back to DB."""
        print('Processing..')
        securicadAdapter.modelData2DB(securicadAdapter.mergeData(con), con)

    def do_getstringdata(self, args): #METRICS Claims
        """Gets data from the DB in a long string format."""
        print('Processing..')
        self.data = preprocess.getDataInbound(con)
        self.fdata = preprocess.flattenConData(self.data, con)
        #Flattened claim counter
        fcounter=0
        for key, val in self.fdata.items():
            cld=val.get('claimData')
            for c in cld:
                fcounter+=1
        print('-------------------------------------------')
        print('Claims generated',fcounter)
        print('Done!')

    def do_generateids(self, args): #METRICS new ids
        """Generates new unique data source independent id values for model elements."""
        if(self.data!=None):
            print('Processing..')
            self.hashedGroups = preprocess.groupIDvalues(self.data)
            counter = 0
            for k, v in self.hashedGroups.items():
                print('Added:', 'new key:', k, 'old keys:', v)
                counter+=1
            print('-------------------------------------------')
            print('New unique keys:',counter)
            print('Done!')
        else:
            print('Get data in long string format first!')

    def do_sortassoc(self, args): #METRICS single and multi claims
        """Sorts data according to the association multiplicities defined in the model."""
        if (self.fdata != None):
            print('Processing..')
            self.multiDT = preprocess.getMultiData(self.fdata)
            self.single = preprocess.getSingleData(self.fdata)
            scounter=0
            mcounter=0
            for key, val in self.multiDT.items():
                cld=val.get('claimData')
                for c in cld:
                    mcounter+=1
            for key, val in self.single.items():
                cld = val.get('claimData')
                for c in cld:
                    scounter += 1
            print('-------------------------------------------')
            print('Exclusive claims found:', scounter,' Non-exclusive claims found:',mcounter)
            print('Done!')
        else:
            print('Get data in long string format first!')

    def do_gennegative(self, args): #METRICS generated existence amount
        """Generates negative values according to predefined criteria to factor in uncertainty."""
        if (self.multiDT != None and self.single != None):
            print('Processing..')
            self.singleED = preprocess.generateSingleExistence(self.single)
            self.multiED = preprocess.generateMultiExistence(self.multiDT)
            print('Done!')
        else:
            print('Sort data according to associations first!')


    def do_sortconflicting(self, args): #METRICS conflicting claims for the truth analysis
        """Sorts conflicting values from non-conflicting ones."""
        if (self.multiED != None and self.singleED != None):
            print('Processing..')
            self.cMD = preprocess.getMultiConflicting(self.multiED)
            self.nonCMD = preprocess.getMultiNonConflicting(self.multiED)
            self.nonCSD = preprocess.getSingleNonConflicting(self.singleED)
            self.cSD = preprocess.getSingleConflicting(self.singleED)
            self.mergedConflictSet = preprocess.mergeSingleMultiForLCA(self.cSD, self.cMD)
            #Metrics: Counting claims
            mccounter=0
            for key, val in self.cMD.items():
                cld=val.get('claimData')
                for c in cld:
                    mccounter+=1
            sccounter=0
            for key, val in self.cSD.items():
                cld=val.get('claimData')
                for c in cld:
                    sccounter+=1
            sncounter=0
            for key, val in self.nonCSD.items():
                cld=val.get('claimData')
                for c in cld:
                    sncounter+=1
            mncounter=0
            for key, val in self.nonCMD.items():
                cld=val.get('claimData')
                for c in cld:
                    mncounter+=1
            print('-------------------------------------------')
            print('Exclusive non-conflicting claims:',sncounter)
            print('Non-exclusive non-conflicting claims:',mncounter)
            print('-------------------------------------------')
            print('Exclusive conflicting claim:',sccounter)
            print('Non-exclusive conflicting claims:',mccounter)
            print('-------------------------------------------')
            print('Done!')
        else:
            print('Generate existence first!')

    def do_runtruth(self, args): #METRICS
        """Runs the truth analysis to resolve conflicts."""
        if (self.mergedConflictSet != None and self.nonCSD != None and self.nonCMD != None and self.hashedGroups != None ):
            print('Processing..')
            self.hashedGroups = preprocess.groupIDvalues(self.data)
            self.truthData = LCA3_quick.run(self.mergedConflictSet)
            self.mergeAllD = preprocess.mergeAll(self.nonCSD, self.nonCMD, self.truthData)
            #preprocess.analyzed2DB(self.mergeAllD, self.hashedGroups, con)
            #Metrics: count
            counter=0
            for key, val in self.mergeAllD.items():
                cld=val.get('claimData')
                for c in cld:
                    counter+=1
            self.conflicts=preprocess.countSortConflictsGenerated(self.mergedConflictSet)
            sourceCount=preprocess.countDataSourcesMatching(self.conflicts)
            sourceCountF=preprocess.countDataSourcesFalse(self.conflicts)
            sourceCountNF=preprocess.countDataSourcesNotFalse(self.conflicts)
            print('-------------------------------------------')
            print('Matching claims before truth calculation')
            pprint(sourceCount)
            print('False claims before truth calculation')
            pprint(sourceCountF)
            print('Non negative claims before truth calculation')
            pprint(sourceCountNF)
            print('-------------------------------------------')
            print('All claims AFTER truth calculation',counter)
            print('-------------------------------------------')
            print('Calculated trust values for data sources')
            pprint(self.truthData.get('sources'))
            print('-------------------------------------------')
            print('Done!')
        else:
            print('Sort conflicting claims from non-conflicting first!')

    def do_runnaive(self, args): #METRICS
        """Runs a naive analysis without factoring in uncertainty. A simple frequency based comparison is done."""
        if (self.single != None):
            print('Processing..')
            self.flatsinglenonconfl = preprocess.getSingleNonConflicting(self.single)
            self.fdataConflicting =  preprocess.getSingleConflicting(self.single)
            self.origdata, self.sourceCount = naive.countSortConflictsOriginal(self.fdataConflicting)
            self.groupedOrigD = naive.groupBasedOnEntity(self.origdata)
            self.fdataConflictsSolved = naive.getEntityBestValue(self.groupedOrigD, self.sourceCount)
            fnccounter = 0
            for key, val in self.flatsinglenonconfl.items():
                # if ('Association' not in key or 'Property' in key):
                cld = val.get('claimData')
                for c in cld:
                    fnccounter += 1
            mnccounter = 0
            for key, val in self.multiDT.items():
                cld = val.get('claimData')
                for c in cld:
                    mnccounter += 1
            cscounter = 0
            for key in self.fdataConflictsSolved.keys():
                cscounter += 1
            fccounter=0
            for key, val in self.fdataConflicting.items():
                cld=val.get('claimData')
                for c in cld:
                    fccounter+=1
            pprint(self.sourceCount)
            print('-------------------------------------------')
            print('Total non-conflicting claims', fnccounter + mnccounter)
            print('Total conflicting claims', fccounter)
            print('Conflicts solved with Naive analysis claims', cscounter)
            print('-------------------------------------------')
            print('Done!')
        else:
            print('Sort data according to associations first!')

    def do_genseccadfile(self, args): #METRICS
        """Generates a securiCAD model file that can be opened in the tool."""
        print('Processing..')
        securicadFileWriter.prepareXML('securiCAD.xml', '02/10/2017', con)
        print('''

 ad88888ba   88        88    ,ad8888ba,    ,ad8888ba,   88888888888  ad88888ba    ad88888ba
d8"     "8b  88        88   d8"'    `"8b  d8"'    `"8b  88          d8"     "8b  d8"     "8b
Y8,          88        88  d8'           d8'            88          Y8,          Y8,
`Y8aaaaa,    88        88  88            88             88aaaaa     `Y8aaaaa,    `Y8aaaaa,
  `"""""8b,  88        88  88            88             88"""""       `"""""8b,    `"""""8b,
        `8b  88        88  Y8,           Y8,            88                  `8b          `8b
Y8a     a8P  Y8a.    .a8P   Y8a.    .a8P  Y8a.    .a8P  88          Y8a     a8P  Y8a     a8P
 "Y88888P"    `"Y8888Y"'     `"Y8888Y"'    `"Y8888Y"'   88888888888  "Y88888P"    "Y88888P"

        ''')

    def do_truncatecommon(self, args):
        """Deletes common imported data from multiple sources."""
        print("Truncating imported data.")
        con['element'].truncate()
        con['metaelement'].truncate()
        con['elementAssoc'].truncate()
        con['metaelementAssoc'].truncate()
        print("Done!")

    def do_truncatemodel(self, args):
        """Deletes securiCAD data from multiple sources."""
        print("Truncating securiCAD data.")
        con['collectedModel'].truncate()
        con['collectedModelAssoc'].truncate()
        print("Done!")

    def do_quit(self, args):
        """Quits the program."""
        print("Quitting.")
        raise SystemExit


if __name__ == '__main__':
    prompt = autodataPrompt()
    prompt.prompt = '> '
    prompt.cmdloop()
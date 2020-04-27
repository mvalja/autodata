# Automatic data collection and modeling project

IT architecture is constantly changing and data sources provide information that can deviate from reality to some degree. There can be problems with varying accuracy (e.g. actuality and coverage), representation (e.g. data syntax and file format), or inconsistent semantics. Integration of heterogeneous data from different sources needs to handle data quality problems of the sources. This can be done by using probabilistic models. 

This repository contains files from a project where we attempted to use truth discovery algorithms to reason over the validity of enterprise architecture data for the purpose of improving the accuracy of model. The pythons scripts of a prototype are given under the folder **framework**. Different information sources were used in the project and one of them, data from a SCADA small utility lab setup is given under the folder **labDATA**.

To launch the framework run autodataShell.py, note however that the framework requires access to an Arango database instance to work properly.

The framework consist of the following steps:
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

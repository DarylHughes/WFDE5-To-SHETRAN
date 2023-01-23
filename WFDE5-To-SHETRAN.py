# -*- coding: utf-8 -*-
"""
Date created:   2023.01.23
Last modified:  2023.01.23
@author:        Daryl Hughes


This script:
    - Reads downloaded WFDE5 NetCDF data for each monthyear
    - Plots WFDE5 data
    - Clips WFDE5 to data domain
    - Writes clipped WFDE5 NetCDF files for each monthyear
    - Reads clipped WFDE5 NetCDF files for each monthyear
    - Creates CSVs of clipped WFDE5 for each monthyear
    - Concatenates all clipped monthyear CSVs into a single CSV
        
File information:
    - WFDE5 files contain a single variable for a given month, 
    at hourly intervals, for the entire globe at 0.5 x 0.5 degree.
    - The filename format is '<variable>_<dataset>_<yearmonth>_<modelversion>.nc'
    - The variable of interest is 'Rainf' (Rainfall Flux) in units kg/m-2/s-1

Outputs are:
    - A precipitation map for a SHETRAN model (with some GIS processing)
    - A precipitation time series for a SHETRAN model
    
The user must define:
    - 'FunctionsLibrary' which contains custom functions
    - 'DirectoryRaw' which contains the downloaded WFDE5 NetCDF data for each monthyear
    - 'DataVersion' which contains the version of the downloaded WFDE5 data, assumed to be in the filenames
    - 'ExtIn' which is the file extension of the downloaded WFDE5 data
    - 'DirectoryClipped' which is the location for writing clipped data
    - 'DirectoryConcat' which is the location for writing concatenated data
    - 'North'  which is the northern limit of the data domain
    - 'South' which is the southern limit of the data domain
    - 'West' which is the western limit of the data domain
    - 'East' which is the eastern limit of the data domain


"""


#%% User-defined variables

FunctionsLibrary    = 'C:/Users/DH/OneDrive - Heriot-Watt University/Documents/HydrosystemsModellerRA/Writing(Shared)/Paper1'
DirectoryRaw        = 'C:/Users/DH/OneDrive - Heriot-Watt University/Documents/HydrosystemsModellerRA/HydroModelling/HydroInputData/RainTimeSeries/WFDE5/dataset/'
DataVersion         = 'v2.1'                                                    # Set to data version e.g. 'v2.1'
ExtIn               = '.nc'                                                     # Set to data extension i.e. '.nc'
DirectoryClipped    = 'C:/Users/DH/Downloads/'                                  # Set to location for writing clipped data
DirectoryConcat     = 'C:/Users/DH/Downloads/'                                  # Set to location for writing clipped concatenated data
North               = 8.21                                                      # Northern limit of data domain (lat)
South               = 1.09                                                      # Southern limit of data domain (lat)
West                = -62.94                                                    # Western limit of data domain (lon)
East                = -57.67                                                    # Eastern limit of data domain (lon)


#%% Import modules and functions

import os
import numpy as np
import pandas as pd
import glob
import time
from netCDF4 import Dataset

os.chdir(FunctionsLibrary)                                                      # Sets working directory to enable custom functions to be used
from CustomFunctionsToSHETRAN import NetCDFPlotter
from CustomFunctionsToSHETRAN import WFDE5NetCDFClipper
from CustomFunctionsToSHETRAN import NetCDFToSHETRAN


#%% Read in each monthyear and wrangle data

# Define directory and file locations
PathListNC        = glob.glob(DirectoryRaw + '*' + DataVersion + ExtIn)         # Create list of files with full path names and extensions

# Create list of file names only (without filepath or extension)
FileNameList= []                                                                # Create blank list to store file names without extensions
for Path in PathListNC:
    FileName = Path.split('\\',-1)[1]                                           # Extract filename and extension from entire path
    FileName = FileName.split(ExtIn,-1)[0]                                      # Extract filename without extension
    FileNameList.append(FileName)
    
File        = FileNameList[0]
WFDE5       = Dataset(DirectoryRaw + File + ExtIn)

# Interrogate data
WFDE5.variables.keys()
WFDE5.variables

# Return size of arrays
LonLen  = len(WFDE5.variables['lon'][:])
LatLen  = len(WFDE5.variables['lat'][:])
TimeLen = len(WFDE5.variables['time'][:])

# Get the longitude(x) and latitude(y) variables from the dataset
Lons = WFDE5.variables['lon'][:]
Lats = WFDE5.variables['lat'][:]

# Get the index of the closest value to the easting and northing, plus 1 to cover domain
IdxNorth    = (np.abs(Lats - North)).argmin() + 1
IdxSouth    = (np.abs(Lats - South)).argmin()
IdxWest     = (np.abs(Lons - West)).argmin()
IdxEast     = (np.abs(Lons - East)).argmin() + 1

# Define unit conversion (from kg/m-2/s-1 to mm/hour)
SecsPerHour = 60**2
KgPerCubicM = 10**3
MmPerMetre  = 1000
UnitConversion = SecsPerHour / KgPerCubicM * MmPerMetre
#%% Plot map of time point, and time series of point

# Call NetCDFPlotter function on clipped extent
NetCDFPlotter(Variable          = 'Rainf',
              Data              = WFDE5,
              Time              = 250,                                          # Set for time point of map
              Lon               = 244,                                          # Set for Lon of time series
              Lat               = 190,                                          # Set for Lat of time series
              South             = IdxSouth,                                     # Set 0=globe OR IdxSouth=domain
              North             = IdxNorth,                                     # Set LatLen=globe OR IdxNorth=domain
              West              = IdxWest,                                      # Set 0=globe OR IdxWest=domain
              East              = IdxEast,                                      # Set LonLen0=globe OR IdxEast=domain
              UnitConversion    = UnitConversion,
              )


#%% Clip WFDE5 data by returning array and write <WFDE5Clip>.nc, for all monthyear files

TimeCount1 = time.perf_counter()

for File in FileNameList:
    WFDE5 = Dataset(DirectoryRaw + File + ExtIn)
    WFDE5NetCDFClipper(Path         = DirectoryClipped,
                       FileRaw      = WFDE5,
                       IdxWest      = IdxWest,
                       IdxEast      = IdxEast,
                       IdxNorth     = IdxNorth,
                       IdxSouth     = IdxSouth,
                       FileClipped  = DirectoryClipped + File + '_Clip' + ExtIn)
print('WFDE5NetCDFClipper: All NetCDF files clipped')

TimeCount2 = time.perf_counter()

print('Seconds taken = ', TimeCount2 - TimeCount1)


#%% Wrangle <WFDE5Clip>.nc data into <WFDE5Clip>.csv format using NetCDFToSHETRAN function, for all files

TimeCount1 = time.perf_counter()

for File in FileNameList:
    WFDE5Clip   = Dataset(DirectoryClipped + File + '_Clip' + ExtIn)
    DfVarTimeSeriesCells = NetCDFToSHETRAN(Data            = WFDE5Clip,
                                           Variable        = 'Rainf',
                                           LongitudeName   = 'lon',
                                           LatitudeName    = 'lat',
                                           Path            = DirectoryClipped,
                                           File            = File + '_Clip.csv',
                                           UnitConversion  = UnitConversion
                                           )

# Convert units (from kg/m-2/s-1 to mm/hour)
DfVarTimeSeriesCells = DfVarTimeSeriesCells * UnitConversion

TimeCount2 = time.perf_counter()
print('seconds taken = ', TimeCount2 - TimeCount1)


#%% Concatenate each monthyear's DataFrame into a master DataFrame and wrangle datetimes, time interval, and NoData values

PathListCSV = glob.glob(DirectoryClipped + '*' + DataVersion + '_Clip.csv')     # Create list of files with full path names and extensions

# Loop through each CSV in CSVPathList to create list of monthyear DataFrames
DfList      = []
for CSV in PathListCSV:
    Df      = pd.read_csv(filepath_or_buffer    = CSV,
                          index_col             = (0))
    DfList.append(Df)

# Concatenate all Dfs in list to master Df
Mdf         = pd.concat(DfList)
Mdf         = Mdf.sort_index(ascending = True)

# Create datetime index (units are hours since 1900-01-01 00:00:00)
DateIndex = pd.Series(pd.date_range(start='1900-01-01 00:00:00',
                                    end = '2011-01-01 00:00:00',
                                    freq = 'H'))

# Set new date index to MDf by subsetting DateIndex to the first and late dates in Mdf
MdfStart    = Mdf.index[0]
MdfEnd      = Mdf.index[-1]+1
Mdf.index   = DateIndex[MdfStart:MdfEnd]

# Aggregate from hourly to daily
Mdf = Mdf.resample('D').sum()

# Change NoData numbers (in practice, > 1000) to 0.001
Replacer = lambda x: 0.001 if x>1000 else x
for Col in Mdf.columns:
    Mdf[Col] = Mdf[Col].map(Replacer)

# Write out Mdf to csv
Mdf.to_csv(path_or_buf=(DirectoryConcat + 'Rainf_WFDE5_CRU+GPCC_2000-2010_v2.1_ClipConcat.csv'))







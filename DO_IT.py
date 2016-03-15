# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 02:27:52 2016

@author: Rdebbout
"""
import sys
import os
import arcpy
from arcpy.sa import ExtractValuesToPoints
import pandas as pd
import pysal as ps
from collections import OrderedDict
import geopandas as gpd
sys.path.append('D:/Projects/Scipts')
from StreamCat_functions import dbf2DF

class LicenseError(Exception):
    pass

inputs = OrderedDict([('10U', 'MS'), ('10L', 'MS'), ('07', 'MS'), ('11', 'MS'), ('06', 'MS'),
                      ('05', 'MS'), ('08', 'MS'), ('01', 'NE'), ('02', 'MA'), ('03N', 'SA'),
                      ('03S', 'SA'), ('03W', 'SA'), ('04', 'GL'), ('09', 'SR'), ('12', 'TX'),
                      ('13', 'RG'), ('14', 'CO'), ('15', 'CO'), ('16', 'GB'), ('17', 'PN'),
                      ('18', 'CA')])
                      
NHD_dir = 'C:/Users/Rdebbout/temp/NHDPlusV21'
point_dir = 'D:\Projects\splitCatAuto\pracSplits.shp'  #   sys.argv[1]
natcat = NHD_dir + '/NHDPlusNationalData/nationalcat'
wd = '/'.join(point_dir.split('\\')[:-1])
try:
    if arcpy.CheckExtension("spatial") == "Available":
        arcpy.CheckOutExtension("spatial")
    else:
        raise LicenseError
        
    ExtractValuesToPoints (point_dir, natcat, '%s/gridded.shp' % wd, '', 'ALL')

    arcpy.CheckInExtension("spatial")
except LicenseError:
    print("Spatial Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
    
pts = dbf2DF('%s/gridded.dbf' % wd)
codes = tuple(pts.RASTERVALU.values)

template = catchment = NHD_dir + "/NHDPlusSR/NHDPlus09/NHDPlusCatchment/Catchment.shp"
spatial_reference = arcpy.Describe(template).spatialReference
arcpy.CreateFeatureclass_management(wd, 'cats.shp', "POLYGON", template, "DISABLED", "DISABLED", spatial_reference)


tots = []
for zone in inputs:
    hydroregion = inputs[zone]
    catchment = NHD_dir + "/NHDPlus%s/NHDPlus%s/NHDPlusCatchment/Catchment.shp"%(hydroregion, zone)
    lr = arcpy.MakeFeatureLayer_management(catchment, "lyr_%s" % zone)    
    arcpy.SelectLayerByAttribute_management(lr, "NEW_SELECTION", ' "GRIDCODE" IN %s ' % str(codes)) 
    arcpy.CopyFeatures_management("lyr_%s" % zone, "%s/%s.shp" % (wd, zone))
    tots.append("%s/%s.shp" % (wd, zone))    
arcpy.Append_management(tots, "%s/cats.shp" % wd, "TEST","","")
for f in tots:
    arcpy.Delete_management(f)

os.mkdir("%s/pour_points/" % (wd)) 
arcpy.MakeFeatureLayer_management("%s/pour_points/site_%s.shp" % (wd, str(pt)), "pt__%s" % pt)
   
sitesCursor = arcpy.SearchCursor("%s/gridded.shp" % wd)
siteRow = sitesCursor.next()
while siteRow:
    pt = siteRow.getValue("PID")  # Get unique field!
    arcpy.Select_analysis("%s/gridded.shp" % wd, "%s/pour_points/site_%s.shp" % (wd, str(pt)), '"PID" = %s ' % pt)
    arcpy.SelectLayerByLocation_management ("pt__%s" % pt, "WITHIN", "%s/NHDPlusGlobalData/BoundaryUnit.shp" % (NHD_dir))
    desc = arcpy.Describe("pt__%s" % pt)
    for t in desc.fields:
        print t.name
        
    
    siteRow = sitesCursor.next()
    
    
    
    #os.mkdir("%s/watersheds/ws%s" % (wd, str(pt)))
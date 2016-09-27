# coding=utf-8
import arcpy
import sys

def addLayer(layer):

    #if arcpy.AddMessage(sys.executable)

    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataFrame = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    newlayer = arcpy.mapping.Layer(layer)
    arcpy.mapping.AddLayer(dataFrame, newlayer, "TOP")
    arcpy.RefreshActiveView()
    arcpy.RefreshTOC()

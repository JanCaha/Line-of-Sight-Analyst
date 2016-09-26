# coding=utf-8
import arcpy


def addLayer(layer):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    dataFrame = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    newlayer = arcpy.mapping.Layer(layer)
    #existing_layers = [layer1.dataSource for layer1 in arcpy.mapping.ListLayers(mxd, "*", dataFrame)]

    #arcpy.AddMessage(layer)
    #for extLay in existing_layers:
    #    arcpy.AddMessage(extLay)

    #if layer not in existing_layers:
    arcpy.mapping.AddLayer(dataFrame, newlayer, "TOP")
    arcpy.RefreshActiveView()
    arcpy.RefreshTOC()

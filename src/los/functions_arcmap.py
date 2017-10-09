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


def prepareDataColumns(data, columns_list):
    fieldObjList = arcpy.ListFields(data)
    fieldNameList = []
    for field in fieldObjList:
        if not field.required:
            fieldNameList.append(field.name)

    for field in columns_list:
        if any(field[0] in s for s in fieldNameList):
            arcpy.DeleteField_management(data, field[0])

        arcpy.AddField_management(data, field[0], field[2], field_alias=field[1])
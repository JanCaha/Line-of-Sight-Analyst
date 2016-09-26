# coding=utf-8
import arcpy
import os

def fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, paramNo, layer, fieldType, fieldName):

    if not parameters[paramNo].altered:

        fieldsLayer = arcpy.Describe(layer).fields

        fieldsWithType = findFieldsByType(layer, fieldType, fields=fieldsLayer)

        parameters[paramNo].filter.type = "ValueList"
        parameters[paramNo].filter.list = fieldsWithType
        if checkIfFieldExists(layer, fieldName, fields=fieldsLayer):
            parameters[paramNo].value = fieldName


def checkIfFieldExists(layer, fieldName, fields = None):
    if fields == None:
        fields = {x.name for x in arcpy.Describe(layer).fields}
    else:
        fields = {x.name for x in fields}

    if fieldName in fields:
        return True
    else:
        return False


def findFieldsByType(layer, fieldType, fields = None):
    if fields == None:
        fields = {x for x in arcpy.Describe(layer).fields}

    names = []
    for i in range(0, len(fields)):
        if fields[i].type == fieldType:
         names.append(fields[i].name)
    return names


def uniqueValues(table, field):
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor})


def getPath(data):
    workspace = os.path.dirname(data)
    if [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(workspace)]:
        return workspace
    else:
        return os.path.dirname(workspace)


def checkProjected(params, paramNo):
    if params[paramNo].value:
        if arcpy.Describe(params[paramNo].value).spatialReference.type != "Projected":
            params[paramNo].setErrorMessage(
                "Layer - {0} - is not in Projected Coordinate System. The calculation cannot be done properly.".format(
                    params[paramNo].valueAsText))
        else:
            params[paramNo].clearMessage()


def enableParamIfPoint(params, paramNo, paramNoEnabled):
    if params[paramNo].value:
        if arcpy.Describe(params[paramNo].value).shapeType != "Point":
            params[paramNoEnabled].enabled = 0
        else:
            params[paramNoEnabled].enabled = 1


def enableParamIfLine(params, paramNo, paramNoEnabled):
    if params[paramNo].value:
        if arcpy.Describe(params[paramNo].value).shapeType != "Polyline":
            params[paramNoEnabled].enabled = 0
        else:
            params[paramNoEnabled].enabled = 1

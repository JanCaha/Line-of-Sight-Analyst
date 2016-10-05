# coding=utf-8
import math
import os
import arcpy
import numpy as np
import functions_validation as fv
import functions_visibility as visibility
from los import functions_arcmap

class OptimizePointsLocation(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Optimize Point Location"
        self.description = "A tool for finding highest raster value in defined neighborhood and optimizing point location. "
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param1 = arcpy.Parameter(
            displayName="Optimization raster",
            name="in_surface",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param0 = arcpy.Parameter(
            displayName="Points to be optimized",
            name="in_points_optimize",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Point"]

        param2 = arcpy.Parameter(
            displayName="Distance for searching",
            name="in_distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        param2.value = 50

        param3 = arcpy.Parameter(
            displayName="Optimized points",
            name="in_optimized_points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        param4 = arcpy.Parameter(
            displayName="Use mask?",
            name="in_use_mask",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param4.value = False

        param5 = arcpy.Parameter(
            displayName="Mask",
            name="in_mask",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input")
        param5.enabled = False

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        if parameters[4].value == True:
            parameters[5].enabled = True
            parameters[5].parameterType = "Required"
        else:
            parameters[5].enabled = False
            parameters[5].parameterType = "Optional"

        if parameters[0].value and not parameters[3].altered:
            desc = arcpy.Describe(parameters[0].valueAsText)
            parameters[3].value = os.path.dirname(desc.catalogPath) + "\\" + desc.name + "_optimized"

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        fv.checkProjected(parameters, 0)

        if parameters[4].value == True and not parameters[5].value:
            parameters[5].setErrorMessage("Mask layer must be set!")
        else:
            parameters[5].clearMessage()
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        points_to_optimize = parameters[0].valueAsText
        raster = parameters[1].valueAsText
        distance = parameters[2].value
        optimized_points = parameters[3].valueAsText
        useMask = parameters[4].value

        if useMask:
            mask = parameters[5].valueAsText

        inRas = arcpy.Raster(raster)

        if useMask:
            maskRas = arcpy.Raster(mask)
            maskNoData = maskRas.noDataValue

        cellSize = inRas.meanCellWidth
        distanceCells = distance / cellSize

        noDataValue = inRas.noDataValue


        spatial_ref = arcpy.Describe(points_to_optimize).spatialReference
        arcpy.CopyFeatures_management(points_to_optimize, optimized_points)

        newPoint = arcpy.Point()

        number_of_points = int(arcpy.GetCount_management(points_to_optimize).getOutput(0))
        arcpy.SetProgressor("step", "Updating location of points", 0, number_of_points, 1)

        with arcpy.da.UpdateCursor(optimized_points, ["SHAPE@XY", "SHAPE@"]) as cursor:
            for row in cursor:

                array = arcpy.RasterToNumPyArray(inRas, arcpy.Point(row[0][0] - distance, row[0][1] - distance),
                                                 distanceCells * 2, distanceCells * 2, noDataValue)

                maxValue = noDataValue
                maxX = row[0][0]
                maxY = row[0][1]

                for i in range(0, len(array)):
                    for j in range(0, len(array[0])):
                        x = row[0][0] + (j - distanceCells) * cellSize
                        y = row[0][1] - (i - distanceCells) * cellSize

                        if useMask:
                            maskValue = arcpy.RasterToNumPyArray(maskRas, arcpy.Point(x, y), 1, 1, maskNoData)

                        if array[i][j] > maxValue and array[i][j] != noDataValue and \
                                        visibility.distance(row[0][0], row[0][1], x, y) < distance:
                            if useMask:
                                if maskValue[0][0] > 0:
                                    maxValue = array[i][j]
                                    maxX = x
                                    maxY = y
                            else:
                                maxValue = array[i][j]
                                maxX = x
                                maxY = y

                newPoint.X = maxX
                newPoint.Y = maxY
                row[1] = arcpy.PointGeometry(newPoint)
                cursor.updateRow(row)
                arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()
        functions_arcmap.addLayer(optimized_points)
        return
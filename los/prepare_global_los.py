# coding=utf-8
import math

import arcpy

import functions_validation as fv
import functions_visibility as visibility
from los import functions_arcmap

class PrepareGlobalLoS(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Global Lines of Sight"
        self.description = "A tool to create Lines of Sight from observer to target points and further beyond target " \
                           "points to the spatial extent of the surface layer. This is necessary to analyze targets " \
                           "relation to the global horizon. The shapefile itself does not store information about " \
                           "observer's and target's offsets. This information is stored in appropriate fields."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Surface",
            name="in_surface",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Observer points",
            name="in_observers",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param1.filter.list = ["Point"]

        param2 = arcpy.Parameter(
            displayName="Observer points offset",
            name="in_observer_offset",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param2.filter.list = ["Double"]
        param2.parameterDependencies = [param1.name]
        param2.enabled = 0

        param3 = arcpy.Parameter(
            displayName="Target points",
            name="in_targets",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param3.filter.list = ["Point"]

        param4 = arcpy.Parameter(
            displayName="Target points offset",
            name="in_target_offset",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param4.filter.list = ["Double"]
        param4.parameterDependencies = [param3.name]
        param4.enabled = 0

        param5 = arcpy.Parameter(
            displayName="Sampling distance",
            name="in_sampling_distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        # param5.value = 0

        param6 = arcpy.Parameter(
            displayName="Output feature layer",
            name="in_output_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="output")

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        if arcpy.CheckOutExtension("spatial") == "CheckedOut" and arcpy.CheckOutExtension("3D") == "CheckedOut":
            return True
        else:
            return False

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        fv.enableParamIfPoint(parameters, 1, 2)
        fv.enableParamIfPoint(parameters, 3, 4)

        if not parameters[6].value:
            parameters[6].value = str(arcpy.env.workspace) + "\\Global_LoS"

        if parameters[0].value and not parameters[5].altered:
            parameters[5].value = str(arcpy.Describe(parameters[0].valueAsText).meanCellHeight)
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        fv.checkProjected(parameters, 1)
        fv.checkProjected(parameters, 3)
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        surface = parameters[0].valueAsText
        observer_points = parameters[1].valueAsText
        observer_offset = parameters[2].valueAsText
        target_points = parameters[3].valueAsText
        target_offset = parameters[4].valueAsText
        sampling_distance = parameters[5].valueAsText
        output_los = parameters[6].valueAsText

        sightlines = arcpy.ConstructSightLines_3d(observer_points, target_points,
                                                  arcpy.CreateScratchName(prefix="sightlines",
                                                                          workspace=arcpy.env.scratchGDB),
                                                  observer_offset, target_offset, "<None>", 1,
                                                  "NOT_OUTPUT_THE_DIRECTION")

        raster_extent = arcpy.sa.Raster(surface).extent

        maximal_possible_distance = math.sqrt(
            math.pow(max(raster_extent.XMax - raster_extent.XMin, raster_extent.YMax - raster_extent.YMin), 2) * 2)

        spatial_ref = arcpy.Describe(sightlines).spatialReference

        visibility.makeGlobalLoS(sightlines, maximal_possible_distance, spatial_ref)

        arcpy.AddField_management(sightlines, "ID_OBSERV", "LONG")
        arcpy.CalculateField_management(sightlines, "ID_OBSERV", "!OID_OBSERV!", "PYTHON")
        arcpy.AddField_management(sightlines, "ID_TARGET", "LONG")
        arcpy.CalculateField_management(sightlines, "ID_TARGET", "!OID_TARGET!", "PYTHON")
        arcpy.DeleteField_management(sightlines, ["OID_TARGET", "OID_OBSERV"])

        temp_los_name = arcpy.CreateScratchName(prefix="los", workspace=arcpy.env.scratchGDB)

        arcpy.InterpolateShape_3d(surface, sightlines, temp_los_name, sample_distance=sampling_distance, method="BILINEAR")

        visibility.updateLoS(temp_los_name, output_los, sightlines, target_points, True)

        arcpy.DeleteField_management(output_los, "SourceOID")

        visibility.verifyShapeStructure(sightlines, output_los)

        functions_arcmap.addLayer(output_los)
        return


# coding=utf-8
import arcpy

import functions_validation as fv
import functions_visibility as visibility
from los import functions_arcmap


class PrepareLoS(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Creation of Line of Sight"
        self.description = "A tool to create Lines of Sight between observer and target points. The shapefile itself " \
                           "does not store information about observer's and target's offsets. This information is " \
                           "stored in appropriate fields."
        self.canRunInBackground = True

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
        param5.value = 1

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
            parameters[6].value = str(arcpy.env.workspace) + "\\LoS"
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

        temp_los_name = arcpy.CreateScratchName(prefix="los", workspace=arcpy.env.scratchGDB)
        sightlines_name = arcpy.CreateScratchName(prefix="sightlines", workspace=arcpy.env.scratchGDB)

        sightlines = arcpy.ConstructSightLines_3d(observer_points, target_points, sightlines_name, observer_offset,
                                                  target_offset, "<None>", sampling_distance, "NOT_OUTPUT_THE_DIRECTION")

        arcpy.LineOfSight_3d(surface, sightlines, temp_los_name,
                             arcpy.CreateScratchName(prefix="obstcl", workspace=arcpy.env.scratchGDB))

        visibility.updateLoS(temp_los_name, output_los, sightlines, target_points, False)

        arcpy.DeleteField_management(output_los, "SourceOID")

        visibility.verifyShapeStructure(sightlines, output_los)

        functions_arcmap.addLayer(output_los)
        return

# coding=utf-8
import math

import arcpy

import functions_validation as fv
import functions_visibility as visibility
from los import functions_arcmap


class ExtractGlobalHorizons(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Extraction of Global Horizons"
        self.description = "A tool for extraction of horizons from global lines of sight."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Lines of Sight",
            name="in_los",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="ID observer",
            name="in_id_observer",
            datatype="GPString",
            #datatype="Field",
            parameterType="Required",
            direction="Input")
        #param1.filter.list = ["Integer"]
        #param1.parameterDependencies = [param0.name]
        param1.enabled = 0

        param2 = arcpy.Parameter(
            displayName="Observer points offset",
            name="in_observer_offset",
            datatype="GPString",
            # datatype="Field",
            parameterType="Required",
            direction="Input")
        #param2.filter.list = ["Double"]
        #param2.parameterDependencies = [param0.name]
        param2.enabled = 0

        param3 = arcpy.Parameter(
            displayName="ID target",
            name="in_id_target",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        #param3.filter.list = ["Integer"]
        #param3.parameterDependencies = [param0.name]
        param3.enabled = 0

        param4 = arcpy.Parameter(
            displayName="Target points offset",
            name="in_target_offset",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        #param4.filter.list = ["Double"]
        #param4.parameterDependencies = [param0.name]
        param4.enabled = 0

        param5 = arcpy.Parameter(
            displayName="Target points X coordinate",
            name="in_target_x",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        #param5.filter.list = ["Double"]
        #param5.parameterDependencies = [param0.name]
        param5.enabled = 0

        param6 = arcpy.Parameter(
            displayName="Target points Y coordinate",
            name="in_target_y",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        #param6.filter.list = ["Double"]
        #param6.parameterDependencies = [param0.name]
        param6.enabled = 0

        param7 = arcpy.Parameter(
            displayName="Output feature layer",
            name="in_output_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="output")

        params = [param0, param1, param2, param3, param4, param5, param6, param7]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        fv.enableParamIfLine(parameters, 0, 1)
        fv.enableParamIfLine(parameters, 0, 2)
        fv.enableParamIfLine(parameters, 0, 3)
        fv.enableParamIfLine(parameters, 0, 4)
        fv.enableParamIfLine(parameters, 0, 5)
        fv.enableParamIfLine(parameters, 0, 6)

        if not parameters[7].value:
            parameters[7].value = str(arcpy.env.workspace) + "\\Global_Horizons"

        if parameters[0].value:
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 1, parameters[0].valueAsText,
                                                           "SmallInteger", "OID_OBSERV")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 2, parameters[0].valueAsText,
                                                           "Double", "observ_offset")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 3, parameters[0].valueAsText,
                                                           "SmallInteger", "OID_TARGET")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 4, parameters[0].valueAsText,
                                                           "Double", "target_offset")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 5, parameters[0].valueAsText,
                                                           "Double", "target_x")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 6, parameters[0].valueAsText,
                                                           "Double", "target_y")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        fv.checkProjected(parameters, 0)

        if parameters[0].value:
            message = "The input layer does not have fields typical for Global Sight Line. This analysis should be performed on " \
                      "Global Sight Lines. Are you sure you want to proceed?"
            fieldnames = [field.name for field in arcpy.ListFields(parameters[0].value)]

            if "target_x" not in fieldnames and "target_y" not in fieldnames:
                parameters[5].setWarningMessage(message)
                parameters[6].setWarningMessage(message)
            else:
                parameters[5].clearMessage()
                parameters[6].clearMessage()

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        visibility_lines = parameters[0].valueAsText
        id_observer_field = parameters[1].valueAsText
        observer_offset_field = parameters[2].valueAsText
        id_target_field = parameters[3].valueAsText
        target_offset_field = parameters[4].valueAsText
        target_x_field = parameters[5].valueAsText
        target_y_field = parameters[6].valueAsText
        horizons = parameters[7].valueAsText

        workspace = fv.getPath(horizons)

        file_name = horizons.replace(workspace + "\\", "")

        arcpy.CreateFeatureclass_management(workspace, file_name, "POINT", has_z="ENABLED",
                                            spatial_reference=arcpy.Describe(visibility_lines).spatialReference)

        field_list = [id_observer_field, id_target_field, "Elevation", "Hor_Type", "Hide_Tar", "ViewAngle",
                      "AngleDiff_Tar", "Dist_Observ", "Behind_Tar" ,"OID_LoS"]

        self.prepareDataColumns(horizons, field_list, id_observer_field, id_target_field)

        arcpy.AddMessage("\t Determination of horizons started...")

        insert_cursor = arcpy.da.InsertCursor(horizons, ["SHAPE@"] + field_list)

        number_of_LoS = int(arcpy.GetCount_management(visibility_lines).getOutput(0))
        arcpy.SetProgressor("step", "Analyzing " + str(number_of_LoS) + " lines of sight...", 0, number_of_LoS, 1)

        with arcpy.da.SearchCursor(visibility_lines,
                                   ["OBJECTID", "SHAPE@", id_observer_field, id_target_field, observer_offset_field,
                                    target_offset_field, target_x_field, target_y_field]) as cursor:
            for row in cursor:

                target_x = row[6]
                target_y = row[7]
                target_offset = row[5]

                points = []
                wkt = row[1].WKT.replace("))", "").replace(" ((", "").replace("MULTILINESTRING ", "") \
                    .replace("ZM", "").replace("Z", "").replace("), (", ", ")

                poi = wkt.split(", ")
                # get coordinates of first point for distance calculation
                start_point_x = float(poi[0].split(" ")[0])
                start_point_y = float(poi[0].split(" ")[1])
                observer_elev = float(poi[0].split(" ")[2]) + float(row[4])

                target_distance = visibility.distance(target_x, target_y, start_point_x, start_point_y)
                sampling_distance = visibility.distance(float(poi[1].split(" ")[0]), float(poi[1].split(" ")[1]),
                                                        start_point_x, start_point_y)
                target_index = -1

                # for every point do this
                for i in range(0, len(poi)):
                    parts = poi[i].split(" ")
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                    dist = visibility.distance(x, y, start_point_x, start_point_y)
                    if i == 0:
                        points.append([x, y, 0, observer_elev, -90])
                    elif math.fabs(target_distance - dist) < sampling_distance / 2:
                        points.append(
                            [x, y, dist, z + target_offset, visibility.angle(dist, z + target_offset - observer_elev)])
                        target_index = i
                    else:
                        points.append([x, y, dist, z, visibility.angle(dist, z - observer_elev)])

                results = visibility.findGlobalHorizons(points, target_index)

                point = arcpy.Point()

                for i in range(0, len(results)):
                    hor_type = 0
                    point.X = results[i][0]
                    point.Y = results[i][1]
                    point.Z = results[i][3]
                    ptGeometry = arcpy.PointGeometry(point)
                    if i == len(results) - 1:
                        hor_type = 1

                    insert_cursor.insertRow([ptGeometry, row[2], row[3], results[i][3], hor_type,
                                             results[i][5], results[i][4], results[i][6], results[i][2], results[i][7], row[0]])

                arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()
        arcpy.AddMessage("\t Determination of horizons sucessfuly ended.")

        functions_arcmap.addLayer(horizons)
        return

    def prepareDataColumns(self, data, columns_list, id_observer_field, id_target_field):
        fieldObjList = arcpy.ListFields(data)
        fieldNameList = []
        for field in fieldObjList:
            if not field.required:
                fieldNameList.append(field.name)

        for field_vis in columns_list:
            if any(field_vis in s for s in fieldNameList):
                arcpy.DeleteField_management(data, field_vis)
            if field_vis == "OID_LoS" or field_vis == "Hor_Type" or field_vis == "Hide_Tar" \
                    or field_vis == id_observer_field  or field_vis == id_target_field:
                arcpy.AddField_management(data, field_vis, "SHORT")
            else:
                arcpy.AddField_management(data, field_vis, "DOUBLE")
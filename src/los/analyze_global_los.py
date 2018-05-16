# coding=utf-8
import math
import arcpy
import functions_validation as fv
import functions_visibility as visibility
import functions_arcmap as farcmap


class AnalyseGlobalLoS(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Analyse Global Lines of Sight"
        self.description = "A tool for analysing Lines of Sight between observer and points behind target points."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Global Lines of Sight",
            name="in_los",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ["Polyline"]

        param1 = arcpy.Parameter(
            displayName="Observer points offset",
            name="in_observer_offset",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        # param1.filter.list = ["Double"]
        # param1.parameterDependencies = [param0.name]
        param1.enabled = 0

        param2 = arcpy.Parameter(
            displayName="Target points offset",
            name="in_target_offset",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        # param2.filter.list = ["Double"]
        # param2.parameterDependencies = [param0.name]
        param2.enabled = 0

        param3 = arcpy.Parameter(
            displayName="Target points X coordinate",
            name="in_target_x",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        # param3.filter.list = ["Double"]
        # param3.parameterDependencies = [param0.name]
        param3.enabled = 0

        param4 = arcpy.Parameter(
            displayName="Target points Y coordinate",
            name="in_target_y",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        # param4.filter.list = ["Double"]
        # param4.parameterDependencies = [param0.name]
        param4.enabled = 0

        param5 = arcpy.Parameter(
            displayName="Use earth curvature and refraction corrections?",
            name="in_use_curvature",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input",
            category="Curvature corrections")
        param5.value = True

        param6 = arcpy.Parameter(
            displayName="Refractivity coefficient ",
            name="in_ref_coeff",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
            category="Curvature corrections")
        param6.value = 0.13

        params = [param0, param1, param2, param3, param4, param5, param6]
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

        if parameters[0].value:
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 1, parameters[0].valueAsText,
                                                           "Double", "observ_offset")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 2, parameters[0].valueAsText,
                                                           "Double", "target_offset")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 3, parameters[0].valueAsText,
                                                           "Double", "target_x")
            fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 4, parameters[0].valueAsText,
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
                parameters[3].setWarningMessage(message)
                parameters[4].setWarningMessage(message)
            else:
                parameters[3].clearMessage()
                parameters[4].clearMessage()
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        visibility_lines = parameters[0].valueAsText
        observer_offset_field = parameters[1].valueAsText
        target_offset_field = parameters[2].valueAsText
        target_x_field = parameters[3].valueAsText
        target_y_field = parameters[4].valueAsText

        useCurvatures = parameters[5].value
        refCoeff = parameters[6].value

        fieldsNew = [("Visible", "Visibility of target", "SHORT"),
                     ("AngleDiff_GH", "Angle difference of target to global horizon", "DOUBLE"),
                     ("ElevDiff_GH", "Elevation difference of target to global horizon", "DOUBLE"),
                     ("HorDist", "Distance of horizon from target point", "DOUBLE"),
                     ("Horizon_C", "Horizon count behind target point", "SHORT")]

        fieldsNames = [row[0] for row in fieldsNew]

        columns = ["OBJECTID", "SHAPE@"] + [observer_offset_field, target_offset_field, target_x_field, target_y_field]

        farcmap.prepareDataColumns(visibility_lines, fieldsNew)

        number_of_LoS = int(arcpy.GetCount_management(visibility_lines).getOutput(0))

        arcpy.SetProgressor("step", "Analyzing " + str(number_of_LoS) + " lines of sight...", 0, number_of_LoS, 1)

        with arcpy.da.UpdateCursor(visibility_lines, columns + fieldsNames) as cursor:
            for row in cursor:

                points = []
                poi = visibility.WKTtoPoints(row[1].WKT)
                # get coordinates of first point for distance calculation

                observer_offset = row[2]
                target_offset = row[3]
                target_x = row[4]
                target_y = row[5]

                start_point_x = float(poi[0].split(" ")[0])
                start_point_y = float(poi[0].split(" ")[1])
                observer_elev = float(poi[0].split(" ")[2]) +  observer_offset

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

                    if useCurvatures:
                        z = visibility.curvatureCorrections(z, dist, refCoeff)

                    if i == 0:
                        points.append([x, y, 0, observer_elev, -90])
                    elif math.fabs(target_distance - dist) < sampling_distance/2:
                        points.append([x, y, dist, z + target_offset, visibility.angle(dist, z + target_offset - observer_elev)])
                        target_index = i
                    else:
                        points.append([x, y, dist, z, visibility.angle(dist, z - observer_elev)])

                results = self.analyzeLoS(points, target_index)
                for i in range(0, len(results)):
                    row[i + 6] = results[i]
                cursor.updateRow(row)
                arcpy.SetProgressorPosition()

        arcpy.ResetProgressor()

        return

    def analyzeLoS(self, points, target_index):

        limit_angle = points[target_index][4]
        isVisible = 1
        max_angle_horizon = - 180
        elev_difference_horizon = None
        angle_difference_horizon = None

        horizon_count = 0
        horizon_distance = 0
        horizon_index = 0

        for i in range(1, len(points) - 1):
            if not i == target_index:
                if points[i][4] > limit_angle and points[i][2] < points[target_index][2]:
                    isVisible = 0
                if visibility.isHorizon(points, i, 4, points[len(points) - 1][4]) and points[i][4] > max_angle_horizon:
                    max_angle_horizon = points[i][4]
                    horizon_distance = points[i][2] - points[target_index][2]
                    horizon_index = i
                    if points[i][2] > points[target_index][2] and points[i][4] > points[target_index][4]:
                        horizon_count += 1

        elev_difference_horizon = points[target_index][3] - (points[0][3] + math.tan(math.radians(points[horizon_index][4]))*points[target_index][2])


        angle_difference_horizon = limit_angle - max_angle_horizon

        return [isVisible, angle_difference_horizon, elev_difference_horizon, horizon_distance, horizon_count]



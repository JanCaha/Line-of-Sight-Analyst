# coding=utf-8
import math

import arcpy

import functions_validation as fv
import functions_visibility as visibility
import functions_arcmap

class ExportLoS(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export of Line of Sight into CSV"
        self.description = "A tool for export of Line of Sight into CSV (comma-separated values)."
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
            displayName="Line of Sight ID",
            name="in_id",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")
        param1.enabled = False

        param2 = arcpy.Parameter(
            displayName="Output file",
            name="out_file",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["csv"]
        param2.enabled = False

        param3 = arcpy.Parameter(
            displayName="Include offsets?",
            name="in_include_offsets",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param3.value = True

        param4 = arcpy.Parameter(
            displayName="Global Line of Sight?",
            name="in_global_los",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param4.value = False

        param5 = arcpy.Parameter(
            displayName="Observer point offset",
            name="in_observer_offset",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Offsets")
        param5.enabled = False

        param6 = arcpy.Parameter(
            displayName="Target point offset",
            name="in_target_offset",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Offsets")
        param6.enabled = False

        param7 = arcpy.Parameter(
            displayName="Target point X coordinate",
            name="in_target_x",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Global Line of Sight")
        param7.enabled = False

        param8 = arcpy.Parameter(
            displayName="Target point Y coordinate",
            name="in_target_y",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Global Line of Sight")
        param8.enabled = False

        params = [param0, param1, param2 ,param3, param4, param5, param6, param7, param8]
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

        if parameters[3].value == True:
            parameters[5].enabled = 1
            parameters[6].enabled = 1
            parameters[5].parameterType = "Required"
            parameters[6].parameterType = "Required"
        else:
            parameters[5].enabled = 0
            parameters[6].enabled = 0
            parameters[5].parameterType = "Optional"
            parameters[6].parameterType = "Optional"


        if parameters[4].value == True:
            parameters[7].enabled = 1
            parameters[8].enabled = 1
            parameters[7].parameterType = "Required"
            parameters[8].parameterType = "Required"
        else:
            parameters[7].enabled = 0
            parameters[8].enabled = 0
            parameters[7].parameterType = "Optional"
            parameters[8].parameterType = "Optional"

        if parameters[0].value:
            parameters[1].filter.type = "ValueList"
            parameters[1].filter.list = fv.uniqueValues(parameters[0].valueAsText, "OBJECTID")

        if parameters[0].value:
            if parameters[3].value == True:
                fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 5, parameters[0].valueAsText,
                                                               "Double", "observ_offset")
                fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 6, parameters[0].valueAsText,
                                                               "Double", "target_offset")
            if parameters[4].value == True:
                fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 7, parameters[0].valueAsText,
                                                               "Double", "target_x")
                fv.fillParamaterWithFieldTypeAndDefaultFieldIfExists(parameters, 8, parameters[0].valueAsText,
                                                               "Double", "target_y")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        fv.checkProjected(parameters, 0)

        if parameters[0].value:
            field = "OBJECTID"
            fieldnames = [field.name for field in arcpy.ListFields(parameters[0].valueAsText)]
            if field in fieldnames:
                parameters[0].clearMessage()
            else:
                parameters[0].setErrorMessage("Field OBJECTID not found in the layer. The field is necessary for "
                                              "proper function of this tool.")

        if parameters[0].value and parameters[4].value == False:
            fieldnames = [field.name for field in arcpy.ListFields(parameters[0].valueAsText)]

            if "target_x" in fieldnames and "target_y" in fieldnames:
                parameters[4].setWarningMessage("The input layer has fields typical for Global Sight Line, if you want"
                                                " to correctly export Global Line of Sight please check this button.")
            else:
                parameters[4].clearMessage()

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        visibility_lines = parameters[0].valueAsText
        id_los = parameters[1].valueAsText
        output_file = parameters[2].valueAsText

        include_offsets = parameters[3].value
        global_los =  parameters[4].value

        observer_offset_field = parameters[5].valueAsText
        target_offset_field = parameters[6].valueAsText
        target_x_field = parameters[7].valueAsText
        target_y_field = parameters[8].valueAsText

        delimiter = ";"
        end_of_line = "\n"

        strings = []

        fields = ["OBJECTID", "SHAPE@"]

        if include_offsets:
            fields = fields + [observer_offset_field, target_offset_field]

        if global_los:
            fields = fields + [target_x_field, target_y_field]

        with arcpy.da.SearchCursor(visibility_lines, fields,
                                   """"OBJECTID" = """ + str(id_los)) as cursor_sightline:

            for row_sightline in cursor_sightline:
                points = []
                # get geometry as WKT and remove beginning and ending
                wkt = row_sightline[1].WKT.replace("))", "").replace(" ((", "").replace("MULTILINESTRING ", "") \
                    .replace("ZM", "").replace("Z", "").replace("), (", ", ")
                # split WKT of line into points
                poi = wkt.split(", ")
                # get coordinates of first point for distance calculation

                #observer_offset = row[2]
                #target_offset = row[3]

                start_point_x = float(poi[0].split(" ")[0])
                start_point_y = float(poi[0].split(" ")[1])
                #observer_elev = float(poi[0].split(" ")[2]) + observer_offset

                sampling_distance = visibility.distance(float(poi[1].split(" ")[0]), float(poi[1].split(" ")[1]),
                                                        start_point_x, start_point_y)

                # for every point do this

                distance_observer_target = 0
                if global_los:
                    distance_observer_target = visibility.distance(start_point_x, start_point_y,
                                       row_sightline[cursor_sightline.fields.index(target_x_field)],
                                       row_sightline[cursor_sightline.fields.index(target_y_field)])

                strings.append("\"distance\"")
                strings.append(delimiter)
                strings.append("\"elevation\"")
                if global_los:
                    strings.append(delimiter)
                    strings.append("\"target point\"")
                strings.append(end_of_line)

                isTargetPoint = 0

                for i in range(0, len(poi)):
                    parts = poi[i].split(" ")
                    x = float(parts[0])
                    y = float(parts[1])

                    if include_offsets:
                        if i == 0:
                            z = float(parts[2]) + float(row_sightline[cursor_sightline.fields.index(observer_offset_field)])
                        elif i == len(poi)-1 and not global_los:
                            z = float(parts[2]) + float(row_sightline[cursor_sightline.fields.index(target_offset_field)])
                        else:
                            z = float(parts[2])
                    else:
                        z = float(parts[2])

                    dist = visibility.distance(x, y, start_point_x, start_point_y)

                    if global_los and include_offsets and math.fabs(distance_observer_target-dist) < sampling_distance/2:
                        z += float(row_sightline[cursor_sightline.fields.index(target_offset_field)])
                        isTargetPoint = 1
                    else:
                        isTargetPoint = 0

                    strings.append(str(dist))
                    strings.append(delimiter)
                    strings.append(str(z))
                    if global_los:
                        strings.append(delimiter)
                        strings.append(str(isTargetPoint))

                    strings.append(end_of_line)

        complete_string = "".join(strings)

        with open(output_file, 'w') as file:
            file.write(complete_string)
            file.close()

        return

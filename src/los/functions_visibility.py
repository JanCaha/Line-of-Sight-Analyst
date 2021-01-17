# coding=utf-8
import math
import arcpy
from operator import itemgetter

def fuzzyVisibility(dist, b1, beta, h):
    b2 = h / ( 2 * math.tan(beta/2))
    if dist < b1:
        return 1
    else:
        return 1/(1 + math.pow((dist-b1)/b2, 2))

def isHorizon(points, i, ANG,limit_angle):
    if i < len(points)-2:
        return testHorizon(points[i][ANG], points[i+1][ANG])
    elif i == len(points)-2:
        return testHorizon(points[i][ANG], limit_angle)

def testHorizon(angle_closer, angle_distant):
    if angle_closer > angle_distant:
        return True
    else:
        return False


def angle(dist, elev_diff):
    return math.degrees(math.atan(elev_diff/dist))


def distance(x1, y1, x2, y2):
    return math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))


def WKTtoPoints(wkt):
    return wkt.replace("))", "").replace(" ((", "").replace("MULTILINESTRING ", "").replace("ZM","").replace("Z", "").replace("), (", ", ").split(", ")


def curvatureCorrections(elev, dist, refCoeff):
    earthDiam = 12740000
    return elev - (math.pow(dist, 2)/earthDiam) + refCoeff * (math.pow(dist, 2)/earthDiam)


# updates resulting LoS with necessary fields
def updateLoS(los_temp, los_final, sightlines, target_points, isGlobal):

    arcpy.Copy_management(los_temp, los_final)

    arcpy.AddField_management(los_final, "observ_offset", "DOUBLE")
    arcpy.AddField_management(los_final, "target_offset", "DOUBLE")

    fieldList = ["OBJECTID", "observ_offset", "target_offset", "SHAPE@"]
    if isGlobal:
        arcpy.AddField_management(los_final, "target_x", "DOUBLE")
        arcpy.AddField_management(los_final, "target_y", "DOUBLE")
        fieldList = fieldList + ["target_x", "target_y"]

    id_sightlines = arcpy.Describe(sightlines).OIDFieldName
    id_target_points = arcpy.Describe(target_points).OIDFieldName

    with arcpy.da.UpdateCursor(los_final, fieldList) as cursor_LoS:
        for row_LoS in cursor_LoS:

            with arcpy.da.SearchCursor(sightlines, [id_sightlines, "SHAPE@", "ID_OBSERV", "ID_TARGET"],
                                       id_sightlines + " = " + str(row_LoS[0])) as cursor:
                for row in cursor:
                    row_LoS[1] = row[1].firstPoint.Z
                    row_LoS[2] = row[1].lastPoint.Z

            if isGlobal:
                with arcpy.da.SearchCursor(target_points, [id_target_points, "SHAPE@"],
                                           id_target_points + " = " + str(row[3])) as cursor_target:
                    for row_target in cursor_target:
                        row_LoS[4] = row_target[1].lastPoint.X
                        row_LoS[5] = row_target[1].lastPoint.Y

            cursor_LoS.updateRow(row_LoS)


# extends LoS behind the target point
def makeGlobalLoS(data, maximal_possible_distance, spatial_ref):
    number_of_LoS = int(arcpy.GetCount_management(data).getOutput(0))

    arcpy.SetProgressor("step", "Updating " + str(number_of_LoS) + " lines of sight...", 0, number_of_LoS, 1)

    start_point = arcpy.Point()
    end_point = arcpy.Point()
    polyline_array = arcpy.Array()

    mid_point = arcpy.Point()

    with arcpy.da.UpdateCursor(data, ["OID", "SHAPE@"]) as cursor:
        for row in cursor:
            start_point.X = row[1].firstPoint.X
            start_point.Y = row[1].firstPoint.Y
            start_point.Z = row[1].firstPoint.Z
            end_point.X = row[1].lastPoint.X
            end_point.Y = row[1].lastPoint.Y
            end_point.Z = row[1].lastPoint.Z

            mid_point.X = row[1].lastPoint.X
            mid_point.Y = row[1].lastPoint.Y
            mid_point.Z = row[1].lastPoint.Z

            start_pointGeometry = arcpy.PointGeometry(start_point, spatial_ref, True)
            end_pointGeometry = arcpy.PointGeometry(end_point, spatial_ref, True)

            new_end_pointGeometry = start_pointGeometry.pointFromAngleAndDistance(
                start_pointGeometry.angleAndDistanceTo(end_pointGeometry)[0], maximal_possible_distance)

            end_point.X = new_end_pointGeometry.centroid.X
            end_point.Y = new_end_pointGeometry.centroid.Y

            polyline_array.add(start_point)
            polyline_array.add(mid_point)
            polyline_array.add(end_point)

            polyline_new = arcpy.Polyline(polyline_array, spatial_ref, True)

            polyline_array.removeAll()

            row[1] = polyline_new
            cursor.updateRow(row)
            arcpy.SetProgressorPosition()

    arcpy.ResetProgressor()

#function for finding horizons between observer and target
def findLocalHorizons(points):
    limit_angle = points[len(points) - 1][4]
    horizons = []
    vis_angle = -180
    hide_target = 0
    max_horizon_angle_before = - 180
    angle_diff = 0
    for i in range(1, len(points) - 1):
        if isHorizon(points, i, 4, limit_angle) and points[i][4] > vis_angle:
            if points[i][4] > limit_angle:
                hide_target = 1
            if max_horizon_angle_before != -180:
                angle_diff = points[i][4] - max_horizon_angle_before
            horizons.append(points[i] + [hide_target, angle_diff])
            max_horizon_angle_before = points[i][4]
        if points[i][4] > vis_angle:
            vis_angle = points[i][4]

    return horizons

#function for finding horizons even after the target
def findGlobalHorizons(points, target_index):
    limit_angle = points[target_index][4]
    horizons = []
    vis_angle = -180
    hide_target = 0
    max_horizon_angle_before = - 180
    angle_diff = 0
    behind_tar = 0
    for i in range(1, len(points) - 1):
        if not i == target_index:
            if isHorizon(points, i, 4, limit_angle) and points[i][4] > vis_angle:
                if points[i][4] > limit_angle and points[i][2]<points[target_index][2]:
                    hide_target = 1
                if max_horizon_angle_before != -180:
                    angle_diff = points[i][4] - limit_angle #points[i][4] - max_horizon_angle_before
                if points[i][2]>points[target_index][2]:
                    behind_tar = 1
                horizons.append(points[i] + [hide_target, angle_diff, behind_tar])
                max_horizon_angle_before = points[i][4]
            if points[i][4] > vis_angle:
                vis_angle = points[i][4]

    points = sorted(horizons, key=itemgetter(4))

    return [points[len(points)-1]] #horizons

def verifyShapeStructure(lines_of_sight, visibility_lines):

    spatial_ref = arcpy.Describe(visibility_lines).spatialReference

    number_of_LoS = int(arcpy.GetCount_management(visibility_lines).getOutput(0))

    arcpy.SetProgressor("step", "Verifing structure of " + str(number_of_LoS) + " lines of sight...", 0, number_of_LoS, 1)

    with arcpy.da.UpdateCursor(visibility_lines, ["SHAPE@", "OBJECTID"]) as cursor:
        for row in cursor:

            with arcpy.da.SearchCursor(lines_of_sight, ["SHAPE@"], """"OID" = """ + str(row[1])) as cursor_lines:
                for row_lines in cursor_lines:
                    start_point_x = row_lines[0].firstPoint.X
                    start_point_y = row_lines[0].firstPoint.Y
                    #end_point_x = row_lines[0].lastPoint.X
                    #end_point_y = row_lines[0].lastPoint.Y

            wkt = row[0].WKT.replace("))", "").replace(" ((", "").replace("MULTILINESTRING ", "") \
                .replace("ZM", "").replace("Z", "").replace("), (", ", ")

            poi = wkt.split(", ")

            start_p_x= float(poi[0].split(" ")[0])
            start_p_y = float(poi[0].split(" ")[1])
            #end_p_x = float(poi[len(poi)-1].split(" ")[0])
            #end_p_y = float(poi[len(poi)-1].split(" ")[1])

            points = []

            if distance(start_point_x, start_point_y, start_p_x, start_p_y) > 1:

                for i in range(0, len(poi)):
                    parts = poi[i].split(" ")
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                    dist = distance(x, y, start_point_x, start_point_y)
                    points.append([x, y, z, dist])

                points = sorted(points, key=itemgetter(3))

                point = arcpy.Point()
                array = arcpy.Array()

                for i in range(0, len(poi)):
                    point.X = points[i][0]
                    point.Y = points[i][1]
                    point.Z = points[i][2]
                    array.add(point)

                polyline = arcpy.Polyline(array, spatial_ref, True)
                row[0] = polyline
                cursor.updateRow(row)
            arcpy.SetProgressorPosition()

    arcpy.ResetProgressor()
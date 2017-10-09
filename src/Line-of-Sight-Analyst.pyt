# coding=utf-8
import arcpy
from los.prepare_los import PrepareLoS
from los.prepare_global_los import PrepareGlobalLoS
from los.analyze_los import AnalyseLoS
from los.analyze_global_los import AnalyseGlobalLoS
from los.extract_horizons import ExtractLocalHorizons
from los.extract_global_horizons import ExtractGlobalHorizons
from los.export_los import ExportLoS
from los.optimize_point_location import OptimizePointsLocation

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Line of Sight Analyst"
        self.alias = "losAnalyst"

        # List of tool classes associated with this toolbox
        self.tools = [PrepareLoS, PrepareGlobalLoS, AnalyseLoS, AnalyseGlobalLoS, ExtractLocalHorizons, ExtractGlobalHorizons, ExportLoS, OptimizePointsLocation]
# coding=utf-8
import arcpy
from los.prepare_los import PrepareLoS
from los.prepare_global_los import PrepareGlobalLoS
from los.analyze_los import AnalyzeLoS
from los.analyze_global_los import AnalyzeGlobalLoS
from los.extract_horizons import ExtractLocalHorizons
from los.extract_global_horizons import ExtractGlobalHorizons
from los.export_los import ExportLoS


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Line of Sight Analyst"
        self.alias = "losAnalyst"

        # List of tool classes associated with this toolbox
        self.tools = [PrepareLoS, PrepareGlobalLoS, AnalyzeLoS, AnalyzeGlobalLoS, ExtractLocalHorizons, ExtractGlobalHorizons, ExportLoS]
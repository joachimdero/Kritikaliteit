import os
import arcpy
import importlib

import berekeningAri_methods

importlib.reload(berekeningAri_methods)


class BerekenARI(object):
    def __init__(self):
        self.label = "bereken ARI"
        self.description = "Bereken de ARI (ACI*AHI)."

    def getParameterInfo(self):
        parameters = []

        # Bestaande parameters
        p0 = arcpy.Parameter(
            displayName="ACI Feature Class",
            name="ACI_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input",
        )
        p0.value = r"C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\kritikaliteit20250725.gdb\aci_methode1"  # Default input name


        p1 = arcpy.Parameter(
            displayName="AHI Feature Class",
            name="AHI_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )
        p1.value = r"C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\kritikaliteit20250725.gdb\ahi"  # Default input name

        p2 = arcpy.Parameter(
            displayName="Output Feature Class voor ARI",
            name="output_ari_fc",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Output"
        )
        p2.value = "ari"  # Default output name

        parameters.extend([p0, p1, p2])

        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Inputwaarden
        berekeningAri_methods.bereken_ari(
            in_aci_fc=parameters[0].valueAsText,
            in_ahi_fc=parameters[1].valueAsText,
            out_ari_fc=parameters[2].valueAsText
        )


    def postExecute(self, parameters):
        return

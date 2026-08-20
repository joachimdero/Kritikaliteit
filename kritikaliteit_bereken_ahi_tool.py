import os
import arcpy
import importlib
import staatvandewegXaci_methods

importlib.reload(staatvandewegXaci_methods)
maak_minimale_fc = staatvandewegXaci_methods.maak_minimale_fc
bereken_ahi = staatvandewegXaci_methods.bereken_ahi
bereken_ahi_netwerksegmenten = staatvandewegXaci_methods.bereken_ahi_netwerksegmenten


class BerekenAHI(object):
    def __init__(self):
        self.label = "bereken AHI"
        self.description = "Bereken de AHI (Algemene Health Index) op basis van staat van de weg metingen."

    def getParameterInfo(self):
        parameters = []

        # Bestaande parameters
        p0 = arcpy.Parameter(
            displayName="Staat van de weg Feature Class (gebiedsdekkend)",
            name="staat_van_de_weg_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input",
        )

        p1 = arcpy.Parameter(
            displayName="Veld voor globale index",
            name="veld_globale_index",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        p1.parameterDependencies = [p0.name]
        p1.filter.list = ["Short", "Long", "Float", "Double"]

        p2 = arcpy.Parameter(
            displayName="Veld voor globale klasse",
            name="veld_globale_klasse",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
        p2.parameterDependencies = [p0.name]
        p2.filter.list = ["Text"]

        p3 = arcpy.Parameter(
            displayName="Netwerksegmenten Feature Class",
            name="netwerksegmenten_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p4 = arcpy.Parameter(
            displayName="Output Feature Class voor AHI",
            name="output_ahi_fc",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Output"
        )
        p4.value = "ahi"  # Default output name

        parameters.extend([p0, p1, p2, p3, p4])

        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Inputwaarden
        staat_van_de_weg_fc_in = parameters[0].valueAsText
        f_globaleindex = parameters[1].valueAsText
        f_globaleklasse = parameters[2].valueAsText
        netwerksegmenten_fc_in = parameters[3].valueAsText
        ahi_fc = parameters[4].valueAsText
        arcpy.env.workspace = os.path.basename(ahi_fc)
        maak_minimale_fc(staat_van_de_weg_fc_in, ahi_fc)
        bereken_ahi(ahi_fc, f_globaleindex, f_globaleklasse)
        bereken_ahi_netwerksegmenten(ahi_fc, "ahi", netwerksegmenten_fc_in)

    def postExecute(self, parameters):
        return

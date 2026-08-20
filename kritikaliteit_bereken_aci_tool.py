import importlib
import arcpy

import berekeningAci_Main
importlib.reload(berekeningAci_Main)

VELDEN_INPUTWAARDEN = ["VR_ETM", "PW_ETM", "sat_max", "vr_aandeel", "categorie", "UV"]

class BerekenACI(object):
    def __init__(self):
        self.label = "bereken ACI"
        self.description = "Bereken de ACI (Algemene Criticiteit Index) voor een verkeersmodel."

    def getParameterInfo(self):
        parameters = []

        # Bestaande parameters
        p0 = arcpy.Parameter(
            displayName="Input Verkeersmodel",
            name="verkeersmodel_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p1 = arcpy.Parameter(
            displayName="Netwerksegmenten",
            name="netwerksegmenten_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p2 = arcpy.Parameter(
            displayName="Wegenregister",
            name="wegenregister_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p3 = arcpy.Parameter(
            displayName="Uitzonderlijk Vervoer(UV)",
            name="uv_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p4 = arcpy.Parameter(
            displayName="Openbaar Vervoer",
            name="ov_fc_in",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input"
        )

        p5 = arcpy.Parameter(
            displayName="Output ACI",
            name="aci_out",
            datatype="Feature Class",
            parameterType="Required",
            direction="Output"
        )

        p6 = arcpy.Parameter(
            displayName="Outlier Threshold",
            name="outlier_threshold",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
        )
        p6.value = 3

        parameters.extend([p0, p1, p2, p3, p4, p5, p6])

        # Extra ACI-parameters gegroepeerd per wegtype
        wegtypes = {
            "Hoofdwegen": "H",
            "Dragend wegennet": "S",
            "Lokaal wegennet": "L"
        }

        aci_param_namen = [
            ("VR_ETM", "Vrachtwagen gewicht"),
            ("PW_ETM", "Personenwagen gewicht"),
            ("sat_max", "Saturatie gewicht"),
            ("OV", "Openbaar vervoer gewicht"),
            ("UV", "Uitzonderlijk vervoer gewicht"),
            ("vr_aandeel", "Aandeel vrachtwagens gewicht"),
        ]

        for group_label, prefix in wegtypes.items():
            for param_code, param_display in aci_param_namen:
                p = arcpy.Parameter(
                    displayName=param_display,
                    name=f"{prefix}_{param_code}",
                    datatype="GPLong",
                    parameterType="Required",
                    direction="Input"
                )
                p.category = group_label
                parameters.append(p)

        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # Defaultwaarden alleen instellen als nog niet ingevuld

        # gewichten
        defaultwaarden = {
            "H": {"VR_ETM": 40, "PW_ETM": 25, "sat_max": 20, "OV": 10, "UV": 5, "vr_aandeel": 0},
            "S": {"VR_ETM": 30, "PW_ETM": 20, "sat_max": 10, "OV": 20, "UV": 20, "vr_aandeel": 0},
            "L": {"VR_ETM": 10, "PW_ETM": 45, "sat_max": 5, "OV": 20, "UV": 10, "vr_aandeel": 0}
        }

        wegtypes = ["H", "S", "L"]
        velden = ["VR_ETM", "PW_ETM", "sat_max", "OV", "UV", "vr_aandeel"]
        basisindex = 7  # Index van eerste ACI-parameter in parameters-lijst

        for i, prefix in enumerate(wegtypes):
            for j, veld in enumerate(VELDEN_INPUTWAARDEN):
                index = basisindex + i * len(VELDEN_INPUTWAARDEN) + j
                if parameters[index].value is None:
                    parameters[index].value = defaultwaarden[prefix][veld]
#"""testen"""
    def updateMessages(self, parameters):
        # Controleer of som per groep 100 is
        basisindex = 7
        wegtypes = {
            "Hoofdwegen": "H",
            "Dragend wegennet": "S",
            "Lokaal wegennet": "L"
        }

        velden = ["VR_ETM", "PW_ETM", "sat_max", "categorie", "UV", "WEGCAT"]

        for i, (groep_label, prefix) in enumerate(wegtypes.items()):
            totaal = 0
            param_indices = []

            for j, veld in enumerate(VELDEN_INPUTWAARDEN):
                index = basisindex + i * len(VELDEN_INPUTWAARDEN) + j
                try:
                    waarde = parameters[index].value
                    if waarde is not None:
                        totaal += int(waarde)
                    param_indices.append(index)
                except:
                    pass

            if totaal != 100:
                foutmelding = f"De som van de waarden in categorie '{groep_label}' is {totaal}, maar moet 100 zijn."
                parameters[param_indices[0]].setErrorMessage(foutmelding)

    def execute(self, parameters, messages):
        # Inputwaarden
        verkeersmodel_fc_in = parameters[0].valueAsText
        netwerksegmenten_fc_in = parameters[1].valueAsText
        wegenregister_fc_in = parameters[2].valueAsText
        uv_fc_in = parameters[3].valueAsText
        ov_fc_in = parameters[4].valueAsText
        out_aci = parameters[5].valueAsText
        outlier_threshold = int(parameters[6].value)

        # Gewichtstructuur opbouwen
        basisindex = 7
        gewicht = {}
        groepen = ["H", "S", "L"]
        # velden = ["VR_ETM", "PW_ETM", "sat_max","vr_aandeel", "categorie", "UV"]

        for i, groep in enumerate(groepen):
            groep_dict = {}
            for j, veld in enumerate(VELDEN_INPUTWAARDEN):
                index = basisindex + (i * 6) + j
                groep_dict[veld] = int(parameters[index].value)
            gewicht[groep] = groep_dict

        messages.addMessage(f"Gewichtstructuur succesvol opgebouwd:{gewicht}")
        messages.addMessage(f"???????? {str(gewicht)}")
        messages.addMessage(f"???????? {gewicht}")

        # Hier volgt je verdere ACI-verwerking...
        berekeningAci_Main.bereken_aci(
            verkeersmodel_fc_in=verkeersmodel_fc_in,
            netwerksegmenten_fc_in=netwerksegmenten_fc_in,
            wegenregister_fc_in=wegenregister_fc_in,
            uv_fc_in=uv_fc_in,
            ov_fc_in=ov_fc_in,
            out_aci=out_aci,
            outlier_threshold=outlier_threshold,
            gewicht=gewicht
        )

    def postExecute(self, parameters):
        return

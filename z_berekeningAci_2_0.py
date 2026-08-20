import importlib
import json
import sys

import arcpy

import bereken_refwaarden
import berekeningAci_methods
importlib.reload(berekeningAci_2_0_methods)

# --------------------------------
input_table = arcpy.GetParameterAsText(0)
netwerksegmenten = arcpy.GetParameterAsText(1)

#bereken per wegcategorie de maxwaarde, extreme waarden worden niet meegenomen
# Definieer een drempelwaarde voor sterke afwijkingen (bijv. 3 standaardafwijkingen)
outlier_threshold = arcpy.GetParameterAsText(6)
refwaarden = bereken_refwaarden.berekening_refwaarden(input_table, outlier_threshold)
arcpy.AddMessage(json.dumps(refwaarden, indent=4, sort_keys=True))

# maak veld aan met sat_max
arcpy.AddMessage('- maak veld aan met sat_max')
berekeningAci_2_0_methods.bereken_sat_max(input_table)


arcpy.AddMessage('- berekening_aci')
berekeningAci_2_0_methods.berekening_aci(in_table=input_table, refwaarden=refwaarden)

# sys.exit()
arcpy.AddMessage('- bereken_aci_buur')
berekeningAci_2_0_methods.bereken_aci_buur(in_table=input_table, in_segmentering = netwerksegmenten)

# freq(input_table, f_outfc)

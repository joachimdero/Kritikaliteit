import importlib
import json
import sys

import arcpy

import BerekenAci
import MetadataSchrijven
import bereken_refwaarden
import berekeningAci_methods

importlib.reload(berekeningAci_methods)
# importlib.reload(bereken_refwaarden)
importlib.reload(BerekenAci)

# --------------------------------

def bereken_aci(verkeersmodel_fc_in, netwerksegmenten_fc_in, wegenregister_fc_in, uv_fc_in, ov_fc_in, out_aci, outlier_threshold, gewicht):
    arcpy.AddMessage(f"bereken_aci (verkeersmodel_fc_in={verkeersmodel_fc_in}, netwerksegmenten_fc_in={netwerksegmenten_fc_in}, wegenregister_fc_in={wegenregister_fc_in}, out_aci={out_aci}, outlier_threshold={outlier_threshold}, gewicht={gewicht})")
    arcpy.AddMessage(f"len {verkeersmodel_fc_in}: {arcpy.GetCount_management(verkeersmodel_fc_in).getOutput(0)}")
    arcpy.AddMessage(f"- maak feature class ACI ({out_aci})")

    out_aci = berekeningAci_methods.maak_fc_aci(
        in_verkeersmodel=verkeersmodel_fc_in,
        in_wegenregister=wegenregister_fc_in,
        in_uv=uv_fc_in,
        in_vervoernet=ov_fc_in,
        out_aci=out_aci
    )
    #bereken per wegcategorie de maxwaarde, extreme waarden worden niet meegenomen
    # Definieer een drempelwaarde voor sterke afwijkingen (bijv. 3 standaardafwijkingen)
    arcpy.AddMessage(f'- bereken referentiewaarden ({out_aci})')
    refwaarden = bereken_refwaarden.berekening_refwaarden(out_aci, outlier_threshold)
    arcpy.AddMessage(json.dumps(refwaarden, indent=4, sort_keys=True))

    arcpy.AddMessage(f"len {out_aci}; {arcpy.GetCount_management(out_aci).getOutput(0)}")

    # maak veld aan met sat_max
    arcpy.AddMessage(f'- maak veld aan met sat_max (out_aci)')
    berekeningAci_methods.bereken_sat_max(out_aci)
    arcpy.AddMessage(f"len {out_aci}: {arcpy.GetCount_management(out_aci).getOutput(0)}")

    arcpy.AddMessage(f'- maak veld aandeel vrachtwagens')
    berekeningAci_methods.bereken_aandeelvrachtwagens(out_aci)

    arcpy.AddMessage(f'- berekening_aci ({out_aci})')
    BerekenAci.berekening_aci(in_table=out_aci, refwaarden=refwaarden,gewicht=gewicht)
    arcpy.AddMessage(f"len {out_aci}: {arcpy.GetCount_management(out_aci).getOutput(0)}")

    arcpy.AddMessage(f'- bereken_aci_buur ({out_aci})')
    arcpy.AddMessage(f"len {out_aci}: {arcpy.GetCount_management(out_aci).getOutput(0)}")
    berekeningAci_methods.bereken_aci_buur_wegcat(
        in_table=out_aci,
        in_segmentering=netwerksegmenten_fc_in,
        in_wegenregister=wegenregister_fc_in)

    berekeningAci_methods.aci_netwerksegment(
        in_aci_table=out_aci,
        in_segmentering=netwerksegmenten_fc_in
    )
    MetadataSchrijven.schrijf_gewichten_naar_metadata(out_aci, gewicht)
    # freq(input_table, f_outfc)


import importlib
import math
import os
import sys
import arcpy
import berekeningAci_methods
from constants import *

try:
    # importeer Awv functie en downloadFunctie
    from ....AwvFunctiesAlgemeen import AwvFunctiesAlgemeen
    from ....AwvFunctiesAlgemeen import Locatieservices2 as Ls2
except ImportError:
    from sys import path

    pythonVersion = sys.version_info.major
    basemap = "GIStools"
    basispath = os.path.realpath(__file__).split(basemap)[0]
    print("basispath = %s" % basispath)
    path2 = os.path.join(basispath, basemap, "AwvFuncties")
    path.append(path2)
    import AwvFunctiesAlgemeen
    import Locatieservices2 as Ls2

    if pythonVersion == 3:
        importlib.reload(AwvFunctiesAlgemeen)
        importlib.reload(Ls2)

def bereken_ahi_bucket(globaleklasse):
    ahi_ahi_bucket = {
        "": 0,
        "Uitstekend": 1,
        "Normaal": 2,
        "Behoorlijk": 3,
        "Matig": 4,
        "Onvoldoende": 5,
    }
    if globaleklasse not in ahi_ahi_bucket:
        arcpy.AddMessage(f"globaleklasse:{globaleklasse}")

    return ahi_ahi_bucket[globaleklasse]


def bereken_ahi(staatvandeweg, f_globaleindex, f_globaleklasse):
    arcpy.AddMessage("- bereken_ahi")
    f_uc = [f_globaleindex, f_globaleklasse, F_AHI_SEGMENT, F_AHI_SEGMENT_BUCKET]

    for field in (F_AHI_SEGMENT, F_AHI_SEGMENT_BUCKET):
        if field not in [f.name for f in arcpy.ListFields(staatvandeweg)]:
            arcpy.AddField_management(
                in_table=staatvandeweg,
                field_name=field,
                field_type="LONG"
            )
#test
    with arcpy.da.UpdateCursor(staatvandeweg, f_uc) as uc:
        for i, row in enumerate(uc):
            # arcpy.AddMessage(f"staatvandeweg:{staatvandeweg}")
            # arcpy.AddMessage(f"row:{row}")
            globaleindex, globaleklasse, ahi_segment, ahi_segment_bucket = row
            if i % 10000 == 0:
                arcpy.AddMessage(f"{i} rijen behandeld")
            ahi_segment = 100 - float(globaleindex)  # omkeren indexwaarde
            if globaleklasse in (0, None, ""):
                ahi_segment = None
            ahi_segment_bucket = bereken_ahi_bucket(globaleklasse)
            row_upd = [globaleindex, globaleklasse, ahi_segment, ahi_segment_bucket]
            uc.updateRow(row_upd)


def lees_ahi_netwerksegmenten(fc_staatvandeweg, f_netwerkid):
    arcpy.AddMessage("- lees_ahi_netwerksegmenten")
    netwerkid_ahi = {}
    f_sc = [f_netwerkid, F_AHI_SEGMENT, "SHAPE@LENGTH"]
    with arcpy.da.SearchCursor(fc_staatvandeweg, f_sc) as sc:
        for row in sc:
            netwerkid, ahi, lengte = row
            if lengte is not None and lengte > 0 and ahi is not None:
                if netwerkid not in netwerkid_ahi:
                    netwerkid_ahi[netwerkid] = []
                netwerkid_ahi[netwerkid].append((ahi, lengte))
        return netwerkid_ahi


def bereken_ahi_netwerksegmenten(staatvandeweg_table, fc_netwerksegmenten):
    arcpy.AddMessage('-bereken_ahi_netwerksegmenten')
    f_netwerkid = "netwerk_id"
    arcpy.AddMessage(f'join veld {f_netwerkid}')
    AwvFunctiesAlgemeen.JoinFieldMultipleJoinFields(
        inputTable=staatvandeweg_table,
        inputJoinField=["ws_oidn", "richting_meting"],
        joinTable=fc_netwerksegmenten,
        outputJoinField=["ws_oidn", "richting_segment"],
        joinFields=[f_netwerkid]
    )

    f_ahi_gewogen_gemiddelde = "ahi_gewogen_gemiddelde"
    f_ahi_gewogen_gemiddelde_bucket = "ahi_gewogen_gemiddelde_bucket"

    for field in (f_ahi_gewogen_gemiddelde, f_ahi_gewogen_gemiddelde_bucket, F_AHI_NETWERKSEGMENT, F_AHI_NETWERKSEGMENT_BUCKET):
        if field not in [f.name for f in arcpy.ListFields(staatvandeweg_table)]:
            arcpy.AddField_management(
                in_table=staatvandeweg_table,
                field_name=field,
                field_type="LONG"
            )
    netwerkid_ahi = lees_ahi_netwerksegmenten(staatvandeweg_table, f_netwerkid)
    # arcpy.AddMessage(f"netwerkid_ahi: {str(netwerkid_ahi)[:10000]} ")
    netwerkid_stats = bereken_netwerkid_stats(netwerkid_ahi)
    # arcpy.AddMessage(f"netwerkid_stats: {str(netwerkid_stats)[:1000]} ")

    f_uc = [f_netwerkid, F_AHI_SEGMENT, F_AHI_NETWERKSEGMENT, F_AHI_NETWERKSEGMENT_BUCKET, f_ahi_gewogen_gemiddelde, f_ahi_gewogen_gemiddelde_bucket]
    with arcpy.da.UpdateCursor(staatvandeweg_table, f_uc) as uc:
        for i, row in enumerate(uc):
            netwerkid, ahi, ahi_netwerksegment, ahi_netwerksegment_bucket, ahi_gewogen_gemiddelde, ahi_gewogen_gemiddelde_bucket = row
            if i % 10000 == 0:
                arcpy.AddMessage(f"{i} rijen behandeld")
            ahi_netwerksegment = max(netwerkid_stats.get(netwerkid, {}).get("karakteristieke_toestand", 0),0)  # karakteristieke toestand is altijd >= 0

            ahi_netwerksegment_bucket = berekeningAci_methods.bereken_bucket(ahi_netwerksegment)
            ahi_gewogen_gemiddelde = max(netwerkid_stats.get(netwerkid, {}).get('gemiddelde',0),0)
            ahi_gewogen_gemiddelde_bucket = berekeningAci_methods.bereken_bucket(ahi_gewogen_gemiddelde)
            row_upd = [netwerkid, ahi, ahi_netwerksegment, ahi_netwerksegment_bucket, ahi_gewogen_gemiddelde, ahi_gewogen_gemiddelde_bucket]
            uc.updateRow(row_upd)


def bereken_netwerkid_stats(netwerkid_ahi):
    arcpy.AddMessage("- bereken_netwerkid_stats")
    netwerkid_stats = {}
    for netwerkid, waarden in netwerkid_ahi.items():
        total_length = sum(length for ahi, length in waarden)

        # Gewogen gemiddelde
        gewogen_gem = sum(ahi * length for ahi, length in waarden) / total_length
        ((5*100)+(10*10))/110

        # Gewogen variantie
        if total_length == 0:
            variance = 0  # Of bijvoorbeeld: float("nan") of None
        else:
            variance = sum(length * ((ahi - gewogen_gem) ** 2) for ahi, length in waarden) / total_length

        stddev = math.sqrt(variance)
        karakteristieke_toestand = gewogen_gem - (
                1.645 * stddev)  # 1.645 is de z-waarde voor een betrouwbaarheidsniveau van 95%

        netwerkid_stats[netwerkid] = {
            "gemiddelde": gewogen_gem,
            "standaardafwijking": stddev,
            "karakteristieke_toestand": karakteristieke_toestand,
        }
    return netwerkid_stats


def maak_minimale_fc(in_fc, out_fc):
    """
    Exporteert features met veldmapping die automatisch gegenereerd wordt. Enkel de nodige velden worden behouden.

    :param in_fc: Input feature class
    :param out_fc: Output feature class
    :param benodigde_velden: lijst met veldnamen als strings
    """
    arcpy.AddMessage(f"- maak_minimale_fc {in_fc} => {out_fc}")
    benodigde_velden = [
    "WS_OIDN",
    "FMEAS",
    "TMEAS",
    "id2",
    "jaar",
    "globale_index",
    "globale_klasse",
    "globale_structuurKlasse",
    "globale_veiligheidKlasse",
    "richting",
    "ident8",
    "wegnummer",
    "richting_wegnr",
    "richting_meting"
]
    # Maak een lege FieldMappings container
    field_mappings = arcpy.FieldMappings()

    # Doorloop de velden die je wil behouden
    for veldnaam in benodigde_velden:
        if veldnaam in [f.name for f in arcpy.ListFields(in_fc)]:
            # Maak een FieldMap object per veld
            fm = arcpy.FieldMap()
            fm.addInputField(in_fc, veldnaam)

            # Optioneel: instellen van alias of output field name
            out_field = fm.outputField
            out_field.name = veldnaam  # of pas aan indien gewenst
            out_field.aliasName = veldnaam
            fm.outputField = out_field

            # Voeg toe aan de field_mappings
            field_mappings.addFieldMap(fm)
        else:
            arcpy.AddWarning(f"Veld '{veldnaam}' niet gevonden in {in_fc}. Wordt overgeslagen.")

    # Voer export uit met de gegenereerde mapping
    arcpy.ExportFeatures_conversion(
        in_features=in_fc,
        out_features=out_fc,
        field_mapping=field_mappings
    )

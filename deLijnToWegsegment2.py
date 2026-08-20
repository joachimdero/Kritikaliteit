# -------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      derojp
#
# Created:     28/02/2023
# Copyright:   (c) derojp 2023
# Licence:     <your licence>
# -------------------------------------------------------------------------------

# overzetten De Lijn naar wegenregister
# buslijnen worden overgezet naar wegbanen + knw
# wegbanen met zelfde lijnattributen worden samengevoegd
# wegsegmenten worden (meerdere malen) verrijkt met lijnattributen indien ze volledig in een samengevoegd wegsegment vallen

import arcpy
import os
# check pythonversie
import sys, os

pythonVersion = sys.version_info.major
import arcpy

arcpy.AddMessage('import arcpy')

# importeer Awv functie en downloadFunctie
from sys import path

basemap = "GIStools"
basispath = os.path.realpath(__file__).split(basemap)[0]
print("basispath = %s" % basispath)
path2 = os.path.join(basispath, basemap, "AwvFuncties")
path.append(path2)
import AwvFunctiesAlgemeen

if pythonVersion == 3:
    import importlib

    importlib.reload(AwvFunctiesAlgemeen)
    arcpy.AddMessage("reload python 3")
elif pythonVersion == 2:
    reload(AwvFunctiesAlgemeen)
    arcpy.AddMessage("reload python 2")

# -------------------------------

# input parameters
wegsegmenten = arcpy.GetParameterAsText(0)
wegnummer = arcpy.GetParameterAsText(1)
wegbanen = arcpy.GetParameterAsText(2)
knw = arcpy.GetParameterAsText(3)
vervoernet = arcpy.GetParameterAsText(4)
output = arcpy.GetParameterAsText(5)
temp_ws = arcpy.GetParameterAsText(6)

arcpy.env.overwriteOutput = True
arcpy.env.workspace = temp_ws

# ------------------------------------------------------------------------
# VOORBEREIDING WEGSEGMENTEN
def voorbereiding_wegsegmenten(wegsegmenten, wegnummer):
    # maak een selectie van wegsegmenten (beheerder AWV, morfologie, toestand) en schrijf deze weg, behoudt velden WS_OIDN (wegsegment)
    # maak lijst van WS_OIDN die tot een genummerde weg behoren
    arcpy.AddMessage("maak lijst van WS_OIDN die tot een genummerde weg behoren")
    genummerde_wegen_WSOIDN = str(tuple([row[0] for row in arcpy.da.SearchCursor(wegnummer, ["WS_OIDN", "wegnummer"]) if
                                         len(row) < 5 or row[1][4] != '7']))
    # - maak field_map
    field_mapping = arcpy.FieldMappings()
    field_map_a = arcpy.FieldMap()
    field_map_a.addInputField(wegsegmenten, "WS_OIDN")
    output_field_a = field_map_a.outputField
    output_field_a.aliasName = "WS_OIDN"
    output_field_a.type = "Double"
    output_field_a.length = 10
    output_field_a.precision = 2
    field_map_a.outputField = output_field_a
    field_mapping.addFieldMap(field_map_a)

    morf = ('autosnelweg',
            'op- of afrit, behorende tot een gelijkgrondse verbinding',
            'op- of afrit, behorende tot een niet-gelijkgrondse verbinding',
            'parallelweg',
            'rotonde',
            'weg bestaande uit één rijbaan',
            'weg met gescheiden rijbanen die geen autosnelweg is',
            'speciale verkeerssituatie')
    where_clause = f"""
        LBLSTATUS = 'in gebruik' And
        LBLMORF IN {morf} And
        WS_OIDN IN {genummerde_wegen_WSOIDN} And
        BEHEER LIKE 'AWV%'"""
    wegsegmenten_tmp1 = os.path.join(temp_ws, "wegsegmenten_tmp1_selectieAwv")
    arcpy.FeatureClassToFeatureClass_conversion(wegsegmenten, temp_ws, os.path.basename(wegsegmenten_tmp1), where_clause,
                                                field_mapping)
    return wegsegmenten_tmp1


# maak fc van wegbanen en knw
def maak_wegbanen_knw(wegbanen, knw, vervoernet):
    wegbanen_knw = "wegbaan_knw"
    arcpy.AddMessage(f'maak nieuwe fc {wegbanen_knw} van {wegbanen} en {knw}')
    if arcpy.Exists(wegbanen_knw):
        arcpy.AddWarning(f"Bestaat al: {wegbanen_knw}, datalaag wordt niet opnieuw aangemaakt.")
        return wegbanen_knw

    for fc in (wegbanen, knw):
        arcpy.AddMessage(f"maak layer voor {fc}")
        arcpy.MakeFeatureLayer_management(
            in_features=fc,
            out_layer=os.path.basename(fc) + "_lyr",
        )
        arcpy.AddMessage(f'SelectLayerByLocation_management')
        arcpy.SelectLayerByLocation_management(
            in_layer=os.path.basename(fc) + "_lyr",
            overlap_type="INTERSECT",
            select_features=vervoernet,
            selection_type="NEW_SELECTION"
        )
    arcpy.Merge_management(
        inputs=[os.path.basename(wegbanen) + "_lyr", os.path.basename(fc) + "_lyr"],
        output=wegbanen_knw)
    return wegbanen_knw


# verrijk data wegbanen_knw met attributen van vervoernet
def verrijk_wegbanen_knw(wegbanen_knw, vervoernet):
    wegbanen_knw_vervoernet = "wegbanen_knw_vervoernet"
    wegbanen_knw_vervoernet_dissolve = "wegbanen_knw_vervoernet_dissolve"
    arcpy.AddMessage(f"verrijk data wegbanen_knw met attributen van vervoernet => {wegbanen_knw_vervoernet_dissolve}")
    arcpy.analysis.SpatialJoin(
        target_features=wegbanen_knw,
        join_features=vervoernet,
        out_feature_class=wegbanen_knw_vervoernet,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_COMMON",
        match_option="INTERSECT",
        search_radius=None,
        distance_field_name=""
    )
    arcpy.AddMessage(f"dissolve {wegbanen_knw_vervoernet}=>{wegbanen_knw_vervoernet_dissolve}")
    arcpy.management.Dissolve(
        in_features=wegbanen_knw_vervoernet,
        out_feature_class=wegbanen_knw_vervoernet_dissolve,
        dissolve_field="Categorie",
        statistics_fields=None,
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES",
        concatenation_separator=""
    )
    return wegbanen_knw_vervoernet_dissolve


def verrijk_wegsegmenten_vervoernet(wegsegmenten, wegbanen_knw_vervoernet):
    wegsegment_vervoernet = "wegsegment_vervoernet"
    arcpy.AddMessage(f"verrijk_wegsegmenten_vervoernet: {wegsegment_vervoernet}")
    arcpy.analysis.SpatialJoin(
        target_features=wegsegmenten,
        join_features=wegbanen_knw_vervoernet,
        out_feature_class=wegsegment_vervoernet,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_COMMON",
        field_mapping='WS_OIDN "WS_OIDN" true true false 8 Double 0 0,First,#,WegsegmentPco,WS_OIDN,-1,-1;Descriptio '
                      '"Descriptio" true true false 254 Text 0 0,First,#,'
                      'wegbaan_knw_Spatial_Dissolve,Descriptio,0,254;Categorie "Categorie" true true false 254 Text 0 '
                      '0,First,#,wegbaan_knw_Spatial_Dissolve,Categorie,0,254',
        match_option="COMPLETELY_WITHIN",
        search_radius=None,
        distance_field_name=""
    )
    return wegsegment_vervoernet


def eindscore(wegsegment_vervoernet, output):
    arcpy.AddMessage(f"maak fc met ws_oidn en max_categorie: {output}")
    arcpy.CreateFeatureclass_management(out_path=os.path.dirname(output), out_name=os.path.basename(output),
                                        geometry_type="POLYLINE")
    arcpy.AddField_management(
        in_table=output,
        field_name="WS_OIDN",
        field_type="LONG",
    )
    arcpy.AddField_management(
        in_table=output,
        field_name="categorie",
        field_type="TEXT",
        field_length=35
    )

    ws_oidn_net_dict = {}
    with arcpy.da.SearchCursor(wegsegment_vervoernet, ["SHAPE@", "WS_OIDN", "Categorie"]) as sc:
        for row in sc:
            if row[2] and row[2] != "":
                if row[2] == "Vervoer op Maat":
                    continue
                elif row[1] not in ws_oidn_net_dict:
                    ws_oidn_net_dict[row[1]] = [row[0], row[2]]
                elif ws_oidn_net_dict[row[1]][1] == "Kernnet":
                    continue
                else:
                    ws_oidn_net_dict[row[1]] = [row[0], row[2]]

    with arcpy.da.InsertCursor(output, ["SHAPE@", "WS_OIDN", "categorie"]) as ic:
        for key, value in ws_oidn_net_dict.items():
            row = (value[0], key, value[1])
            ic.insertRow(row)


# -------------------------------------------
wegsegmenten_tmp1 = voorbereiding_wegsegmenten(wegsegmenten, wegnummer)
wegbanen_knw = maak_wegbanen_knw(wegbanen, knw, vervoernet)
wegbanen_knw_vervoernet = verrijk_wegbanen_knw(wegbanen_knw, vervoernet)
wegsegment_vervoernet = verrijk_wegsegmenten_vervoernet(wegsegmenten_tmp1, wegbanen_knw_vervoernet)
# bereken_net(wegsegment_vervoernet)
eindscore(wegsegment_vervoernet, output)

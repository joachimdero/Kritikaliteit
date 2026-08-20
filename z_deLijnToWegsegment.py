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
arcpy.AddMessage("input paramaters")
# input parameters
wegsegmenten = arcpy.GetParameterAsText(0)
wegnummer = arcpy.GetParameterAsText(1)
wegbanen = arcpy.GetParameterAsText(2)
knw = arcpy.GetParameterAsText(3)
vervoernet = arcpy.GetParameterAsText(4)
output = arcpy.GetParameterAsText(5)

arcpy.env.overwriteOutput = True

temp = "in_memory"
temp = os.path.dirname(output)
temp = r'C:\GoogleTeamDrive\GISprojecten\1AnalysesAddHoc\criticaliteit\test.gdb'

# ------------------------------------------------------------------------
# VOORBEREIDING WEGSEGMENTEN
def voorbereiding_wegsegmenten(wegsegmenten,wegnummer):
    # maak een selectie van wegsegmenten (beheerder AWV, morfologie, toestand) en schrijf deze weg, behoudt velden WS_OIDN (wegsegment)
    # maak lijst van WS_OIDN die tot een genummerde weg behoren
    arcpy.AddMessage("maak lijst van WS_OIDN die tot een genummerde weg behoren")
    genummerde_wegen_WSOIDN = str(
        tuple([row[0] for row in arcpy.da.SearchCursor(wegnummer, ["WS_OIDN", "IDENT8"]) if row[1][4] != '7']))
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
    wegsegmenten_tmp1 = os.path.join(temp, "wegsegmenten_tmp1_selectieAwv")
    arcpy.FeatureClassToFeatureClass_conversion(wegsegmenten, temp, os.path.basename(wegsegmenten_tmp1), where_clause,
                                                field_mapping)
    return wegsegmenten_tmp1




# maak fc van wegbanen en knw
def maak_wegbanen_knw(wegbanen, knw, vervoernet):
    wegbanen_knw = "wegbaan_knw"
    arcpy.AddMessage(f'maak nieuwe fc {wegbanen_knw} van {wegbanen} en {knw}')
    for fc in (wegbanen,knw):
        arcpy.AddMessage(f"maak layer voor {fc}")
        arcpy.MakeFeatureLayer_management(
            in_features=fc,
            out_layer=os.path.basename(fc)+"_lyr",
        )
        arcpy.SelectLayerByLocation_management(
            in_layer=os.path.basename(fc)+"_lyr",
            overlap_type="INTERSECT",
            select_features=vervoernet,
            selection_type="NEW_SELECTION"
        )
    arcpy.Merge_management(
        inputs=[os.path.basename(wegbanen)+"_lyr", os.path.basename(fc)+"_lyr"],
        output=wegbanen_knw)
    return wegbanen_knw





# verrijk data wegbanen_knw met attributen van vervoernet
def verrijk_wegbanen_knw(wegbanen_knw, vervoernet):
    wegbanen_knw_vervoernet = "wegbanen_knw_vervoernet"
    wegbanen_knw_vervoernet_dissolve = "wegbanen_knw_vervoernet_dissolve"
    arcpy.AddMessage(f"verrijk data wegbanen_knw met attributen van vervoernet:{wegbanen_knw_vervoernet_dissolve}")
    arcpy.analysis.SpatialJoin(
        target_features=wegbanen_knw,
        join_features=vervoernet,
        out_feature_class=wegbanen_knw_vervoernet,
        join_operation="JOIN_ONE_TO_MANY",
        join_type="KEEP_ALL",
        field_mapping='OIDN "OIDN" true true false 8 Double 0 0,First,#,Wbn selection,OIDN,-1,-1;UIDN "UIDN" true '
                      'true false 8 Double 0 0,First,#,Wbn selection,UIDN,-1,-1;VERSIE "VERSIE" true true false 2 '
                      'Short 0 0,First,#,Wbn selection,VERSIE,-1,-1;BEGINDATUM "BEGINDATUM" true true false 8 Date 0 '
                      '0,First,#,Wbn selection,BEGINDATUM,-1,-1;VERSDATUM "VERSDATUM" true true false 8 Date 0 0,'
                      'First,#,Wbn selection,VERSDATUM,-1,-1;TYPE "TYPE" true true false 2 Short 0 0,First,#,'
                      'Wbn selection,TYPE,-1,-1;LBLTYPE "LBLTYPE" true true false 32 Text 0 0,First,#,Wbn selection,'
                      'LBLTYPE,0,32;OPNDATUM "OPNDATUM" true true false 8 Date 0 0,First,#,Wbn selection,OPNDATUM,-1,'
                      '-1;BGNINV "BGNINV" true true false 2 Short 0 0,First,#,Wbn selection,BGNINV,-1,-1;LBLBGNINV '
                      '"LBLBGNINV" true true false 32 Text 0 0,First,#,Wbn selection,LBLBGNINV,0,32;LENGTE "LENGTE" '
                      'true true false 8 Double 0 0,First,#,Wbn selection,LENGTE,-1,-1;OPPERVL "OPPERVL" true true '
                      'false 8 Double 0 0,First,#,Wbn selection,OPPERVL,-1,-1;Shape_Length "Shape_Length" false true '
                      'true 8 Double 0 0,First,#,Wbn selection,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true '
                      'true 8 Double 0 0,First,#,Wbn selection,Shape_Area,-1,-1;OIDN_1 "OIDN" true true false 8 '
                      'Double 0 0,First,#,DeLijn_clip_singlep,OIDN,-1,-1;UIDN_1 "UIDN" true true false 8 Double 0 0,'
                      'First,#,DeLijn_clip_singlep,UIDN,-1,-1;ROUTEID "ROUTEID" true true false 4 Long 0 0,First,#,'
                      'DeLijn_clip_singlep,ROUTEID,-1,-1;LIJN "LIJN" true true false 8 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,LIJN,0,8;NAAMLIJN "NAAMLIJN" true true false 64 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,NAAMLIJN,0,64;DIRID "DIRID" true true false 2 Short 0 0,First,#,'
                      'DeLijn_clip_singlep,DIRID,-1,-1;RICHTING "RICHTING" true true false 64 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,RICHTING,0,64;VARIANTID "VARIANTID" true true false 9 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,VARIANTID,0,9;VARIANT "VARIANT" true true false 64 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,VARIANT,0,64;VOERTUIG "VOERTUIG" true true false 16 Text 0 0,First,#,'
                      'DeLijn_clip_singlep,VOERTUIG,0,16;LENGTE_1 "LENGTE" true true false 8 Double 0 0,First,#,'
                      'DeLijn_clip_singlep,LENGTE,-1,-1;id_verkeersmodel "id_verkeersmodel" true true false 4 Long 0 '
                      '0,First,#,DeLijn_clip_singlep,id_verkeersmodel,-1,-1;bearing_verkeersmodel '
                      '"bearing_verkeersmodel" true true false 4 Long 0 0,First,#,DeLijn_clip_singlep,'
                      'bearing_verkeersmodel,-1,-1;lengte_verkeersmodel "lengte_verkeersmodel" true true false 8 '
                      'Double 0 0,First,#,DeLijn_clip_singlep,lengte_verkeersmodel,-1,-1;ORIG_FID "ORIG_FID" true '
                      'true false 4 Long 0 0,First,#,DeLijn_clip_singlep,ORIG_FID,-1,-1;Shape_Length_1 "Shape_Length" '
                      'false true true 8 Double 0 0,First,#,DeLijn_clip_singlep,Shape_Length,-1,-1',
        match_option="INTERSECT",
        search_radius=None,
        distance_field_name=""
    )
    arcpy.management.Dissolve(
        in_features=wegbanen_knw_vervoernet,
        out_feature_class=wegbanen_knw_vervoernet_dissolve,
        dissolve_field="LIJN;NAAMLIJN;VOERTUIG",
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
        field_mapping='WS_OIDN "WS_OIDN" true true false 8 Double 0 0,First,#,WegsegmentPco,WS_OIDN,-1,-1;LBLMORF '
                      '"LBLMORF" true true false 64 Text 0 0,First,#,WegsegmentPco,LBLMORF,0,64;LBLWEGCAT "LBLWEGCAT" '
                      'true true false 64 Text 0 0,First,#,WegsegmentPco,LBLWEGCAT,0,64;LSTRNM "LSTRNM" true true '
                      'false 80 Text 0 0,First,#,WegsegmentPco,LSTRNM,0,80;RSTRNM "RSTRNM" true true false 80 Text 0 '
                      '0,First,#,WegsegmentPco,RSTRNM,0,80;LBLBEHEER "LBLBEHEER" true true false 64 Text 0 0,First,#,'
                      'WegsegmentPco,LBLBEHEER,0,64;legende "legende" true true false 4 Long 0 0,First,#,'
                      'WegsegmentPco,legende,-1,-1;LIJN "LIJN" true true false 8 Text 0 0,First,#,'
                      'Wbnselection_Spatia_Dissolve,LIJN,0,8;NAAMLIJN "NAAMLIJN" true true false 64 Text 0 0,First,#,'
                      'Wbnselection_Spatia_Dissolve,NAAMLIJN,0,64;VOERTUIG "VOERTUIG" true true false 16 Text 0 0,'
                      'First,#,Wbnselection_Spatia_Dissolve,VOERTUIG,0,16',
        match_option="COMPLETELY_WITHIN",
        search_radius=None,
        distance_field_name=""
    )
    return wegsegment_vervoernet





def bereken_net(wegsegment_vervoernet):
    arcpy.AddMessage("bereken_net")
    arcpy.AddField_management(
        in_table=wegsegment_vervoernet,
        field_name="net",
        field_type="TEXT",
        field_length=20)
    regex_patroon_1 = r'^[^0-9]*\d[^0-9]*$'
    regex_patroon_2 = r'^[^0-9]*\d{2}[^0-9]*$'
    regex_patroon_3 = r'^[^0-9]*\d{2}[^0-9]*$'

    with arcpy.da.UpdateCursor(wegsegment_vervoernet, ["lijn", "net"]) as uc:
        for row in uc:
            if re.match(regex_patroon_1, row[0]):
                row[1] = "kern"
            elif re.match(regex_patroon_2, row[0]) or re.match(regex_patroon_3, row[0]):
                row[1] = "kern"
            uc.updateRow(row)
    return wegsegment_vervoernet



def eindscore(wegsegment_vervoernet, output):
    arcpy.AddMessage(f"maak fc met ws_oidn en max_net: {output}")
    arcpy.CreateFeatureclass_management(out_path=os.path.dirname(output), out_name=os.path.basename(output),
                                        geometry_type="POLYLINE")
    arcpy.AddField_management(
        in_table=output,
        field_name="WS_OIDN",
        field_type="LONG",
        )
    arcpy.AddField_management(
        in_table=output,
        field_name="net",
        field_type="TEXT",
        field_length=20
        )

    ws_oidn_net_dict = {}
    with arcpy.da.SearchCursor(wegsegment_vervoernet,["SHAPE@","WS_OIDN","net"]) as sc:
        for row in sc:
            if row[2] and row[2] != "":
                if row[1] not in ws_oidn_net_dict:
                    ws_oidn_net_dict[row[1]] = [row[0],row[2]]
                elif row[1] == "kern":
                    ws_oidn_net_dict[row[0]] = [row[0],row[2]]

    with arcpy.da.InsertCursor(output,["SHAPE@","WS_OIDN","net"]) as ic:
        for key, value in ws_oidn_net_dict.items():
            row = (value[0],key,value[1])
            ic.insertRow(row)


#-------------------------------------------
wegsegmenten_tmp1 = voorbereiding_wegsegmenten(wegsegmenten,wegnummer)
wegbanen_knw = maak_wegbanen_knw(wegbanen, knw,vervoernet)
wegbanen_knw_vervoernet = verrijk_wegbanen_knw(wegbanen_knw, vervoernet)
wegsegment_vervoernet = verrijk_wegsegmenten_vervoernet(wegsegmenten_tmp1, wegbanen_knw_vervoernet)
bereken_net(wegsegment_vervoernet)
eindscore(wegsegment_vervoernet,output)
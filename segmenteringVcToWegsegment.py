# -------------------------------------------------------------------------------
# Name:        segmenten verkeerscentrum naar wegsegmenten wegenregister
# Purpose:
#
# Author:      derojp
#
# Created:     28/02/2023
# Copyright:   (c) derojp 2023
# Licence:     <your licence>
# -------------------------------------------------------------------------------

""" overzetten segmentering VC naar wegenregister
wegenregistersegmenten worden opgeknipt in delen waar deze in 1 of meerdere buffers rond de segmenteringdata vallen.
Er wordt een score berekend voor de overlaps met de buffers rond de segmentering data
er wordt een score berekend of de lijnen dezelfde zin en richting hebben
de meest betrouwbare data wordt overgezet op de wegsegmenten"""

import importlib
import os
import re
import sys
import arcpy

try:
    from ....AwvFunctiesAlgemeen import AwvFunctiesAlgemeen
    importlib.reload(AwvFunctiesAlgemeen)
except (ModuleNotFoundError, ImportError):
    basemap = "GIStools"
    basispath = os.path.realpath(__file__).split(basemap)[0]
    print("basispath = %s" % basispath)
    path2 = os.path.join(basispath, basemap, "AwvFuncties")
    sys.path.append(path2)
    import AwvFunctiesAlgemeen
    importlib.reload(AwvFunctiesAlgemeen)
# -------------------------------
# importeer nodige bestanden
wegsegmenten = arcpy.GetParameterAsText(0)
rijstroken = arcpy.GetParameterAsText(1)
wegnummer = arcpy.GetParameterAsText(2)
segmentering = arcpy.GetParameterAsText(3)
output = arcpy.GetParameterAsText(4)
temp = arcpy.GetParameterAsText(5)

arcpy.env.overwriteOutput = True

# temp = "in_memory"
# temp = os.path.dirname(output)
# temp = r'C:\GoogleTeamAim\Team AIM\Team AIM\Data beheer\Projecten\AddHoc\criticaliteit\test.gdb'
arcpy.env.workspace = temp


# ------------------------------------------------------------------------

def voorbereiding_wegsegmenten(wegnummer, wegsegmenten, rijstroken):
    arcpy.AddMessage(f"voorbereiding wegsegmenten")
    # maak een selectie van wegsegmenten (beheerder AWV, morfologie, toestand) en schrijf deze weg, behoudt velden WS_OIDN (wegsegment)
    # maak lijst van WS_OIDN die tot een genummerde weg behoren
    arcpy.AddMessage(f"maak lijst van genummerde wegen")
    genummerde_wegen_wsoidn = (
        set([row[0] for row in arcpy.da.SearchCursor(wegnummer, ["WS_OIDN", "wegnummer"]) if
             len(row[1]) < 5 or row[1][4] != '7']))
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

    arcpy.AddMessage(f"maak feature layer {'wegsegmenten_selectie_lyr'}")
    arcpy.management.MakeFeatureLayer(
        in_features=wegsegmenten,
        out_layer="wegsegmenten_selectie_lyr"
    )
    arcpy.AddMessage(f"FeatureClassToFeatureClass_conversion")
    segmentering_tmp1 = "wegsegmenten_tmp1_selectieAwv"

    arcpy.management.CreateFeatureclass(
        out_path=temp,
        out_name=segmentering_tmp1,
        geometry_type="POLYLINE",
        spatial_reference='PROJCS["Belge_Lambert_1972",GEOGCS["GCS_Belge_1972",DATUM["D_Belge_1972",SPHEROID['
                          '"International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",'
                          '0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",'
                          '150000.013],PARAMETER["False_Northing",5400088.438],PARAMETER["Central_Meridian",'
                          '4.367486666666666],PARAMETER["Standard_Parallel_1",49.8333339],PARAMETER['
                          '"Standard_Parallel_2",51.16666723333333],PARAMETER["Latitude_Of_Origin",90.0],'
                          'UNIT["Meter",1.0]];-35872700 -30622700 10000;-100000 10000;-100000 '
                          '10000;0.001;0.001;0.001;IsHighPrecision'
    )
    arcpy.AddField_management(
        in_table=segmentering_tmp1,
        field_name="WS_OIDN",
        field_type="LONG"
    )
    f_cursor = ["SHAPE@", "WS_OIDN"]
    ic = arcpy.da.InsertCursor(
        in_table=segmentering_tmp1,
        field_names=f_cursor
    )
    arcpy.AddMessage(f"start vullen fc")
    with arcpy.da.SearchCursor("wegsegmenten_selectie_lyr",
                               ["SHAPE@", "WS_OIDN", "LBLSTATUS", "LBLMORF", "BEHEER"]) as sc:
        i = 0
        for row in sc:
            if row[2] == 'in gebruik' and row[3] in morf and row[1] in genummerde_wegen_wsoidn and "AWV" in row[4]:
                # if row[1] in genummerde_wegen_WSOIDN:
                i += 1
                if i in range(0, 10000000, 1000):
                    arcpy.AddMessage(f"al {i}features gekopieerd")
                # if i > 10:
                # sys.exit()
                # arcpy.AddMessage(f"row:{row[:2]}")
                ic.insertRow(row[:2])
    del ic

    # koppel rijrichting van attrijstroken aan wegsegmenten, het is mogelijk dat er meerdere waarden voor een segment zijn maar dit wordt genegeerd
    arcpy.AddMessage(f"koppel rijrichting van attrijstroken aan wegsegmenten")
    AwvFunctiesAlgemeen.JoinField(
        table_target=segmentering_tmp1,
        f_join_target="WS_OIDN",
        table_join=rijstroken,
        f_join_join="WS_OIDN",
        joinFields=["RICHTING"],
        veld_overschrijven=False
    )

    # kopieer wegsegmenten die bestaan in 2 richtingen zodat rijrichting 3 (beide) niet meer voorkomt
    arcpy.AddMessage("kopieer wegsegmenten die bestaan in 2 richtingen zodat rijrichting 3 (beide) niet meer voorkomt")
    where_clause = "RICHTING = 3"
    cursor_fields = ["WS_OIDN", "RICHTING", "SHAPE@"]
    segmenten_beide_richting = [list(row) for row in
                                arcpy.da.SearchCursor(segmentering_tmp1, cursor_fields, where_clause)]
    with arcpy.da.UpdateCursor(segmentering_tmp1, "RICHTING", where_clause) as uc:
        for row in uc:
            if row[0] == 3:
                row[0] = 1
                uc.updateRow(row)
    with arcpy.da.InsertCursor(segmentering_tmp1, cursor_fields) as ic:
        for segment in segmenten_beide_richting:
            segment[1] = 2
            ic.insertRow(segment)

    # schrijf de richting (bearing) van het segment, gecorrigeerd met rijrichting, weg in een veld
    arcpy.AddMessage("schrijf de richting (bearing) van het segment, gecorrigeerd met rijrichting, weg in een veld")
    arcpy.AddField_management(segmentering_tmp1, "bearing_wegsegment", "LONG")
    arcpy.management.CalculateGeometryAttributes(
        in_features=segmentering_tmp1,
        geometry_property="bearing_wegsegment LINE_BEARING",
        coordinate_system='PROJCS["Belge_Lambert_1972",GEOGCS["GCS_Belge_1972",DATUM["D_Belge_1972",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",150000.013],PARAMETER["False_Northing",5400088.438],PARAMETER["Central_Meridian",4.367486666666666],PARAMETER["Standard_Parallel_1",49.8333339],PARAMETER["Standard_Parallel_2",51.16666723333333],PARAMETER["Latitude_Of_Origin",90.0],UNIT["Meter",1.0]]',
        coordinate_format="SAME_AS_INPUT"
    )

    where_clause = "RICHTING = 2"
    with arcpy.da.UpdateCursor(segmentering_tmp1, ["RICHTING", "bearing_wegsegment"], where_clause) as uc:
        for row in uc:
            if row[0] == 2:
                row[1] = (row[1] + 180) % 360  # draai richting om
                uc.updateRow(row)

    # schrijf de lengte van het wegsegment weg in veld lengte_wegsegment
    arcpy.AddMessage("schrijf de lengte van het wegsegment weg in veld lengte_wegsegment")
    arcpy.AddField_management(segmentering_tmp1, "lengte_wegsegment", "DOUBLE")
    arcpy.management.CalculateField(
        in_table=segmentering_tmp1,
        field="lengte_wegsegment",
        expression="!Shape_Length!"
    )

    arcpy.AddMessage(f"voorbereiding wegsegmenten: resultaat {segmentering_tmp1}")
    return segmentering_tmp1


def voorbereiding_segmentering(segmentering):
    arcpy.AddMessage("VOORBEREIDING segmentering")
    # voeg id toe om terug te kunnen kijken naar originele lijn na de bewerkingen
    segmentering_tmp1 = "segmentering_tmp1"
    arcpy.conversion.ExportFeatures(
        in_features=segmentering,
        out_features=segmentering_tmp1
    )
    arcpy.management.AddField(segmentering_tmp1, "id_segmentering", "LONG")
    arcpy.management.CalculateField(
        in_table=segmentering_tmp1,
        field="id_segmentering",
        expression="!OBJECTID!"
    )
    # schrijf de richting van het segment weg in veld bearing_segmentering
    arcpy.AddMessage("schrijf de richting van het segment weg in veld bearing_segmentering")
    arcpy.AddField_management(segmentering_tmp1, "bearing_segmentering", "LONG")
    arcpy.management.CalculateGeometryAttributes(
        in_features=segmentering_tmp1,
        geometry_property="bearing_segmentering LINE_BEARING",
        coordinate_system='PROJCS["Belge_Lambert_1972",GEOGCS["GCS_Belge_1972",DATUM["D_Belge_1972",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",150000.013],PARAMETER["False_Northing",5400088.438],PARAMETER["Central_Meridian",4.367486666666666],PARAMETER["Standard_Parallel_1",49.8333339],PARAMETER["Standard_Parallel_2",51.16666723333333],PARAMETER["Latitude_Of_Origin",90.0],UNIT["Meter",1.0]]',
        coordinate_format="SAME_AS_INPUT"
    )

    # schrijf de lengte van het segment weg in een veld
    arcpy.AddMessage("schrijf de lengte van het segment weg in een veld")
    arcpy.AddField_management(segmentering_tmp1, "lengte_segmentering", "DOUBLE")
    arcpy.management.CalculateField(
        in_table=segmentering_tmp1,
        field="lengte_segmentering",
        expression="!Shape_Length!"
    )
    return segmentering_tmp1


def combineer_wegsegmenten_segmentering(wegsegmenten_tmp1, segmentering):
    arcpy.AddMessage("COMBINEER WEGSEGMENTEN EN segmentering")
    # creëer een buffer rond de lijnen van het segmentering
    segmentering_buffer = os.path.join(temp, os.path.basename(segmentering) + "_buffer")
    arcpy.analysis.Buffer(
        in_features=segmentering,
        out_feature_class=segmentering_buffer,
        buffer_distance_or_field="10 Meters",
        line_side="FULL",
        line_end_type="ROUND",
        dissolve_option="NONE",
        dissolve_field=None,
        method="PLANAR"
    )

    # knip de wegsegmenten op volgens de bufferpolygonen van het segmentering
    wegsegmenten_tmp2 = os.path.join(temp, "wegsegmenten_tmp2_intersectSegmentering")
    arcpy.AddMessage(f"knip de wegsegmenten op volgens de bufferpolygonen van de segmentering: {wegsegmenten_tmp2}")
    arcpy.analysis.Identity(
        in_features=wegsegmenten_tmp1,
        identity_features=segmentering_buffer,
        out_feature_class=wegsegmenten_tmp2,
        join_attributes="ALL",
        cluster_tolerance=None,
        relationship="NO_RELATIONSHIPS"
    )

    # voeg segmenten die zelfde wegsegment en buffer als bron hebben samen
    inputvelden = [f.name for f in arcpy.ListFields(wegsegmenten_tmp2)]
    arcpy.AddMessage(f'inputvelden: {inputvelden}')
    wegsegmenten_tmp3 = os.path.join(temp, "wegsegmenten_tmp3_intersectSegmentering_dissolve")
    arcpy.AddMessage(f"voeg segmenten die zelfde wegsegment en buffer als bron hebben samen: {wegsegmenten_tmp3}")
    arcpy.AddMessage(f"velden in {wegsegmenten_tmp2}: {[f.name for f in arcpy.ListFields(wegsegmenten_tmp2)]}")
    arcpy.management.Dissolve(
        in_features=wegsegmenten_tmp2,
        out_feature_class=wegsegmenten_tmp3,
        dissolve_field="WS_OIDN;RICHTING;bearing_wegsegment;lengte_wegsegment;Code;id2;SG_ID;Hoofdrichtingen;Subrichtingen;Knoop_naam;SG_naam;bearing_segmentering;id_segmentering;lengte_segmentering;ORIG_FID",
        statistics_fields=None,
        multi_part="MULTI_PART",
        unsplit_lines="DISSOLVE_LINES"
    )
    # #verwijder segmenten waar geen link gevonden is
    # arcpy.MakeFeatureLayer_management(
    #     in_features=wegsegmenten_tmp3,
    #     out_layer="wegsegmenten_verwijderen",
    #     where_clause="ORIG_FID = 0"
    #     )
    # arcpy.DeleteFeatures_management(in_features="wegsegmenten_verwijderen")
    # arcpy.Delete_management(in_data="wegsegmenten_verwijderen",data_type="Layer")
    return wegsegmenten_tmp3


def bereken_scores(wegsegmenten):
    def bereken_score_overlap(wegsegmenten):
        # bereken score overlap
        arcpy.AddField_management(wegsegmenten, "scoreOverlap", "LONG")
        arcpy.management.CalculateField(
            in_table=wegsegmenten,
            field="scoreOverlap",
            expression="0.01*(!Shape_Length!/!lengte_wegsegment!*100)**2",
            expression_type="PYTHON3",
            code_block="",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        return wegsegmenten

    def bereken_score_richting(wegsegmenten):
        # bereken score richting
        arcpy.AddField_management(wegsegmenten, "scoreRichting", "LONG")
        arcpy.AddMessage(f"bereken score richting: {wegsegmenten}")
        # scores worden versneld dalend gemaakt (0.01*waarde**2)
        arcpy.management.CalculateField(
            in_table=wegsegmenten,
            field="scoreRichting",
            expression="0.01*(100-(abs(berekenHoek(!bearing_wegsegment!,!bearing_segmentering!))/180*100))**2",
            expression_type="PYTHON3",
            code_block="""def berekenHoek(bearing1, bearing2):
            # bereken de hoek tussen 2 lijnen met als bron 'bearing' van de lijn
            r = (bearing2 - bearing1) % 360.0
            while r >= 180.0:
                r -= 360.0
            return r""",
            field_type="TEXT",
            enforce_domains="NO_ENFORCE_DOMAINS"
        )
        return wegsegmenten

    def nabijheid(wegsegmenten, type):
        # bereken score nabijheid, score mag niet toegekend worden wanneer richting en overlapscore laag zijn
        if type == "lijn":
            wegsegmenten_neartable = os.path.join(temp, "wegsegmenten_tmp4_nearSegmenten")
            f_score = "scoreAfstand"
        elif type == "midpoint":
            wegsegmenten_neartable = os.path.join(temp, "wegsegmenten_tmp6_nearMidpointSegmenten")
            f_score = "scoreAfstandMid"
        arcpy.AddField_management(wegsegmenten, f_score, "LONG")
        arcpy.AddMessage(
            f"bereken score nabijheid, score mag niet toegekend worden wanneer richting en overlapscore laag zijn: {wegsegmenten}/{wegsegmenten_neartable}")
        arcpy.analysis.GenerateNearTable(
            in_features=wegsegmenten,
            near_features=segmentering,
            out_table=wegsegmenten_neartable,
            search_radius="16 Meters",
            location="NO_LOCATION",
            angle="NO_ANGLE",
            closest="ALL",
            closest_count=5,
            method="PLANAR",
            distance_unit="Meters"
        )

        AwvFunctiesAlgemeen.JoinField(wegsegmenten_neartable, "NEAR_FID", segmentering, "OBJECTID", ["id_segmentering", ],
                              veld_overschrijven=True)

        score_near = {(row[0], row[1]): int(0.01 * (100 - ((row[2] * 100) / 16)) ** 2) for row in
                      arcpy.da.SearchCursor(wegsegmenten_neartable, ["IN_FID", "id_segmentering", "NEAR_DIST"])}
        arcpy.AddMessage(f'score_near (<500): {str(score_near)[:500]}')
        with arcpy.da.UpdateCursor(wegsegmenten, ["OBJECTID", "id_segmentering", f_score]) as uc:
            for row in uc:
                row = list(row)
                # arcpy.AddMessage(f'row:{row}')
                if (row[0], row[1]) in score_near:
                    row[2] = score_near[(row[0], row[1])]
                else:
                    row[2] = 0
                uc.updateRow(row)
        return wegsegmenten

    def nabijheid_midpoint(wegsegmenten):
        wegsegmenten_midpoint = "wegsegmenten_tmp5_midpoint"
        arcpy.AddMessage(
            f"nabijheid_midpoint: wegsegmenten:{wegsegmenten},wegsegmenten_midpoint:{wegsegmenten_midpoint}")
        arcpy.FeatureVerticesToPoints_management(
            in_features=wegsegmenten,
            out_feature_class=wegsegmenten_midpoint,
            point_location="MID"
        )
        wegsegmenten_midpoint = nabijheid(wegsegmenten_midpoint, type="midpoint")
        AwvFunctiesAlgemeen.JoinField(
            table_target=wegsegmenten,
            f_join_target="OBJECTID",
            table_join=wegsegmenten_midpoint,
            f_join_join="ORIG_FID",
            joinFields=["scoreAfstandMid"],
            veld_overschrijven=False
        )

        return wegsegmenten

    def bereken_score_wegnummer(wegsegmenten):
        ws_oidn_ident2 = {}
        with arcpy.da.SearchCursor(wegnummer, ["WS_OIDN", "wegnummer"]) as sc:
            for row in sc:
                if row[0] not in ws_oidn_ident2:
                    ws_oidn_ident2[row[0]] = [row[1]]
                else:
                    ws_oidn_ident2[row[0]].append(row[1])
        arcpy.AddMessage(f"len WS_OIDN_ident2 = {len(ws_oidn_ident2)}")

        f_score = "scoreWegnummer"
        arcpy.AddField_management(wegsegmenten, f_score, "LONG")
        with arcpy.da.UpdateCursor(wegsegmenten, ["WS_OIDN", "id2", "scoreWegnummer"]) as uc:
            for row in uc:
                # wegnummers_id2 = [wegnr[0] + str(int(wegnr[1:4])) for wegnr in WS_OIDN_ident2[row[0]]]
                wegnummers_id2 = [
                    wegnr[0] + re.match(r"(\d+)", wegnr[1:]).group(1)
                    if re.match(r"(\d+)", wegnr[1:])
                    else wegnr[0]  # Fallback als geen cijfers worden gevonden
                    for wegnr in ws_oidn_ident2[row[0]]
                ]
                if row[1] != "" and row[1] is not None:
                    if row[1] in wegnummers_id2:
                        row[2] = 100
                    else:
                        row[2] = 0
                else:
                    row[2] = 1
                uc.updateRow(row)
        return wegsegmenten

    wegsegmenten = bereken_score_overlap(wegsegmenten)
    wegsegmenten = bereken_score_richting(wegsegmenten)
    wegsegmenten = nabijheid(wegsegmenten, type="lijn")
    wegsegmenten = nabijheid_midpoint(wegsegmenten)
    wegsegmenten = bereken_score_wegnummer(wegsegmenten)

    return wegsegmenten


def bereken_totale_score(wegsegmenten):
    # hou de hoogste score over, heb aandacht voor segmenten die geen hoge score hebben
    arcpy.AddField_management(
        in_table=wegsegmenten,
        field_name="score",
        field_type="LONG"
    )
    arcpy.management.CalculateField(
        in_table=wegsegmenten,
        field="score",
        expression="((!scoreRichting!*5)+(!scoreOverlap!*3)+(!scoreAfstand!*1)+(!scoreAfstandMid!*3)+("
                   "!scoreWegnummer!*2))/14",
        expression_type="PYTHON3",
        code_block="",
        field_type="TEXT",
        enforce_domains="NO_ENFORCE_DOMAINS"
    )
    return wegsegmenten


def kies_beste_waarde(wegsegmenten_tmp3):
    # sorteer de gegevens
    wegsegmenten_dissolve = os.path.join(temp, "wegsegmenten_tmp7_intersectSegmenten_dissolve_sort")
    arcpy.management.Sort(
        in_dataset=wegsegmenten_tmp3,
        out_dataset=wegsegmenten_dissolve,
        sort_field="score DESCENDING",
        spatial_sort_method="UR"
    )

    # voeg samen met eerste (hoogste score) waarde als resultaat
    arcpy.AddWarning(f"fields:{[f.name for f in arcpy.ListFields(wegsegmenten_dissolve)]}")
    arcpy.management.Dissolve(
        in_features=wegsegmenten_dissolve,
        out_feature_class=output,
        dissolve_field="WS_OIDN;RICHTING;bearing_wegsegment;lengte_wegsegment",
        statistics_fields="Code FIRST;id2 FIRST;Hoofdrichtingen FIRST; Subrichtingen FIRST;Knoop_naam FIRST;SG_naam FIRST;id_segmentering FIRST;scoreOverlap FIRST;scoreRichting "
                          "FIRST;scoreAfstand FIRST;scoreAfstandMid FIRST;scoreWegnummer FIRST;score FIRST;ORIG_FID_1 FIRST;Shape_Length FIRST",
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES",
        concatenation_separator=""
    )
    for field in [f.name for f in arcpy.ListFields(output) if f.name.startswith("FIRST_") and f.name != 'FIRST_Shape_Length']:
        arcpy.AddMessage("AlterField: %s" % field)
        arcpy.management.AlterField(
            in_table=output,
            field=field,
            new_field_name=field.replace("FIRST_", ""),
            new_field_alias=field.replace("FIRST_", "")
        )


# VOORBEREIDING WEGSEGMENTEN
wegsegmenten_tmp1 = voorbereiding_wegsegmenten(
    wegnummer=wegnummer,
    wegsegmenten=wegsegmenten,
    rijstroken=rijstroken
)
# VOORBEREIDING segmentering
segmentering = voorbereiding_segmentering(segmentering=segmentering)
# COMBINEER WEGSEGMENTEN EN segmentering
wegsegmenten_tmp3 = combineer_wegsegmenten_segmentering(wegsegmenten_tmp1=wegsegmenten_tmp1,
                                                        segmentering=segmentering)

# BEREKEN SCORES
wegsegmenten_tmp3 = bereken_scores(wegsegmenten_tmp3)
arcpy.AddMessage(f"wegsegmenten_tmp3 = {wegsegmenten_tmp3}")
wegsegmenten_tmp3 = bereken_totale_score(wegsegmenten_tmp3)

# KIES BESTE WAARDE
kies_beste_waarde(wegsegmenten_tmp3)

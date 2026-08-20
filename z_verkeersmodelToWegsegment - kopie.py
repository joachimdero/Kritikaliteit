#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      derojp
#
# Created:     28/02/2023
# Copyright:   (c) derojp 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# overzetten verkeersmodel naar wegenregister
# wegenregistersegmenten worden opgeknipt in delen waar deze in 1 of meerdere buffers rond de verkeersmodeldata vallen.
#Er wordt een score berekend voor de overlaps met de buffers rond de verkeersmodellen data
#er wordt een score berekend of de lijnen dezelfde zin en richting hebben
# de meest betrouwbare data wordt overgezet op de wegsegmenten

import arcpy
import os
#check pythonversie
import sys,os
pythonVersion = sys.version_info.major

#importeer Awv functie en downloadFunctie
from sys import path
basemap = "GIStools"
basispath =  os.path.realpath(__file__).split(basemap)[0]
print ("basispath = %s"% basispath)
path2 =  os.path.join(basispath,basemap, "AwvFuncties")
path.append(path2)
import AwvFunctiesAlgemeen

if pythonVersion == 3:
    import importlib
    importlib.reload(AwvFunctiesAlgemeen)
    arcpy.AddMessage("reload python 3")
elif pythonVersion == 2:
    reload (AwvFunctiesAlgemeen)
    arcpy.AddMessage("reload python 2")






#-------------------------------
# importeer nodige bestanden
wegsegmenten = arcpy.GetParameterAsText(0)
rijstroken = arcpy.GetParameterAsText(1)
wegnummer = arcpy.GetParameterAsText(2)
verkeersmodel = arcpy.GetParameterAsText(3)
output = arcpy.GetParameterAsText(4)

arcpy.env.overwriteOutput = True

temp = "in_memory"
temp = os.path.dirname(output)

#------------------------------------------------------------------------
# VOORBEREIDING WEGSEGMENTEN

# maak een selectie van wegsegmenten (beheerder AWV, morfologie, toestand) en schrijf deze weg, behoudt velden WS_OIDN (wegsegment)
# maak lijst van WS_OIDN die tot een genummerde weg behoren
genummerde_wegen_WSOIDN = str(tuple([row[0] for row in arcpy.da.SearchCursor(wegnummer,["WS_OIDN","IDENT8"]) if row[1][4]!='7'] ) )
#- maak field_map
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
arcpy.FeatureClassToFeatureClass_conversion(wegsegmenten,temp, os.path.basename(wegsegmenten_tmp1),where_clause,field_mapping)

# koppel rijrichting van attrijstroken aan wegsegmenten, het is mogelijk dat er meerdere waarden voor een segment zijn maar dit wordt genegeerd
inputTable = wegsegmenten_tmp1
inputJoinField = "WS_OIDN"
joinTable = rijstroken
outputJoinField = "WS_OIDN"
joinFields = ["RICHTING"]
AwvFunctiesAlgemeen.JoinField(inputTable, inputJoinField, joinTable, outputJoinField, joinFields,veld_overschrijven=False)

# kopieer wegsegmenten die bestaan in 2 richtingen zodat rijrichting 3 (beide) niet meer voorkomt
arcpy.AddMessage("kopieer wegsegmenten die bestaan in 2 richtingen zodat rijrichting 3 (beide) niet meer voorkomt")
where_clause = "RICHTING = 3"
cursor_fields = ["WS_OIDN","RICHTING","SHAPE@"]
segmenten_beide_richting = [list(row) for row in arcpy.da.SearchCursor(wegsegmenten_tmp1,cursor_fields,where_clause)]
with arcpy.da.UpdateCursor(wegsegmenten_tmp1,"RICHTING",where_clause) as uc:
    for row in uc:
        if row[0] == 3:
            row[0] = 1
            uc.updateRow(row)
with arcpy.da.InsertCursor(wegsegmenten_tmp1,cursor_fields) as ic:
    for segment in segmenten_beide_richting:
        segment[1] = 2
        ic.insertRow(segment)


# schrijf de richting (bearing) van het segment, gecorrigeerd met rijrichting, weg in een veld
arcpy.AddMessage("schrijf de richting (bearing) van het segment, gecorrigeerd met rijrichting, weg in een veld")
arcpy.AddField_management(wegsegmenten_tmp1,"bearing_wegsegment","LONG")
arcpy.management.CalculateGeometryAttributes(
    in_features=wegsegmenten_tmp1,
    geometry_property="bearing_wegsegment LINE_BEARING",
    length_unit="",
    area_unit="",
    coordinate_system='PROJCS["Belge_Lambert_1972",GEOGCS["GCS_Belge_1972",DATUM["D_Belge_1972",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",150000.013],PARAMETER["False_Northing",5400088.438],PARAMETER["Central_Meridian",4.367486666666666],PARAMETER["Standard_Parallel_1",49.8333339],PARAMETER["Standard_Parallel_2",51.16666723333333],PARAMETER["Latitude_Of_Origin",90.0],UNIT["Meter",1.0]]',
    coordinate_format="SAME_AS_INPUT"
)
where_clause = "RICHTING = 2"
with arcpy.da.UpdateCursor(wegsegmenten_tmp1,["RICHTING","bearing_wegsegment"],where_clause) as uc:
    for row in uc:
        if row[0] == 2:
            row[1] = (row[1]+180) %360 #draai richting om
            uc.updateRow(row)

# schrijf de lengte van het wegsegment weg in veld lengte_wegsegment
arcpy.AddMessage("schrijf de lengte van het wegsegment weg in veld lengte_wegsegment")
arcpy.AddField_management(wegsegmenten_tmp1,"lengte_wegsegment","DOUBLE")
arcpy.management.CalculateField(
    in_table=wegsegmenten_tmp1,
    field="lengte_wegsegment",
    expression="!Shape_Length!"
)



# VOORBEREIDING VERKEERSMODEL
arcpy.AddMessage("VOORBEREIDING VERKEERSMODEL")
# voeg id toe om terug te kunnen kijken naar originele lijn na de bewerkingen
arcpy.management.AddField(verkeersmodel,"id_verkeersmodel","LONG")
arcpy.management.CalculateField(
    in_table=verkeersmodel,
    field="id_verkeersmodel",
    expression="!OBJECTID!"
)
# schrijf de richting van het segment weg in veld bearing_verkeersmodel
arcpy.AddMessage("schrijf de richting van het segment weg in veld bearing_verkeersmodel")
arcpy.AddField_management(verkeersmodel,"bearing_verkeersmodel","LONG")
arcpy.management.CalculateGeometryAttributes(
    in_features=verkeersmodel,
    geometry_property="bearing_verkeersmodel LINE_BEARING",
    length_unit="",
    area_unit="",
    coordinate_system='PROJCS["Belge_Lambert_1972",GEOGCS["GCS_Belge_1972",DATUM["D_Belge_1972",SPHEROID["International_1924",6378388.0,297.0]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",150000.013],PARAMETER["False_Northing",5400088.438],PARAMETER["Central_Meridian",4.367486666666666],PARAMETER["Standard_Parallel_1",49.8333339],PARAMETER["Standard_Parallel_2",51.16666723333333],PARAMETER["Latitude_Of_Origin",90.0],UNIT["Meter",1.0]]',
    coordinate_format="SAME_AS_INPUT"
)

# schrijf de lengte van het segment weg in een veld
arcpy.AddMessage("schrijf de lengte van het segment weg in een veld")
arcpy.AddField_management(verkeersmodel,"lengte_verkeersmodel","DOUBLE")
arcpy.management.CalculateField(
    in_table=verkeersmodel,
    field="lengte_verkeersmodel",
    expression="!Shape_Length!"
)




# COMBINEER WEGSEGMENTEN EN VERKEERSMODEL
arcpy.AddMessage("COMBINEER WEGSEGMENTEN EN VERKEERSMODEL")
# creëer een buffer rond de lijnen van het verkeersmodel
verkeersmodel_buffer = os.path.join(temp,os.path.basename(verkeersmodel) + "_buffer")
arcpy.analysis.Buffer(
    in_features=verkeersmodel,
    out_feature_class=verkeersmodel_buffer,
    buffer_distance_or_field="16 Meters",
    line_side="FULL",
    line_end_type="ROUND",
    dissolve_option="NONE",
    dissolve_field=None,
    method="PLANAR"
)

# knip de wegsegmenten op volgens de bufferpolygonen van het verkeersmodel
wegsegmenten_tmp2 = os.path.join(temp,"wegsegmenten_tmp2_intersectVerkeersmodel")
arcpy.AddMessage(f"knip de wegsegmenten op volgens de bufferpolygonen van het verkeersmodel: {wegsegmenten_tmp2}")
arcpy.analysis.Identity(
    in_features=wegsegmenten_tmp1,
    identity_features=verkeersmodel_buffer,
    out_feature_class=wegsegmenten_tmp2,
    join_attributes="ALL",
    cluster_tolerance=None,
    relationship="NO_RELATIONSHIPS"
)

# voeg segmenten die zelfde wegsegment en buffer als bron hebben samen
inputvelden = [f.name for f in arcpy.ListFields(wegsegmenten_tmp2)]
arcpy.AddMessage(f'inputvelden: {inputvelden}')
wegsegmenten_tmp3 =  os.path.join(temp,"wegsegmenten_tmp3_intersectVerkeersmodel_dissolve")
arcpy.AddMessage(f"voeg segmenten die zelfde wegsegment en buffer als bron hebben samen: {wegsegmenten_tmp3}")
arcpy.management.Dissolve(
    in_features=wegsegmenten_tmp2,
    out_feature_class=wegsegmenten_tmp3,
    dissolve_field="WS_OIDN;RICHTING;bearing_wegsegment;lengte_wegsegment;A_KNOOP;B_KNOOP;PW_ETM;VR_ETM;SAT_ETMAAL;PAE_ETMAAL;F17_VolPAE;F17_VolPW;F17_VolVR;F17_Saturat;F08_VolPAE;F08_VolPW;F08_VolVR;F08_Saturat;Kl17Sat;Kl17Sat_R;Kl08Sat;Kl08Sat_R;KlEtmSat;KlEtmSat_R;bearing_verkeersmodel;id_verkeersmodel;lengte_verkeersmodel;ORIG_FID",
    statistics_fields=None,
    multi_part="MULTI_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator=""
)



# BEREKEN SCORES
# bereken score overlap
arcpy.AddField_management(wegsegmenten_tmp3,"scoreOverlap","LONG")
arcpy.management.CalculateField(
    in_table=wegsegmenten_tmp3,
    field="scoreOverlap",
    expression="!Shape_Length!/!lengte_wegsegment!*100",
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

# bereken score richting
arcpy.AddField_management(wegsegmenten_tmp3,"scoreRichting","LONG")
arcpy.management.CalculateField(
    in_table=wegsegmenten_tmp3,
    field="scoreRichting",
    expression="100-(abs(berekenHoek(!bearing_wegsegment!,!bearing_verkeersmodel!))/180*100)",
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

# hou de hoogste score over, heb aandacht voor segmenten die geen hoge score hebben
arcpy.AddField_management(wegsegmenten_tmp3,"score","LONG")
arcpy.management.CalculateField(
    in_table=wegsegmenten_tmp3,
    field="score",
    expression="(!scoreRichting!+!scoreOverlap!)/2",
    expression_type="PYTHON3",
    code_block="",
    field_type="TEXT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

# KIES BESTE WAARDE
#sorteer de gegevens
wegsegmenten_tmp4 = os.path.join(temp,"wegsegmenten_tmp4_intersectVerkeersmodel_dissolve_sort")
arcpy.management.Sort(
    in_dataset=wegsegmenten_tmp3,
    out_dataset=wegsegmenten_tmp4,
    sort_field="score DESCENDING",
    spatial_sort_method="UR"
)

#voeg samen met eerste waarde als resultaat
##wegsegmenten_tmp5 = "wegsegmenten_layer1_score"
##where_clause = "SCORE >50"
##arcpy.management.MakeFeatureLayer(wegsegmenten_tmp4,wegsegmenten_tmp5,where_clause)
arcpy.management.Dissolve(
    in_features=wegsegmenten_tmp4,
    out_feature_class= output,
    dissolve_field="WS_OIDN;RICHTING;bearing_wegsegment;lengte_wegsegment",
    statistics_fields="id_verkeersmodel FIRST;A_KNOOP FIRST;B_KNOOP FIRST;PW_ETM FIRST;VR_ETM FIRST;SAT_ETMAAL FIRST;PAE_ETMAAL FIRST;F17_VolPAE FIRST;F17_VolPW FIRST;F17_VolVR FIRST;F17_Saturat FIRST;F08_VolPAE FIRST;F08_VolPW FIRST;F08_VolVR FIRST;F08_Saturat FIRST;Kl17Sat FIRST;Kl17Sat_R FIRST;Kl08Sat FIRST;Kl08Sat_R MAX;KlEtmSat FIRST;KlEtmSat_R MAX;bearing_verkeersmodel FIRST;lengte_verkeersmodel FIRST;ORIG_FID FIRST;scoreOverlap FIRST;scoreRichting FIRST;score FIRST",
    multi_part="SINGLE_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator=""
)


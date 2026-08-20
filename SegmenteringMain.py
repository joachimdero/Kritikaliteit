import os
import sys
import arcpy

wegsegmenten_wr_input = arcpy.GetParameterAsText(0)
wegknopen_wr_input = arcpy.GetParameterAsText(1)
wegsegmenten_fs_input = arcpy.GetParameterAsText(2)
segmentering_vc = arcpy.GetParameterAsText(3)
ws = arcpy.GetParameterAsText(4)

arcpy.env.workspace = ws

# voeg pad toe
path_add = os.path.join(os.path.realpath(__file__).split("GIStools")[0], "GIStools", "AwvFuncties")
arcpy.AddMessage(f"voeg pad {path_add} toe")
sys.path.append(os.path.join(os.path.realpath(__file__).split("GIStools")[0], "GIStools", "AwvFuncties"))
import AwvFunctiesAlgemeen
import WegenregisterAnalyse

# -----------------
# selectie data
segmenten_joinfields = "wegsegmenten_wr_tmp1copyjoinfields"
arcpy.CopyFeatures_management(
    in_features=wegsegmenten_wr_input,
    out_feature_class=segmenten_joinfields
)
AwvFunctiesAlgemeen.JoinField(
    inputTable=segmenten_joinfields,
    inputJoinField="WS_OIDN",
    joinTable=wegsegmenten_fs_input,
    outputJoinField="id",
    joinFields=["ident2", "ident7", "ident8", "eu", "doorsteken", "tweemaaltwee"],
    veld_overschrijven=True
)
AwvFunctiesAlgemeen.JoinField(
    inputTable=segmenten_joinfields,
    inputJoinField="WS_OIDN",
    joinTable=segmentering_vc,
    outputJoinField="id",
    joinFields=['Code', 'id2', 'Hoofdrichtingen', 'Subrichtingen', 'Knoop_naam', 'G_naam'],
    veld_overschrijven=True
)
segmenten_selectie = "wegsegmenten_wr_tmp2Selectie"
where_clause = "LBLWEGCAT IN " \
               "('europese hoofdweg','vlaamse hoofdweg', " \
               "'interlokale weg', 'regionale weg','interlokale'" \
               "'lokale onstsluitingsweg', " \
               "'hoofdweg','primaire weg I', 'primaire weg II', 'lokale weg type 1'," \
               "'secundaire weg', 'secundaire weg type 1', 'secundaire weg type 2', " \
               "'secundaire weg type 3', 'secundaire weg type 4'" \
               "AND lblstatus = 'in gebruik' " \
               "AND lbltgbep = 'openbare weg' " \
               "AND doorsteek IN ('0') " \
               "AND beheer <> 'PARTIC' And morf IN (102, 103, 105, 104, 106, 107, 109, 110))"
arcpy.ExportFeatures_conversion(
    in_features=segmenten_joinfields,
    out_features=segmenten_selectie,
    where_clause=where_clause
)

segmenten_buffer = "wegsegmenten_wr_buffer_tmp1"
arcpy.Buffer_analysis(
    in_features=segmenten_joinfields,
    out_feature_class=segmenten_buffer,
    buffer_distance_or_field="1 Meters",
    line_side="FULL",
    line_end_type="ROUND",
    dissolve_option="LIST",
    dissolve_field=["ident2", "LBLWEGCAT"]
)
segmenten_buffer_singlepart = "wegsegmenten_wr_buffer_tmp2singlepart"
arcpy.MultipartToSinglepart_management(
    in_features=segmenten_buffer,
    out_feature_class=segmenten_buffer_singlepart
)
arcpy.CalculateField_management(
    in_table=segmenten_buffer_singlepart,
    field="id_buffer",
    field_type="LONG",
    expression=[f.name for f in arcpy.ListFields(segmenten_buffer_singlepart) if f.type == "OID"][0]
)

segmenten_spjoin_buffer = "wegsegmenten_wr_tmp3spjoinbuffer"
arcpy.SpatialJoin_analysis(
    target_features=segmenten_selectie,
    join_features=segmenten_buffer_singlepart,
    out_feature_class=segmenten_spjoin_buffer,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="HAVE_THEIR_CENTER_IN"
)

segmenten_dissolve = "wegsegmenten_wr_tmp4dissolve"
arcpy.Dissolve_management(
    in_features=segmenten_spjoin_buffer,
    out_feature_class=segmenten_dissolve,
    dissolve_field=["ident2", "LBLWEGCAT", "id_buffer"],
    statistics_fields=None,
    multi_part="MULTI_PART",
    unsplit_lines="DISSOLVE_LINES"
)

wegknopen = WegenregisterAnalyse(wegknopen_wr_input, wegsegmenten_wr_input)
wegknopen_selectie = arcpy.MakeFeatureLayer_management(
    in_features=wegknopen,
    out_layer="wegknopen_overig",
    where_clause="knooptype = 'knopen_overig'"
)

wegknopen_buffer = "wegknopen_tmp1Buffer"
arcpy.Buffer_analysis(
    in_features=wegknopen_selectie,
    out_feature_class=wegknopen_buffer,
    buffer_distance_or_field="1 Centimeters",
    line_side="FULL",
    dissolve_field=["ident2", "LBLWEGCAT"]
)

wegknopen_buffer_singlepart = "wegknopen_tmp2Singlepart"
arcpy.MultipartToSinglepart_management(
    in_features=wegknopen_buffer,
    out_feature_class=wegknopen_buffer_singlepart
)
arcpy.CalculateField_management(
    in_table=wegknopen_buffer_singlepart,
    field="id_wegknopen_buffer",
    field_type="LONG",
    expression=[f.name for f in arcpy.ListFields(segmenten_buffer_singlepart) if f.type == "OID"][0]
)

segmenten_erase = "wegsegmenten_wr_tmp5erase"
arcpy.Erase_analysis(
    in_features=segmenten_dissolve,
    erase_features=wegknopen_buffer_singlepart,
    out_feature_class=segmenten_erase
)

segmenten_erase_buffer = "wegsegmenten_wr_buffer2_tmp1"
arcpy.Buffer_analysis(
    in_features=segmenten_erase,
    out_feature_class=segmenten_erase_buffer,
    buffer_distance_or_field="1 Centimeters",
    line_side="FULL",
    dissolve_field=["ident2", "LBLWEGCAT"]
)

segmenten_erase_buffer_singlepart = "wegsegmenten_wr_buffer2_tmp2singlepart"
arcpy.MultipartToSinglepart_management(
    in_features=segmenten_erase_buffer,
    out_feature_class=segmenten_erase_buffer_singlepart
)

arcpy.CalculateField_management(
    in_table=segmenten_erase_buffer_singlepart,
    field="id_erasebuffer",
    field_type="LONG",
    expression=[f.name for f in arcpy.ListFields(segmenten_buffer_singlepart) if f.type == "OID"][0]
)

segmenten_spjoin_buffer2 = "wegsegmenten_wr_tmp6spjoinbuffer2"
arcpy.SpatialJoin_analysis(
    target_features=segmenten_selectie,
    join_features=segmenten_erase_buffer_singlepart,
    out_feature_class=segmenten_spjoin_buffer2,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="HAVE_THEIR_CENTER_IN"
)

segmenten_dissolve2 = "wegsegmenten_wr_tmp7dissolve"
arcpy.Dissolve_management(
    in_features=segmenten_spjoin_buffer,
    out_feature_class=segmenten_dissolve2,
    dissolve_field=["ident2", "LBLWEGCAT", "id_erasebuffer"],
    statistics_fields=None,
    multi_part="MULTI_PART",
    unsplit_lines="DISSOLVE_LINES"
)
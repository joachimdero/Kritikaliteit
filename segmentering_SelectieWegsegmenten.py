"""
Script documentation

- Tool parameters are accessed using arcpy.GetParameter() or 
                                     arcpy.GetParameterAsText()
- Update derived parameter values using arcpy.SetParameter() or
                                        arcpy.SetParameterAsText()
"""
import arcpy


def script_tool(in_wegsegment, in_segmenten_vc):
    # selecteer alle wegsegmenten die behoren tot L1 og hoger of in beheer zijn van AWV (met voorwaarden)
    where_clause = """
        (wegcat IN ('L1', 'PI', 'PII', 'PII-1', 'PII-2', 'PII-4', 'S', 'S1', 'S2', 'S3', 'S4', 'H') 
            Or (lblbeheer LIKE 'Agentschap Wegen en Verkeer%' And ident8 <> '' And ident8 IS NOT NULL AND ident8 NOT LIKE '____7%')) 
        And lblstatus = 'in gebruik' And lbltgbep IN ('openbare weg', 'tolweg') 
        And (doorsteek IN ('0', 'False') Or (doorsteek NOT IN ('0', 'False') And morf = 104)) 
        And beheer <> 'PARTIC' 
        And morf IN (101,102, 103, 105, 104, 106, 107, 109, 110)
        """
    tmp_SelectieWegsegmentenL1Plus = basisnaam+"_tmp1SelectieL1Plus"
    arcpy.ExportFeatures_conversion(
        in_features=in_wegsegment,
        out_features=tmp_SelectieWegsegmentenL1Plus,
        where_clause=where_clause
    )


    # selecteer alle wegsegmenten die gebruikt worden in segmenten_vc
    arcpy.AddMessage("selecteer alle wegsegmenten die gebruikt worden in segmenten_vc")
    wsoidn_vc = [row[0] for row in arcpy.da.SearchCursor(in_segmenten_vc,["WS_OIDN","FIRST_Code"]) if row[1] not in ("",None)]
    where_clause = f"id IN {wsoidn_vc}"
    arcpy.AddMessage(f"whereclause:{where_clause[:200],'....',where_clause[-10:]}")

    arcpy.MakeFeatureLayer_management(
        in_features=tmp_SelectieWegsegmentenL1Plus,
        out_layer="layer_SelectieWegsegmentenL1Plus"
    )
    #selecteer wegsegmenten die gebruikt worden in segmenten_vc
    arcpy.SelectLayerByAttribute_management(
        in_layer_or_view="layer_SelectieWegsegmentenL1Plus",
        selection_type="NEW_SELECTION",
        where_clause=f"id IN {tuple(wsoidn_vc)}"
    )
    #selecteer aansluitende op- en afritten
    arcpy.MakeFeatureLayer_management(
        in_features=in_wegsegment,
        out_layer="layer_wegsegment_inuitrit",
        where_clause = "lblmorf = 'op- of afrit, behorende tot een niet-gelijkgrondse verbinding'"
    )
    arcpy.SelectLayerByLocation_management(
        in_layer="layer_wegsegment_inuitrit",
        overlap_type="WITHIN_A_DISTANCE",
        select_features=in_segmenten_vc,
        search_distance="50 Meters",
        selection_type="NEW_SELECTION"
    )
    wsoidn_inuitrit = [row[0] for row in arcpy.da.SearchCursor("layer_wegsegment_inuitrit", ["id"])]
    arcpy.AddMessage(f"wsoidn 1148508 in wsoidn_inuitrit: {1148508 in wsoidn_inuitrit}")
    arcpy.AddMessage(f"{len(wsoidn_vc)} wegsegmenten in segmenten_vc")
    wsoidn_vc = tuple(set(wsoidn_vc + wsoidn_inuitrit))
    arcpy.AddMessage(f"wsoidn 1148508 in wsoidn_vc: {1148508 in wsoidn_vc}")
    arcpy.ExportFeatures_conversion("layer_wegsegment_inuitrit","testlocation")

    arcpy.AddMessage(f"{len(wsoidn_vc)} wegsegmenten in segmenten_vc")

    # selecteer bijkomende wegsegmenten omdat hun wegnummer (of deel er van) voorkomt in de selectie VC, hierdoor kunnen overige takken die geen naam hebben mee geselecteerd worden
    arcpy.AddMessage("selecteer alle wegnummers die gebruikt worden in segmenten_vc")
    wegnummer_vc_selectie = tuple(set([row[0] for row in arcpy.da.SearchCursor("layer_SelectieWegsegmentenL1Plus",["ident8"]) if row[0] not in (None,"") and row[0][0]not in ("N",)]))
    arcpy.AddMessage(f"{len(wegnummer_vc_selectie)} wegnummers gebruikt in segmenten_vc: {wegnummer_vc_selectie[:20]}")

    # wegnummer_vc_selectie2 = [wegnummer[:6] for wegnummer in wegnummer_vc_selectie]
    # arcpy.AddMessage(f"{len(wegnummer_vc_selectie)} wegnummers gebruikt in segmenten_vc: {wegnummer_vc_selectie2[:200]}")

    wsoidn_wegsegment = []
    with arcpy.da.SearchCursor(tmp_SelectieWegsegmentenL1Plus,["id","ident8"]) as sc:
        for row in sc:
            if row[1] == None:
                continue
            elif row[1] in wegnummer_vc_selectie or row[0] in wsoidn_vc:
                wsoidn_wegsegment.append(row[0])
    wsoidn_wegsegment = tuple(set(wsoidn_wegsegment))
    wsoidn_vc = wsoidn_vc+wsoidn_wegsegment
    arcpy.AddMessage(f"wsoidn 1148508 in wsoidn_vc: {1148508 in wsoidn_vc}")
    arcpy.AddMessage(f"{len(wsoidn_vc)} segmenten behoren tot net vc")
    where_clause = f"id NOT IN {wsoidn_vc}"
    arcpy.AddMessage(f"whereclause:{where_clause[:200],'....',where_clause[-10:]}")

    tmp_wegsegmenten_nietvc = basisnaam+"_tmp2SelectieNietVc"
    arcpy.AddMessage(f"tussentijds resultaat")
    arcpy.ExportFeatures_conversion(
        in_features=tmp_SelectieWegsegmentenL1Plus,
        out_features=tmp_wegsegmenten_nietvc,
        where_clause=f"id NOT IN {wsoidn_vc}"
    )
    return tmp_wegsegmenten_nietvc


if __name__ == "__main__":
    in_wegsegment = arcpy.GetParameterAsText(0)
    in_segmenten_vc = arcpy.GetParameterAsText(1)
    basisnaam = "wegenregister_fs"
    tmp_wegsegmenten_nietvc = script_tool(in_wegsegment, in_segmenten_vc)
    wegenregister_selectie = basisnaam+"_tmp3SelectieWegsegmenten"
    arcpy.AddMessage(f"voeg segementen onderliggend wegennet en vc samen")
    arcpy.Merge_management(
        inputs=[tmp_wegsegmenten_nietvc,in_segmenten_vc],
        output=wegenregister_selectie
    )
    arcpy.AddMessage(f"maak intersection")
    arcpy.analysis.Intersect(
        in_features=[f"{wegenregister_selectie}"],
        out_feature_class= basisnaam + "_intersection",
        join_attributes="ONLY_FID",
        cluster_tolerance=None,
        output_type="POINT"
    )
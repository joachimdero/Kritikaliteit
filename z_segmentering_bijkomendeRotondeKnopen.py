import arcpy


# -*- coding: utf-8 -*-

def BijkomendeRotondeKnopen(in_wegsegment, in_wegknopen_geselecteerd, in_wegknopen_preselectie,
                            out_wegknoop):  # BijkomendeRotondeKnopen
    arcpy.management.Dissolve(
        in_features=in_wegsegment,
        out_feature_class="wegenregister_fs_1tmp1_dissMorfologie",
        dissolve_field=["lblmorf"],
        multi_part="SINGLE_PART",
        unsplit_lines="UNSPLIT_LINES")

    # maak layer met enkel rotondes en verkeerspleinen
    arcpy.MakeFeatureLayer_management(
        in_features="wegenregister_fs_1tmp1_dissMorfologie",
        out_layer="rotondes",
        where_clause="lblmorf IN ('rotonde', 'speciale verkeerssituatie')"
    )

    # selecteer in rotondes degene waar reeds een knoop voor geselecteerd werd (overige knopen)
    arcpy.SelectLayerByLocation_management(
        in_layer="rotondes",
        overlap_type="INTERSECT",
        select_features=in_wegknopen_geselecteerd,
        selection_type="NEW_SELECTION"
    )

    # selecteer knopen (reeds eerder geselecteerde (rotondeknopen) voor de geselecteerde rotondes
    arcpy.MakeFeatureLayer_management(
        in_features=in_wegknopen_preselectie,
        out_layer="in_wegknopen_preselectie_rotonde",
        where_clause="knooptype = 'knopen_rotonde_zonder_wijziging'"
    )

    # selecteer knopen op geselecteerde rotondes
    arcpy.SelectLayerByLocation_management(
        in_layer="in_wegknopen_preselectie_rotonde",
        overlap_type="INTERSECT",
        select_features="rotondes",
        selection_type="NEW_SELECTION"
    )

    # exporter de geselecteerde rotondeknopen
    arcpy.conversion.ExportFeatures(
        in_features="in_wegknopen_preselectie_rotonde",
        out_features=out_wegknoop
    )


# ----------------------


in_wegsegment = arcpy.GetParameterAsText(0)
in_wegknopen_geselecteerd = arcpy.GetParameterAsText(1)
in_wegknopen_preselectie = arcpy.GetParameterAsText(2)
out_wegknoop = arcpy.GetParameterAsText(3)

BijkomendeRotondeKnopen(in_wegsegment, in_wegknopen_geselecteerd, in_wegknopen_preselectie, out_wegknoop)

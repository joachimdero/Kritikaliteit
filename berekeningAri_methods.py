import importlib
import os
import sys
import arcpy
import importlib
import constants

importlib.reload(constants)
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


def bereken_ari(in_aci_fc, in_ahi_fc, out_ari_fc):
    arcpy.AddMessage("- bereken_ari")
    arcpy.ExportFeatures_conversion(
        in_features=in_ahi_fc,
        out_features=out_ari_fc
    )

    AwvFunctiesAlgemeen.join_field_multiple_join_fields(
        input_table=out_ari_fc,
        f_join_inputtable=["ws_oidn", "richting_meting"],
        join_table=in_aci_fc,
        f_join_jointable=["WS_OIDN", "RICHTING"],
        f_add=[
            F_WEGCAT,
            F_ACI_SEGMENT,
            F_ACI_SEGMENT_BUCKET,
            F_ACI_NETWERKSEGMENT,
            F_ACI_NETWERKSEGMENT_BUCKET
        ]
    )

    f_uc = [F_ACI_SEGMENT, F_ACI_NETWERKSEGMENT, F_AHI_SEGMENT, F_AHI_NETWERKSEGMENT, F_ARI_SEGMENT,
            F_ARI_SEGMENT_BUCKET, F_ARI_NETWERKSEGMENT, F_ARI_NETWERKSEGMENT_BUCKET,
            "ahi_gewogen_gemiddelde", "ari_netwerksegment2", "ari_netwerksegment2_bucket"]

    for field in (F_ARI_SEGMENT, F_ARI_SEGMENT_BUCKET, F_ARI_NETWERKSEGMENT, F_ARI_NETWERKSEGMENT_BUCKET,
                  "ari_netwerksegment2", "ari_netwerksegment2_bucket"):
        if field not in [f.name for f in arcpy.ListFields(out_ari_fc)]:
            arcpy.AddField_management(
                in_table=out_ari_fc,
                field_name=field,
                field_type="LONG"
            )

    with (arcpy.da.UpdateCursor(out_ari_fc, f_uc) as uc):
        for i, row in enumerate(uc):
            if i % 10000 == 0 or i < 5:
                arcpy.AddMessage(f"{i} rijen behandeld")
            aci_segment, aci_netwerksegment, ahi_segment, ahi_netwerksegment, ari_segment, ari_segment_bucket, \
                ari_netwerksegment, ari_netwerksegment_bucket, ahi_gewogen_gemiddelde, ari_netwerksegment2, ari_netwerksegment2_bucket = row
            # if aci_segment is None:
            #     aci_segment = 0
            # if aci_netwerksegment is None:
            #     aci_netwerksegment = 0

            if ahi_segment is None or aci_segment is None or not (0 <= ahi_segment < 100 or 0 <= aci_segment < 100):
                if i in range(0, 1000):
                    arcpy.AddMessage(f"kan niet berekenen: v_staat,v_aci:{ahi_segment, aci_segment}")
                    ari_segment, ari_segment_bucket = 0, 0
            else:
                ari_segment = aci_segment * ahi_segment
                ari_segment_bucket = bereken_ari_bucket(ari_segment)

            if ahi_netwerksegment is None or aci_netwerksegment is None or not (0 <= ahi_netwerksegment < 100 or 0 <= aci_netwerksegment < 100):
                if i in range(0, 1000):
                    arcpy.AddMessage(f"kan niet berekenen: v_staat,v_aci:{ahi_segment, aci_segment}")
                    ari_segment, ari_segment_bucket = 0, 0
            else:
                ari_netwerksegment = aci_netwerksegment * ahi_netwerksegment
                ari_netwerksegment_bucket = bereken_ari_bucket(ari_netwerksegment)
                ari_netwerksegment2 = aci_netwerksegment * ahi_gewogen_gemiddelde
                ari_netwerksegment2_bucket = bereken_ari_bucket(ari_netwerksegment2)

            row_upd = [aci_segment, aci_netwerksegment, ahi_segment, ahi_netwerksegment, ari_segment,
                       ari_segment_bucket,
                       ari_netwerksegment, ari_netwerksegment_bucket, ahi_gewogen_gemiddelde, ari_netwerksegment2,
                       ari_netwerksegment2_bucket]
            uc.updateRow(row_upd)


def bereken_ari_bucket(v_ari):
    if v_ari is None or v_ari == 0:
        return 0
    elif 800 > v_ari >= 0:
        return 1
    elif v_ari < 1600:
        return 2
    elif v_ari < 4000:
        return 3
    elif v_ari < 6400:
        return 4
    elif v_ari < 10000:
        return 5

import os
import sys
import arcpy
import importlib

import staatvandewegXaci_methods
importlib.reload(staatvandewegXaci_methods)
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
from staatvandewegXaci_methods import  bereken_ari,   \
    bereken_ahi, bereken_ahi_netwerksegmenten, maak_minimale_fc

# ---------------------------
i = 0
fc_staatvandeweg = arcpy.GetParameterAsText(i)
i += 1
f_globaleindex = arcpy.GetParameterAsText(i)
i += 1
f_globaleklasse = arcpy.GetParameterAsText(i)
i += 1
aci_fc = arcpy.GetParameterAsText(i)
i += 1
f_aci = arcpy.GetParameterAsText(i)
i += 1
fc_netwerksegmenten = arcpy.GetParameterAsText(i)
i += 1
wegsegmenten_fc = arcpy.GetParameterAsText(i)
i += 1
arcpy.env.workspace = arcpy.GetParameterAsText(i)
i += 1
cookie = arcpy.GetParameterAsText(i)
i += 1
del i

# ---------------------------
fc_output = "ari"
maak_minimale_fc(fc_staatvandeweg,fc_output)
# bereken de ahi
bereken_ahi(fc_output, f_globaleindex, f_globaleklasse)
#bereken de aci van een netwerksegment
bereken_ahi_netwerksegmenten(fc_output, "ahi", fc_netwerksegmenten)

# table = aci_fc_to_aci_table(aci_fc)

bereken_ari(
    in_staatvandeweg=fc_output,
    in_aci=aci_fc,
    out_ari="ari"
)

# ari_fc = add_geometry(aci_fc, wegsegmenten_fc)
# ari_fc_met_wegnr_lyr = "ari_fc_met_wegnr_lyr"
# arcpy.MakeFeatureLayer_management(
#     in_features=ari_fc,
#     out_layer=ari_fc_met_wegnr_lyr,
#     where_clause="ident8 <> '' AND ident8 IS NOT NULL"
# )
# arcpy.AddMessage(f"aantal features met wegnummer: {arcpy.GetCount_management(ari_fc_met_wegnr_lyr)[0]}")

# add_relatieve_weglocatie(
#     cookie=cookie,
#     input_fc=ari_fc_met_wegnr_lyr
# )

# ---------------------------------------------------------------------
# if __name__ == '__main__':
#     print("test")
#     add_relatieve_weglocatie(
#         cookie="8b68337f38be41068071a6d52868a0ff",
#         input_fc="C:\\GoogleTeamAim\\Team AIM\\Team AIM\\Data beheer\\Projecten\\AddHoc\\criticaliteit\\staatvandeweg.gdb\\ari_fc"
#     )

import os.path
import sys

import arcpy

in_wegsegmenten_fc = arcpy.GetParameterAsText(0)
in_uv_fc = arcpy.GetParameterAsText(1)#uitzonderlijkvervoer uit awvdata.gdb/featureserver
out_fc = arcpy.GetParameterAsText(2)

arcpy.env.workspace = arcpy.GetParameterAsText(3)

#controle of inputfc de nodige velden bevat
def controle_input(in_wegsegmenten_fc,in_uv_fc):
    f_in_wegsegmenten = [f.name for f in arcpy.ListFields(in_wegsegmenten_fc)]
    if not "WS_OIDN" in f_in_wegsegmenten:
        arcpy.AddError(f"WS_OIDN ontbreekt in {in_wegsegmenten_fc}")
        sys.exit()

    f_in_uv_fc = [f.name for f in arcpy.ListFields(in_uv_fc)]
    verwachte_veldnamen = ['WS_OIDN', 'UV90Ton_Ne', 'UV108Ton_N',
                           'UV120Ton_N', 'UVsnelwege', ]
    for f in verwachte_veldnamen:
        if f not in f_in_uv_fc:
            arcpy.AddError(f"{f} ontbreekt in {in_uv_fc}")
            sys.exit()

    return verwachte_veldnamen

def in_uc_fc_to_dict(in_uv_fc,f_sc):
    uv_dict = {}
    with arcpy.da.SearchCursor(in_uv_fc,f_sc) as sc:
        for row in sc:
            if 'ja' in row[1:] or 'Ja' in row[1:] or 'JA' in row[1:]:
                uv_dict[row[0]] = 'uv'
    return uv_dict

def schrijf_to_out_fc(in_wegsegmenten_fc,uv_dict,out_fc):
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(out_fc),
        out_name=os.path.basename(out_fc),
        geometry_type=arcpy.Describe(in_wegsegmenten_fc).shapeType,
        template=in_wegsegmenten_fc)
    f_uv = "UV"
    arcpy.AddField_management(
        in_table=out_fc,
        field_name=f_uv,
        field_type="TEXT",
        field_length=10
    )
    f_sc = [f.name.replace("Shape","Shape@") for f in arcpy.ListFields(in_wegsegmenten_fc) if f.name not in ("SHAPE_Length","Shape_Length")]
    f_ic = f_sc + [f_uv]
    arcpy.AddMessage(f"f_sc:{f_sc}")
    arcpy.AddMessage(f"f_ic:{f_ic}")
    ic = arcpy.da.InsertCursor(out_fc,f_ic)
    with arcpy.da.SearchCursor(in_wegsegmenten_fc,f_sc) as sc:
        for row in sc:
            row = list(row)
            if row[f_sc.index("WS_OIDN")] in uv_dict:
                row.append(uv_dict[row[f_sc.index("WS_OIDN")]])
            else:
                row.append("-")
            ic.insertRow(row)
    del ic

#------------------------------------
arcpy.AddMessage("controle inputgegevens")
f_uv_sc = controle_input(in_wegsegmenten_fc,in_uv_fc)
arcpy.AddMessage("lees gegevens uitzonderlijk vervoer")
uv_dict = in_uc_fc_to_dict(in_uv_fc,f_uv_sc)
arcpy.AddMessage(f"uv_dict:{str(uv_dict)[:500]}")
arcpy.AddMessage("schrijf weg")
schrijf_to_out_fc(in_wegsegmenten_fc,uv_dict,out_fc)


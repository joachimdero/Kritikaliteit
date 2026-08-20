import os.path
import sys
import arcpy
from constants import *

try:
    # importeer Awv functie en downloadFunctie
    from ....AwvFunctiesAlgemeen import AwvFunctiesAlgemeen

except ImportError:
    from sys import path

    pythonVersion = sys.version_info.major
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


def bereken_bucket(index):
    aci_groepen = {
        (-100, 0.000): 0,
        (0.000, 20): 1,
        (20, 40): 2,
        (40, 60): 3,
        (60, 80): 4,
        (80, 100): 5,
    }

    for aci_groep in aci_groepen:
        if aci_groep[0] <= index <= aci_groep[1]:
            # return f'{aci_groep},{aci_groepen[aci_groep]}'
            return aci_groepen[aci_groep]
        else:
            aci_groepen[aci_groep] = 'niet in klasse'


def voeg_aci_velden_toe(f_list_input_values, f_uc, in_table):
    arcpy.AddMessage(f'voeg_aci_velden_toe: {f_list_input_values}')
    f_in_table = [f.name for f in arcpy.ListFields(in_table)]
    for f in f_list_input_values + ['totaal']:
        field_name = f + "_aci"
        if field_name not in f_in_table:
            arcpy.AddMessage(f'voeg veld {field_name} toe')
            arcpy.AddField_management(in_table=in_table,
                                      field_name=field_name,
                                      field_type='DOUBLE'
                                      )
        f_uc.append(field_name)

        field_name = f + "_aci_bucket"
        if field_name not in f_in_table:
            arcpy.AddMessage(f'voeg veld {field_name} toe')
            arcpy.AddField_management(in_table=in_table,
                                      field_name=field_name,
                                      field_type='TEXT',
                                      field_length=20
                                      )
        f_uc.append(field_name)

    return f_uc


def z_bereken_aci_wegcat(value, refwaarde):
    aci = refwaarde

    return aci


def bereken_aci_uv(value, refwaarde):
    if value == "uv":
        aci = 100
    else:
        aci = 0
    return aci


def bereken_aci_net(value, refwaarde):
    if value is not None:
        if value == "Kernnet":
            aci = 100
        elif "Aanvullend" in value:
            aci = 50
        else:
            aci = 0
    else:
        aci = 0
    return aci


def bereken_aci_aantal(value, refwaarde):
    if value > 0 and refwaarde > 0:
        aci = min(value / refwaarde * 100, 100)
    else:
        aci = 0
    return aci


def bereken_aci_sat(value, refwaarde):
    aci = value
    return aci


def bereken_aci_segment(values, gewicht):  # vrachtwagens 3*personenwagens
    """    gewicht = {
        "H": {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 50,
            'sat_max': 20,
            'OV': 10,
            'UV': 0,
        },
        "S": {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 20,
            'sat_max': 20,
            'OV': 30,
            'UV': 10,
        },
        "L": {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 20,
            'sat_max': 20,
            'OV': 30,
            'UV': 10,
        }
    }
    gewicht_aandeel_vrachtwagens = {
        "H": {
            'WEGCAT': 0,
            'PW_ETM': 0,
            'VR_ETM': 0,
            'sat_max': 20,
            'OV': 10,
            'UV': 0,
            'vr_aandeel': 70
        },
        "S": {
            'WEGCAT': 0,
            'PW_ETM': 0,
            'VR_ETM': 0,
            'sat_max': 20,
            'OV': 30,
            'UV': 10,
            'vr_aandeel': 40
        },
        "L": {
            'WEGCAT': 0,
            'PW_ETM': 0,
            'VR_ETM': 0,
            'sat_max': 20,
            'OV': 30,
            'UV': 10,
            'vr_aandeel': 40
        }
    }"""

    def bereken_wegcatgroep(wegcat):
        if wegcat in ("-8", "-9", "EW", "OW", "L", "L1", "L2", "L3"):
            wegcatgroep = "L"
        elif wegcat in ("P", "EHW", "VHW", "PI", "PII", "PII-4", "PII-2", "H"):
            wegcatgroep = "H"
        elif wegcat in ("IW", "RW", "S", "S1", "S2", "S3"):
            wegcatgroep = "S"
        else:
            wegcatgroep = wegcat[0]
            arcpy.AddError(f"wegcatgroep niet herkend: {wegcatgroep} voor {wegcat}")
        return wegcatgroep

    aci_gewicht = 0
    if values['PW_ETM'] == 0 and values['VR_ETM'] == 0 and values['sat_max'] == 0:
        return 0

    # arcpy.AddMessage(f'values:{values}')
    wegcat = values['WEGCAT']
    # wegcategorie moet nog vertaald worden naar één van de klassen, mss niet hier
    # arcpy.AddMessage("/")
    for v in values:
        if v == 'WEGCAT':
            continue
        else:
            v_gewicht = values[v] * gewicht[bereken_wegcatgroep(wegcat)][v] / 100
            aci_gewicht += v_gewicht

    return max(aci_gewicht, 1)  # minimum 1, zodat er geen segmenten zijn met aci=0


def freq(in_table, fields_output):
    frequencys = [f for f in fields_output if '_bucket' in f]
    for frequency_fields in frequencys:
        arcpy.analysis.Frequency(
            in_table=in_table,
            out_table=in_table + "_Freq" + frequency_fields,
            frequency_fields=frequency_fields,
            summary_fields="lengte_km"
        )


def bereken_sat_max(in_table):
    if 'sat_max' not in [f.name for f in arcpy.ListFields(in_table)]:
        arcpy.AddField_management(in_table=in_table,
                                  field_name='sat_max',
                                  field_type='DOUBLE'
                                  )
    with arcpy.da.UpdateCursor(in_table, ['sat_08', 'sat_17', 'sat_max']) as uc:
        for row in uc:
            row[2] = max(row[0], row[1])
            uc.updateRow(row)

def bereken_aandeelvrachtwagens(in_table):
    f_vr_aandeel = 'vr_aandeel'
    if f_vr_aandeel not in [f.name for f in arcpy.ListFields(in_table)]:
        arcpy.AddField_management(in_table=in_table,
                                  field_name=f_vr_aandeel,
                                  field_type='DOUBLE'
                                  )
    with arcpy.da.UpdateCursor(in_table, ['pw_etm', 'vr_etm', f_vr_aandeel]) as uc:
        for pw, vr, vr_aandeel in uc:
            if pw + vr > 0:
                vr_aandeel = max((vr / (pw + vr) * 100), 0)
            else:
                vr_aandeel = 0
            uc.updateRow((pw, vr, vr_aandeel))


def bereken_aci_buur_wegcat(in_table, in_segmentering, in_wegenregister):
    def wk(in_table, in_wegenregister):
        # voeg "B_WK_OIDN;E_WK_OIDN" toe aan de segmenten
        arcpy.AddMessage(f"voeg B_WK_OIDN;E_WK_OIDN van {in_wegenregister} toe aan {in_table}")
        if 'B_WK_OIDN' not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.management.JoinField(
                in_data=in_table,
                in_field="WS_OIDN",
                join_table=in_wegenregister,
                join_field="WS_OIDN",
                fields="B_WK_OIDN;E_WK_OIDN",
                fm_option="NOT_USE_FM",
                field_mapping=None
            )

    def bereken_aci_endpoints(in_table):
        endpoints = {}
        with arcpy.da.SearchCursor(in_table,
                                   ['WEGCAT', 'totaal_aci', 'B_WK_OIDN', 'E_WK_OIDN']) as sc:
            for row in sc:
                if None in row:
                    arcpy.AddMessage(f"row met None: {row}")
                for wk_oidn in (row[2], row[3]):
                    aci = row[1]
                    if wk_oidn not in endpoints:
                        endpoints[wk_oidn] = {row[0]: [aci]}
                    elif row[0] not in endpoints[wk_oidn]:
                        endpoints[wk_oidn][row[0]] = [aci]
                    else:
                        endpoints[wk_oidn][row[0]].append(aci)
        arcpy.AddMessage(f"len endpoints: {len(endpoints)}")
        arcpy.AddMessage(f"endpoints (<200): {str(endpoints)[:200]}")
        return endpoints

    def bereken_verbinding(in_table, in_segmentering):
        arcpy.MakeFeatureLayer_management(
            in_features=in_table,
            out_layer=in_table + "_lyr"
        )
        arcpy.AddField_management(
            in_table=in_table,
            field_name="verbinding",
            field_type="TEXT",
            field_length=20
        )
        arcpy.AddMessage(f"velden in {in_segmentering}: {[f.name for f in arcpy.ListFields(in_segmentering)]}")

        arcpy.MakeFeatureLayer_management(
            in_features=in_segmentering,
            out_layer=os.path.basename(in_segmentering + "_lyr"),
            where_clause="SG_naam LIKE '%complex%' Or SG_naam LIKE '%knoop%' Or SG_naam LIKE "
                         "'%verbinding%' Or SG_naam LIKE '%tussen oprit%' Or SG_naam LIKE '%tussen afrit%'"
        )
        arcpy.MakeFeatureLayer_management(
            in_features=in_table + '_lyr',
            out_layer=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH"
        )
        arcpy.SelectLayerByLocation_management(
            in_layer=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH",
            overlap_type="SHARE_A_LINE_SEGMENT_WITH",
            select_features=os.path.basename(in_segmentering + "_lyr"),
            selection_type="SUBSET_SELECTION"
        )
        arcpy.CalculateField_management(
            in_table=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH",
            field="verbinding",
            expression="'ja'"
        )
        return in_table + "_lyr"

    def schrijf_aci_buur(in_table, endpoints):
        if "totaal_aci_buur" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="FLOAT")

        with arcpy.da.UpdateCursor(in_table,
                                   ['totaal_aci', 'totaal_aci_buur', 'B_WK_OIDN', 'E_WK_OIDN', 'WEGCAT']) as uc:
            for row in uc:
                row = list(row)
                B_WK_aci = max(endpoints[row[2]][row[4]])
                E_WK_aci = max(endpoints[row[3]][row[4]])
                aci_buur = min(B_WK_aci, E_WK_aci)
                row[1] = aci_buur
                uc.updateRow(row)

    def bereken_aci_mix(in_table):
        if F_ACI_SEGMENT not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name=F_ACI_SEGMENT, field_type="FLOAT")
        if F_ACI_SEGMENT_BUCKET not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name=F_ACI_SEGMENT_BUCKET, field_type="TEXT",
                                      field_length=50)
        with arcpy.da.UpdateCursor(in_table, ['verbinding', 'totaal_aci',
                                              'totaal_aci_buur', F_ACI_SEGMENT, F_ACI_SEGMENT_BUCKET]) as uc:
            for row in uc:
                row = list(row)
                if row[0] == 'ja':
                    row[3] = max(row[1], row[2])
                else:
                    row[3] = row[1]

                row[4] = bereken_bucket(row[3])
                uc.updateRow(row)

    # indien 'B_WK_OIDN', 'E_WK_OIDN' toevoegen indien afwezig
    wk(in_table, in_wegenregister=in_wegenregister)
    arcpy.AddMessage('-- bereken endpoints')
    endpoints = bereken_aci_endpoints(in_table=in_table)
    arcpy.AddMessage('-- bereken_verbinding')
    in_table = bereken_verbinding(in_table, in_segmentering)
    arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="LONG")
    arcpy.AddMessage('-- bereken schrijf_aci_buur')
    schrijf_aci_buur(in_table=in_table, endpoints=endpoints)
    arcpy.AddMessage('-- bereken_aci_mix')
    bereken_aci_mix(in_table=in_table)


def bereken_aci_buur_wegcat_netwerksegment(in_table, in_segmentering, in_wegenregister):
    def wk(in_table, in_wegenregister):
        # voeg "B_WK_OIDN;E_WK_OIDN" toe aan de segmenten
        if 'B_WK_OIDN' not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.management.JoinField(
                in_data=in_table,
                in_field="WS_OIDN",
                join_table=in_wegenregister,
                join_field="WS_OIDN",
                fields="B_WK_OIDN;E_WK_OIDN",
                fm_option="NOT_USE_FM",
                field_mapping=None
            )

    def bereken_aci_endpoints(in_table):
        endpoints = {}
        with arcpy.da.SearchCursor(in_table,
                                   ['WEGCAT', 'totaal_aci', 'B_WK_OIDN', 'E_WK_OIDN']) as sc:
            for row in sc:
                for wk_oidn in (row[2], row[3]):
                    aci = row[1]
                    if wk_oidn not in endpoints:
                        endpoints[wk_oidn] = {row[0]: [aci]}
                    elif row[0] not in endpoints[wk_oidn]:
                        endpoints[wk_oidn][row[0]] = [aci]
                    else:
                        endpoints[wk_oidn][row[0]].append(aci)
        arcpy.AddMessage(f"len endpoints: {len(endpoints)}")
        arcpy.AddMessage(f"endpoints (<200): {str(endpoints)[:200]}")
        return endpoints

    def bereken_verbinding(in_table, in_segmentering):
        arcpy.MakeFeatureLayer_management(
            in_features=in_table,
            out_layer=in_table + "_lyr"
        )
        arcpy.AddField_management(
            in_table=in_table,
            field_name="verbinding",
            field_type="TEXT",
            field_length=20
        )
        arcpy.MakeFeatureLayer_management(
            in_features=in_segmentering,
            out_layer=os.path.basename(in_segmentering + "_lyr"),
            where_clause="beschrijving LIKE '%complex%' Or beschrijving LIKE '%knoop%' Or beschrijving LIKE "
                         "'%verbinding%' Or beschrijving LIKE '%tussen oprit%' Or beschrijving LIKE '%tussen afrit%'"
        )
        arcpy.MakeFeatureLayer_management(
            in_features=in_table + '_lyr',
            out_layer=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH"
        )
        arcpy.SelectLayerByLocation_management(
            in_layer=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH",
            overlap_type="SHARE_A_LINE_SEGMENT_WITH",
            select_features=os.path.basename(in_segmentering + "_lyr"),
            selection_type="SUBSET_SELECTION"
        )
        arcpy.CalculateField_management(
            in_table=in_table + "_lyr_SHARE_A_LINE_SEGMENT_WITH",
            field="verbinding",
            expression="'ja'"
        )
        return in_table + "_lyr"

    def schrijf_aci_buur(in_table, endpoints):
        if "totaal_aci_buur" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="FLOAT")

        with arcpy.da.UpdateCursor(in_table,
                                   ['totaal_aci', 'totaal_aci_buur', 'B_WK_OIDN', 'E_WK_OIDN', 'WEGCAT']) as uc:
            for row in uc:
                row = list(row)
                B_WK_aci = max(endpoints[row[2]][row[4]])
                E_WK_aci = max(endpoints[row[3]][row[4]])
                aci_buur = min(B_WK_aci, E_WK_aci)
                row[1] = aci_buur
                uc.updateRow(row)

    def bereken_aci_mix(in_table):
        if "totaal_aci_mix" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_mix", field_type="FLOAT")
        if "totaal_aci_mix_bucket" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_mix_bucket", field_type="TEXT",
                                      field_length=50)
        with arcpy.da.UpdateCursor(in_table, ['verbinding', 'totaal_aci',
                                              'totaal_aci_buur', 'totaal_aci_mix', 'totaal_aci_mix_bucket']) as uc:
            for row in uc:
                row = list(row)
                if row[0] == 'ja':
                    row[3] = max(row[1], row[2])
                else:
                    row[3] = row[1]

                row[4] = bereken_bucket(row[3])
                uc.updateRow(row)

    # indien 'B_WK_OIDN', 'E_WK_OIDN' toevoegen indien afwezig
    wk(in_table, in_wegenregister=in_wegenregister)
    arcpy.AddMessage('-- bereken endpoints')
    endpoints = bereken_aci_endpoints(in_table=in_table)
    arcpy.AddMessage('-- bereken_verbinding')
    in_table = bereken_verbinding(in_table, in_segmentering)
    arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="LONG")
    arcpy.AddMessage('-- bereken schrijf_aci_buur')
    schrijf_aci_buur(in_table=in_table, endpoints=endpoints)
    arcpy.AddMessage('-- bereken_aci_mix')
    bereken_aci_mix(in_table=in_table)


def bereken_aci_buur_old(in_table, in_segmentering, in_wegenregister):
    def wk(in_table, in_wegenregister):
        # voeg "B_WK_OIDN;E_WK_OIDN" toe aan de segmenten
        if 'B_WK_OIDN' not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.management.JoinField(
                in_data=in_table,
                in_field="WS_OIDN",
                join_table=in_wegenregister,
                join_field="WS_OIDN",
                fields="B_WK_OIDN;E_WK_OIDN",
                fm_option="NOT_USE_FM",
                field_mapping=None
            )

    def bereken_aci_endpoints(in_table):
        endpoints = {}
        with arcpy.da.SearchCursor(in_table,
                                   ['totaal_aci', 'B_WK_OIDN', 'E_WK_OIDN']) as sc:
            for row in sc:
                for wk_oidn in (row[1], row[2]):
                    aci = row[0]
                    if wk_oidn not in endpoints:
                        endpoints[wk_oidn] = [aci]
                    else:
                        endpoints[wk_oidn].append(aci)
        return endpoints

    def bereken_verbinding(in_table, in_segmentering):
        arcpy.AddField_management(in_table=in_table, field_name="verbinding", field_type="TEXT", field_length=20)
        arcpy.MakeFeatureLayer_management(
            in_features=in_segmentering,
            out_layer=os.path.basename(in_table + "_lyr"),
            where_clause="beschrijving LIKE '%complex%' Or beschrijving LIKE '%knoop%' Or beschrijving LIKE "
                         "'%verbinding%' Or beschrijving LIKE '%tussen oprit%' Or beschrijving LIKE '%tussen afrit%'"
        )
        arcpy.SelectLayerByLocation_management(
            in_layer=in_table,
            overlap_type="SHARE_A_LINE_SEGMENT_WITH",
            select_features=os.path.basename(in_table + "_lyr"),
            selection_type="NEW_SELECTION"
        )
        arcpy.CalculateField_management(
            in_table=in_table,
            field="verbinding",
            expression="'ja'"
        )
        arcpy.SelectLayerByAttribute_management(
            in_layer_or_view=in_table,
            selection_type="CLEAR_SELECTION"
        )

    def schrijf_aci_buur(in_table, endpoints):
        if "totaal_aci_buur" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="FLOAT")
        with arcpy.da.UpdateCursor(in_table,
                                   ['totaal_aci', 'totaal_aci_buur', 'B_WK_OIDN', 'E_WK_OIDN']) as uc:
            for row in uc:
                row = list(row)
                B_WK_aci = max(endpoints[row[2]])
                E_WK_aci = max(endpoints[row[3]])
                aci_buur = min(B_WK_aci, E_WK_aci)
                row[1] = aci_buur
                uc.updateRow(row)

    def bereken_aci_mix(in_table):
        if F_ACI_SEGMENT not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name=F_ACI_SEGMENT, field_type="FLOAT")
        if F_ACI_SEGMENT_BUCKET not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table=in_table, field_name=F_ACI_SEGMENT_BUCKET, field_type="TEXT",
                                      field_length=50)
        with arcpy.da.UpdateCursor(in_table, ['verbinding', 'totaal_aci',
                                              'totaal_aci_buur', F_ACI_SEGMENT, F_ACI_SEGMENT_BUCKET]) as uc:
            for row in uc:
                row = list(row)
                if row[0] == 'ja':
                    row[3] = max(row[1], row[2])
                else:
                    row[3] = row[1]

                row[4] = bereken_bucket(row[3])
                uc.updateRow(row)

    # indien 'B_WK_OIDN', 'E_WK_OIDN' toevoegen indien afwezig
    wk(in_table, in_wegenregister=in_wegenregister)
    arcpy.AddMessage('-- bereken endpoints')
    endpoints = bereken_aci_endpoints(in_table=in_table)
    arcpy.AddMessage('-- bereken_verbinding')
    bereken_verbinding(in_table, in_segmentering)
    arcpy.AddField_management(in_table=in_table, field_name="totaal_aci_buur", field_type="LONG")
    arcpy.AddMessage('-- bereken schrijf_aci_buur')
    schrijf_aci_buur(in_table=in_table, endpoints=endpoints)
    arcpy.AddMessage('-- bereken_aci_mix')
    bereken_aci_mix(in_table=in_table)


def outliers(values, outlier_threshold):
    import numpy
    arcpy.AddMessage(f"aantal waarden: {len(values)}")

    # Bereken het gemiddelde en de standaardafwijking
    mean_value = numpy.mean(values)
    arcpy.AddMessage(f"mean_value: {mean_value}")

    std_dev = numpy.std(values)
    arcpy.AddMessage(f"std_dev: {std_dev}")

    # Definieer een drempelwaarde voor sterke afwijkingen (bijv. 3 standaardafwijkingen)
    outlier_threshold = outlier_threshold

    # Filter de sterk afwijkende waarden
    outliers = [value for value in values if abs(value - mean_value) > outlier_threshold * std_dev]
    values2 = [value for value in values if value not in outliers]

    arcpy.AddMessage(f" lenSterk afwijkende waarden:{len(outliers)}")
    arcpy.AddMessage(f"Sterk afwijkende waarden (eerste 20):{outliers[:20]}")
    arcpy.AddMessage(f"min waarden origineel: {min(values)} => {min(values2)}")
    arcpy.AddMessage(f"max waarden origineel: {max(values)} => {max(values2)}")
    return max(values2)


def maak_fc_aci(in_verkeersmodel, in_wegenregister, in_uv, in_vervoernet, out_aci):
    # data samenvoegen
    # arcpy.AddMessage('maak_fc_aci met whereclause OBJECTID < 10')
    # enkel nodige velden overhouden
    def field_mapping_verkeersmodel(in_verkeersmodel):
        """Maak een field mapping voor de velden die we nodig hebben in het ACI netwerk"""
        arcpy.AddMessage(f"maak field mapping voor {in_verkeersmodel}")
        fields = arcpy.ListFields(in_verkeersmodel)
        field_mapping = arcpy.FieldMappings()
        for f in fields:
            if f.name in ['WS_OIDN', 'RICHTING', 'PW_ETM', 'VR_ETM', 'SAT_08', 'SAT_17',
                          'id_verkeersmodel']:
                field_map = arcpy.FieldMap()
                field_map.addInputField(in_verkeersmodel, f.name)
                field_mapping.addFieldMap(field_map)
        return field_mapping

    arcpy.AddMessage(f"export features van {in_verkeersmodel} naar {out_aci}")
    arcpy.ExportFeatures_conversion(
        in_features=in_verkeersmodel,
        out_features=out_aci,
        field_mapping=field_mapping_verkeersmodel(in_verkeersmodel)
        # where_clause="OBJECTID < 10",
    )
    field_names = {f.name for f in arcpy.ListFields(out_aci)}
    if "WEGCAT" not in field_names:
        arcpy.AddMessage(f"wegcat toevoegen aan {out_aci}")
        arcpy.JoinField_management(
            in_data=out_aci,
            in_field="WS_OIDN",
            join_table=in_wegenregister,
            join_field="WS_OIDN",
            fields="WEGCAT")
    arcpy.AddMessage(f"UV  toevoegen aan {out_aci}")

    if "UV" not in field_names:
        arcpy.AddMessage(f"UV toevoegen aan {out_aci}")
        AwvFunctiesAlgemeen.JoinField(
            table_target=out_aci,
            f_join_target="WS_OIDN",
            table_join=in_uv,
            f_join_join="WS_OIDN",
            joinFields=["UV"],
            veld_overschrijven=True)
    if "categorie" not in field_names and "OV" not in field_names:
        arcpy.AddMessage(f"vervoernet  toevoegen aan {out_aci}")
        arcpy.JoinField_management(
            in_data=out_aci,
            in_field="WS_OIDN",
            join_table=in_vervoernet,
            join_field="WS_OIDN",
            fields="categorie")
        arcpy.AlterField_management(
            in_table=out_aci,
            field="categorie",
            new_field_name="OV",
            new_field_alias="OV"
        )

    # velden hernoemen
    fields = arcpy.ListFields(out_aci)
    # Loop door alle velden
    arcpy.AddMessage(f"velden hernoemen {out_aci}")
    for f in fields:
        if f.name.startswith("FIRST_") and f.name not in ("FIRST_Shape_Length",):
            new_field_name = f.name.replace("FIRST_", "")
            arcpy.AlterField_management(
                in_table=out_aci,
                field=f.name,
                new_field_name=new_field_name,
                new_field_alias=new_field_name
            )

    return out_aci


def aci_netwerksegment(in_aci_table, in_segmentering):
    # voeg netwerkinformatie toe aan features
    AwvFunctiesAlgemeen.JoinFieldMultipleJoinFields(
        inputTable=in_aci_table,
        inputJoinField=["WS_OIDN", "RICHTING"],
        joinTable=in_segmentering,
        outputJoinField=["ws_oidn", "richting_segment"],
        joinFields=["netwerk_id", "SG_naam"]
    )

    # zoek hoogste aci waarde per feature
    aci_max_netwerksegment = {}  # netwerksegment:aci
    with arcpy.da.SearchCursor(in_aci_table, ["netwerk_id", F_ACI_SEGMENT, F_ACI_SEGMENT_BUCKET]) as sc:
        for row in sc:
            if row[0] not in aci_max_netwerksegment:
                aci_max_netwerksegment[row[0]] = [row[1], row[2]]
            elif aci_max_netwerksegment[row[0]][0] < row[1]:
                aci_max_netwerksegment[row[0]] = [row[1], row[2]]
    # schrijf hoogste waarde weg
    arcpy.AddField_management(
        in_table=in_aci_table,
        field_name=F_ACI_NETWERKSEGMENT,
        field_type="FLOAT"
    )
    arcpy.AddField_management(
        in_table=in_aci_table,
        field_name=F_ACI_NETWERKSEGMENT_BUCKET,
        field_type="SHORT"
    )
    with arcpy.da.UpdateCursor(in_aci_table, ["netwerk_id", F_ACI_NETWERKSEGMENT, F_ACI_NETWERKSEGMENT_BUCKET]) as uc:
        for row in uc:
            aci = aci_max_netwerksegment[row[0]][0]
            aci_bucket = aci_max_netwerksegment[row[0]][1]
            row_upd = (row[0], aci, aci_bucket)
            uc.updateRow(row_upd)


def bereken_aci_aandeel(vr_aandeel, refwaarde):
    """Bereken het aandeel vrachtwagens in de totale verkeersintensiteit."""
    if vr_aandeel > 0:
        return min(vr_aandeel / refwaarde * 100, 100)
    else:
        return 0

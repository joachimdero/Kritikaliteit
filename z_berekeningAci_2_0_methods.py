import os.path

import arcpy
import copy


def bereken_groep(aci):
    aci_groepen = {
        (0, 10): 'Zeer klein',
        (10, 20): 'Zeer klein',
        (20, 30): 'Klein',
        (30, 40): 'Klein',
        (40, 50): 'Matig',
        (50, 60): 'Matig',
        (60, 70): 'Groot',
        (70, 80): 'Groot',
        (80, 90): 'Zeer groot',
        (90, 100): 'Zeer groot',
    }

    for aci_groep in aci_groepen:
        if aci_groep[0] <= aci <= aci_groep[1]:
            return f'{aci_groep},{aci_groepen[aci_groep]}'
        else:
            aci_groepen[aci_groep] = 'niet in klasse'


def berekening_aci(in_table, f_list_input_values=['WEGCAT', 'PW_ETM', 'VR_ETM', 'sat_max','UV','net'], refwaarden=None):
    arcpy.AddMessage('-berekening_aci')

    f_uc = copy.deepcopy(f_list_input_values)
    arcpy.AddMessage(f'f_list_input_values {f_list_input_values} ')
    f_uc, f_list_input_values = voeg_aci_velden_toe(f_list_input_values, f_uc, in_table)

    with arcpy.da.UpdateCursor(in_table, f_uc) as uc:
        for row in uc:
            # arcpy.AddMessage(f'row:{row}')
            for f in f_list_input_values:
                # arcpy.AddMessage(f'f:{f}')
                f_bron = row[f_uc.index(f)]
                if f in ('WEGCAT'):
                    continue
                #     row[f_uc.index(f + '_aci')] = bereken_aci_wegcat(f_bron, refwaarden[row[0]][f])
                #     row[f_uc.index(f + '_aci_groep')] = bereken_groep(row[f_uc.index(f + '_aci')])
                elif f in ('PW_ETM', 'VR_ETM'):
                    row[f_uc.index(f + '_aci')] = bereken_aci_aantal(f_bron, refwaarden[row[0]][f])
                    row[f_uc.index(f + '_aci_groep')] = bereken_groep(row[f_uc.index(f + '_aci')])
                elif f in ('sat_max'):
                    row[f_uc.index(f + '_aci')] = bereken_aci_sat(f_bron, refwaarden[row[0]][f])
                    row[f_uc.index(f + '_aci_groep')] = bereken_groep(row[f_uc.index(f + '_aci')])
                elif f in ('UV'):
                    row[f_uc.index(f + '_aci')] = bereken_aci_uv(f_bron, 100)
                elif f in ('net'):
                    row[f_uc.index(f + '_aci')] = bereken_aci_net(f_bron, 100)
                else:
                    arcpy.AddError(f'probleem met fields_uc: {f_uc}, f:{f}')
            v_bron = {
                'WEGCAT': row[f_uc.index('WEGCAT')],
                'PW_ETM': row[f_uc.index('PW_ETM_aci')],
                'VR_ETM': row[f_uc.index('VR_ETM_aci')],
                'sat_max': row[f_uc.index('sat_max_aci')],
                'UV': row[f_uc.index('UV_aci')],
                'net': row[f_uc.index('net_aci')],
            }
            #v_bron moet geen aci van wegcat meegeven maar wel de wegcat
            row[f_uc.index('totaal_aci')] = bereken_aci_totaal(v_bron)
            row[f_uc.index('totaal_aci_groep')] = bereken_groep(row[f_uc.index('totaal_aci')])

            uc.updateRow(row)


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

        field_name = f + "_aci_groep"
        if field_name not in f_in_table:
            arcpy.AddMessage(f'voeg veld {field_name} toe')
            arcpy.AddField_management(in_table=in_table,
                                  field_name=field_name,
                                  field_type='TEXT',
                                  field_length=20
                                  )
        f_uc.append(field_name)

    return f_uc, f_list_input_values


def bereken_aci_wegcat(value, refwaarde):
    aci = refwaarde

    return aci

def bereken_aci_uv(value, refwaarde):
    if value == "uv":
        aci = 100
    else:
        aci = 0
    return aci

def bereken_aci_net(value, refwaarde):
    if value == "kern":
        aci = 100
    elif value == "aanvullend":
        aci = 50
    else:
        aci = 0
    return aci

def bereken_aci_aantal(value, refwaarde):
    if value > 0:
        aci = min(value / refwaarde * 100,100)
    else:
        aci = 0
    return aci


def bereken_aci_sat(value, refwaarde):
    aci = value
    return aci


def bereken_aci_totaal(values):  # vrachtwagens 3*personenwagens
    gewicht= {
        "H" : {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 60,
            'sat_max': 20,
            'net': 0,
            'UV': 0,
    },
        "S" : {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 20,
            'sat_max': 20,
            'net': 30,
            'UV': 10,
    },
        "L" : {
            'WEGCAT': 0,
            'PW_ETM': 20,
            'VR_ETM': 20,
            'sat_max': 20,
            'net': 30,
            'UV': 10,
    }
    }

    aci_gewicht = 0
    if values['PW_ETM'] == 0 and values['VR_ETM'] == 0 and values['sat_max'] == 0:
        return -9

    # arcpy.AddMessage(f'values:{values}')
    wegcat = values['WEGCAT']
    gewicht_klasse = {
        '-9':'L', 'L3':'L', 'L2':'L', 'L1':'L',
        'S3':'S', 'S2':'S', 'S1':'S', 'S':'S',
        'PI':'H', 'PII':'H', 'PII-4':'H', 'PII-2':'H', 'H':'H'}
    # wegcategorie moet nog vertaald worden naar één van de klassen, mss niet hier
    for v in values:
        # arcpy.AddMessage(f'v:{v}')
        if v == 'WEGCAT':
            continue
        else:
            v_gewicht = values[v] * gewicht[gewicht_klasse[wegcat]][v] / 100
            aci_gewicht += v_gewicht

    # arcpy.AddMessage(f'aci_gewicht:{aci_gewicht}')
    return aci_gewicht


def freq(in_table, fields_output):
    frequencys = [f for f in fields_output if '_groep' in f]
    for frequency_fields in frequencys:
        arcpy.analysis.Frequency(
            in_table=in_table,
            out_table=in_table + "_Freq" + frequency_fields,
            frequency_fields=frequency_fields,
            summary_fields="lengte_km"
        )


def berekening_refwaarden(input_table,outlier_threshold):
    refwaarden = {
        '-9': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'L3': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'L2': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'L1': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'S3': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'S2': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'S1': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'S': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'PI': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'PII': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'PII-4': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'PII-2': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
        'H': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0},
    }
    f_sc = ['WEGCAT', 'PW_ETM', 'VR_ETM', 'sat_08', 'sat_17']


    with arcpy.da.SearchCursor(input_table, f_sc) as sc:
        for row in sc:
            for f in f_sc[1:]:
                if f == 'PW_ETM':
                    if type(refwaarden[row[0]][f])!= list:
                        refwaarden[row[0]][f] = []
                    refwaarden[row[0]][f].append(row[f_sc.index(f)])
                elif f == 'VR_ETM':
                    if type(refwaarden[row[0]][f])!= list:
                        refwaarden[row[0]][f] = []
                    refwaarden[row[0]][f].append(row[f_sc.index(f)])
                elif row[f_sc.index(f)] > refwaarden[row[0]][f]:
                    refwaarden[row[0]][f] = row[f_sc.index(f)]

    for cat in refwaarden:
        for ref in refwaarden[cat]:
            if ref in ('PW_ETM', 'VR_ETM'):
                # pas waarde aan rekening houdend met outliers
                arcpy.AddMessage(f'{cat},{ref}')
                refwaarden[cat][ref] = outliers(refwaarden[cat][ref],outlier_threshold)
                # refwaarden[cat][ref] = refwaarden[cat][ref] * 1.1
            elif ref in ('sat_max'):
                refwaarden[cat][ref] = max(refwaarden[cat]['sat_08'], refwaarden[cat]['sat_17'])

    return refwaarden


def bereken_sat_max(in_table):
    if 'sat_max' not in [f.name for f in arcpy.ListFields(in_table)]:
        arcpy.AddField_management(in_table=in_table,
                                field_name='sat_max',
                                field_type='DOUBLE'
                                )
    arcpy.CalculateField_management(in_table=in_table, field='sat_max', expression=max('!sat_08!', '!sat_17!'))


def bereken_aci_buur(in_table,in_segmentering):
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


    def bereken_verbinding(in_table,in_segmentering):
        arcpy.AddField_management(in_table= in_table,field_name="verbinding",field_type="TEXT",field_length=20)
        arcpy.MakeFeatureLayer_management(
            in_features=in_segmentering,
            out_layer=os.path.basename(in_table+"_lyr"),
            where_clause="bechrijving LIKE '%complex%' Or bechrijving LIKE '%knoop%' Or bechrijving LIKE "
                         "'%verbinding%' Or bechrijving LIKE '%tussen oprit%' Or bechrijving LIKE '%tussen afrit%'"
        )
        arcpy.SelectLayerByLocation_management(
            in_layer=in_table,
            overlap_type="SHARE_A_LINE_SEGMENT_WITH",
            select_features=os.path.basename(in_table+"_lyr"),
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
            arcpy.AddField_management(in_table= in_table,field_name="totaal_aci_buur",field_type="FLOAT")
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
        if "totaal_aci_mix" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table= in_table,field_name="totaal_aci_mix",field_type="FLOAT")
        if "totaal_aci_mix_groep" not in [f.name for f in arcpy.ListFields(in_table)]:
            arcpy.AddField_management(in_table= in_table,field_name="totaal_aci_mix_groep",field_type="TEXT", field_length=50)
        with arcpy.da.UpdateCursor(in_table, ['verbinding', 'totaal_aci',
                                              'totaal_aci_buur', 'totaal_aci_mix', 'totaal_aci_mix_groep']) as uc:
            for row in uc:
                row = list(row)
                if row[0] == 'ja':
                    row[3] = max(row[1], row[2])
                else:
                    row[3] = row[1]

                row[4] = bereken_groep(row[3])
                uc.updateRow(row)

    arcpy.AddMessage('-- bereken endpoints')
    endpoints = bereken_aci_endpoints(in_table=in_table)
    arcpy.AddMessage('-- bereken_verbinding')
    bereken_verbinding(in_table, in_segmentering)
    arcpy.AddField_management(in_table= in_table,field_name="totaal_aci_buur",field_type="LONG")
    arcpy.AddMessage('-- bereken schrijf_aci_buur')
    schrijf_aci_buur(in_table=in_table, endpoints=endpoints)
    arcpy.AddMessage('-- bereken_aci_mix')
    bereken_aci_mix(in_table=in_table)


def outliers(values,outlier_threshold):
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

    arcpy.AddMessage(f"Sterk afwijkende waarden:{outliers}")
    arcpy.AddMessage(f" lenSterk afwijkende waarden:{len(outliers)}")
    arcpy.AddMessage(f"min waarden: {min(values)}")
    arcpy.AddMessage(f"max waarden: {max(values)}")
    arcpy.AddMessage(f"min waarden: {min(values2)}")
    arcpy.AddMessage(f"max waarden: {max(values2)}")
    return max (values2)

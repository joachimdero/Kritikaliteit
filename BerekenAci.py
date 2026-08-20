import copy
import importlib

import arcpy
import berekeningAci_methods
import constants
importlib.reload(berekeningAci_methods)


def berekening_aci(in_table, gewicht, f_input_fields=['PW_ETM', 'VR_ETM', 'sat_max', 'UV', 'OV', 'vr_aandeel'],
                                  refwaarden=None):
    arcpy.AddMessage(f'-berekening_aci ({in_table})')

    f_uc = ['WEGCAT'] + copy.deepcopy(f_input_fields)
    f_uc = berekeningAci_methods.voeg_aci_velden_toe(f_input_fields, f_uc, in_table)
    arcpy.AddMessage(f"f_uc = {f_uc}")

    with arcpy.da.UpdateCursor(in_table, f_uc) as uc:
        for i, row in enumerate(uc):
            # arcpy.AddMessage(f"row:{row}")
            wegcat, pw, vr, sat, uv, ov, vr_aandeel = row[:7]
            if wegcat in ("-8", "-9", "EW", "OW", "L", "L1", "L2", "L3"):
                wegcatgroep = "L"
            elif wegcat in ("P", "EHW", "VHW", "PI", "PII", "PII-4", "PII-2", "H"):
                wegcatgroep = "H"
            elif wegcat in ("IW", "RW", "S", "S1", "S2", "S3"):
                wegcatgroep = "S"
            else:
                wegcatgroep = wegcat[0]
                arcpy.AddError(f"wegcatgroep niet herkend: {wegcatgroep} voor {wegcat}")

            for f in f_input_fields:
                f_bron = row[f_uc.index(f)]
                if f in ('PW_ETM', 'VR_ETM'):
                    row[f_uc.index(f + '_aci')] = berekeningAci_methods.bereken_aci_aantal(f_bron, refwaarden[wegcatgroep][f])
                    row[f_uc.index(f + '_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index(f + '_aci')])
                elif f in ('vr_aandeel'):
                    row[f_uc.index(f + '_aci')] = berekeningAci_methods.bereken_aci_aandeel(vr_aandeel, refwaarden[wegcatgroep][f])
                    row[f_uc.index(f + '_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index(f + '_aci')])
                elif f in ('sat_max'):
                    row[f_uc.index(f + '_aci')] = berekeningAci_methods.bereken_aci_sat(f_bron, refwaarden[wegcatgroep][f])
                    row[f_uc.index(f + '_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index(f + '_aci')])
                elif f in ('UV'):
                    row[f_uc.index(f + '_aci')] = berekeningAci_methods.bereken_aci_uv(f_bron, 100)
                    row[f_uc.index(f + '_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index(f + '_aci')])
                elif f in ('OV'):
                    row[f_uc.index(f + '_aci')] = berekeningAci_methods.bereken_aci_net(f_bron, 100)
                    row[f_uc.index(f + '_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index(f + '_aci')])
                else:
                    arcpy.AddError(f'probleem met fields_uc: {f_uc}, f:{f}')
            v_bron = {
                'WEGCAT': row[f_uc.index('WEGCAT')],
                'PW_ETM': row[f_uc.index('PW_ETM_aci')],
                'VR_ETM': row[f_uc.index('VR_ETM_aci')],
                'sat_max': row[f_uc.index('sat_max_aci')],
                'UV': row[f_uc.index('UV_aci')],
                'OV': row[f_uc.index('OV_aci')],
                'vr_aandeel': row[f_uc.index('vr_aandeel_aci')]
            }
            # v_bron moet geen aci van wegcat meegeven maar wel de wegcat
            row[f_uc.index('totaal_aci')] = berekeningAci_methods.bereken_aci_segment(v_bron, gewicht)
            row[f_uc.index('totaal_aci_bucket')] = berekeningAci_methods.bereken_bucket(row[f_uc.index('totaal_aci')])

            uc.updateRow(row)
    arcpy.AddMessage(f"aci voor {i} rijen berekend")

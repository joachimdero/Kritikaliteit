# import arcpy
import math
import arcpy


def bereken_aci_en_index(input_value, a, b):
    # arcpy.AddMessage(f'input_value:{input_value}')
    # max_aci moet een dict zijn van de mogelijke maxwaarden (exp, lin,kwa), vb. {exp: 7045,lin: 7045,kwa: 7045}
    # bereken exponentieel, exponentieel index 0-100, liniaire, liniaire index 0-100, kwadratisch, kwadratisch index 0-100 + groepen

    aci = {'exp': None,
           'aci': None,
           'kwa': None,
           'exp_index': None,
           'lin_index': None,
           'kwa_index': None,
           }

    aci['aci'] = a * input_value

    return aci


def bereken_groep(aci):
    # arcpy.AddMessage(f' aci:{aci}')
    aci_klassen_domein = {
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

    aci_klassen = {
        #  'exp_groep' : None,
        'aci_groep': None,
        # 'kwa_groep': None,
        # 'exp_index_groep' : None,
        # 'lin_index_groep': None,
        # 'kwa_index_groep': None,
    }

    for aci_klasse in aci_klassen:
        arcpy.AddMessage(f'aci_klassen:{aci_klassen}')
        aci_par = aci_klasse.replace('_groep', '')
        # arcpy.AddMessage(f'aci_par {aci_par}')
        for domeinklasse in aci_klassen_domein:
            # arcpy.AddMessage(f'domeinklasse[0]:{domeinklasse[0]},aci[aci_par]:{aci[aci_par]},domeinklasse[1]:{domeinklasse[1]}')
            if domeinklasse[0] <= aci[aci_par] <= domeinklasse[1]:
                aci_klassen[aci_klasse] = str(domeinklasse[0]) + '_' + aci_klassen_domein[domeinklasse]
                break
            else:
                aci_klassen[aci_klasse] = 'niet in klasse'

    # arcpy.AddWarning(f'aci/aciklassen{aci, aci_klassen}')

    return aci_klassen


def berekening_aci(input_table, input_field, fields_output):
    formulewaarden = {
        'PW_ETM': {
            'a': 0.000909091,
            'b': 1
        },
        'VR_ETM': {
            'a': 0.004,
            'b': 1
        },
        'SAT_ETM': {
            'a': 1.25,
            'b': 1
        },
        'sat_max': {
            'a': 1,
            'b': 1
        },
    }
    formulewaarden_input_field = formulewaarden[input_field.replace('FIRST_', '')]
    arcpy.AddMessage(f'gebruikte formulewaarden: {formulewaarden_input_field}')

    arcpy.AddMessage('-bereken waarde')
    fields_uc = [input_field] + fields_output
    with arcpy.da.UpdateCursor(input_table, fields_uc) as uc:
        for row in uc:
            input_value = row[0]
            aci = bereken_aci_en_index(input_value, a=formulewaarden_input_field['a'],
                                       b=formulewaarden_input_field['b'])
            arcpy.AddMessage(f'aci : {aci}')
            aci_klassen = bereken_groep(aci)
            for field in fields_uc[1:]:
                key = field.replace(input_field.replace('FIRST_', '') + '_', '')
                if key in aci:
                    row[fields_uc.index(field)] = aci[key]
                elif key in aci_klassen:
                    row[fields_uc.index(field)] = aci_klassen[key]
                else:
                    arcpy.AddError('waarde kan niet weggeschreven worden')
                    arcpy.AddError(f'field:{field}')
                    arcpy.AddError(f'key:{key}')
                    arcpy.AddError(f'aci : {aci}')

            # arcpy.AddMessage(f'****row : {row}')
            # arcpy.AddMessage(f'****fields_uc : {fields_uc}')
            uc.updateRow(row)


def freq(in_table, fields_output):
    frequencys = [f for f in fields_output if '_groep' in f]
    for frequency_fields in frequencys:
        arcpy.analysis.Frequency(
            in_table=in_table,
            out_table=in_table + "_Freq" + frequency_fields,
            frequency_fields=frequency_fields,
            summary_fields="lengte_km"
        )


# --------------------------------
input_table = arcpy.GetParameterAsText(0)
input_field = arcpy.GetParameterAsText(1)

f_aci = [
    'aci',
    'aci_groep'
]
f_outfc = [input_field.replace('FIRST_', '') + '_' + f for f in f_aci]

for field in f_outfc:
    arcpy.AddMessage(f'***{field}')
    if field not in [f.name for f in arcpy.ListFields(input_table)] and 'groep' not in field:
        arcpy.AddField_management(input_table, field, 'FLOAT')
    elif field not in [f.name for f in arcpy.ListFields(input_table)] and 'groep' in field:
        arcpy.AddField_management(input_table, field, 'TEXT', field_length=15)

berekening_aci(input_table, input_field, f_outfc)

freq(input_table, f_outfc)

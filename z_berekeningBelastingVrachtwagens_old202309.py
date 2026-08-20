# import arcpy
import math
import arcpy


def indexAlternatieveGroep(input_value, klasse, aci_range):
    # arcpy.AddMessage (f'input_value: {input_value}, klasse: {klasse}, aci_range: {aci_range}')
    a = 0.0163
    b = 0.003

    aci_temp = a * (math.exp((input_value) * b))
    aci = min(100, aci_temp)

    aci_klassen = {
        (0, 20): 'Zeer klein',
        (20, 40): 'Klein',
        (40, 60): 'Matig',
        (60, 80): 'Groot',
        (80, 100): 'Zeer groot',
    }
    print(aci_klassen)
    for aci_klasse in aci_klassen:
        aci_groep = 0

        if aci_klasse[0] < aci <= aci_klasse[1]:
            aci_groep = aci_klassen[aci_klasse]
            break

    if aci_groep == 0:
        arcpy.AddWarning(f'*****************{aci}')

    return aci, aci_groep


def index(input_value, klasse, aci_range):
    # arcpy.AddMessage (f'input_value: {input_value}, klasse: {klasse}, aci_range: {aci_range}')
    a = 0.0163
    b = 0.003

    aci_temp = a * (math.exp((input_value) * b))
    aci = min(100, aci_temp)

    aci_klassen = {
        (0, 0.01): 'Zeer klein',
        (0.01, 0.1): 'Klein',
        (0.1, 1): 'Matig',
        (1, 10): 'Groot',
        (10, 100): 'Zeer groot',
    }
    print(aci_klassen)
    for aci_klasse in aci_klassen:
        aci_groep = 0

        if aci_klasse[0] < aci <= aci_klasse[1]:
            aci_groep = aci_klassen[aci_klasse]
            break

    if aci_groep == 0:
        arcpy.AddWarning(f'*****************{aci}')

    return aci, aci_groep


def berekening_aci_saturatie(input_table, input_field, output_aci_field, output_acigroep_field):
    klassen = {
        (0, 3000): ['Zeer klein', [0, 0.01]],
        (3000, 6000): ['Klein', [0.01, 0.1]],
        (6000, 10000): ['Matig', [0.1, 1]],
        (10000, 15000): ['Groot', [1, 10]],
        (15000, 30000): ['Zeer groot', [10, 100]],
    }

    with arcpy.da.UpdateCursor(input_table, [input_field, output_aci_field, output_acigroep_field]) as uc:
        # i = 0
        for row in uc:
            for klasse in klassen:
                if klasse[0] < row[0] <= klasse[1]:
                    aci, aci_klasse = indexAlternatieveGroep(row[0], klasse, klassen[klasse][1])
                    row[1], row[2] = aci, aci_klasse
                    uc.updateRow(row)
                    continue


input_table = arcpy.GetParameterAsText(0)
input_field = arcpy.GetParameterAsText(1)
output_aci_field = arcpy.GetParameterAsText(2)
output_acigroep_field = arcpy.GetParameterAsText(3) + '_alt'

if output_aci_field not in [f.name for f in arcpy.ListFields(input_table)]:
    arcpy.AddField_management(input_table, output_aci_field, 'FLOAT')
if output_acigroep_field not in [f.name for f in arcpy.ListFields(input_table)]:
    arcpy.AddField_management(input_table, output_acigroep_field, 'TEXT', field_length=15)

berekening_aci_saturatie(input_table, input_field, output_aci_field, output_acigroep_field)

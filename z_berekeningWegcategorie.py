import arcpy


def berekening_aci_wegcategorie(input_table, input_field, f_outfc):
    klassen = {
        ('', None, '-9', '-8'): ['Zeer klein', 0],
        ('L3',): ['Zeer klein', 10],
        ('L2',): ['Klein', 30],
        ('L1',): ['Matig', 40],
        ('S3',): ['Matig', 55],
        ('S2', 'S'): ['Groot', 60],
        ('S1',): ['Groot', 65],
        ('P1', 'P2', 'PI', 'PII', 'PII-4', 'PII-2'): ['Zeer groot', 80],
        ('H',): ['Zeer groot', 90],
    }

    fields_uc = [input_field] + f_outfc
    with arcpy.da.UpdateCursor(input_table, fields_uc) as uc:
        # i = 0
        for row in uc:
            for klasse in klassen:
                if row[0] in klasse:
                    row[1], row[2] = klassen[klasse][1], str(klassen[klasse][1])+'_'+(klassen[klasse][0])
                    uc.updateRow(row)
                    break
            if row[1] == None:
                arcpy.AddWarning(f'geen berekening mogelijk voor row: {row}')


def freq(in_table, fields_output):
    frequencys = [f for f in fields_output if '_groep' in f]
    for frequency_fields in frequencys:
        arcpy.analysis.Frequency(
            in_table=in_table,
            out_table=in_table + "_Freq" + frequency_fields,
            frequency_fields=frequency_fields,
            summary_fields="lengte_km"
        )


# ---------------------------------
input_table = arcpy.GetParameterAsText(0)
input_field = arcpy.GetParameterAsText(1)

f_aci = [
    'aci',
    'aci_groep'
]
f_outfc = [input_field.replace('FIRST_', '') + '_' + f for f in f_aci]

for field in f_outfc:
    if field not in [f.name for f in arcpy.ListFields(input_table)] and 'groep' not in field:
        arcpy.AddField_management(input_table, field, 'FLOAT')
    elif field not in [f.name for f in arcpy.ListFields(input_table)] and 'groep' in field:
        arcpy.AddField_management(input_table, field, 'TEXT', field_length=15)

berekening_aci_wegcategorie(input_table, input_field, f_outfc)

freq(input_table, f_outfc)

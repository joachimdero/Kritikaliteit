# import arcpy
import math
import arcpy


def berekening_aci_totaal(input_table, f_aci_sat_etm,f_aci_pw_etm,f_aci_vr_etm,f_aci_wegcat,output_aci_field,output_aci_groep_field):
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
    with arcpy.da.UpdateCursor(input_table, [f_aci_sat_etm,f_aci_pw_etm,f_aci_vr_etm,f_aci_wegcat,output_aci_field,output_aci_groep_field]) as uc:
        for row in uc:
            aci_sat_etm, aci_pw_etm, aci_vr_etm, aci_wegcat = row[0],row[1],row[2],row[3]
            if not None in (row[0],row[1],row[2],row[3]):
                aci = (aci_sat_etm * 0.25) + (aci_pw_etm *0.25) + (aci_vr_etm * 0.25) + (aci_wegcat*0.25)

                for aci_klasse in aci_klassen_domein:
                    aci_groep = 'geen'
                    if aci_klasse[0] < aci <= aci_klasse[1]:
                        aci_groep =  str(aci_klasse[0]) + '_' + aci_klassen_domein[aci_klasse]
                        # arcpy.AddMessage(aci_groep)
                        break
                row[4],row[5] = aci, aci_groep
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

#------------------------------------
# input_table = arcpy.GetParameterAsText(0)
#
# f_aci_sat_etm =  arcpy.GetParameterAsText(1)
# f_aci_pw_etm =  arcpy.GetParameterAsText(2)
# f_aci_vr_etm =  arcpy.GetParameterAsText(3)
# f_aci_wegcat =  arcpy.GetParameterAsText(4)
# output_aci_field =  arcpy.GetParameterAsText(5)
# output_aci_groep_field =  arcpy.GetParameterAsText(6)
# f_outfc = [output_aci_field,output_aci_groep_field]
#
# if output_aci_field not in [f.name for f in arcpy.ListFields(input_table)]:
#     arcpy.AddField_management(input_table,output_aci_field,'FLOAT')
# if output_aci_groep_field not in [f.name for f in arcpy.ListFields(input_table)]:
#     arcpy.AddField_management(input_table,output_aci_groep_field,'TEXT',field_length=15)
#
# berekening_aci_totaal(input_table, f_aci_sat_etm,f_aci_pw_etm,f_aci_vr_etm,f_aci_wegcat,output_aci_field,output_aci_groep_field)
#
# freq(input_table, f_outfc)
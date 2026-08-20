# import arcpy
import math
import arcpy


def index(input_value, klasse, aci_range):
    print (f'input_value: {input_value}, klasse: {klasse}, aci_range: {aci_range}')
    a = 0.0005
    b = 10.234
    a = 0.0005
    b = 15.234

    print (f'aci_temp = {a} * (math.exp({input_value / 100} * {b}))')
    aci_temp = a * (math.exp((input_value/100) * b))
    aci = min(100,aci_temp)

    # if not klasse[0]<input_value <= klasse[1]:
    #     arcpy.AddWarning(f'klasse[0]<:{klasse[0]} input_value:{input_value} <= klasse[1]:{klasse[1]}')
    # if not aci_range[0] < aci <= aci_range[1]:
    #     print (f'aci:{aci}')
    #     arcpy.AddWarning(f'input_value: {input_value} aci_range[0] {aci_range[0]}< aci {aci} <= aci_range[1] {aci_range[1]}')

    aci_klassen={
        (0,0.01): 'Zeer klein',
        (0.01,0.1): 'Klein',
        (0.1, 1): 'Matig',
        (1, 10): 'Groot',
        (10, 100): 'Zeer groot',
    }
    print (aci_klassen)
    for aci_klasse in aci_klassen:
        aci_groep = 0

        if aci_klasse[0] < aci <= aci_klasse[1]:
            # arcpy.AddMessage(f'++++{aci_klasse[0]} < {aci} <= {aci_klasse[1]}')
            aci_groep = aci_klassen[aci_klasse]
            # arcpy.AddMessage (aci_groep)
            break


    if aci_groep == 0:
        arcpy.AddWarning(f'*****************{aci}')

    return aci, aci_groep


def berekening_aci_saturatie(input_table, input_field, output_aci_field,output_acigroep_field):
    klassen = {
        (0, 30): ['Zeer klein',[0,0.01]],
        (30, 60): ['Klein',[0.01,0.1]],
        (60, 70): ['Matig',[0.1 , 1]],
        (70, 90): ['Groot',[1 , 10]],
        (90, 120): ['Zeer groot',[10 , 100]],
    }

    with arcpy.da.UpdateCursor(input_table, [input_field,output_aci_field,output_acigroep_field]) as uc:
        # i = 0
        for row in uc:
            for klasse in klassen:
                if klasse[0] < row[0] <= klasse[1]:
                    aci, aci_klasse = index(row[0], klasse, klassen[klasse][1])
                    row[1],row[2] = aci, aci_klasse
                    uc.updateRow(row)
                    continue




input_table = arcpy.GetParameterAsText(0)
# input_table = r"C:\\GoogleTeamDrive\\GISprojecten\\1AnalysesAddHoc\\criticaliteit\\criticaliteit20221019.gdb\\Verkeersmodel2017ToWegsegment"
input_field = arcpy.GetParameterAsText(1)
# input_field = "FIRST_SAT_ETM"
output_aci_field =  arcpy.GetParameterAsText(2)
output_acigroep_field =  arcpy.GetParameterAsText(3)

if output_aci_field not in [f.name for f in arcpy.ListFields(input_table)]:
    arcpy.AddField_management(input_table,output_aci_field,'FLOAT')
if output_acigroep_field not in [f.name for f in arcpy.ListFields(input_table)]:
    arcpy.AddField_management(input_table,output_acigroep_field,'TEXT',field_length=15)

berekening_aci_saturatie(input_table, input_field,output_aci_field,output_acigroep_field)

print (index(30, klasse= (60, 70), aci_range= [0.1, 1]) )


print (0.0005*(math.exp(0.60*10.234)))
import arcpy
import ast
import json

# voeg informatie uit granzende knopen aan netwerksegment



def groupknopenXsegmentenToDict(gegroepeerde_knopen):
    gegroepeerde_knopen_dict = {}
    with arcpy.da.SearchCursor(gegroepeerde_knopen,["GROUP_ID","segmenten"]) as sc:
        for row in sc:
            segmenten_list = ast.literal_eval (row[1])
            if row[0] not in gegroepeerde_knopen_dict:
                gegroepeerde_knopen_dict[row[0]] = segmenten_list
            elif row[0] in gegroepeerde_knopen_dict and segmenten_list not in gegroepeerde_knopen_dict[row[0]]:
                gegroepeerde_knopen_dict[row[0]] = gegroepeerde_knopen_dict[row[0]]+segmenten_list
            else:
                pass

    return gegroepeerde_knopen_dict



def netwerksegmentenXgroupKnopenToDict(netwerksegmenten):
    arcpy.AddMessage("netwerksegmentenXgroupKnopenToDict(netwerksegmenten), netwerksegementen: %s"%netwerksegmenten)
    # maak dict {id_netwerksegment: [ident2,ident2,]}
    netwerksegmenten_wegnummer = {}
    # maak dict {id_netwerksegment: [groupknoop,groupknoop,]}
    id_netwerksegmenten_id_group_knopen_dict = {}

    with arcpy.da.SearchCursor(netwerksegmenten,["id2","GROUP_ID","IDENT2"]) as sc:
        for row in sc:
            if row[0] not in id_netwerksegmenten_id_group_knopen_dict:
                id_netwerksegmenten_id_group_knopen_dict[row[0]] = []
            if row[1] not in id_netwerksegmenten_id_group_knopen_dict[row[0]] and row[1] not in (None,'',' '):
                id_netwerksegmenten_id_group_knopen_dict[row[0]].append(row[1])
            else:
                pass

            if row[0] not in netwerksegmenten_wegnummer:
                netwerksegmenten_wegnummer[row[0]] = []
            if row[2] not in netwerksegmenten_wegnummer[row[0]] and row[2] not in (None,'',' '):
                netwerksegmenten_wegnummer[row[0]].append(row[2])
            else:
                pass
    return netwerksegmenten_wegnummer, id_netwerksegmenten_id_group_knopen_dict



#---------------
netwerksegmenten = arcpy.GetParameterAsText(0)
##gegroepeerde_knopen = arcpy.GetParameterAsText(1)
knopen_met_wegsegmentattr  = arcpy.GetParameterAsText(1)


#groepeer de knopen
arcpy.AddMessage("groepeer knopen: alle knopen die minder dan 40m uit elkaar liggen krijgen een zelfde groepid")
gegroepeerde_knopen = knopen_met_wegsegmentattr+"_group"
arcpy.gapro.GroupByProximity(knopen_met_wegsegmentattr, gegroepeerde_knopen, "NEAR_PLANAR", "40 Meters", "NONE", None, '')
gegroepeerde_knopen_dict = groupknopenXsegmentenToDict(gegroepeerde_knopen)
arcpy.AddMessage("gegroepeerde_knopen_dict: %s"% str(gegroepeerde_knopen_dict) )


# join wegsegmenten met gegroepeerde knopen
arcpy.AddMessage("join wegsegmenten met gegroepeerde knopen")
netwerksegmenten_spjoin_gegroepeerdeknopen = netwerksegmenten + "_groepknoop"
arcpy.analysis.SpatialJoin(netwerksegmenten, gegroepeerde_knopen, netwerksegmenten_spjoin_gegroepeerdeknopen, "JOIN_ONE_TO_MANY", "KEEP_ALL", 'id2 "id2" true true false 4 Long 0 0,First,#,SegmentenOefening,id2,-1,-1;GROUP_ID "GROUP_ID" true true false 8 Double 0 0,First,#,testWegsegment_Nationweg_attribuutWegsegmentToKnoop_GroupByProximity,GROUP_ID,-1,-1;IDENT2 "ident2" true true false 6 Text 0 0,First,#,SegmentenOefening,IDENT2,0,8', "INTERSECT", None, '')
netwerksegmenten_wegnummer, id_netwerksegmenten_id_group_knopen_dict = netwerksegmentenXgroupKnopenToDict(netwerksegmenten_spjoin_gegroepeerdeknopen)
##arcpy.AddMessage("id_netwerksegmenten_id_group_knopen_dict: %s"% str(id_netwerksegmenten_id_group_knopen_dict) )
##arcpy.AddMessage("netwerksegmenten_wegnummer: %s"% str(netwerksegmenten_wegnummer) )


# selecteer de correcte beschrijving van de eindpunten van netwerksegmenten
beschrijving_netwerkid = {}

for netwerksegment, knopen in id_netwerksegmenten_id_group_knopen_dict.items():
    van_tot = []
    arcpy.AddMessage('--------')
    arcpy.AddMessage("netwerksegment: %s heeft knopen %s" %(netwerksegment, knopen) )
    if len(id_netwerksegmenten_id_group_knopen_dict[netwerksegment]) == 0:
        arcpy.AddWarning("netwerksegment: %s heeft geen knopen"%netwerksegment)
        knopen_1 = 'ongekend'
        knopen_2 = 'ongekend'
    elif len(id_netwerksegmenten_id_group_knopen_dict[netwerksegment]) > 2:
        arcpy.AddWarning("netwerksegment: %s heeft te veel knopen"%netwerksegment)
        knopen_1 = 'ongekend'
        knopen_2 = 'ongekend'
    else:
##        arcpy.AddMessage("gegroepeerde_knopen_dict[netwerksegment]:%s "%gegroepeerde_knopen_dict[netwerksegment])
        if knopen[0] != None:
            arcpy.AddMessage("gegroepeerde_knopen_dict[knopen[0]]:%s"%gegroepeerde_knopen_dict[knopen[0]])
            arcpy.AddMessage("netwerksegmenten_wegnummer[netwerksegment]:%s"%netwerksegmenten_wegnummer[netwerksegment])
            arcpy.AddMessage("TEST groepknooplist"%[groepknoop for groepknoop in gegroepeerde_knopen_dict[knopen[0]]])

            knopen_1 = [groepknoop for groepknoop in gegroepeerde_knopen_dict[knopen[0]] if groepknoop[0] not in  netwerksegmenten_wegnummer[netwerksegment]]#aanpassing 20230220

        else:
            knopen_1 = 'ongekend'
            arcpy.AddMessage('ongekend')

        if len(id_netwerksegmenten_id_group_knopen_dict[netwerksegment]) >1 and knopen[1] != None:
##            knopen_2 = gegroepeerde_knopen_dict[knopen[1]]
            knopen_2 = [groepknoop for groepknoop in gegroepeerde_knopen_dict[knopen[1]] if groepknoop[0] not in netwerksegmenten_wegnummer[netwerksegment]]#aanpassing 20230220
        else:
            knopen_2 = 'ongekend'
            arcpy.AddMessage('ongekend')


    for knoop in (knopen_1,knopen_2):
        arcpy.AddMessage('-')
##            arcpy.AddMessage("knoop: %s"%knoop)
        # dubbels uithalen, wegnummer gebruiken indien er één is
        if knoop != None and knoop != 'ongekend':
            wegnummers = set([str(segment[0]) for segment in knoop if segment[0] not in (None,'',' ')])
            straatnamen = set([segment[1] for segment in knoop  if segment[1] not in (None,'',' ')])
            arcpy.AddMessage("wegnummers: %s, straatnamen: %s" %(wegnummers,straatnamen))

            if len(wegnummers) > 0:
                knoop_beschrijving = "/".join(wegnummers)
##                arcpy.AddMessage("WEGNR : %s" % knoop_beschrijving)
                van_tot.append(wegnummers)
            elif len(straatnamen) > 0:
                knoop_beschrijving = "/".join(straatnamen)
##                arcpy.AddMessage("STRAATNAMEN : %s" % straatnamen)
                van_tot.append(straatnamen)
            else:
                van_tot.append("ongekend")
        else:
            van_tot.append("ongekend")

        arcpy.AddMessage("van_tot:%s" %van_tot)

##        arcpy.AddMessage("netwerksegment %s//%s tussen %s en %s" %(netwerksegment,netwerksegmenten_wegnummer[netwerksegment],knopen_1,knopen_2))
    arcpy.AddMessage("netwerksegmenten_wegnummer[netwerksegment]:%s"%netwerksegmenten_wegnummer[netwerksegment])
    netwerksegment_wegnummer = "/".join(netwerksegmenten_wegnummer[netwerksegment])
    if netwerksegment_wegnummer == '':
        netwerksegment_wegnummer = 'ongekend'
    arcpy.AddMessage("netwerksegment %s: %s tussen %s en %s" %(netwerksegment,netwerksegment_wegnummer,van_tot[0],van_tot[1]))
    beschrijving_netwerkid [netwerksegment] = "%s tussen %s en %s" %(netwerksegment_wegnummer,van_tot[0],van_tot[1])


arcpy.AddMessage("beschrijving_netwerkid:%s"%beschrijving_netwerkid)
# schrijf data weg naar de netwerksegmenten
# maak veld aan
arcpy.AddField_management(netwerksegmenten,"beschrijving","TEXT", field_length = 300)
with arcpy.da.UpdateCursor(netwerksegmenten, ["id2","beschrijving"]) as uc:
    for row in uc:
        arcpy.AddMessage("row[0]: %s" %row[0])
        arcpy.AddMessage(beschrijving_netwerkid[row[0]])
        row[1] = beschrijving_netwerkid[row[0]]
        uc.updateRow(row)

import importlib
import math
import os
import sys

import arcpy

import berekeningAci_methods

try:
    # importeer Awv functie en downloadFunctie
    from ....AwvFunctiesAlgemeen import AwvFunctiesAlgemeen
    from ....AwvFunctiesAlgemeen import Locatieservices2 as Ls2
except ImportError:
    from sys import path

    pythonVersion = sys.version_info.major
    basemap = "GIStools"
    basispath = os.path.realpath(__file__).split(basemap)[0]
    print("basispath = %s" % basispath)
    path2 = os.path.join(basispath, basemap, "AwvFuncties")
    path.append(path2)
    import AwvFunctiesAlgemeen
    import Locatieservices2 as Ls2

    if pythonVersion == 3:
        importlib.reload(AwvFunctiesAlgemeen)
        importlib.reload(Ls2)


def maak_minimale_fc(in_fc, out_fc):
    # arcpy.ExportFeatures_conversion(
    #     in_features=fc,
    #     out_features=fc_new,
    #     field_mapping=r'WS_OIDN "WS_OIDN" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,WS_OIDN,-1,-1;FMEAS "FMEAS" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,FMEAS,-1,-1;TMEAS "TMEAS" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,TMEAS,-1,-1;id2 "id" true true false 65536 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,id2,0,65535;jaar "jaar" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,jaar,-1,-1;globale_index "globale_index" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,globale_index,-1,-1;globale_klasse "globale_klasse" true true false 65536 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,globale_klasse,0,65535;globale_structuurKlasse "globale_structuurKlasse" true true false 65536 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,globale_structuurKlasse,0,65535;globale_veiligheidKlasse "globale_veiligheidKlasse" true true false 65536 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,globale_veiligheidKlasse,0,65535;richting "richting" true true false 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,richting,-1,-1;ident8 "ident8" true true false 65536 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,ident8,0,65535;wegnummer "wegnummer" true true false 10 Text 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,wegnummer,0,9;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,Shape_Length,-1,-1;richting_wegnr "richting_wegnr" true true false 2 Short 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,richting_wegnr,-1,-1;richting_meting "richting_meting" true true false 2 Short 0 0,First,#,C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\staatvandeweg_verwerking20250325.gdb\staatvandeweg_gebiedsdekkend,richting_meting,-1,-1',
    # )

    """
    Exporteert features met veldmapping die automatisch gegenereerd wordt. Enkel de nodige velden worden behouden.

    :param in_fc: Input feature class
    :param out_fc: Output feature class
    :param benodigde_velden: lijst met veldnamen als strings
    """
    arcpy.AddMessage(f"- maak_minimale_fc {in_fc} => {out_fc}")
    benodigde_velden = [
    "WS_OIDN",
    "FMEAS",
    "TMEAS",
    "id2",
    "jaar",
    "globale_index",
    "globale_klasse",
    "globale_structuurKlasse",
    "globale_veiligheidKlasse",
    "richting",
    "ident8",
    "wegnummer",
    "richting_wegnr",
    "richting_meting"
]
    # Maak een lege FieldMappings container
    field_mappings = arcpy.FieldMappings()

    # Doorloop de velden die je wil behouden
    for veldnaam in benodigde_velden:
        if veldnaam in [f.name for f in arcpy.ListFields(in_fc)]:
            # Maak een FieldMap object per veld
            fm = arcpy.FieldMap()
            fm.addInputField(in_fc, veldnaam)

            # Optioneel: instellen van alias of output field name
            out_field = fm.outputField
            out_field.name = veldnaam  # of pas aan indien gewenst
            out_field.aliasName = veldnaam
            fm.outputField = out_field

            # Voeg toe aan de field_mappings
            field_mappings.addFieldMap(fm)
        else:
            arcpy.AddWarning(f"Veld '{veldnaam}' niet gevonden in {in_fc}. Wordt overgeslagen.")

    # Voer export uit met de gegenereerde mapping
    arcpy.ExportFeatures_conversion(
        in_features=in_fc,
        out_features=out_fc,
        field_mapping=field_mappings
    )


def z_aci_fc_to_aci_table(aci_fc):
    aci_table = aci_fc + "_tmp1table"
    arcpy.AddMessage(f"- aci_fc_to_aci_table {aci_fc} => {aci_table}")
    # voeg RID field, Wsoidn_richting toe
    arcpy.management.CalculateField(
        in_table=aci_fc,
        field="Wsoidn_richting",
        expression='str(!WS_OIDN!)+"_"+str(!RICHTING!)',
        expression_type="PYTHON3",
        code_block="",
        field_type="TEXT",
        enforce_domains="NO_ENFORCE_DOMAINS"
    )
    # voeg VanM; TotM toe
    for f in ("VanM", "TotM"):
        arcpy.AddField_management(
            in_table=aci_fc,
            field_name=f,
            field_type="FLOAT"
        )

    with arcpy.da.UpdateCursor(aci_fc, ["SHAPE@LENGTH", "VanM", "TotM"]) as uc:
        for row in uc:
            row_upd = (row[0], 0, row[0])
            uc.updateRow(row_upd)
    arcpy.conversion.ExportTable(
        in_table=aci_fc,
        out_table=aci_table,
        where_clause="Shape_Length <> 0"
    )
    return aci_table


def bereken_ahi_bucket(globaleklasse):
    ahi_ahi_bucket = {
        "": 0,
        "Uitstekend": 1,
        "Normaal": 2,
        "Behoorlijk": 3,
        "Matig": 4,
        "Onvoldoende": 5,
    }
    if globaleklasse not in ahi_ahi_bucket:
        arcpy.AddMessage(f"globaleklasse:{globaleklasse}")

    return ahi_ahi_bucket[globaleklasse]


def bereken_ari(in_staatvandeweg, in_aci, out_ari):
    arcpy.AddMessage("- bereken_ari")
    AwvFunctiesAlgemeen.join_field_multiple_join_fields(
        input_table=in_staatvandeweg,
        f_join_inputtable=["ws_oidn", "richting_meting"],
        join_table=in_aci,
        f_join_jointable=["WS_OIDN", "RICHTING"],
        f_add=["totaal_aci", "totaal_aci_bucket", "aci_segment", "aci_segment_bucket"]

    )

    f_aci = "totaal_aci"
    f_aci_segm = "aci_segment"
    f_ahi = "ahi"
    f_ahi_segm = "ahi_netwerksegment"
    f_ari = "ari"
    f_ari_bucket = "ari_bucket"
    f_ari_segm = "ari_segm"
    f_ari_segm_bucket = "ari_segm_bucket"
    f_uc = [f_aci, f_aci_segm, f_ahi, f_ahi_segm, f_ari,
            f_ari_bucket, f_ari_segm, f_ari_segm_bucket]

    for field in (f_ari, f_ari_bucket, f_ari_segm, f_ari_segm_bucket):
        if field not in [f.name for f in arcpy.ListFields(out_ari)]:
            arcpy.AddField_management(
                in_table=out_ari,
                field_name=field,
                field_type="LONG"
            )

    with arcpy.da.UpdateCursor(out_ari, f_uc) as uc:
        for i, row in enumerate(uc):
            if i % 10000 == 0:
                arcpy.AddMessage(f"{i} rijen behandeld")
            aci, aci_segm, ahi, ahi_segm, ari, ari_bucket, ari_segm, ari_segm_bucket = row
            if aci is None:
                aci = 0
            if aci_segm is None:
                aci_segm = 0

            if not (0 <= ahi < 100 or 0 <= aci < 100):
                if i in range(0, 1000):
                    arcpy.AddMessage(f"kan niet berekenen: v_staat,v_aci:{ahi, aci}")
                    ari, ari_bucket, ari_segm, ari_segm_bucket = 0, 0, 0, 0

            else:
                ari = ahi * aci
                ari_bucket = bereken_ari_bucket(ari)
                ari_segm = ahi_segm * aci_segm
                ari_segm_bucket = bereken_ari_bucket(ari_segm)

            row_upd = [aci, aci_segm, ahi, ahi_segm, ari, ari_bucket, ari_segm, ari_segm_bucket]
            uc.updateRow(row_upd)


def bereken_ari_bucket(v_ari):
    if v_ari < 800:
        return 1
    elif v_ari < 1600:
        return 2
    elif v_ari < 4000:
        return 3
    elif v_ari < 6400:
        return 4
    elif v_ari < 10000:
        return 5


def add_geometry(ari_table, wegsegmenten):
    arcpy.AddMessage("- add_geometry")
    ari_eventlayer = "ari_eventlayer"
    ari_fc = "ari_fc"
    arcpy.MakeRouteEventLayer_lr(
        in_routes=wegsegmenten,
        route_id_field="id",
        in_table=ari_table,
        in_event_properties="ws_oidn; LINE; VanM; TotM",
        out_layer=ari_eventlayer,
        offset_field=None,
        add_error_field="ERROR_FIELD"
    )
    arcpy.ExportFeatures_conversion(
        in_features=ari_eventlayer,
        out_features=ari_fc
    )
    return ari_fc


def z_add_relatieve_weglocatie(cookie=None, input_fc=None):
    arcpy.AddMessage(f"- add_relatieve_weglocatie voor {arcpy.GetCount_management(input_fc)[0]} rows")
    start = 0
    limit = 8000
    session = auth.prepareSession(cookie=cookie)

    selectie_veld = [f.name for f in arcpy.ListFields(input_fc) if f.type == 'OID']
    objectids = tuple([row[0] for row in arcpy.da.SearchCursor(input_fc, [selectie_veld, "Shape_Length", "Ident8"]) if
                       row[1] > 0 and row[2] != ""])
    totaal_aantal_features = len(objectids)
    arcpy.AddMessage(f"{totaal_aantal_features}features waarvoor een relatieve weglocatie opgevraagd wordt")

    # Itereer door de data in blokken
    while start < totaal_aantal_features:
        objectids_selectie = objectids[start:start + limit]
        arcpy.AddMessage(f'maak json met inputlocaties op basis van fc of table van {start} tot {start + limit}')
        # maak json met inputlocaties op basis van fc of table
        # arcpy.AddMessage(f"objectids_selectie : {objectids_selectie}")
        locaties, type_locatie = Ls2.maakJsonVanFcOrTblCoordinaten(
            input_table=input_fc,
            crs=31370,
            f_wegnr="ident8",
            f_begin_x="SHAPE",
            f_begin_y="SHAPE",
            f_eind_x="SHAPE",
            f_eind_y="SHAPE",
            objectids_selectie=objectids_selectie,
        )
        arcpy.AddMessage(f"len locaties: {len(locaties)}")

        responses = Ls2.requestLs2Puntlocatie(
            locaties=locaties,
            omgeving="productie",
            zoekafstand=5,
            crs=31370,
            session=session
        )
        # arcpy.AddMessage(f"responses:{responses}")
        arcpy.AddMessage(f" len responses:{len(responses)}")
        # schrijf gegevens weg
        Ls2.schrijfGegevens(
            input_table=input_fc,
            response=responses,
            type_locatie=type_locatie,
            objectids_selectie=objectids_selectie
        )
        start += limit


def bereken_ahi(staatvandeweg, f_globaleindex, f_globaleklasse):
    arcpy.AddMessage("- bereken_ahi")
    f_ahi = "ahi"
    f_ahi_bucket = "ahi_bucket"
    f_uc = [f_globaleindex, f_globaleklasse, f_ahi, f_ahi_bucket]

    for field in (f_ahi, f_ahi_bucket):
        if field not in [f.name for f in arcpy.ListFields(staatvandeweg)]:
            arcpy.AddField_management(
                in_table=staatvandeweg,
                field_name=field,
                field_type="LONG"
            )

    with arcpy.da.UpdateCursor(staatvandeweg, f_uc) as uc:
        for i, row in enumerate(uc):
            # arcpy.AddMessage(f"staatvandeweg:{staatvandeweg}")
            # arcpy.AddMessage(f"row:{row}")
            globaleindex, globaleklasse, ahi, ahi_bucket = row
            if i % 10000 == 0:
                arcpy.AddMessage(f"{i} rijen behandeld")
            ahi = 100 - float(globaleindex)  # omkeren indexwaarde
            if globaleklasse in (0, None, ""):
                ahi = None
            ahi_bucket = bereken_ahi_bucket(globaleklasse)
            row_upd = [globaleindex, globaleklasse, ahi, ahi_bucket]
            uc.updateRow(row_upd)


def lees_ahi_netwerksegmenten(fc_staatvandeweg, f_netwerkid, f_ahi):
    arcpy.AddMessage("- lees_ahi_netwerksegmenten")
    netwerkid_ahi = {}
    f_sc = [f_netwerkid, f_ahi, "SHAPE@LENGTH"]
    with arcpy.da.SearchCursor(fc_staatvandeweg, f_sc) as sc:
        for row in sc:
            netwerkid, ahi, lengte = row
            if lengte is not None and lengte > 0 and ahi is not None:
                if netwerkid not in netwerkid_ahi:
                    netwerkid_ahi[netwerkid] = []
                netwerkid_ahi[netwerkid].append((ahi, lengte))
        return netwerkid_ahi


def bereken_netwerkid_stats(netwerkid_ahi):
    arcpy.AddMessage("- bereken_netwerkid_stats")
    netwerkid_stats = {}
    for netwerkid, waarden in netwerkid_ahi.items():
        total_length = sum(length for ahi, length in waarden)

        # Gewogen gemiddelde
        gewogen_gem = sum(ahi * length for ahi, length in waarden) / total_length

        # Gewogen variantie
        if total_length == 0:
            variance = 0  # Of bijvoorbeeld: float("nan") of None
        else:
            variance = sum(length * ((ahi - gewogen_gem) ** 2) for ahi, length in waarden) / total_length

        stddev = math.sqrt(variance)
        karakteristieke_toestand = gewogen_gem - (
                1.645 * stddev)  # 1.645 is de z-waarde voor een betrouwbaarheidsniveau van 95%

        netwerkid_stats[netwerkid] = {
            "gemiddelde": gewogen_gem,
            "standaardafwijking": stddev,
            "karakteristieke_toestand": karakteristieke_toestand,
        }
    return netwerkid_stats


def bereken_ahi_netwerksegmenten(staatvandeweg_table, f_ahi, fc_netwerksegmenten):
    arcpy.AddMessage('-bereken_ahi_netwerksegmenten')
    f_netwerkid = "netwerk_id"
    arcpy.AddMessage(f'join veld {f_netwerkid}')
    AwvFunctiesAlgemeen.JoinFieldMultipleJoinFields(
        inputTable=staatvandeweg_table,
        inputJoinField=["ws_oidn", "richting_meting"],
        joinTable=fc_netwerksegmenten,
        outputJoinField=["ws_oidn", "richting_segment"],
        joinFields=[f_netwerkid]
    )

    f_ahi_gewogen_gemiddelde = "ahi_gewogen_gemiddelde"
    f_ahi_gewogen_gemiddelde_bucket = "ahi_gewogen_gemiddelde_bucket"
    f_ahi_segm = "ahi_netwerksegment"
    f_ahi_bucket_segm = "ahi_bucket_netwerksegment"

    for field in (f_ahi_gewogen_gemiddelde, f_ahi_gewogen_gemiddelde_bucket, f_ahi_segm, f_ahi_bucket_segm):
        if field not in [f.name for f in arcpy.ListFields(staatvandeweg_table)]:
            arcpy.AddField_management(
                in_table=staatvandeweg_table,
                field_name=field,
                field_type="LONG"
            )
    netwerkid_ahi = lees_ahi_netwerksegmenten(staatvandeweg_table, f_netwerkid, f_ahi)
    # arcpy.AddMessage(f"netwerkid_ahi: {str(netwerkid_ahi)[:10000]} ")
    netwerkid_stats = bereken_netwerkid_stats(netwerkid_ahi)
    # arcpy.AddMessage(f"netwerkid_stats: {str(netwerkid_stats)[:1000]} ")

    f_uc = [f_netwerkid, f_ahi, f_ahi_segm, f_ahi_bucket_segm, f_ahi_gewogen_gemiddelde, f_ahi_gewogen_gemiddelde_bucket]
    with arcpy.da.UpdateCursor(staatvandeweg_table, f_uc) as uc:
        for i, row in enumerate(uc):
            netwerkid, ahi, ahi_segm, ahi_segm_bucket, ahi_gewogen_gemiddelde, ahi_gewogen_gemiddelde_bucket = row
            if i % 10000 == 0:
                arcpy.AddMessage(f"{i} rijen behandeld")
            ahi_segm = max(netwerkid_stats.get(netwerkid, {}).get("karakteristieke_toestand", 0),0)  # karakteristieke toestand is altijd >= 0

            ahi_segm_bucket = berekeningAci_methods.bereken_bucket(ahi_segm)
            ahi_gewogen_gemiddelde = max(netwerkid_stats.get(netwerkid, {}).get('gemiddelde',0),0)
            ahi_gewogen_gemiddelde_bucket = berekeningAci_methods.bereken_bucket(ahi_gewogen_gemiddelde)
            row_upd = [netwerkid, ahi, ahi_segm, ahi_segm_bucket, ahi_gewogen_gemiddelde, ahi_gewogen_gemiddelde_bucket]
            uc.updateRow(row_upd)

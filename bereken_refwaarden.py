import arcpy

from berekeningAci_methods import outliers


def berekening_refwaarden(input_table, outlier_threshold):
    refwaarden = {
        'L': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0, 'vr_aandeel': 0},
        'S': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0, 'vr_aandeel': 0},
        'H': {'PW_ETM': 0, 'VR_ETM': 0, 'sat_08': 0, 'sat_17': 0, 'sat_max': 0, 'vr_aandeel': 0},
    }
    f_sc = ['WEGCAT', 'PW_ETM', 'VR_ETM', 'sat_08', 'sat_17']

    with arcpy.da.SearchCursor(input_table, f_sc) as sc:
        for i,row in enumerate(sc):
            wegcat, pw, vr, sat08, sat17 = row
            if wegcat in ("-8", "-9", "EW", "OW", "L", "L1", "L2", "L3"):
                wegcatgroep = "L"
            elif wegcat in ("P", "EHW", "VHW", "PI", "PII", "PII-4", "PII-2", "H"):
                wegcatgroep = "H"
            elif wegcat in ("IW", "RW", "S", "S1", "S2", "S3"):
                wegcatgroep = "S"
            else:
                arcpy.AddWarning(f"input_table: {input_table}, rij {i}")
                arcpy.AddWarning(f"f_sc: {f_sc}")
                arcpy.AddError(f"wegcat niet herkend: {row} voor {input_table}, rij {i}")
                arcpy.AddError(f"wegcatgroep niet herkend: {wegcatgroep} voor {wegcat}, bron: {input_table}, rij {i}")
                wegcatgroep = wegcat[0]

            for f in f_sc[1:]:
                if f in ('PW_ETM', 'VR_ETM'):
                    if type(refwaarden[wegcatgroep][f]) != list:
                        refwaarden[wegcatgroep][f] = []
                    refwaarden[wegcatgroep][f].append(row[f_sc.index(f)])
                    if f == 'VR_ETM':
                        if type(refwaarden[wegcatgroep]["vr_aandeel"]) != list:
                            refwaarden[wegcatgroep]["vr_aandeel"] = []
                        # bereken aandeel vrachtwagens
                        # arcpy.AddMessage(f"refwaarden = {refwaarden}")
                        refwaarden[wegcatgroep]["vr_aandeel"].append(vr/ (pw + vr) * 100 if (pw + vr) > 0 else 0)
                elif row[f_sc.index(f)] > refwaarden[wegcatgroep][f]:
                    refwaarden[wegcatgroep][f] = row[f_sc.index(f)]

    for cat in refwaarden:
        for ref in refwaarden[cat]:
            arcpy.AddMessage(f"categorie: {cat}")
            arcpy.AddMessage(f"ref: {ref}")
            arcpy.AddMessage(f"f:{f}")
            if refwaarden[cat][f] == 0:
                continue
            elif ref in ('PW_ETM', 'VR_ETM', 'vr_aandeel'):
                # pas waarde aan rekening houdend met outliers
                refwaarden[cat][ref] = outliers(refwaarden[cat][ref], outlier_threshold)
            elif ref in ('sat_max'):
                refwaarden[cat][ref] = max(refwaarden[cat]['sat_08'], refwaarden[cat]['sat_17'])

    return refwaarden


import arcpy
import arcpy.metadata as md
import json
def schrijf_gewichten_naar_metadata(feature_class, gewichten):
# feature_class = r"C:\GoogleSharedDrives\Team GIS\Projecten\AddHoc\criticaliteit\criticaliteit20250325.gdb\aci_methode1"

    # Metadata-object ophalen
    metadata = md.Metadata(feature_class)



    # Omzetten naar geformatteerde tekst
    gewichten_str = json.dumps(gewichten, indent=4)
    arcpy.AddMessage(f"Gewichten: {gewichten_str}")

    #  Toevoegen aan de beschrijving
    metadata.description = (
        "ACI-resultaat dataset.\n\n"
        "Gewichten gebruikt in de berekening:\n"
        f"{gewichten_str}"
    )

    # Eventueel ook tags
    metadata.tags = "ACI, criticaliteit, gewichten, berekening"

    # Opslaan
    metadata.save()
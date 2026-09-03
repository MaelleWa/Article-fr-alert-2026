import pandas as pd
from pathlib import Path

#lecture du fichier xls
df_main = pd.read_excel(Path(r"C:\Users\Maell\Documents\fr_alert\these\data\scores_compliance_main.xlsx"))
df_code = pd.read_excel(Path(r"C:\Users\Maell\Documents\fr_alert\these\data\scores_compliance_code.xlsx"))


colonnes = [i for i in range(1, 25)]

df_comparaison = pd.DataFrame()

def diagnostiquer(val_main, val_code):
    if val_main == 1 and val_code == 1:
        return "Vrai positif"  # Vrai Positif
    elif val_main == 0 and val_code == 1:
        return "Faux positif"  # Faux Positif (Le code détecte alors qu'il n'y a rien)
    elif val_main == 1 and val_code == 0:
        return "Faux négatif"  # Faux Négatif (Le code rate quelque chose)
    elif val_main == 0 and val_code == 0:
        return "Vrai négatif"  # Vrai Négatif
    elif val_main == 0.5 and val_code == 0.5:
        return "Vrai positif"
    elif val_main == 0.5 and val_code == 0:
        return "Faux négatif"
    elif val_main == 0 and val_code == 0.5:
        return "Faux positif"
    elif val_main == "x" and val_code == "x":
        return "pas attendu"
    elif val_main == "x" and val_code == 1:
        return "Faux positif, devrait être x code"
    elif val_main == "x" and val_code == 0:
        return "Erreur, devrait être x code"
    elif val_main == 1 and val_code == "x":
        return "Faux négatif, code n'attend rien"
    elif val_main == 0 and val_code == "x":
        return "Erreur, code attend rien"
    return "Erreur, " + str(val_main) + " , " + str(val_code)

for col in colonnes:
    df_comparaison[f"Resultat_{col}"] = df_main.apply(
        lambda x: diagnostiquer(df_main.loc[x.name, col], df_code.loc[x.name, col]), 
        axis=1
    )

if "ID" in df_main.columns:
    df_comparaison.insert(0, "ID", df_main["ID"])

df_comparaison.to_excel(Path(r"C:\Users\Maell\Documents\fr_alert\these\data\matrice_confusion.xlsx"), index=False)

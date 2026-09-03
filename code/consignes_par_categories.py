import pandas as pd
from pathlib import Path

#mots clés consignes

keywords_map = {
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment": 
        ["abritez-vous", "abritez vous", "confinez-vous", "confinez vous", "regagnez un bâtiment", "abri" ,"confin"],
    
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / évacuez": 
        ["abritez vous en hauteur", "réfugiez vous en hauteur", "réfugiez vous","réfugiez-vous", "évacuez","abri", "évac" , "evac" ],
    
    "Fermez portes et fenêtres (+ volets si besoin)": 
        ["fermez vos portes", "fermez vos fenêtres", "fermez les portes", "fermez les fenêtres", "fermez fenêtres", "fermez portes", "fermez volets", "fermez les volets"],
    
    "Evitez la zone / Eloignez-vous des fonds de vallée": 
        ["évitez la zone", "éloignez-vous", "évacuez", "évacuer", "éloignez vous", "evitez la zone", "eloignez vous"],
    
    "Reportez vos déplacements / Evitez activité extérieure": 
        ["reportez vos déplacements", "annulez vos déplacements", "évitez toute activité extérieure", "evitez toute activité extérieure"],
    
    "Coupez eau, gaz ou électricité / la ventilation": 
        ["coupez l'eau", "coupez le gaz", "coupez l'électricité", "coupez la ventilation", "coupez eau", "coupez gaz", "coupez électricité", "coupez ventilation", "arrêtez l'eau", "arrêtez le gaz", "arrêtez l'électricité", "arrêtez la ventilation", "arrêtez eau", "arrêtez gaz", "arrêtez électricité", "arrêtez ventilation"],

    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)": 
        ["équipements", "pneus", "chaînes", "école", "eau potable", "consommer"],
    
    "Restez en lieu sûr": 
        ["restez en lieu sûr"],
    
    "Restez à l'écoute d'informations des autorités": 
        ["restez à l'écoute", "suivez les consignes", "respectez les consignes des autorités"]
}

# dictionnaire de correspondance : nature du danger -> liste des consignes attendues
referentiel_danger = {
"cyclone / ouragan" : [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Coupez eau, gaz ou électricité / la ventilation",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"eau potable" : [
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Coupez eau, gaz ou électricité / la ventilation",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"environnemental" : [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment", 
    "Fermez portes et fenêtres (+ volets si besoin)",  
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],  
"éruption volcanique" : [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"feu de forêt" : [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
     "Restez à l'écoute d'informations des autorités",
],
"industriel" : [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Coupez eau, gaz ou électricité / la ventilation",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"inondation" : [
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / évacuez",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Coupez eau, gaz ou électricité / la ventilation",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"neige et verglas" : [
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
     "Restez à l'écoute d'informations des autorités",
],
"nrbce" : [
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"orage": [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure", 
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"rupture digue": [
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / Evacuez",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"sanitaire": [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"sécurité publique": [
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / Evacuez",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",   
],
"submersion marine": [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
     "Restez à l'écoute d'informations des autorités",
],
"tempête": [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
],
"tsunami": [
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / évacuez",  
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
]
}

# liste  de toutes les consignes possibles (pour créer les colonnes)
consignes_globales = [
    "Abritez-vous dans un bâtiment, en dur / fermé ; Confinez-vous . Regagnez un bâtiment",
    "Abritez vous en hauteur (réfugiez vous le plus haut possible) / évacuez",
    "Fermez portes et fenêtres (+ volets si besoin)",
    "Evitez la zone / Eloignez-vous des fonds de vallée",
    "Reportez vos déplacements / Evitez activité extérieure",
    "Coupez eau, gaz ou électricité / la ventilation",
    "Autres consignes en plus (Munissez-vous d'équipements spéciaux (neige) ; Enfants (inondations) ; Consommation (pollution)",
    "Restez en lieu sûr",
    "Restez à l'écoute d'informations des autorités",
]

def verifier_ligne(row):
# récupération et mise en minuscule des données d'entrée
    danger_actuel = str(row['Nature du danger']).lower().strip()
    message_text = str(row['Description']).lower()
    # on récupère les consignes attendues pour ce danger (liste vide si non trouvé)
    attendues = referentiel_danger.get(danger_actuel, [])
    resultat = {}
    for consigne_nom, mots_cles in keywords_map.items():
        if consigne_nom not in attendues:
            resultat[consigne_nom] = "x"
        else:
            trouve = any(mot in message_text for mot in mots_cles)
            resultat[consigne_nom] = 1 if trouve else 0
    return pd.Series(resultat)

# execution

# chargement des données 
input_file = Path("C:/Users/Maell/Documents/fr_alert/these/data/messages_fr_alert.xlsx")
df = pd.read_excel(input_file)

df_analyse = df.apply(verifier_ligne, axis=1)
df_final = pd.concat([df, df_analyse], axis=1)


# export final 

output_file = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/analyse_consignes.xlsx")
df_final.to_excel(output_file, index=False)

if __name__ == "__main__":
    input_file = Path("C:/Users/Maell/Documents/fr_alert/these/data/messages_fr_alert.xlsx")
    df = pd.read_excel(input_file)
    
    df_analyse = df.apply(verifier_ligne, axis=1)
    df_final = pd.concat([df, df_analyse], axis=1)
    
    output_file = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/analyse_consignes.xlsx")
    df_final.to_excel(output_file, index=False)
    print("Exécution standalone terminée.")
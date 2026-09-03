import re
import spacy
import pandas as pd
from pathlib import Path
from unidecode import unidecode

from consignes_par_categories import verifier_ligne
from detection_communes import build_pipeline, detect_commune_for_invariant

nlp = spacy.load("fr_core_news_lg")

communes_csv = Path("C:/Users/Maell/Documents/fr_alert/these/data/communes_sans_doublon.csv")
df_communes = pd.read_csv(communes_csv)
communes = df_communes["commune"].dropna().astype(str).tolist()
nlp_communes = build_pipeline(communes)


def normalize(s):
    s = unidecode(s.lower())
    s = re.sub(r"[-'’]", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def detect_alerte(text):
    t = text.lower()
    if re.search(r"alerte\s+(?:de\s+la\s+)?préfecture", t) or re.search(r"alerte\s+(?:du\s+)?préfet", t):
        return 0.5, "alerte préfecture"

    evenements = ["inondation", "cyclone", "cyclonique", "tempête", "tempete", "incendie", 
                  "feu", "volcan", "éruption","eruption", "seisme", "séisme", 
                  "orages", "météo", "meteo", "crue", "accident industriel", "pluies intenses", 
                  "neige-verglas", "neige", "tsunami", "sanitaire", 
                  "explosion" ]
    evts_pipe = "|".join(evenements)
    
    regex_apres = rf"\balerte\b\W+(?:\w+\W+){{0,4}}(?:{evts_pipe})\b"
    regex_avant = rf"\b(?:{evts_pipe})\b\W+(?:\w+\W+){{0,4}}\balerte\b"

    match_apres = re.search(regex_apres, t)
    match_avant = re.search(regex_avant, t)
    
    if match_apres or match_avant:
        info = (match_apres or match_avant).group(0)
        return 1, f"alerte événement : {info}"

    keywords = ["vigilance", "prévention"]
    for k in keywords:
        if k in text.lower():
            return 0.5, k

    return 0, ""


# 2. Nom du département
departements = [
    "ain","aisne","allier","alpes-de-haute-provence","alpes de haut provence","hautes-alpes","hautes alpes","alpes-maritimes","alpes maritimes",
    "ardèche","ardeche","ardennes","ariège","ariege","aube","aude","aveyron","bouches-du-rhône","bouches-du-rhone","bouches du rhône","bouches du rhone","calvados",
    "cantal","charente","charente-maritime","charente maritime","cher","corrèze","correze","corse-du-sud","corse du sud","haute corse","haute-corse",
    "côte-d'or","côte d'or","côte d or","cote-d'or","côtes-d'armor","cotes-d'amor","côtes d'armor","côtes d armor","cotes d'armor","cotes d armor",
    "creuse","dordogne","doubs","drôme","drome","eure","eure-et-loir","eure et loir",
    "finistère","finistere","gard","haute-garonne","haute garonne","gers","gironde","hérault","herault","ille-et-vilaine","ille et vilaine","indre",
    "indre-et-loire","d’indre-et-loire","indre et loire","isère","isere","jura","landes","loir-et-cher","loir et cher","loire","haute-loire","haute loire",
    "loire-atlantique","loire atlantique","loiret","lot","lot-et-garonne","lot et garonne","lozère","lozere","maine-et-loire","maine et loire","manche",
    "marne","haute-marne","haute marne","mayenne","meurthe-et-moselle","meurthe et moselle","meuse","morbihan","moselle",
    "nièvre","nievre","nord","oise","orne","pas-de-calais","pas de calais","puy-de-dôme","puy de dôme","puy-de-dome","puy de dome","pyrénées-atlantiques",
    "pyrenees-atlantiques", "pyrénées atlantiques","pyrenees atlantiques",
    "hautes-pyrénées","hautes pyrénées","hautes-pyrenees","hautes pyrenees","pyrénées-orientales","pyrenees-orientales","pyrénées orientales","pyrenees orientales",
    "bas-rhin","bas rhin","haut-rhin","haut rhin","rhône","rhone","haute-saône","haute saône","haute-saone","haute saone",
    "saône-et-loire","saône et loire","saone-et-loire","saone et loire","sarthe","savoie","haute-savoie","haute savoie","paris","seine-maritime","seine maritime",
    "seine-et-marne","seine et marne","yvelines","deux-sèvres","deux sèvres","deux-sevres", "deux sevres","somme","tarn","tarn-et-garonne", "tarn et garonne","var",
    "vaucluse","vendée","vendee","vienne","haute-vienne","haute vienne","vosges","yonne","territoire-de-belfort", "territoire de belfort",
    "essonne","hauts-de-seine","hauts de seine","seine-saint-denis","seine saint denis","val-de-marne","val de marne","val-d'oise","val d'oise","val d oise",
    "guadeloupe","martinique","guyane","la réunion","la reunion","mayotte"
]

departements.sort(key=len, reverse=True)
noms_dep_regex = "|".join(re.escape(dep) for dep in departements)

regex_dep_strict = re.compile(
    rf"\b(?:préfecture|préfectures|prefecture|prefectures|prefet|prefets|préfet|préfets|département|départements|departement|departements)\b\W+(?:\w+\W+){{0,8}}({noms_dep_regex})\b", 
    re.IGNORECASE
)

def detect_departement(text):
    # On cherche directement dans le texte original
    match_dpt = regex_dep_strict.search(text)
    
    if match_dpt:
        return 1, match_dpt.group(0)
    
    # --- Reste de ta fonction (numéros) ---
    match_num_pref = re.search(r"préfecture\s*(?:du\s*)?(\d+)", text, re.IGNORECASE)
    match_num_dpt = re.search(r"d[ée]partement\s*(?:du\s*)?(\d+)", text, re.IGNORECASE)
    
    if match_num_pref:
        return 0.5, f"Préfecture du {match_num_pref.group(1)}"
    if match_num_dpt:
        return 0.5, f"Département {match_num_dpt.group(1)}"

    return 0, ""

    
# 3. Site internet / numéro téléphone
def detect_site_tel(text):
    t = text.lower()
    # URL
    m_site = re.search(r"https?://", t)
    if m_site:
        return 1, m_site.group(0)
    # Numéro de téléphone français à 10 chiffres
    tel_pattern = r"(0\d)([\s.-]?\d{2}){4}"
    m_tel = re.search(tel_pattern, text)
    if m_tel:
        return 1, m_tel.group(0)
    # www.
    if "www." in t:
        return 1, "www."
    if "@" in t:
        return 0.5, "@"
    return 0, ""

# 4. Catégorie
def detect_categorie(text):
    categories = [
        "inondation", "inondations", "tempête", "tempete", "cyclone","cyclonique", "incendie", "tsunami",
        "éruption","séisme","pollution","fuite de gaz","houle"
        "incident nucléaire","épidémie","pandémie","incident agro-alimentaire",
        "accident routier","accident ferroviaire","accident aérien","incident industriel","accident industriel",
        "acte à caractère terroriste","feu industriel","crue","risque radiologique",
        "événement majeur de sécurité publique","rupture d'ouvrage hydraulique",
        "vents violents","feu de forêt","orage","pluie intense","pluies intenses",
        "accident impliquant des matières dangereuses","inondation rapide","typhon","ouragan",
        "accident de centrale nucléaire","submersion marine","risque nucléaire",
        "risque biologique","rupture de digue","accident transport de matières dangereuses",
        "risque chimique","accident de la circulation",
        "canicule", "neige-verglas", "neige", "explosion", "sanitaire", "Incident sur le réseau d’eau potable"
    ]
    t = text.lower()

    for c in categories:
        if c in t:
            return 1, c
    return 0, ""

# 5. Impacts
def detect_impacts(text):
    keywords = [
        "dégâts", "dommages", "blessés", "victimes",
        "interruption", "coupure",
        "risque de", "impact", "conséquences",
        "perturbation", "effondrement"
    ]
    t = text.lower()
    for k in keywords:
        if k in t:
            return 1, k
    return 0, ""


# 6. Précisions
def detect_precisions(text):
    motscles1= ["pic", "forte houle", 
               "très violent","très violente","très violents","très violentes","forte augmentation", "fortes augmentations",
               "fortes précipitations",       
                "hauteurs d’eau", "hauteur d’eau", "hauteurs d'eau", "hauteur d'eau","hauteurs attendues", "hauteur attendue"]
    
    motscles05 = ["exceptionnel", "exceptionnelle", "exceptionnels", "exceptionnelles", "historique","extrêmement violent"
    "extrêmements violents"]
    t = text.lower()
    for p in motscles1:
        if p in t:
            return 1, p
    for p in motscles05:
        if p in t:
            return 0.5, p
        
    return 0, ""
        
    # ajouter les chiffres attendus pour les précisions (atteindre 8.68m par exemple)
    #pattern_chiffres = r"\b(?:atteindre|jusqu'à|jusqu’à|prévoir|prévue|prévu|prévisibles|prévisible|attendues?|estimées?|estimé|estimée|de l'ordre de|de l’ordre de)\s+(\d{1,2}(?:[.,]\d{1,2})?)\s*(mètres?|m\b)"
    #m_chiffres = re.search(pattern_chiffres, t)
    #if m_chiffres:
    #    return 0.5, m_chiffres.group(1) + " " + m_chiffres.group(2)

# 7. Site
def detect_site(text):
    t = text.lower()

    sites_fixes = ["piton de la fournaise", "site inoe", "usine arcelor mittal", "faubourg", "col bagargiak", 
                   "entreprise elkem silicones sud","les Marquises","Mayotte","La réunion"]
    for s in sites_fixes:
        if s.lower() in t:
            return 1, s

    sites_motscles = [
        "usine", "bassin", "canal", "auberge", "chemin", "avenue", "rue",
        "col", "secteur", "quartier", "gymnase", "salle des fêtes", "école", "le long", 
        "la partie ouest", "la partie est", "la partie nord", "la partie sud", "la vallee", "la vallée", "refuge", 
        "réservoir"
    ]

    pattern = r"\b(?:" + "|".join(sites_motscles) + r")\s+(?:de\s+|du\s+|d[’'']\s*)"
    
    match = re.search(pattern, t)
    if match:
        return 1, match.group(0).strip()

    # Fleuves / rivières
    fleuves_csv = Path("C:/Users/Maell/Documents/fr_alert/these/data/fleuves_rivieres.csv")
    df_fleuves = pd.read_csv(fleuves_csv, encoding='iso-8859-1')
    noms_fleuves = df_fleuves["nom"].dropna().astype(str).tolist()
    mc_eau = ["crue","hauteurs d'eau", "hauteur d'eau", "hauteurs d’eau", "hauteur d’eau", "inondation rapide"]
    for f in noms_fleuves:
        pattern_fleuve = rf"(?<![\w-])({re.escape(f)})(?![\w-])"
        for m in mc_eau:
            if re.search(m, t, re.IGNORECASE) and re.search(pattern_fleuve, t, re.IGNORECASE):
                        return 1, f
    return 0, ""

# 8. Commune
def detect_commune(text):
    return detect_commune_for_invariant(nlp_communes, text)

# 9. Emprise touchée
def detect_emprise(text, nb_communes=0):

    if nb_communes > 1:
        return 1, f"multiples communes ({nb_communes})"


    keywords = [
        "zone", "secteur", "quartier", "territoire",
        "communes de","dans les zones",
        "zones concernées", "l'accès",
        "la circulation", "les routes", "les voies","l'ensemble du département"
    ]
    t = text.lower()
    for k in keywords:
        if k in t:
            return 1, k
            
    return 0, ""

# 10. Horaires
def detect_horaires(text):
    t = text.lower()

    pattern_heure = r"\b\d{1,2}\s?h\s?\d{0,2}\b|\b\d{1,2}:\d{2}\b"
    m_heure = re.search(pattern_heure, t)
    
    m_midi = re.search(r"(?<!après[- ])\bmidi\b|\bminuit\b", t)

    if m_heure:
        return 1, m_heure.group(0)
    if m_midi:
        return 1, m_midi.group(0)

    pattern_date_lettres = r"\b(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+\d{1,2}\b|\b\d{1,2}\s+(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|octobre|novembre|d[ée]cembre)\b"

    pattern_date_num = r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b"
    
    m_date_L = re.search(pattern_date_lettres, t)
    m_date_N = re.search(pattern_date_num, t)

    if m_date_L:
        return 0.5, m_date_L.group(0)
    if m_date_N:
        return 0.5, m_date_N.group(0)

    return 0, ""

# 11. Indications temporelles
def detect_indications(text):
    patterns_1 = [
        "en cours","à prévoir","à venir","actuellement",
         "immédiat","prochainement","maintenant",
        "dans les prochaines minutes","dès que possible",
        "le plus rapidement possible","aussitôt que possible",
        "ce jour",
        "aujourd'hui", "aujourdhui", "demain", "ce soir",
        "cette nuit", "dans la soirée", "dans la nuit", "au cours de la nuit", "sans délai", "pour une durée indéterminée", 
        "toute la nuit", "en voie d", "demeure actif", 
    ]
    patterns_05 = [
        "durant la matinée", "immédiatement", "en fin de matinée", "en début d'après-midi", "la journée du", "impérativement avant", 
        "dans les prochaines heures", "pour le moment", "jusqu'à "
    ]

    text_lower = text.lower()
    for p in patterns_1:
        if p in text_lower:
            return 1, p
    for p in patterns_05:
        if p in text_lower:
            return 0.5, p  

    return 0, ""

# 12. Consignes numérotées
def detect_consignes_num(text):
    # tirets
    if re.search(r'(?m)^\s*-\s+', text):
        return 0.5, "-"

    # extraire nums en début de ligne
    pattern = r'(?m)^\s*(\d+)(?:[\.\)\s-]|$)'
    matches = re.findall(pattern, text)

    if matches:
        # Conversion en entiers pour vérifier la suite
        nums = [int(n) for n in matches]
        
        # vérifier si suite correcte 
        expected_seq = list(range(nums[0], nums[0] + len(nums)))
        
        if nums == expected_seq:
            return 1, f"correctement numéroté : {nums[0]}-{nums[-1]}"
        else:
            return 0.5, f"Numéroté mais désordonné : {nums}"

    return 0, None

# 14. Absence de négations
def detect_absence_negations(text):
    neg_patterns = [
        r"\bne\s+pas\b", 
        r"n'", 
        r"\baucun(?:e)?\b", 
        r"\bjamais\b", 
        r"\bpas\b(?!\s*[- ]de\s*calais)", 
        r"\bpas\s+de\b(?!\s*calais)"
    ]
    
    t = text.lower()
    
    for pattern in neg_patterns:
        match = re.search(pattern, t, re.IGNORECASE)
        if match:
            return 0, match.group(0)
                
    return 1, ""

# 15. Standard d'écriture
def detect_standard_ecriture(text):
    if re.search(r"[A-Z]{4,}", text):
        return 0, "MAJUSCULES"
    if re.search(r"\b[A-Za-z]{1,15}[0-9]{3,}\b", text):
        return 0, "mot_bizarre"
    return 1, ""

# 13. Mise en page aérée
def detect_mise_en_page(text):
    if "\n\n" in text:
        return 1, "double_saut_de_ligne"
    return 0, ""

# Dictionnaire des invariants et leurs fonctions de détection
invariants = {
    "1. Alerte": detect_alerte,
    "2. Nom du département": detect_departement,
    "3. Site internet / numéro téléphone": detect_site_tel,
    "4. Catégorie": detect_categorie,
    "5. Impacts": detect_impacts,
    "6. Précisions": detect_precisions,
    "7. Site": detect_site,
    "8. Commune": detect_commune,
    "9. Emprise touchée": detect_emprise,
    "10. Horaires": detect_horaires,
    "11. Indications temporelles": detect_indications,
    "12. Consignes numérotées": detect_consignes_num,
    "13. Mise en page aérée": detect_mise_en_page,
    "14. Absence de négations": detect_absence_negations,
    "15. Standard d'écriture": detect_standard_ecriture
}


input_file = Path("C:/Users/Maell/Documents/fr_alert/these/data/messages_fr_alert.xlsx")
#input_file = Path("C:/Users/Maell/Documents/fr_alert/these/data/exercice_txt_reduit.xlsx")

output_file = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/analyse_alertes_vdef.xlsx")
#output_file = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/analyse_alertes_exercice.xlsx")

df = pd.read_excel(input_file)
colonne_texte = "Description"

def clean_sheet_name(name):
    # enlever les caractères interdits
    name = re.sub(r"[:\\/*?\[\]]", "_", name)
    # tronquer à 31 caractères
    return name[:31]



with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
    all_sheets_data = {nom: [] for nom in invariants.keys()}

    for _, row in df.iterrows():
        texte = str(row[colonne_texte])
        
        res_commune = detect_commune(texte)
        score_com, noms_com, nb_com = res_commune 
        score_emp, declencheur_emp = detect_emprise(texte, nb_communes=nb_com)

        for nom, func in invariants.items():
            if nom == "8. Commune":
                s, d = score_com, noms_com
            elif nom == "9. Emprise touchée":
                s, d = score_emp, declencheur_emp
            else:
                result = func(texte)
                if result is None:
                    s, d = 0, ""
                else:
                    s, d = result
            
            all_sheets_data[nom].append({
                "id": row.get("id", ""),
                "lien": row.get("lien", ""),
                "Description": texte,
                "Score": s,
                "Déclencheur": d
            })


    df_consignes_seulement = df.apply(verifier_ligne, axis=1)
    df_onglet_consignes_final = pd.concat([
        df[["id", "lien", colonne_texte]], 
        df_consignes_seulement
    ], axis=1)

    for nom, rows in all_sheets_data.items():
        # Écriture de l'onglet de l'invariant actuel
        pd.DataFrame(rows).to_excel(
            writer,
            sheet_name=clean_sheet_name(nom),
            index=False
        )

        if nom == "12. Consignes numérotées":
            df_onglet_consignes_final.to_excel(
                writer,
                sheet_name="Consignes", 
                index=False
            )

print("Export terminé :", output_file)
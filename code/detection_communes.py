import re
import unicodedata
from pathlib import Path
import pandas as pd
import spacy

communes_csv = Path("C:/Users/Maell/Documents/fr_alert/these/data/communes_sans_doublon.csv")
communes_ambigues_csv = Path("C:/Users/Maell/Documents/fr_alert/these/data/communes_ambigues.csv")
seuil_heuristic = 1.5

prep_lieu = {"à", "au", "aux", "dans", "vers", "près"}
mots_loc = {"commune", "communes", "village", "ville", "bourg", "habitants"}
verbes_mvt = {"aller", "venir", "partir", "arriver", "habiter", "déménager"}

df_communes = pd.read_csv(communes_csv)
communes_list = df_communes["commune"].dropna().astype(str).tolist()

df_amb = pd.read_csv(communes_ambigues_csv)
communes_ambigues = set(df_amb["commune"].dropna().str.lower().tolist())

def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = name.replace("’", "'").replace("`", "'")
    name = ''.join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    )
    name = re.sub(r"'+", " ", name)
    name = name.replace("-", " ")
    name = re.sub(r"\s+", " ", name)
    return name

communes_norm_set = {normalize_name(c) for c in communes_list}

def normalize_text_for_detection(text: str) -> str:
    text = re.sub(r"[\/\(\)\[\]\{\}]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def generate_commune_patterns(communes):
    patterns = []
    for c in communes:
        tokens = str(c).strip().split()
        if not tokens:
            continue
        patterns.append({
            "label": "CAND_COMMUNE",
            "pattern": [{"LOWER": t.lower()} for t in tokens]
        })
    return patterns

def build_pipeline(communes_list):
    try:
        nlp = spacy.load("fr_core_news_lg")
    except:
        nlp = spacy.blank("fr")
        print(" fr_core_news_lg introuvable -> modèle vierge utilisé")

    if "ner" in nlp.pipe_names:
        nlp.remove_pipe("ner")

    ruler = nlp.add_pipe(
        "entity_ruler",
        name="gazetteer_communes",
        before="parser" if "parser" in nlp.pipe_names else None
    )
    ruler.add_patterns(generate_commune_patterns(communes_list))
    return nlp

def has_loc_word_before(ent, doc, max_dist=3):
    for i in range(max(ent.start - max_dist, 0), ent.start):
        if doc[i].lower_ in mots_loc:
            return True
    return False

def extract_features(doc, ent):
    anchor = ent[-1]
    prev_tokens = doc[max(0, ent.start - 3):ent.start]

    return {
        "has_preposition_before": any(t.lower_ in prep_lieu for t in prev_tokens),
        "has_loc_word_before": has_loc_word_before(ent, doc),
        "has_movement_verb_before": any(
            t.lemma_.lower() in verbes_mvt for t in prev_tokens
        ),
        "is_propn": int(anchor.pos_ == "PROPN"),
        "is_noun": int(anchor.pos_ == "NOUN"),
        "is_title": int(ent.text[0].isupper()),
        "ambiguous_name": int(ent.text.lower() in communes_ambigues),
        "n_tokens": len(ent),
        "has_hyphen": int("-" in ent.text),
    }

def heuristic_score(f):
    score = 0
    score += f["is_propn"] * 1.2
    score += f["is_noun"] * 0.2
    score += f["has_preposition_before"] * 1.0
    score += f["has_loc_word_before"] * 1.2
    score += f["has_movement_verb_before"] * 0.6
    score += f["is_title"] * 0.5
    score += (f["n_tokens"] > 1) * 0.5
    score += f["has_hyphen"] * 0.3
    score -= f["ambiguous_name"] * 2.0
    return score

def split_communes_in_span(span_text: str):
    text = re.sub(r"(?i)^communes?\s+de\s+", "", span_text)
    text = re.sub(r"\([^)]*\)", "", text)
    parts = re.split(r"\s*,\s*|\s+et\s+", text)
    return [p.strip() for p in parts if p.strip()]

def detect_commune_after_commune_de(text: str):
    results = []
    pattern = re.compile(
        r"\b(?:la|les)\s+(?:communes?|habitants?)\s+de\s+([A-ZÀ-ÖØ-öø-ÿ][\w\-]*)",
        re.IGNORECASE | re.UNICODE
    )
    for m in pattern.finditer(text):
        nom = m.group(1)
        results.append((nom, m.start(1), m.end(1), 999, {"rule": "A0"}))
    return results

def detect_commune_after_a(doc, communes_norm_set, max_tokens=7):
    results = []
    FILLERS = {"la", "le", "les", "l'", "de", "d'", "du", "des", "abords", "proximité", "niveau", "station"}

    for i, tok in enumerate(doc):
        if tok.lower_ not in {"à", "au", "aux"}:
            continue

        if i + 1 < len(doc):
            t = doc[i + 1]
            if t.pos_ == "PROPN":
                norm = normalize_name(t.text)
                if norm in communes_norm_set:
                    results.append((t.text, t.idx, t.idx + len(t.text), 850, {"rule": "A3"}))
                    continue  

        j = i + 1
        steps = 0
        while j < len(doc) and steps < max_tokens:
            t = doc[j]
            steps += 1
            if t.lower_ in FILLERS:
                j += 1
                continue
            if t.pos_ not in {"PROPN", "NOUN"}:
                break
            norm = normalize_name(t.text)
            if norm in communes_norm_set:
                results.append((t.text, t.idx, t.idx + len(t.text), 800, {"rule": "A3"}))
            break
    return results

def detect_commune_rule_a1(doc, threshold=seuil_heuristic):
    results = []
    for span in doc.ents:
        if span.label_ != "CAND_COMMUNE":
            continue

        for c in split_communes_in_span(span.text):
            match = re.search(re.escape(c), span.text, re.IGNORECASE)
            if not match:
                continue

            start = span.start_char + match.start()
            end = span.start_char + match.end()
            sub = doc.char_span(start, end)

            if sub is None:
                continue

            feats = extract_features(doc, sub)
            score = heuristic_score(feats)

            if score >= threshold:
                results.append(
                    (c, start, end, score, {"rule": "A1", **feats})
                )
    return results

def detect_communes_in_text(nlp, text: str, threshold=seuil_heuristic):
    results = []
    text = normalize_text_for_detection(text)
    doc = nlp(text)

    results.extend(detect_commune_after_commune_de(text))  # Règle A0
    results.extend(detect_commune_after_a(doc, communes_norm_set))  # Règle A3
    results.extend(detect_commune_rule_a1(doc, threshold))

    unique = {}
    for nom, start, end, score, meta in results:
        key = (start, end, normalize_name(nom))
        if key not in unique or score > unique[key][3]:
            unique[key] = (nom, start, end, score, meta)

    return list(unique.values())

debug_rows = []

if __name__ == "__main__":
    nlp = build_pipeline(communes_list)

    fichier_source = Path("C:/Users/Maell/Documents/fr_alert/these/data/messages_fr_alert.xlsx")
    df = pd.read_excel(fichier_source)

    has_commune_col = []
    has_emprise_col = []

    for idx, text in enumerate(df["Description"].fillna("")):
        entities = detect_communes_in_text(nlp, text)
        
        noms_trouves = sorted({nom for nom, start, end, score, meta in entities})
        nb_communes = len(noms_trouves)
        communes_fusionnees = ", ".join(noms_trouves) if noms_trouves else ""

        debug_rows.append({
            "Ligne_texte": idx,
            "Texte": text,
            "Communes_detectees": communes_fusionnees,
            "Nb_communes": nb_communes,
            "Score_Max": max([e[3] for e in entities]) if entities else 0,
            "Regles": " ".join(set([e[4].get("rule", "") for e in entities])) if entities else ""
        })

        if nb_communes == 1:
            has_commune_col.append(1)
            has_emprise_col.append(0)
        elif nb_communes > 1:
            has_commune_col.append(0)
            has_emprise_col.append(1)
        else:
            has_commune_col.append(0)
            has_emprise_col.append(0)

    df["Has_Commune"] = has_commune_col
    df["Has_Emprise"] = has_emprise_col

    df_debug = pd.DataFrame(debug_rows)

    df_debug = df_debug[df_debug["Nb_communes"] > 0]
    df = df[(df["Has_Commune"] == 1) | (df["Has_Emprise"] == 1)]

    debug_path = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/debug_communes.xlsx")
    df_debug.to_excel(debug_path, index=False)

    fichier_destination = Path("C:/Users/Maell/Documents/fr_alert/these/recap_alertes/alertes_reelles_communes.xlsx")
    df.to_excel(fichier_destination, index=False)

    print(f" DEBUG FILTRÉ : {debug_path}")
    print(f" SORTIE FILTRÉE : {fichier_destination}")

def detect_commune_for_invariant(nlp, text):
    entities = detect_communes_in_text(nlp, text)
    communes_uniques = {e[0] for e in entities}
    nb_communes = len(communes_uniques)
    has_commune = 1 if nb_communes > 0 else 0
    noms_str = ", ".join(sorted(communes_uniques))
    return has_commune, noms_str, nb_communes
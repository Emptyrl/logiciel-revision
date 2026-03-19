import streamlit as st
from google import genai
import json
from PIL import Image
import io
import contextlib

# --- FONCTIONS DE RAPPEL (CALLBACKS) ---
def maj_calculatrice(touche):
    if touche == 'C': st.session_state.calc_expr = ""
    elif touche == '=':
        try:
            if all(c in "0123456789+-*/. " for c in st.session_state.calc_expr):
                st.session_state.calc_expr = str(eval(st.session_state.calc_expr, {"__builtins__": None}, {}))
            else: st.session_state.calc_expr = "Erreur"
        except: st.session_state.calc_expr = "Erreur"
    else:
        if st.session_state.calc_expr == "Erreur": st.session_state.calc_expr = ""
        st.session_state.calc_expr += str(touche)

def aller_aux_instructions(section):
    st.session_state.menu_selection = t["menu_aide"]
    st.session_state.section_instruction = section

# --- INITIALISATION DE LA MÉMOIRE GLOBALE ---
# La clé API est lue uniquement depuis les secrets du serveur (sécurité maximale)
if 'api_key' not in st.session_state:
    try:
        st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.session_state.api_key = ""

if 'lecon' not in st.session_state: st.session_state.lecon = ""
if 'questions' not in st.session_state: st.session_state.questions = []
if 'index_actuel' not in st.session_state: st.session_state.index_actuel = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'reponse_validee' not in st.session_state: st.session_state.reponse_validee = False
if 'evaluation_ia' not in st.session_state: st.session_state.evaluation_ia = None
if 'fiche_revision' not in st.session_state: st.session_state.fiche_revision = ""
if 'outils_actifs' not in st.session_state: st.session_state.outils_actifs = False
if 'calc_expr' not in st.session_state: st.session_state.calc_expr = ""
if 'section_instruction' not in st.session_state: st.session_state.section_instruction = None

if 'langue' not in st.session_state: st.session_state.langue = "Français"
if 'theme' not in st.session_state: st.session_state.theme = "Lumineux"

# --- GESTION DES THÈMES VISUELS (DOUX ET ÉPURÉS) ---
if st.session_state.theme == "Dégradé Bleu Doux":
    st.markdown("""<style>.stApp { background: linear-gradient(to bottom right, #e0eafc, #cfdef3); color: #1e1e1e; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Dégradé Ciel Doux":
    st.markdown("""<style>.stApp { background: linear-gradient(to bottom right, #fdfbfb, #ebedee); color: #1e1e1e; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Sombre":
    st.markdown("""<style>.stApp { background-color: #0e1117; color: white; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Lumineux":
    st.markdown("""<style>.stApp { background-color: #ffffff; color: black; }</style>""", unsafe_allow_html=True)

# --- DICTIONNAIRE DE TRADUCTION ---
if st.session_state.langue == "Français":
    t = {
        "nav": "🧭 Navigation", "menu_lecon": "📖 Leçon", "menu_exo": "🧠 Exercices", "menu_fiches": "📝 Fiches", "menu_aide": "ℹ️ Instructions", "menu_param": "⚙️ Paramètres",
        "statut_ok": "✅ Leçon en mémoire", "statut_ko": "❌ Aucune leçon", "aide_btn": "🤔 Aide",
        "titre_lecon": "📖 Ajouter la leçon", "desc_lecon": "Importe des photos de tes notes, ou colle ton cours en texte.",
        "btn_extraire": "🪄 Extraire le texte", "btn_appliquer": "Appliquer la leçon 💾", "succes_lecon": "Leçon sauvegardée !",
        "titre_exo": "🧠 S'entraîner", "warn_lecon": "⚠️ Ajoute d'abord une leçon.", "config_exo": "### Configuration",
        "type_exo": "Type d'exercice :", "nb_q": "Nombre de questions :", "opt_outils": "🛠️ Activer les outils d'aide",
        "btn_gen_exo": "🚀 Générer l'exercice", "valider": "Valider ✅", "passer": "Passer ⏭️", "suivant": "Suivant ➡️",
        "titre_fiches": "📝 Fiches de révisions", "type_fiche": "Quel type de document ?", "btn_gen_fiche": "🪄 Générer ma fiche",
        "titre_param": "⚙️ Paramètres", "save_param": "Sauvegarder"
    }
else:
    t = {
        "nav": "🧭 Navigation", "menu_lecon": "📖 Lesson", "menu_exo": "🧠 Exercises", "menu_fiches": "📝 Sheets", "menu_aide": "ℹ️ Help", "menu_param": "⚙️ Settings",
        "statut_ok": "✅ Lesson saved", "statut_ko": "❌ No lesson", "aide_btn": "🤔 Help",
        "titre_lecon": "📖 Add Lesson", "desc_lecon": "Upload images of your notes, or paste your text directly.",
        "btn_extraire": "🪄 Extract text", "btn_appliquer": "Save Lesson 💾", "succes_lecon": "Lesson saved!",
        "titre_exo": "🧠 Practice", "warn_lecon": "⚠️ Please add a lesson first.", "config_exo": "### Setup",
        "type_exo": "Exercise type:", "nb_q": "Number of questions:", "opt_outils": "🛠️ Enable helper tools",
        "btn_gen_exo": "🚀 Generate exercise", "valider": "Submit ✅", "passer": "Skip ⏭️", "suivant": "Next ➡️",
        "titre_fiches": "📝 Study Sheets", "type_fiche": "What kind of document?", "btn_gen_fiche": "🪄 Generate sheet",
        "titre_param": "⚙️ Settings", "save_param": "Save settings"
    }

menu_options = [t["menu_lecon"], t["menu_exo"], t["menu_fiches"], t["menu_aide"], t["menu_param"]]
if 'menu_selection' not in st.session_state: st.session_state.menu_selection = menu_options[0]

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.title(t["nav"])
    menu = st.radio("Menu :", menu_options, key="menu_selection")
    st.write("---")
    if st.session_state.lecon: st.success(t["statut_ok"])
    else: st.error(t["statut_ko"])

# ==========================================
# MENU 1 : LEÇON
# ==========================================
if menu == t["menu_lecon"]:
    c1, c2 = st.columns([4, 1])
    with c1: st.title(t["titre_lecon"])
    with c2: st.button(t["aide_btn"], on_click=aller_aux_instructions, args=("Leçon",))
    st.write(t["desc_lecon"])
    
    fichiers_images = st.file_uploader("📸 JPG, PNG :", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    if fichiers_images:
        images_ouvertes = [Image.open(f) for f in fichiers_images]
        cols = st.columns(min(len(fichiers_images), 3) if fichiers_images else 1)
        for i, img in enumerate(images_ouvertes):
            with cols[i % 3]: st.image(img, use_container_width=True)
                
        if st.button(t["btn_extraire"]):
            if not st.session_state.api_key: st.error("Clé API manquante dans les secrets du serveur !")
            else:
                with st.spinner("..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        rep = client.models.generate_content(model='gemini-2.5-flash', contents=["Transcris ce texte."] + images_ouvertes)
                        st.session_state.lecon = rep.text
                    except: st.error("Erreur lors de l'extraction.")

    lecon_temp = st.text_area("Texte de la leçon", value=st.session_state.lecon, height=300, label_visibility="collapsed")
    if st.button(t["btn_appliquer"]):
        st.session_state.lecon = lecon_temp
        st.session_state.questions = []
        st.success(t["succes_lecon"])
        st.rerun()

# ==========================================
# MENU 2 : EXERCICES
# ==========================================
elif menu == t["menu_exo"]:
    c1, c2 = st.columns([4, 1])
    with c1: st.title(t["titre_exo"])
    with c2: st.button(t["aide_btn"], on_click=aller_aux_instructions, args=("Exercices",))
    
    if not st.session_state.lecon: st.warning(t["warn_lecon"])
    elif not st.session_state.api_key: st.error("Clé API manquante dans les secrets du serveur.")
    else:
        if not st.session_state.questions:
            st.write(t["config_exo"])
            col1, col2 = st.columns(2)
            with col1: type_question = st.selectbox(t["type_exo"], ["QCM", "Vrai/Faux", "Mise en situation", "Définitions"])
            with col2: nb_questions = st.number_input(t["nb_q"], min_value=1, max_value=20, value=3)
            st.session_state.outils_actifs = st.checkbox(t["opt_outils"])
            
            if st.button(t["btn_gen_exo"]):
                with st.spinner("..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        fmt = """[{"question": "Q", "choix": ["A", "B", "C"], "reponse_correcte": "B", "explication": "Exp", "outil_recommande": "calculatrice"}]""" if type_question in ["QCM", "Vrai/Faux"] else """[{"question": "Q", "outil_recommande": "dictionnaire"}]"""
                        prompt = f"Crée {nb_questions} questions '{type_question}'. Format JSON strict: {fmt}. Leçon: {st.session_state.lecon}"
                        rep = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        st.session_state.questions = json.loads(rep.text.replace("```json", "").replace("```", "").strip())
                        for q in st.session_state.questions: q['type_q'] = type_question
                        st.session_state.index_actuel = 0
                        st.session_state.score = 0
                        st.rerun()
                    except: st.error("Erreur de génération. L'IA n'a pas pu créer les questions.")
        else:
            if st.session_state.index_actuel < len(st.session_state.questions):
                q = st.session_state.questions[st.session_state.index_actuel]
                st.subheader(f"Question {st.session_state.index_actuel + 1} / {len(st.session_state.questions)}")
                st.write(f"**{q['question']}**")
                
                # OUTILS
                if st.session_state.outils_actifs and q['type_q'] != "Définitions":
                    outil = q.get('outil_recommande', 'aucun').lower()
                    if outil in ['calculatrice', 'dictionnaire', 'python']:
                        with st.expander(f"🛠️ {outil.capitalize()}"):
                            if outil == 'calculatrice':
                                st.text_input("Écran", value=st.session_state.calc_expr, disabled=True, label_visibility="collapsed")
                                for row in [("7","8","9","/"), ("4","5","6","*"), ("1","2","3","-"), ("C","0","=","+")]:
                                    cols = st.columns(4)
                                    for i, btn in enumerate(row): cols[i].button(btn, on_click=maj_calculatrice, args=(btn,), key=f"btn_{btn}_{st.session_state.index_actuel}")
                            elif outil == 'dictionnaire':
                                mot = st.text_input("Mot :", key=f"dic_{st.session_state.index_actuel}")
                                if st.button("Chercher"):
                                    client = genai.Client(api_key=st.session_state.api_key)
                                    st.info(client.models.generate_content(model='gemini-2.5-flash', contents=f"Définition de {mot}").text)
                            elif outil == 'python':
                                code = st.text_area("Code :", key=f"py_{st.session_state.index_actuel}")
                                if st.button("Run"):
                                    client = genai.Client(api_key=st.session_state.api_key)
                                    st.code(client.models.generate_content(model='gemini-2.5-flash', contents=f"Simule l'affichage de ce code Python:\n{code}").text)

                # REPONSE
                choix_u, texte_u = None, None
                if q['type_q'] in ["QCM", "Vrai/Faux"]: choix_u = st.radio("Choix :", q.get('choix', ['Vrai', 'Faux']), index=None, disabled=st.session_state.reponse_validee)
                else: texte_u = st.text_area("Réponse :", disabled=st.session_state.reponse_validee)
                
                if not st.session_state.reponse_validee:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(t["valider"]):
                            if q['type_q'] in ["Mise en situation", "Définitions"]:
                                client = genai.Client(api_key=st.session_state.api_key)
                                prompt_corr = f"""Évalue: "{texte_u}" pour "{q['question']}". JSON: {{"est_correct": true, "explication_correction": "Exp"}}"""
                                st.session_state.evaluation_ia = json.loads(client.models.generate_content(model='gemini-2.5-flash', contents=prompt_corr).text.replace("```json", "").replace("```", "").strip())
                            st.session_state.reponse_validee = True
                            st.rerun()
                    with c2:
                        if st.button(t["passer"]):
                            st.session_state.index_actuel += 1
                            st.session_state.calc_expr = ""
                            st.rerun()
                else:
                    est_correct = (choix_u == q.get('reponse_correcte')) if q['type_q'] in ["QCM", "Vrai/Faux"] else st.session_state.evaluation_ia.get('est_correct', False)
                    if est_correct: st.success("🎉 Correct !")
                    else: st.error("❌ Faux.")
                    st.info(q.get('explication', '') if q['type_q'] in ["QCM", "Vrai/Faux"] else st.session_state.evaluation_ia.get('explication_correction', ''))
                    
                    if st.button(t["suivant"]):
                        st.session_state.index_actuel += 1
                        st.session_state.reponse_validee = False
                        st.session_state.calc_expr = ""
                        st.rerun()
                        
            # --- ÉCRAN DE FIN DE QUIZ ---
            else:
                st.balloons()
                st.write("---")
                st.write(f"### 🏆 Exercice terminé ! Ton score final : {st.session_state.score} / {len(st.session_state.questions)}")
                
                col_fin1, col_fin2 = st.columns(2)
                with col_fin1:
                    if st.button("Refaire cet exercice"):
                        st.session_state.index_actuel = 0
                        st.session_state.score = 0
                        st.session_state.reponse_validee = False
                        st.session_state.evaluation_ia = None
                        st.session_state.calc_expr = ""
                        st.rerun()
                with col_fin2:
                    if st.button("Nouvel exercice"):
                        st.session_state.questions = []
                        st.rerun()

# ==========================================
# MENU 3 : FICHES
# ==========================================
elif menu == t["menu_fiches"]:
    c1, c2 = st.columns([4, 1])
    with c1: st.title(t["titre_fiches"])
    with c2: st.button(t["aide_btn"], on_click=aller_aux_instructions, args=("Fiches",))
    if not st.session_state.lecon: st.warning(t["warn_lecon"])
    elif not st.session_state.api_key: st.error("Clé API manquante dans les secrets du serveur.")
    else:
        type_fiche = st.radio(t["type_fiche"], ["Résumé", "Détaillée"])
        if st.button(t["btn_gen_fiche"]):
            client = genai.Client(api_key=st.session_state.api_key)
            st.session_state.fiche_revision = client.models.generate_content(model='gemini-2.5-flash', contents=f"Fiche de type {type_fiche} sur: {st.session_state.lecon}").text
        if st.session_state.fiche_revision: st.markdown(st.session_state.fiche_revision)

# ==========================================
# MENU 4 : AIDE
# ==========================================
elif menu == t["menu_aide"]:
    st.title(t["menu_aide"])
    with st.expander(t["menu_lecon"], expanded=(st.session_state.section_instruction == "Leçon")): st.write("Importe ou colle ton cours ici.")
    with st.expander(t["menu_exo"], expanded=(st.session_state.section_instruction == "Exercices")): st.write("Génère des questions et utilise les outils IA.")
    with st.expander(t["menu_fiches"], expanded=(st.session_state.section_instruction == "Fiches")): st.write("Génère des synthèses de tes leçons.")
    st.session_state.section_instruction = None

# ==========================================
# MENU 5 : PARAMÈTRES
# ==========================================
elif menu == t["menu_param"]:
    st.title(t["titre_param"])
    langue = st.selectbox("🌐 Langue / Language :", ["Français", "English"], index=0 if st.session_state.langue == "Français" else 1)
    
    themes_disponibles = ["Sombre", "Lumineux", "Dégradé Bleu Doux", "Dégradé Ciel Doux"]
    index_theme = themes_disponibles.index(st.session_state.theme) if st.session_state.theme in themes_disponibles else 1
    theme = st.selectbox("🎨 Thème / Theme :", themes_disponibles, index=index_theme)
    
    if st.button(t["save_param"]):
        st.session_state.langue = langue
        st.session_state.theme = theme
        st.rerun()

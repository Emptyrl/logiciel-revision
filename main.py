import streamlit as st
from google import genai
import json
from PIL import Image
import sys
import io
import contextlib

# --- FONCTIONS DE NAVIGATION ET RAPPELS ---
def aller_aux_instructions(section):
    st.session_state.menu_selection = "ℹ️ Instructions"
    st.session_state.section_instruction = section

def maj_calculatrice(touche):
    if touche == 'C':
        st.session_state.calc_expr = ""
    elif touche == '=':
        try:
            resultat = eval(st.session_state.calc_expr, {"__builtins__": None}, {})
            st.session_state.calc_expr = str(resultat)
        except:
            st.session_state.calc_expr = "Erreur"
    else:
        if st.session_state.calc_expr == "Erreur":
            st.session_state.calc_expr = ""
        st.session_state.calc_expr += str(touche)

# --- INITIALISATION DE LA MÉMOIRE GLOBALE ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = "AIzaSyDqDALd1r6v8nEbA4hnvnRJi_TPnEsc9cc"
if 'lecon' not in st.session_state:
    st.session_state.lecon = ""
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'index_actuel' not in st.session_state:
    st.session_state.index_actuel = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'reponse_validee' not in st.session_state:
    st.session_state.reponse_validee = False
if 'evaluation_ia' not in st.session_state:
    st.session_state.evaluation_ia = None
if 'fiche_revision' not in st.session_state:
    st.session_state.fiche_revision = ""
if 'outils_actifs' not in st.session_state:
    st.session_state.outils_actifs = False
if 'calc_expr' not in st.session_state:
    st.session_state.calc_expr = ""

# Gestion du menu actif
if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = "📖 Leçon"
if 'section_instruction' not in st.session_state:
    st.session_state.section_instruction = None

# --- BARRE DE NAVIGATION (MENU LATÉRAL) ---
with st.sidebar:
    st.title("🧭 Navigation")
    # On relie le radio bouton à la session_state avec la clé "menu_selection"
    menu = st.radio(
        "Choisis un menu :",
        ["📖 Leçon", "🧠 Exercices", "📝 Fiches de révisions", "ℹ️ Instructions", "⚙️ Paramètres"],
        key="menu_selection"
    )
    st.write("---")
    st.write("Statut de la leçon :")
    if st.session_state.lecon:
        st.success("✅ Leçon en mémoire")
    else:
        st.error("❌ Aucune leçon")

# ==========================================
# MENU 1 : LEÇON
# ==========================================
if menu == "📖 Leçon":
    col_titre, col_aide = st.columns([4, 1])
    with col_titre:
        st.title("📖 Ajouter la leçon")
    with col_aide:
        st.button("🤔 Aide", on_click=aller_aux_instructions, args=("Leçon",))
        
    st.write("Importe des photos de tes notes, ou colle directement ton cours en texte.")
    
    fichiers_images = st.file_uploader("📸 Importe les photos de ta leçon (JPG, PNG) :", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if fichiers_images:
        images_ouvertes = []
        colonnes = st.columns(min(len(fichiers_images), 3) if len(fichiers_images) > 0 else 1)
        for i, fichier in enumerate(fichiers_images):
            img = Image.open(fichier)
            images_ouvertes.append(img)
            with colonnes[i % 3]:
                st.image(img, caption=f"Image {i+1}", use_container_width=True)
                
        if st.button("🪄 Extraire le texte des images avec l'IA"):
            with st.spinner("L'IA déchiffre tes notes..."):
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    prompt_ocr = "Voici une ou plusieurs photos d'une leçon. Transcris tout le texte de manière claire et structurée."
                    contenus = [prompt_ocr] + images_ouvertes
                    reponse_ocr = client.models.generate_content(model='gemini-2.5-flash', contents=contenus)
                    st.session_state.lecon = reponse_ocr.text
                    st.success("Extraction réussie !")
                except Exception as e:
                    st.error("Erreur lors de l'extraction.")

    st.write("---")
    lecon_temp = st.text_area("Texte de la leçon :", value=st.session_state.lecon, height=300)
    
    if st.button("Appliquer la leçon 💾"):
        st.session_state.lecon = lecon_temp
        st.session_state.questions = []
        st.session_state.index_actuel = 0
        st.session_state.score = 0
        st.session_state.fiche_revision = ""
        st.success("Leçon sauvegardée en mémoire !")
        st.rerun()

# ==========================================
# MENU 2 : EXERCICES
# ==========================================
elif menu == "🧠 Exercices":
    col_titre, col_aide = st.columns([4, 1])
    with col_titre:
        st.title("🧠 S'entraîner")
    with col_aide:
        st.button("🤔 Aide", on_click=aller_aux_instructions, args=("Exercices",))
    
    if not st.session_state.lecon:
        st.warning("⚠️ Tu dois d'abord ajouter une leçon dans le menu '📖 Leçon' avant de générer des exercices.")
    else:
        if not st.session_state.questions:
            st.write("### Configuration de l'exercice")
            col1, col2 = st.columns(2)
            with col1:
                type_question = st.selectbox("Type d'exercice :", ["QCM", "Vrai/Faux", "Mise en situation", "Définitions"])
            with col2:
                nb_questions = st.number_input("Nombre de questions :", min_value=1, max_value=20, value=3)
            
            st.write("---")
            st.session_state.outils_actifs = st.checkbox("🛠️ Activer les outils d'aide (calculatrice, dico, etc.)")
            
            if st.button("🚀 Générer l'exercice"):
                with st.spinner("L'IA prépare tes questions..."):
                    try:
                        client = genai.Client(api_key=st.session_state.api_key)
                        
                        if type_question in ["QCM", "Vrai/Faux"]:
                            format_json = """[{"question": "Texte de la question", "choix": ["Option 1", "Option 2", "Option 3"], "reponse_correcte": "Option 2", "explication": "Explication", "outil_recommande": "calculatrice"}]"""
                        else:
                            format_json = """[{"question": "Texte de la question ouverte", "outil_recommande": "dictionnaire"}]"""
                            
                        prompt = f"""Tu es un professeur expert. À partir de la leçon ci-dessous, crée {nb_questions} questions de type '{type_question}'.
                        Ajoute un champ "outil_recommande" pour chaque question parmi "calculatrice", "dictionnaire", "python", ou "aucun".
                        Tu dois STRICTEMENT répondre dans ce format JSON :
                        {format_json}
                        Leçon :
                        {st.session_state.lecon}"""
                        
                        reponse = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                        texte_propre = reponse.text.replace("```json", "").replace("```", "").strip()
                        
                        questions_generees = json.loads(texte_propre)
                        for q in questions_generees:
                            q['type_q'] = type_question
                            
                        st.session_state.questions = questions_generees
                        st.session_state.index_actuel = 0
                        st.session_state.score = 0
                        st.session_state.calc_expr = ""
                        st.rerun()
                        
                    except Exception as e:
                        st.error("Une erreur est survenue lors de la génération.")

        else:
            if st.session_state.index_actuel < len(st.session_state.questions):
                q = st.session_state.questions[st.session_state.index_actuel]
                st.subheader(f"Question {st.session_state.index_actuel + 1} / {len(st.session_state.questions)}")
                st.write(f"**{q['question']}**")
                
                # Outils contextuels
                if st.session_state.outils_actifs and q['type_q'] != "Définitions":
                    outil = q.get('outil_recommande', 'aucun').lower()
                    if outil in ['calculatrice', 'dictionnaire', 'python']:
                        with st.expander(f"🛠️ Ouvrir l'outil : {outil.capitalize()}"):
                            if outil == 'calculatrice':
                                st.write("**Calculatrice**")
                                st.text_input("Écran", value=st.session_state.calc_expr, disabled=True, key="ecran_calc", label_visibility="collapsed")
                                c1, c2, c3, c4 = st.columns(4)
                                c1.button("7", on_click=maj_calculatrice, args=("7",), use_container_width=True)
                                c2.button("8", on_click=maj_calculatrice, args=("8",), use_container_width=True)
                                c3.button("9", on_click=maj_calculatrice, args=("9",), use_container_width=True)
                                c4.button("÷", on_click=maj_calculatrice, args=("/",), use_container_width=True)
                                c1.button("4", on_click=maj_calculatrice, args=("4",), use_container_width=True)
                                c2.button("5", on_click=maj_calculatrice, args=("5",), use_container_width=True)
                                c3.button("6", on_click=maj_calculatrice, args=("6",), use_container_width=True)
                                c4.button("×", on_click=maj_calculatrice, args=("*",), use_container_width=True)
                                c1.button("1", on_click=maj_calculatrice, args=("1",), use_container_width=True)
                                c2.button("2", on_click=maj_calculatrice, args=("2",), use_container_width=True)
                                c3.button("3", on_click=maj_calculatrice, args=("3",), use_container_width=True)
                                c4.button("-", on_click=maj_calculatrice, args=("-",), use_container_width=True)
                                c1.button("C", on_click=maj_calculatrice, args=("C",), use_container_width=True)
                                c2.button("0", on_click=maj_calculatrice, args=("0",), use_container_width=True)
                                c3.button("=", on_click=maj_calculatrice, args=("=",), use_container_width=True)
                                c4.button("+", on_click=maj_calculatrice, args=("+",), use_container_width=True)
                            elif outil == 'dictionnaire':
                                mot = st.text_input("Quel mot veux-tu chercher ?", key=f"dico_{st.session_state.index_actuel}")
                                if st.button("Chercher la définition"):
                                    with st.spinner("Recherche..."):
                                        try:
                                            client = genai.Client(api_key=st.session_state.api_key)
                                            rep_dico = client.models.generate_content(model='gemini-2.5-flash', contents=f"Définition simple de '{mot}'.")
                                            st.info(rep_dico.text)
                                        except:
                                            st.error("Erreur de connexion.")
                            elif outil == 'python':
                                code_py = st.text_area("Écris ton code Python ici :", key=f"py_{st.session_state.index_actuel}")
                                if st.button("Exécuter ▶️"):
                                    f = io.StringIO()
                                    with contextlib.redirect_stdout(f):
                                        try:
                                            exec(code_py, {})
                                            st.code(f.getvalue(), language="text")
                                        except Exception as e:
                                            st.error(f"Erreur : {e}")

                st.write("---")
                choix_utilisateur = None
                texte_utilisateur = None
                est_verrouille = st.session_state.reponse_validee
                
                if q['type_q'] in ["QCM", "Vrai/Faux"]:
                    choix_utilisateur = st.radio("Choisis ta réponse :", q.get('choix', ['Vrai', 'Faux']), index=None, disabled=est_verrouille)
                else:
                    texte_utilisateur = st.text_area("Écris ta réponse :", disabled=est_verrouille)
                
                if not st.session_state.reponse_validee:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Valider ma réponse ✅"):
                            if q['type_q'] in ["QCM", "Vrai/Faux"] and choix_utilisateur is None:
                                st.warning("Tu dois choisir une réponse !")
                            elif q['type_q'] in ["Mise en situation", "Définitions"] and not texte_utilisateur:
                                st.warning("Tu dois écrire une réponse !")
                            else:
                                if q['type_q'] in ["Mise en situation", "Définitions"]:
                                    with st.spinner("L'IA analyse ta réponse..."):
                                        client = genai.Client(api_key=st.session_state.api_key)
                                        prompt_correction = f"""Évalue cette réponse : "{texte_utilisateur}" pour la question "{q['question']}".
                                        Dis si c'est vrai, faux, ou partiellement correct. Format JSON : {{"est_correct": true, "explication_correction": "Explication"}}"""
                                        try:
                                            rep_corr = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_correction)
                                            st.session_state.evaluation_ia = json.loads(rep_corr.text.replace("```json", "").replace("```", "").strip())
                                        except Exception:
                                            st.error("Erreur lors de la correction.")
                                st.session_state.reponse_validee = True
                                st.rerun()
                    with col2:
                        if st.button("Passer la question ⏭️"):
                            st.session_state.index_actuel += 1
                            st.session_state.reponse_validee = False
                            st.session_state.evaluation_ia = None
                            st.session_state.calc_expr = ""
                            st.rerun()
                            
                if st.session_state.reponse_validee:
                    est_correct = False
                    explication = ""
                    if q['type_q'] in ["QCM", "Vrai/Faux"]:
                        est_correct = (choix_utilisateur == q.get('reponse_correcte'))
                        explication = q.get('explication', '')
                    else:
                        if st.session_state.evaluation_ia:
                            est_correct = st.session_state.evaluation_ia.get('est_correct', False)
                            explication = st.session_state.evaluation_ia.get('explication_correction', '')
                        
                    if est_correct:
                        st.success("🎉 C'est une bonne réponse !")
                        if 'point_compte' not in st.session_state:
                            st.session_state.score += 1
                            st.session_state.point_compte = True
                    else:
                        st.error("❌ Ce n'est pas tout à fait ça.")
                        
                    st.info(f"**Correction :** {explication}")
                    
                    if st.button("Question suivante ➡️" if st.session_state.index_actuel < len(st.session_state.questions) - 1 else "Voir mes résultats 🏆"):
                        st.session_state.index_actuel += 1
                        st.session_state.reponse_validee = False
                        st.session_state.evaluation_ia = None
                        st.session_state.calc_expr = ""
                        if 'point_compte' in st.session_state:
                            del st.session_state.point_compte
                        st.rerun()
            else:
                st.balloons()
                st.write(f"### 🏆 Exercice terminé ! Ton score : {st.session_state.score} / {len(st.session_state.questions)}")
                if st.button("Refaire un nouvel exercice"):
                    st.session_state.questions = []
                    st.rerun()

# ==========================================
# MENU 3 : FICHES DE RÉVISIONS
# ==========================================
elif menu == "📝 Fiches de révisions":
    col_titre, col_aide = st.columns([4, 1])
    with col_titre:
        st.title("📝 Générateur de Fiches")
    with col_aide:
        st.button("🤔 Aide", on_click=aller_aux_instructions, args=("Fiches",))
        
    if not st.session_state.lecon:
        st.warning("⚠️ Tu dois d'abord ajouter une leçon dans le menu '📖 Leçon'.")
    else:
        type_fiche = st.radio("Quel type de document souhaites-tu ?", ["Un résumé rapide (synthèse globale)", "Une fiche détaillée avec des points clés"])
        if st.button("🪄 Générer ma fiche de révision"):
            with st.spinner("L'IA rédige ta fiche..."):
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    prompt_fiche = f"Crée une fiche de révision sous forme de '{type_fiche}' pour cette leçon : {st.session_state.lecon}"
                    reponse_fiche = client.models.generate_content(model='gemini-2.5-flash', contents=prompt_fiche)
                    st.session_state.fiche_revision = reponse_fiche.text
                except Exception as e:
                    st.error("Erreur lors de la génération.")
                    
        if st.session_state.fiche_revision:
            st.write("---")
            st.markdown(st.session_state.fiche_revision)

# ==========================================
# MENU 4 : INSTRUCTIONS (AIDE)
# ==========================================
elif menu == "ℹ️ Instructions":
    st.title("ℹ️ Mode d'emploi du logiciel")
    st.write("Bienvenue dans le centre d'aide. Clique sur une catégorie pour comprendre comment utiliser l'application.")
    
    # Tiroir Leçon (Ouvert automatiquement si on vient du bouton Aide de Leçon)
    ouvert_lecon = (st.session_state.section_instruction == "Leçon")
    with st.expander("📖 Comment utiliser le menu Leçon ?", expanded=ouvert_lecon):
        st.write("""
        **But du menu :** C'est ici que tu donnes de la matière à l'Intelligence Artificielle.
        - **Méthode 1 :** Tu peux écrire ou coller directement le texte de ton cours dans la grande case.
        - **Méthode 2 :** Prends ton cours en photo et importe les images. Clique ensuite sur "Extraire le texte". L'IA va lire ton écriture et la transformer en vrai texte !
        - N'oublie jamais de cliquer sur **"Appliquer la leçon 💾"** pour que le logiciel la garde en mémoire.
        """)

    # Tiroir Exercices
    ouvert_exo = (st.session_state.section_instruction == "Exercices")
    with st.expander("🧠 Comment utiliser le menu Exercices ?", expanded=ouvert_exo):
        st.write("""
        **But du menu :** Tester tes connaissances sur la leçon en cours.
        - Choisis le **type d'exercice** (QCM, Vrai/Faux, etc.) et le nombre de questions.
        - **L'option "Outils d'aide" :** Si tu coches cette case, l'IA détectera de quoi parle ton cours et te proposera une calculatrice, un dictionnaire, ou un outil de code informatique pendant le quiz pour t'aider.
        - **Les questions ouvertes :** Si tu choisis "Mise en situation" ou "Définitions", tu dois écrire la réponse avec tes mots. L'IA la lira comme un vrai professeur et te corrigera même si tu n'utilises pas les mots exacts du cours !
        - Attention, une fois la réponse validée, tu ne peux plus la modifier.
        """)
        
    # Tiroir Fiches
    ouvert_fiches = (st.session_state.section_instruction == "Fiches")
    with st.expander("📝 Comment utiliser le menu Fiches de révisions ?", expanded=ouvert_fiches):
        st.write("""
        **But du menu :** Transformer un long cours compliqué en un résumé facile à apprendre.
        - Assure-toi d'avoir bien importé une leçon d'abord.
        - Choisis si tu veux un **résumé rapide** (un petit paragraphe) ou une **fiche détaillée** avec des tirets et des titres.
        - Clique sur le bouton magique et copie-colle le résultat pour l'imprimer ou l'enregistrer sur ton ordinateur.
        """)
        
    # On efface la mémoire de redirection pour éviter que le tiroir reste bloqué ouvert la prochaine fois
    st.session_state.section_instruction = None

# ==========================================
# MENU 5 : PARAMÈTRES
# ==========================================
elif menu == "⚙️ Paramètres":
    st.title("⚙️ Paramètres du logiciel")
    nouvelle_cle = st.text_input("Ta clé API Google Gemini :", value=st.session_state.api_key, type="password")
    if st.button("Sauvegarder les paramètres"):
        st.session_state.api_key = nouvelle_cle
        st.success("✅ Nouvelle clé API enregistrée !")

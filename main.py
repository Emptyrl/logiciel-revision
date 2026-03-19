import streamlit as st
from google import genai
import json
from PIL import Image
import sys
import io
import contextlib

# --- FONCTIONS DE NAVIGATION ET RAPPELS ---
def aller_aux_instructions(section):
    st.session_state.menu_selection = "ℹ️ Instructions" if st.session_state.langue == "Français" else "ℹ️ Help"
    st.session_state.section_instruction = section

def maj_calculatrice(touche):
    if touche == 'C':
        st.session_state.calc_expr = ""
    elif touche == '=':
        try:
            caracteres_autorises = "0123456789+-*/. "
            if all(c in caracteres_autorises for c in st.session_state.calc_expr):
                resultat = eval(st.session_state.calc_expr, {"__builtins__": None}, {})
                st.session_state.calc_expr = str(resultat)
            else:
                st.session_state.calc_expr = "Erreur"
        except:
            st.session_state.calc_expr = "Erreur"
    else:
        if st.session_state.calc_expr == "Erreur":
            st.session_state.calc_expr = ""
        st.session_state.calc_expr += str(touche)

# --- INITIALISATION DE LA MÉMOIRE GLOBALE ---
# La clé API est maintenant uniquement cherchée dans les fichiers secrets du serveur
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

# Nouvelles variables pour les paramètres
if 'langue' not in st.session_state: st.session_state.langue = "Français"
if 'theme' not in st.session_state: st.session_state.theme = "Classique"

# --- GESTION DES THÈMES VISUELS (CSS) ---
if st.session_state.theme == "Dégradé Océan":
    st.markdown("""<style>.stApp { background: linear-gradient(to right, #0f2027, #203a43, #2c5364); color: white; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Dégradé Violet":
    st.markdown("""<style>.stApp { background: linear-gradient(to right, #4a00e0, #8e2de2); color: white; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Sombre":
    st.markdown("""<style>.stApp { background-color: #0e1117; color: white; }</style>""", unsafe_allow_html=True)
elif st.session_state.theme == "Lumineux":
    st.markdown("""<style>.stApp { background-color: #ffffff; color: black; }</style>""", unsafe_allow_html=True)

# --- DICTIONNAIRE DE LANGUES ---
# Exemple de traduction dynamique pour le menu
if st.session_state.langue == "Français":
    menu_options = ["📖 Leçon", "🧠 Exercices", "📝 Fiches de révisions", "ℹ️ Instructions", "⚙️ Paramètres"]
    titre_nav = "🧭 Navigation"
    statut_ok = "✅ Leçon en mémoire"
    statut_ko = "❌ Aucune leçon"
else:
    menu_options = ["📖 Lesson", "🧠 Exercises", "📝 Study Sheets", "ℹ️ Help", "⚙️ Settings"]
    titre_nav = "🧭 Navigation"
    statut_ok = "✅ Lesson saved"
    statut_ko = "❌ No lesson"

if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = menu_options[0]

# --- BARRE DE NAVIGATION (MENU LATÉRAL) ---
with st.sidebar:
    st.title(titre_nav)
    menu = st.radio("Menu :", menu_options, key="menu_selection")
    st.write("---")
    if st.session_state.lecon:
        st.success(statut_ok)
    else:
        st.error(statut_ko)

# ==========================================
# MENUS PRINCIPAUX (Leçon, Exercices, Fiches, Instructions)
# [Le code de ces menus reste identique au précédent, 
# tu pourras appliquer la logique de traduction 'if langue == ...' plus tard]
# ==========================================
if menu in ["📖 Leçon", "📖 Lesson"]:
    st.title("📖 Ajouter la leçon" if st.session_state.langue == "Français" else "📖 Add Lesson")
    st.write("Colle directement ton cours en texte ici.")
    lecon_temp = st.text_area("", value=st.session_state.lecon, height=300)
    if st.button("Appliquer la leçon 💾" if st.session_state.langue == "Français" else "Save Lesson 💾"):
        st.session_state.lecon = lecon_temp
        st.success("Sauvegardé !" if st.session_state.langue == "Français" else "Saved!")
        st.rerun()

elif menu in ["🧠 Exercices", "🧠 Exercises"]:
    st.title("🧠 S'entraîner" if st.session_state.langue == "Français" else "🧠 Practice")
    st.warning("Menu en construction pour la traduction..." if st.session_state.langue == "Français" else "Menu under construction for translation...")

elif menu in ["📝 Fiches de révisions", "📝 Study Sheets"]:
    st.title("📝 Fiches" if st.session_state.langue == "Français" else "📝 Sheets")

elif menu in ["ℹ️ Instructions", "ℹ️ Help"]:
    st.title("ℹ️ Mode d'emploi" if st.session_state.langue == "Français" else "ℹ️ User Guide")

# ==========================================
# MENU 5 : PARAMÈTRES (Mis à jour)
# ==========================================
elif menu in ["⚙️ Paramètres", "⚙️ Settings"]:
    if st.session_state.langue == "Français":
        st.title("⚙️ Paramètres du logiciel")
        label_langue = "🌐 Langue de l'interface :"
        label_theme = "🎨 Thème visuel :"
        btn_save = "Sauvegarder les paramètres"
        msg_save = "✅ Paramètres enregistrés ! L'application va se mettre à jour."
    else:
        st.title("⚙️ Software Settings")
        label_langue = "🌐 Interface Language :"
        label_theme = "🎨 Visual Theme :"
        btn_save = "Save settings"
        msg_save = "✅ Settings saved! The app will update."

    # Sélecteurs de paramètres
    choix_langue = st.selectbox(label_langue, ["Français", "English"], index=0 if st.session_state.langue == "Français" else 1)
    choix_theme = st.selectbox(label_theme, ["Classique", "Sombre", "Lumineux", "Dégradé Océan", "Dégradé Violet"], index=["Classique", "Sombre", "Lumineux", "Dégradé Océan", "Dégradé Violet"].index(st.session_state.theme))
    
    if st.button(btn_save):
        st.session_state.langue = choix_langue
        st.session_state.theme = choix_theme
        st.success(msg_save)
        st.rerun()

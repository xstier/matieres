import os
from flask import Flask, redirect, url_for, session, render_template, flash, jsonify, request
from bson import ObjectId
from bs4 import BeautifulSoup
from extensions import mongo
from admin_routes import admin
from auth import auth
import json

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'

# Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/matieres"
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialisation
mongo.init_app(app)

# Enregistrement des blueprints

app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(auth, url_prefix="/auth")

# Raccourcis vers les collections
db = mongo.db
matieres_col = db["matieres"]
themes_col = db["themes"]
exercices_col = db["exercices_interactifs"]

# ... (tout le reste de tes routes reste identique)



@app.context_processor
def inject_matieres():
    matieres = list(matieres_col.find())
    return dict(matieres=matieres)


@app.route("/")
def index():
    
    return render_template(
        "index.html",
        themes=[],
        matiere_exists=False,
    )


def nettoyer_reponse_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Vider les champs input
    for input_tag in soup.find_all("input", class_="interactive-blank"):
        input_tag["value"] = ""

    # Réinitialiser les selects
    for select_tag in soup.find_all("select", class_="interactive-select"):
        for option in select_tag.find_all("option"):
            option.attrs.pop("selected", None)
        if select_tag.option:
            select_tag.option["selected"] = "selected"  # Set le premier

    return str(soup)





@app.route("/themes/<matiere_id>")
def afficher_themes(matiere_id):
    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Cette matière n'existe pas.")
        return redirect(url_for('index'))

    themes = list(themes_col.find({"matiere_id": ObjectId(matiere_id)}))
    for theme in themes:
        theme.setdefault("lessons", [])
        theme.setdefault("exercises", [])

    no_content = not themes or all(not (theme["lessons"] or theme["exercises"]) for theme in themes)

    matieres = list(matieres_col.find())
    return render_template(
        "index.html",
      
        themes=themes,
        selected_id=matiere_id,
        no_content=no_content,
        matiere_exists=True,
        session=session
    )


@app.route("/api/themes/<matiere_id>")
def api_get_themes(matiere_id):
    try:
        # Vérifier que matiere_id est un ObjectId valide
        matiere_obj_id = ObjectId(matiere_id)
        
        # Requête MongoDB
        themes = list(themes_col.find({"matiere_id": matiere_obj_id}))

        for theme in themes:
            # Convertir _id ObjectId en string
            theme["_id"] = str(theme["_id"])
            theme["matiere_id"] = str(theme["matiere_id"])
            
            # Si le thème contient des leçons, on prépare les liens
            for lecon in theme.get("lessons", []):
                if "fichier" in lecon and lecon["fichier"]:
                    # Construire le lien complet vers le fichier statique
                    lecon["lien"] = url_for("static", filename=lecon["fichier"].replace("\\", "/"))
        
        return jsonify(themes)

    except Exception as e:
        # Log l'erreur en console (optionnel)
        print(f"Erreur lors du chargement des thèmes pour matiere_id={matiere_id} : {e}")
        return jsonify({"error": "Erreur lors du chargement des thèmes."}), 500


@app.route("/theme/<theme_id>")
def afficher_theme(theme_id):
    try:
        theme_obj_id = ObjectId(theme_id)
    except:
        flash("ID de thème invalide.")
        return redirect(url_for("index"))

    # Recherche du thème
    theme = themes_col.find_one({"_id": theme_obj_id})
    if not theme:
        flash("Ce thème n'existe pas.")
        return redirect(url_for("index"))

    # Récupération des leçons intégrées dans le document thème
    lecons = theme.get("lessons", [])

    # Récupération des exercices associés à ce thème
    exercices = list(exercices_col.find({"theme_id": theme_obj_id}))

    return render_template(
        "theme.html",
        theme=theme,
        lecons=lecons,
        exercices=exercices,
        session=session
    )



@app.route("/lecon/<theme_nom>/<int:lecon_index>")
def afficher_lecon(theme_nom, lecon_index):
    theme = themes_col.find_one({"nom": theme_nom})
    if not theme or "lessons" not in theme or lecon_index >= len(theme["lessons"]):
        flash("Leçon introuvable.")
        return redirect(url_for("index"))

    lecon = theme["lessons"][lecon_index]
    return render_template("lecon.html", lecon=lecon)

@app.route("/lecon/<theme_id>/<titre>")
def afficher_lecon_contenu(theme_id, titre):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        return "Thème introuvable", 404

    for lecon in theme.get("lessons", []):
        if lecon["titre"] == titre and lecon.get("contenu"):
            return render_template("lecon_contenu.html", lecon=lecon, theme=theme)

    return "Leçon introuvable ou sans contenu texte", 404

@app.route("/exercice/<exercice_id>", methods=["GET", "POST"])
def afficher_exercice(exercice_id):
    exercice = exercices_col.find_one({"_id": ObjectId(exercice_id)})
    if not exercice:
        flash("Exercice non trouvé.")
        return redirect(url_for("index"))

    # Chargement et parsing sécurisé des réponses attendues
    reponses_attendues = {}
    if "reponses_attendues" in exercice:
        try:
            if isinstance(exercice["reponses_attendues"], str):
                reponses_attendues = json.loads(exercice["reponses_attendues"])
            elif isinstance(exercice["reponses_attendues"], dict):
                reponses_attendues = exercice["reponses_attendues"]
        except Exception:
            reponses_attendues = {}

    if request.method == "POST":
        if reponses_attendues:
            user_answers = {}
            champs_non_remplis = []

            # Lire uniquement les champs attendus (field_x)
            for field_name in reponses_attendues:
                valeur = request.form.get(field_name, "").strip()
                if not valeur:
                    champs_non_remplis.append(field_name)
                user_answers[field_name] = valeur

            if champs_non_remplis:
                flash("Veuillez remplir tous les champs requis.", "warning")
                return redirect(url_for("afficher_exercice", exercice_id=exercice_id))

            # Comparaison exacte (insensible à la casse)
            correct = all(
                user_answers.get(field, "").lower() == expected.lower()
                for field, expected in reponses_attendues.items()
            )

            if correct:
                flash("Bravo, votre réponse est correcte !", "success")
            else:
                flash("Désolé, votre réponse est incorrecte.", "danger")

            return redirect(url_for("afficher_exercice", exercice_id=exercice_id))

        else:
          # Cas réponse libre : la réponse attendue est dans `reponse_html`
            reponse_libre = request.form.get("reponse_libre", "").strip()
            if not reponse_libre:
                flash("Veuillez saisir une réponse.", "warning")
                return redirect(url_for("afficher_exercice", exercice_id=exercice_id))

            bonne_reponse = exercice.get("reponse_html", "").strip()
        if bonne_reponse:
            if reponse_libre.lower() == bonne_reponse.lower():
                flash("Bravo, votre réponse est correcte !", "success")
            else:
                flash("Désolé, votre réponse est incorrecte.", "danger")
        else:
            # Aucun critère de validation défini
            flash("Votre réponse a été enregistrée.", "info")


    # Nettoyage du HTML avant affichage, pour éviter d'exposer les bonnes réponses
    exercice["reponse_html"] = nettoyer_reponse_html(exercice.get("reponse_html", ""))

    return render_template(
        "exercice.html",
        exercice={
            **exercice,
            "reponse_html": exercice.get("reponse_html", ""),
            "_id": str(exercice["_id"]),
        },
    )



@app.route('/matieres/<matiere_id>/themes_view')
def themes_view(matiere_id):
    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Matière introuvable.")
        return redirect(url_for('index'))
    return render_template("themes_view.html", matiere=matiere)

if __name__ == "__main__":
    app.run(debug=True)


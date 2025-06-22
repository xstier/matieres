import os
from bson import ObjectId
from flask import Flask, redirect, render_template, session, flash, url_for
from pymongo import MongoClient
from admin_routes import admin
from auth import auth

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# DB client et collections globales
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
matieres_col = db["matieres"]
themes_col = db["themes"]

# Enregistrement des blueprints
app.register_blueprint(auth)
app.register_blueprint(admin)

@app.context_processor
def inject_matieres():
    matieres = list(matieres_col.find())
    return dict(matieres=matieres)


@app.route("/")
def index():
    return render_template("index.html", session=session)

@app.route("/themes/<matiere_id>")
def afficher_themes(matiere_id):
    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Cette matière n'existe pas.")
        return redirect(url_for('index'))

    themes = list(themes_col.find({"matiere_id": matiere_id}))
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

@app.route('/lecon/<theme_id>/<int:lesson_index>')
def afficher_lecon(theme_id, lesson_index):
    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème non trouvé.")
        return redirect(url_for('index'))

    lessons = theme.get('lessons', [])
    if lesson_index < 0 or lesson_index >= len(lessons):
        flash("Leçon non trouvée.")
        return redirect(url_for('afficher_themes', matiere_id=theme.get('matiere_id', '')))

    lesson = lessons[lesson_index]
    return render_template('afficher_lecon.html', lesson=lesson, theme=theme)

if __name__ == "__main__":
    app.run(debug=True)


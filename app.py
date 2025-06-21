from bson import ObjectId
from flask import Flask, redirect, render_template, session , flash, url_for
from pymongo import MongoClient
from admin_routes import admin
from auth import auth

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete'

# DB init pour route /
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
matieres_col = db["matieres"]
themes_col = db["themes"]


# Blueprints
app.register_blueprint(auth)
app.register_blueprint(admin)

@app.route("/")
def index():
    matieres = list(matieres_col.find())
    return render_template("index.html", matieres=matieres, session=session)

@app.route("/themes/<matiere_id>")
def afficher_themes(matiere_id):
    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Cette matière n'existe pas.")
        return redirect(url_for('home'))  # ou une autre page

    themes = list(themes_col.find({"matiere_id": matiere_id}))
    for theme in themes:
        theme.setdefault("lessons", [])
        theme.setdefault("exercises", [])

    # Si aucun thème OU tous les thèmes ont lessons et exercises vides
    if not themes or all(not (theme["lessons"] or theme["exercises"]) for theme in themes):
        no_content = True
    else:
        no_content = False

    matieres = list(matieres_col.find())

    return render_template(
        "index.html",
        matieres=matieres,
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
        flash("Thème non trouvé")
        return redirect(url_for('afficher_themes', matiere_id=''))

    try:
        lesson = theme.get('lessons', [])[lesson_index]
    except IndexError:
        flash("Leçon non trouvée")
        return redirect(url_for('afficher_themes', matiere_id=theme.get('matiere_id', '')))

    return render_template('afficher_lecon.html', lesson=lesson, theme=theme)




if __name__ == "__main__":
    app.run(debug=True)

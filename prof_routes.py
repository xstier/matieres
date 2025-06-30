from flask import Blueprint, render_template, request, redirect, flash, url_for, session
from extensions import mongo
from decorators import role_required
from bson import ObjectId
from datetime import datetime

prof = Blueprint("prof", __name__, template_folder="templates/prof")


@prof.route("/admin_prof")
@role_required("professeur")
def admin_prof():
    users = list(mongo.db.users.find())
    return render_template("home_prof.html", users=users)


@prof.route("/devoirs/add", methods=["GET"])
@role_required("professeur")
def add_devoir():
   

    matieres = list(mongo.db.matieres.find())
    matieres_dict = {str(m["_id"]): m["nom"] for m in matieres}

    themes = list(mongo.db.themes.find())
    themes_dict = {}
    for t in themes:
        theme_id = str(t["_id"])
        matiere_id = str(t.get("matiere_id"))
        nom_matiere = matieres_dict.get(matiere_id, "Matière inconnue")
        themes_dict[theme_id] = {
            "nom_theme": t.get("nom", "Thème inconnu"),
            "nom_matiere": nom_matiere
        }

    exercices = list(mongo.db.exercices_interactifs.find())
    for ex in exercices:
        theme_id = str(ex.get("theme_id"))
        theme_info = themes_dict.get(theme_id, {"nom_theme": "Thème inconnu", "nom_matiere": "Matière inconnue"})
        ex["nom_theme"] = theme_info["nom_theme"]
        ex["nom_matiere"] = theme_info["nom_matiere"]

    return render_template("add_devoir.html", matieres=matieres, themes=themes, exercices=exercices)


@prof.route("/devoirs/add", methods=["POST"])
@role_required("professeur")
def save_devoir():

    titre = request.form.get("titre")
    exercice_ids = request.form.getlist("exercice_id")
    tentatives_list = request.form.getlist("tentatives")

    if not titre or not exercice_ids:
        flash("Le titre et au moins un exercice sont requis.")
        return redirect(url_for("prof.add_devoir"))

    try:
        exercices = []
        for eid, tentative in zip(exercice_ids, tentatives_list):
            exercices.append({
                "exercice_id": ObjectId(eid),
                "tentatives_autorisees": int(tentative)
            })

        devoir = {
            "titre": titre,
            "exercices": exercices,
            "auteur_username": session["username"],
            "date_creation": datetime.now()
        }

        mongo.db.devoirs.insert_one(devoir)
        flash("Devoir créé avec succès.", "success")
        return redirect(url_for("prof.liste_devoirs"))

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for("prof.add_devoir"))


@prof.route("/devoirs")
@role_required("professeur")
def liste_devoirs():
    

    devoirs = list(mongo.db.devoirs.find())
    return render_template("liste_devoirs.html", devoirs=devoirs)


@prof.route("/devoirs/delete/<devoir_id>", methods=["POST"])
@role_required("professeur")
def delete_devoir(devoir_id):


    mongo.db.devoirs.delete_one({"_id": ObjectId(devoir_id)})
    flash("Devoir supprimé avec succès.")
    return redirect(url_for("liste_devoirs.html"))


@prof.route("/devoirs/edit/<devoir_id>", methods=["GET"])
@role_required("professeur")
def edit_devoir_get(devoir_id):
    devoir = mongo.db.devoirs.find_one({"_id": ObjectId(devoir_id)})
    if not devoir:
        flash("Devoir introuvable.", "danger")
        return redirect(url_for("prof.liste_devoirs"))

    # Charger toutes les collections liées
    exercices_all = list(mongo.db.exercices_interactifs.find())
    themes = {str(t["_id"]): t["nom"] for t in mongo.db.themes.find()}
    matieres = {str(m["_id"]): m["nom"] for m in mongo.db.matieres.find()}

    # Dictionnaire pour accès rapide
    exercices_dict = {str(ex["_id"]): ex for ex in exercices_all}

    # Exercices déjà dans le devoir
    exercices_selectionnes = []
    selected_ids = set()
    for item in devoir.get("exercices", []):
        eid = str(item["exercice_id"])
        selected_ids.add(eid)
        ex = exercices_dict.get(eid)
        if ex:
            exercices_selectionnes.append({
                "_id": eid,
                "titre": ex.get("titre", "Sans titre"),
                "theme": themes.get(str(ex.get("theme_id")), "Thème inconnu"),
                "matiere": matieres.get(str(ex.get("matiere_id")), "Matière inconnue"),
                "tentatives_autorisees": item.get("tentatives_autorisees", 1)
            })

    # Exercices restants (non sélectionnés)
    exercices_non_selectionnes = []
    for ex in exercices_all:
        eid = str(ex["_id"])
        if eid not in selected_ids:
            exercices_non_selectionnes.append({
                "_id": eid,
                "titre": ex.get("titre", "Sans titre"),
                "theme": themes.get(str(ex.get("theme_id")), "Thème inconnu"),
                "matiere": matieres.get(str(ex.get("matiere_id")), "Matière inconnue"),
                "tentatives_autorisees": 1  # par défaut
            })

    return render_template("edit_devoir.html",
                           devoir=devoir,
                           exercices_selectionnes=exercices_selectionnes,
                           exercices_non_selectionnes=exercices_non_selectionnes)



@prof.route("/devoirs/edit/<devoir_id>", methods=["POST"])
@role_required("professeur")
def edit_devoir_submit(devoir_id):
    titre = request.form.get("titre", "").strip()
    exercice_ids = request.form.getlist("exercice_id")
    tentatives_list = request.form.getlist("tentatives")

    if not titre or not exercice_ids:
        flash("Le titre et au moins un exercice sont requis.", "danger")
        return redirect(url_for("prof.edit_devoir_get", devoir_id=devoir_id))

    try:
        exercices = []
        for eid, tentative in zip(exercice_ids, tentatives_list):
            exercices.append({
                "exercice_id": ObjectId(eid),
                "tentatives_autorisees": int(tentative)
            })

        mongo.db.devoirs.update_one(
            {"_id": ObjectId(devoir_id)},
            {"$set": {
                "titre": titre,
                "exercices": exercices
            }}
        )

        flash("Devoir mis à jour avec succès.", "success")
        return redirect(url_for("prof.liste_devoirs"))

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for("prof.edit_devoir_get", devoir_id=devoir_id))

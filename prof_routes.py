
from flask import Blueprint, render_template, request, redirect, flash, url_for, session ,abort
from extensions import mongo

prof = Blueprint("prof", __name__, template_folder="templates/prof")

from decorators import role_required
from bson import ObjectId
from datetime import datetime
from constants import ROLES,CLASSES

print("DEBUG mongo.db est :", mongo.db)


reponses_col = mongo.db.reponses_devoirs
exercices_col = mongo.db.exercices_interactifs
reponses_devoir_col = mongo.db.reponses_devoirs
devoirs_col = mongo.db.devoirs

@prof.route("/admin_prof")
@role_required("professeur","admin")
def admin_prof():
    users = list(mongo.db.users.find())
    return render_template("home_prof.html", users=users)


@prof.route("/devoirs/add", methods=["GET"])
@role_required("professeur","admin")
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
@role_required("professeur","admin")
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
@role_required("professeur","admin")
def liste_devoirs():
    

    devoirs = list(mongo.db.devoirs.find())
    return render_template("liste_devoirs.html", devoirs=devoirs)


@prof.route("/devoirs/delete/<devoir_id>", methods=["POST"])
@role_required("professeur","admin")
def delete_devoir(devoir_id):


    mongo.db.devoirs.delete_one({"_id": ObjectId(devoir_id)})
    flash("Devoir supprimé avec succès.")
    return redirect(url_for("liste_devoirs.html"))


@prof.route("/devoirs/edit/<devoir_id>", methods=["GET"])
@role_required("professeur", "admin")
def edit_devoir_get(devoir_id):
    devoir = mongo.db.devoirs.find_one({"_id": ObjectId(devoir_id)})
    if not devoir:
        flash("Devoir introuvable.", "danger")
        return redirect(url_for("prof.liste_devoirs"))

    exercices_all = list(mongo.db.exercices_interactifs.find())
    themes = {str(t["_id"]): t["nom"] for t in mongo.db.themes.find()}
    matieres = {str(m["_id"]): m["nom"] for m in mongo.db.matieres.find()}
    exercices_dict = {str(ex["_id"]): ex for ex in exercices_all}

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

    exercices_non_selectionnes = []
    for ex in exercices_all:
        eid = str(ex["_id"])
        if eid not in selected_ids:
            exercices_non_selectionnes.append({
                "_id": eid,
                "titre": ex.get("titre", "Sans titre"),
                "theme": themes.get(str(ex.get("theme_id")), "Thème inconnu"),
                "matiere": matieres.get(str(ex.get("matiere_id")), "Matière inconnue"),
                "tentatives_autorisees": 1
            })

    # 🔹 Charger les classes disponibles
    classes = list(mongo.db.classes.find())

    return render_template("edit_devoir.html",
                           devoir=devoir,
                           exercices_selectionnes=exercices_selectionnes,
                           exercices_non_selectionnes=exercices_non_selectionnes,
                           classes=CLASSES)




@prof.route("/devoirs/edit/<devoir_id>", methods=["POST"])
@role_required("professeur", "admin")
def edit_devoir_submit(devoir_id):
    titre = request.form.get("titre", "").strip()
    mode = request.form.get("mode", "entrainement")
    classe_id = request.form.get("classe_id","").strip()
    if classe_id not in CLASSES:
        flash("Classe invalide sélectionnée.", "danger")
        return redirect(url_for("prof.edit_devoir_get", devoir_id=devoir_id))
    exercice_ids = request.form.getlist("exercice_id")
    tentatives_list = request.form.getlist("tentatives")

    if not titre or not exercice_ids or not classe_id:
        flash("Le titre, une classe et au moins un exercice sont requis.", "danger")
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
            {
                "$set": {
                    "titre": titre,
                    "mode": mode,
                    "classe_id": classe_id,
                    "exercices": exercices
                }
            }
        )

        flash("Devoir mis à jour avec succès.", "success")
        return redirect(url_for("prof.liste_devoirs"))

    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")
        return redirect(url_for("prof.edit_devoir_get", devoir_id=devoir_id))


    
@prof.route('/resultats', methods=['GET'])
def selectionner_devoir_resultats():
    devoirs = list(mongo.db.devoirs.find())
    for d in devoirs:
        d['_id'] = str(d['_id'])
    return render_template('selectionner_devoir.html', devoirs=devoirs)



@prof.route("/resultats/<devoir_id>")
@role_required("professeur", "admin")
def resultats_devoir(devoir_id):
    devoir = devoirs_col.find_one({"_id": ObjectId(devoir_id)})
    if not devoir:
        flash("Devoir introuvable.")
        return redirect(url_for("prof.admin_prof"))

    reponses = list(reponses_devoir_col.find({"devoir_id": devoir_id}))

    notes_par_eleve = {}

    for rep in reponses:
        eleve = rep["eleve_username"]
        score = rep.get("score", 0)
        total = rep.get("total", 0)

        if eleve not in notes_par_eleve:
            notes_par_eleve[eleve] = {"score": 0, "total": 0}

        notes_par_eleve[eleve]["score"] += score
        notes_par_eleve[eleve]["total"] += total

    return render_template("prof/resultats_resume.html", devoir=devoir, notes=notes_par_eleve)


@prof.route("/resultats/<devoir_id>/eleve/<eleve_username>")
@role_required("professeur", "admin")
def resultats_eleve_devoir(devoir_id, eleve_username):
    devoir = devoirs_col.find_one({"_id": ObjectId(devoir_id)})
    if not devoir:
        flash("Devoir introuvable.")
        return redirect(url_for("prof.admin_prof"))

    reponses = list(reponses_devoir_col.find({
        "devoir_id": devoir_id,
        "eleve_username": eleve_username
    }))

    exercices_cache = {}

    resultats = []

    for rep in reponses:
        exo_id = rep.get("exercice_id")
        if not exo_id:
            continue

        if exo_id not in exercices_cache:
            exercice = exercices_col.find_one({"_id": ObjectId(exo_id)})
            exercices_cache[exo_id] = exercice["titre"] if exercice else "Exercice inconnu"

        resultats.append({
            "titre": exercices_cache[exo_id],
            "score": rep.get("score", 0),
            "total": rep.get("total", 0),
            "date": rep.get("date"),
            "reponses": rep.get("reponses", {})
        })

    return render_template("prof/resultats_detail_eleve.html", devoir=devoir, eleve=eleve_username, resultats=resultats)



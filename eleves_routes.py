from flask import Blueprint, render_template, request, redirect, flash, url_for, session,abort
from extensions import mongo
from decorators import role_required
from bson import ObjectId
from datetime import datetime
from constants import ROLES
from bs4 import BeautifulSoup

eleve = Blueprint("eleve", __name__, template_folder="templates/eleve")

db = mongo.db
devoirs_col = db["devoirs"]
reponses_col = db["reponses_devoirs"]
exercices_col = db["exercices_interactifs"]
reponses_devoir_col = db["reponses_devoirs"]

@eleve.route("/home")
@role_required("eleve")
def home_eleve():
    if session.get("role") != "eleve":
        flash("Accès réservé aux élèves.")
        return redirect(url_for("index"))
    return render_template("eleve/home_eleve.html")

@eleve.route("/mes-devoirs")
@role_required("eleve")
def mes_devoirs():
    if session.get("role") != ROLES["ELEVE"]:
        flash("Accès réservé aux élèves.")
        return redirect(url_for("index"))

    classe_user = session.get("classe", [])
    if not classe_user:
        flash("Aucune classe trouvée pour l'utilisateur.")
        return redirect(url_for("index"))

    mode = request.args.get("mode")  # "controle" ou "entrainement"

    # Rechercher les devoirs pour les classes de l'élève
    query = {
        "classe_id": {"$in": classe_user}
    }
    if mode:
        query["mode"] = mode

    devoirs_disponibles = list(devoirs_col.find(query).sort("date", -1))

    for devoir in devoirs_disponibles:
        if devoir.get("mode") == "controle":
            reponse = reponses_col.find_one({
                "eleve_username": session["username"],
                "devoir_id": str(devoir["_id"])
            })
            if reponse:
                devoir["fait"] = True
                devoir["date_fait"] = reponse.get("date")
            else:
                devoir["fait"] = False
        else:
            devoir["fait"] = False  # entraînement = jamais bloqué

    return render_template("eleve/mes_devoirs.html", devoirs=devoirs_disponibles, classe=classe_user, mode=mode)





@eleve.route("/devoir/<devoir_id>", methods=["GET", "POST"])
def faire_devoir(devoir_id):
    if session.get("role") != "eleve":
        flash("Accès réservé aux élèves.")
        return redirect(url_for("index"))

    devoir = devoirs_col.find_one({"_id": ObjectId(devoir_id)})
    if not devoir:
        flash("Devoir introuvable.")
        return redirect(url_for("eleve.mes_devoirs"))

    # 🚫 Bloquer accès si déjà soumis (mode contrôle)
    if devoir.get("mode") == "controle":
        deja_fait = reponses_col.find_one({
            "eleve_username": session["username"],
            "devoir_id": devoir_id
        })
        if deja_fait:
            flash("Vous avez déjà soumis ce devoir de contrôle.")
            return redirect(url_for("eleve.mes_devoirs"))

    exercices_ids = [exo["exercice_id"] for exo in devoir["exercices"]]
    exercices = list(db["exercices_interactifs"].find({"_id": {"$in": exercices_ids}}))

    for exercice in exercices:
        exo_id_str = str(exercice["_id"])
        html = exercice.get("reponse_html", "")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["input", "textarea", "select"]):
            original_name = tag.get("name")
            if original_name:
                tag["name"] = f"{exo_id_str}_{original_name}"
        exercice["reponse_html_parsed"] = str(soup)

    if request.method == "POST":
        total_score = 0
        total_questions = 0
        details = []

        for exercice in exercices:
            exo_id_str = str(exercice["_id"])
            bonnes_reponses = exercice.get("reponses_attendues", {})
            score = 0
            erreurs = {}
            reponses_donnees = {}

            for field, bonne_valeur in bonnes_reponses.items():
                champ_form = f"{exo_id_str}_{field}"
                valeur = request.form.get(champ_form, "").strip()
                reponses_donnees[field] = valeur

                if valeur.lower() == bonne_valeur.strip().lower():
                    score += 1
                else:
                    erreurs[field] = {
                        "attendue": bonne_valeur,
                        "donnee": valeur
                    }

            total_score += score
            total_questions += len(bonnes_reponses)

            if devoir.get("mode") == "controle":
                reponses_col.insert_one({
                    "eleve_username": session["username"],
                    "devoir_id": devoir_id,
                    "exercice_id": exo_id_str,
                    "reponses": reponses_donnees,
                    "score": score,
                    "total": len(bonnes_reponses),
                    "tentative_num": 1,
                    "date": datetime.now()
                })

            details.append({
                "titre": exercice.get("titre", f"Exercice {exo_id_str}"),
                "score": score,
                "total": len(bonnes_reponses),
                "erreurs": erreurs
            })

        if devoir.get("mode") == "entrainement":
            return render_template("eleve/resultat_entrainement.html", details=details, total=total_score, max=total_questions)

        flash("Réponses enregistrées pour le contrôle.")
        return redirect(url_for("eleve.mes_devoirs"))

    return render_template(
        "eleve/faire_devoir.html",
        devoir=devoir,
        exercices=exercices
    )


@eleve.route("/resultats")
def consulter_resultats():
    if session.get("role") != "eleve":
        flash("Accès réservé aux élèves.")
        return redirect(url_for("index"))
    
    username = session.get("username")
    # Récupérer les résultats de l'élève dans la collection des réponses aux devoirs
    resultats = list(reponses_devoir_col.find({"eleve_username": username}))
    
    return render_template("eleve/resultats.html", resultats=resultats)

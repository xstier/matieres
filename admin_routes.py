import os
from flask import Blueprint, render_template, redirect, request, session, url_for, flash , current_app
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from markupsafe import escape  # Ajout pour échapper le texte


#import logging

# Activer les logs pour PyMongo
# logger = logging.getLogger("pymongo")
# logger.setLevel(logging.DEBUG)

# Afficher les logs dans la console
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
# logger.addHandler(console_handler)


admin = Blueprint('admin', __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
matieres_col = db["matieres"]
themes_col = db["themes"]
users_col = db["users"]
exercises_col = db["exercices"]

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@admin.route("/admin", methods=["GET"])
def admin_home():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))
    matieres = list(matieres_col.find())
    themes = list(themes_col.find())
    return render_template("admin.html", matieres=matieres, themes=themes)

@admin.route("/add_matiere", methods=["POST"])
def add_matiere():
    if session.get("admin"):
        nom = request.form["nom"].strip()
        if len(nom) < 4:
            flash("Le nom de la matière doit contenir au moins 4 caractères.")
            return redirect(url_for("admin.admin_home"))
        matieres_col.insert_one({"nom": nom})
    return redirect(url_for("admin.admin_home"))

@admin.route('/delete_matiere/<matiere_id>', methods=['POST'])
def delete_matiere(matiere_id):
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    matiere = matieres_col.find_one({"_id": ObjectId(matiere_id)})
    if not matiere:
        flash("Matière introuvable.")
        return redirect(url_for("admin.admin_home"))

    # Récupérer tous les thèmes liés
    themes = list(themes_col.find({"matiere_id": matiere_id}))

    for theme in themes:
        # Supprimer fichiers des leçons
        for lesson in theme.get("lessons", []):
            if "fichier" in lesson:
                filepath = os.path.join(UPLOAD_FOLDER, lesson["fichier"])
                if os.path.exists(filepath):
                    os.remove(filepath)

        # Supprimer fichiers des exercices
        for ex in theme.get("exercises", []):
            if "fichier" in ex:
                filepath = os.path.join(UPLOAD_FOLDER, ex["fichier"])
                if os.path.exists(filepath):
                    os.remove(filepath)

    # Supprimer les thèmes liés
    themes_col.delete_many({"matiere_id": matiere_id})

    # Supprimer la matière
    result = matieres_col.delete_one({"_id": ObjectId(matiere_id)})
    if result.deleted_count == 1:
        flash("Matière, thèmes et contenus associés supprimés avec succès.")
    else:
        flash("Erreur lors de la suppression de la matière.")

    return redirect(url_for("admin.admin_home"))


@admin.route("/add_theme", methods=["POST"])
def add_theme():
    if session.get("admin"):
        nom = request.form["nom"]
        matiere_id = request.form["matiere_id"]
        themes_col.insert_one({"nom": nom, "matiere_id": matiere_id})
    return redirect(url_for("admin.admin_home"))

@admin.route('/delete_theme/<theme_id>', methods=['POST'])
def delete_theme(theme_id):
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    theme = themes_col.find_one({"_id": ObjectId(theme_id)})
    if not theme:
        flash("Thème introuvable.")
        return redirect(url_for("admin.admin_home"))

    # Supprimer fichiers associés aux leçons
    for lesson in theme.get("lessons", []):
        if "fichier" in lesson:
            filepath = os.path.join(UPLOAD_FOLDER, lesson["fichier"])
            if os.path.exists(filepath):
                os.remove(filepath)

    # Supprimer fichiers associés aux exercices
    for ex in theme.get("exercises", []):
        if "fichier" in ex:
            filepath = os.path.join(UPLOAD_FOLDER, ex["fichier"])
            if os.path.exists(filepath):
                os.remove(filepath)

    # Supprimer le thème dans la base
    result = themes_col.delete_one({"_id": ObjectId(theme_id)})
    if result.deleted_count == 1:
        flash("Thème et ses contenus supprimés avec succès.")
    else:
        flash("Erreur lors de la suppression du thème.")

    return redirect(url_for("admin.admin_home"))


@admin.route("/admin/manage_users", methods=["GET", "POST"])
def manage_users():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    message = ""

    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")

        if action == "delete":
            user_to_delete = users_col.find_one({"_id": ObjectId(user_id)})
            current_user = users_col.find_one({"username": session.get("username")})

            if not user_to_delete:
                message = "Utilisateur introuvable."
            
            elif str(user_to_delete["_id"]) == str(current_user["_id"]):
                message = "Vous ne pouvez pas supprimer votre propre compte."
            
            elif user_to_delete["role"] == "admin":
                admin_count = users_col.count_documents({"role": "admin"})
                if admin_count <= 1:
                    message = "Impossible de supprimer le dernier administrateur."
                else:
                    users_col.delete_one({"_id": ObjectId(user_id)})
                    message = "Administrateur supprimé avec succès."
            
            else:
                users_col.delete_one({"_id": ObjectId(user_id)})
                message = "Utilisateur supprimé avec succès."

        elif action == "toggle_role":
            user = users_col.find_one({"_id": ObjectId(user_id)})
            current_user = users_col.find_one({"username": session.get("username")})

            if user:
                # Empêcher un admin de modifier son propre rôle
                if str(user["_id"]) == str(current_user["_id"]):
                    message = "Vous ne pouvez pas modifier votre propre rôle."
                
                # Empêcher de retirer le rôle 'admin' s'il ne reste qu'un seul admin
                elif user["role"] == "admin":
                    admin_count = users_col.count_documents({"role": "admin"})
                    if admin_count <= 1:
                        message = "Impossible de retirer le rôle admin : il doit rester au moins un administrateur."
                    else:
                        users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": "user"}})
                        message = "Rôle changé en user."
                
                # Sinon, on peut promouvoir de user à admin
                else:
                    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": "admin"}})
                    message = "Rôle changé en admin."

        elif action == "reset_password":
            new_pw = generate_password_hash("nouveau123")
            users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": new_pw}})
            message = "Mot de passe réinitialisé à 'nouveau123'."

    all_users = list(users_col.find({}, {"password": 0}))  # Ne pas afficher les mots de passe
    return render_template("manage_users.html", users=all_users, message=message)

@admin.route("/add_lesson", methods=["POST"])
def add_lesson():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    theme_id = request.form.get("theme_id")
    matiere_id = request.form.get("matiere_id")
    titre = request.form.get("titre", "").strip()
    contenu = request.form.get("contenu", "").strip()
    fichier = request.files.get("fichier")

    if not titre:
        flash("Le titre est obligatoire.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    if contenu and fichier and fichier.filename:
        flash("Veuillez fournir soit un contenu, soit un fichier, mais pas les deux.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    lesson_data = {"titre": escape(titre)}

    if contenu:
        lesson_data["contenu"] = escape(contenu)
    elif fichier and fichier.filename:
        filename = secure_filename(fichier.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        fichier.save(filepath)
        lesson_data["fichier"] = filename
    else:
        flash("Vous devez fournir soit un contenu texte, soit un fichier.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    try:
        result = themes_col.update_one(
            {"_id": ObjectId(theme_id)},
            {"$push": {"lessons": lesson_data}}
        )

        if result.modified_count == 1:
            print(f"[OK] Leçon ajoutée au thème {theme_id} : {lesson_data}")
            flash("✅ Leçon ajoutée avec succès.")
        else:
            print(f"[ÉCHEC] Leçon non ajoutée. Résultat brut : {result.raw_result}")
            flash("❌ Une erreur est survenue lors de l'ajout.")
    except Exception as e:
        print(f"[EXCEPTION] Erreur lors de l'ajout de la leçon : {e}")
        flash("⚠ Une erreur technique est survenue.")

    return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))


@admin.route("/add_exercise", methods=["POST"])
def add_exercise():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    theme_id = request.form.get("theme_id")
    matiere_id = request.form.get("matiere_id")
    titre = request.form.get("titre", "").strip()
    contenu = request.form.get("contenu", "").strip()
    fichier = request.files.get("fichier")

    if not titre:
        flash("Le titre est obligatoire.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    if contenu and fichier and fichier.filename:
        flash("Veuillez fournir soit un contenu, soit un fichier, mais pas les deux.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    exercise_data = {"titre": escape(titre)}

    if contenu:
        exercise_data["contenu"] = escape(contenu)
    elif fichier and fichier.filename:
        filename = secure_filename(fichier.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        fichier.save(filepath)
        exercise_data["fichier"] = filename
    else:
        flash("Vous devez fournir soit un contenu texte, soit un fichier.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))

    try:
        result = themes_col.update_one(
            {"_id": ObjectId(theme_id)},
            {"$push": {"exercises": exercise_data}}
        )

        if result.modified_count == 1:
            print(f"[OK] Exercice ajouté au thème {theme_id} : {exercise_data}")
            flash("✅ Exercice ajouté avec succès.")
        else:
            print(f"[ÉCHEC] Exercice non ajouté. Résultat brut : {result.raw_result}")
            flash("❌ Une erreur est survenue lors de l'ajout.")
    except Exception as e:
        print(f"[EXCEPTION] Erreur lors de l'ajout de l'exercice : {e}")
        flash("⚠ Une erreur technique est survenue.")

    return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=matiere_id))


@admin.route("/admin/add_content", methods=["GET"])
def add_content():
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    matieres = list(matieres_col.find())
    themes = []

    matiere_id = request.args.get("matiere_id")
    theme_id = request.args.get("theme_id")

    if matiere_id:
        themes = list(themes_col.find({"matiere_id": matiere_id}))

    selected_theme = themes_col.find_one({"_id": ObjectId(theme_id)}) if theme_id else None

    return render_template(
        "add_content.html",
        matieres=matieres,
        themes=themes,
        selected_matiere=matiere_id,
        selected_theme=selected_theme
    )



@admin.route("/delete_lesson/<theme_id>/<int:lesson_index>", methods=["POST"])
def delete_lesson(theme_id, lesson_index):
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    theme = themes_col.find_one({"_id": ObjectId(theme_id)})

    if not theme or "lessons" not in theme or lesson_index >= len(theme["lessons"]):
        flash("Leçon introuvable.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=request.args.get("matiere_id")))

    lesson = theme["lessons"][lesson_index]

    # Supprimer le fichier s’il existe
    if "fichier" in lesson:
        file_path = os.path.join("static/uploads", lesson["fichier"])
        if os.path.exists(file_path):
            os.remove(file_path)

    # Supprimer la leçon de MongoDB
    unset_key = f"lessons.{lesson_index}"
    themes_col.update_one({"_id": ObjectId(theme_id)}, {"$unset": {unset_key: 1}})
    themes_col.update_one({"_id": ObjectId(theme_id)}, {"$pull": {"lessons": None}})

    flash("Leçon supprimée avec succès.")
    return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=request.args.get("matiere_id")))



@admin.route("/delete_exercise/<theme_id>/<int:exercise_index>", methods=["POST"])
def delete_exercise(theme_id, exercise_index):
    if not session.get("admin"):
        return redirect(url_for("auth.login"))

    theme = themes_col.find_one({"_id": ObjectId(theme_id)})

    if not theme or "exercises" not in theme or exercise_index >= len(theme["exercises"]):
        flash("Exercice introuvable.")
        return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=request.args.get("matiere_id")))

    exercise = theme["exercises"][exercise_index]

    # Supprimer le fichier s’il existe
    if "fichier" in exercise:
        file_path = os.path.join("static/uploads", exercise["fichier"])
        if os.path.exists(file_path):
            os.remove(file_path)

    # Supprimer l'exercice de MongoDB
    unset_key = f"exercises.{exercise_index}"
    themes_col.update_one({"_id": ObjectId(theme_id)}, {"$unset": {unset_key: 1}})
    themes_col.update_one({"_id": ObjectId(theme_id)}, {"$pull": {"exercises": None}})

    flash("Exercice supprimé avec succès.")
    return redirect(url_for("admin.add_content", theme_id=theme_id, matiere_id=request.args.get("matiere_id")))


@admin.route("/admin/add_exercice_interactif", methods=["GET", "POST"])
def add_exercice_interactif():
    if request.method == "POST":
        matiere_id = request.form.get("matiere_id")
        theme_id = request.form.get("theme_id")
        titre = request.form.get("titre")
        question = request.form.get("question")
        reponse_html = request.form.get("reponse_html")

        if not (matiere_id and theme_id and titre and question and reponse_html):
            flash("Tous les champs sont obligatoires.", "error")
            return redirect(request.url)

        exercise = {
            "matiere_id": ObjectId(matiere_id),
            "theme_id": ObjectId(theme_id),
            "titre": titre.strip(),
            "question": question.strip(),
            "reponse_html": reponse_html.strip(),
            "date_creation": datetime.now()
        }

        exercises_col.insert_one(exercise)
        flash("Exercice ajouté avec succès.", "success")
        return redirect(url_for("afficher_themes", matiere_id=matiere_id))

    matieres = list(matieres_col.find())
    return render_template("add_exercice_interactif.html", matieres=matieres)

@admin.route("/api/themes/<matiere_id>")
def api_get_themes(matiere_id):
    from bson.json_util import dumps
    themes = list(themes_col.find({"matiere_id": matiere_id}))
    return dumps(themes)  # JSON response



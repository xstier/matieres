from bson import ObjectId
from pymongo import MongoClient
from flask import Blueprint , render_template , request , session


exercice = Blueprint('exercice', __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["matieres"]
users_col = db["users"]
themes_col = db["themes"]

@exercice.route("/exercice/<theme_id>" , methods = ["POST"])
def exercice(theme_id):
    
    theme  = themes_col.find_one({"id_":ObjectId(theme_id)})
    nom = ""
    question = ""
    reponse = ""
    
    return(render_template("add_exercice_perso.html"))
        
    
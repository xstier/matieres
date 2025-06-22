from pymongo import MongoClient
from werkzeug.security import check_password_hash

def test_password(username, password_to_test):
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["matieres"]
        users_col = db["users"]
        print("Connexion à la base OK.")
    except Exception as e:
        print(f"Erreur de connexion à la base : {e}")
        return

    user = users_col.find_one({"username": username})
    if not user:
        print(f"Utilisateur '{username}' non trouvé dans la base.")
        return

    stored_hash = user.get("password")
    if not stored_hash:
        print(f"Utilisateur '{username}' n'a pas de mot de passe stocké.")
        return

    is_correct = check_password_hash(stored_hash, password_to_test)
    if is_correct:
        print(f"Mot de passe CORRECT pour l'utilisateur '{username}'.")
    else:
        print(f"Mot de passe INCORRECT pour l'utilisateur '{username}'.")

if __name__ == "__main__":
    username_input = input("Nom d'utilisateur à tester : ").strip()
    password_input = input("Mot de passe à tester : ")
    test_password(username_input, password_input)

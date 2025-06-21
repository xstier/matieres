// static/js/confirmations.js

const confirmationMessages = {
  deleteTheme:
    "Attention ! La suppression de ce thème supprimera toutes ses leçons et exercices. Voulez-vous continuer ?",
  deleteMatiere:
    "Attention ! La suppression de cette matière supprimera tous les thèmes, leçons, exercices et fichiers associés. Voulez-vous continuer ?",
};

function confirmAction(actionKey) {
  const message = confirmationMessages[actionKey];
  if (!message) {
    console.warn(
      `Aucun message de confirmation trouvé pour l'action : ${actionKey}`
    );
    return false;
  }
  return confirm(message);
}

// Fonctions spécifiques pour compatibilité avec les appels existants
function confirmDeleteTheme() {
  return confirmAction("deleteTheme");
}

function confirmDeleteMatiere() {
  return confirmAction("deleteMatiere");
}

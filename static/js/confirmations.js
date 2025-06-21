// static/js/confirmations.js

function confirmDeleteTheme() {
  return confirm(
    "Attention ! La suppression de ce thème supprimera toutes ses leçons et exercices. Voulez-vous continuer ?"
  );
}

function confirmDeleteMatiere() {
  return confirm(
    "Attention ! La suppression de cette matière supprimera tous les thèmes, leçons, exercices et fichiers associés. Voulez-vous continuer ?"
  );
}

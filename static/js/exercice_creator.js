// Récupère le texte actuellement sélectionné par l'utilisateur
function getSelectedText() {
  const selection = window.getSelection();
  return selection ? selection.toString() : "";
}

// Remplace la sélection courante par un élément <select> avec des options données
function remplacerParSelect(choices) {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;

  const range = selection.getRangeAt(0);
  const select = document.createElement("select");

  choices.forEach((choice) => {
    const option = document.createElement("option");
    option.text = choice;
    select.appendChild(option);
  });

  range.deleteContents();
  range.insertNode(select);

  // Replacer le curseur juste après le select inséré
  range.setStartAfter(select);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}

// Transforme le texte sélectionné en un choix multiple <select> avec options
function transformerSelectionEnChoix() {
  const texte = getSelectedText();
  if (!texte) {
    alert(
      "Veuillez sélectionner une portion du texte dans la zone de réponse."
    );
    return;
  }

  const saisie = prompt(
    `Entrez les choix possibles pour "${texte}", séparés par des virgules :`
  );
  if (!saisie) return;

  const choix = saisie
    .split(",")
    .map((c) => c.trim())
    .filter(Boolean);

  if (choix.length < 2) {
    alert("Veuillez entrer au moins deux choix.");
    return;
  }

  remplacerParSelect(choix);
}

// Prépare le contenu HTML de la zone éditable avant soumission du formulaire
function prepareContenu() {
  const editableArea = document.getElementById("editableArea");
  if (!editableArea) {
    alert("Zone éditable introuvable.");
    return;
  }
  const html = editableArea.innerHTML;
  const contenuHtml = document.getElementById("contenu_html");
  if (!contenuHtml) {
    alert("Champ de contenu HTML introuvable.");
    return;
  }
  contenuHtml.value = html;
  alert("Contenu préparé. Vous pouvez maintenant soumettre le formulaire.");
}

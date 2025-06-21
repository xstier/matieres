document.addEventListener("DOMContentLoaded", () => {
  const matiereSelect = document.getElementById("matiere-select");
  const themeSelect = document.getElementById("theme-select");

  // Charge les thèmes liés à une matière donnée
  async function loadThemes(matiereId) {
    try {
      const response = await fetch(`/api/themes/${matiereId}`);

      if (!response.ok) {
        throw new Error(`Erreur HTTP : ${response.status}`);
      }

      const themes = await response.json();

      // Vide la liste des thèmes actuels
      themeSelect.innerHTML = "";

      // Ajoute une option vide si besoin (optionnel)
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "Sélectionnez un thème";
      themeSelect.appendChild(defaultOption);

      // Ajoute les options des thèmes reçus
      themes.forEach((theme) => {
        const option = document.createElement("option");
        option.value = theme._id;
        option.textContent = theme.nom;
        themeSelect.appendChild(option);
      });
    } catch (error) {
      console.error("Erreur lors du chargement des thèmes :", error);
      themeSelect.innerHTML = `<option value="">Erreur de chargement</option>`;
    }
  }

  // Événement au changement de la matière sélectionnée
  matiereSelect.addEventListener("change", () => {
    const matiereId = matiereSelect.value;
    if (matiereId) {
      loadThemes(matiereId);
    } else {
      // Si aucune matière sélectionnée, vide la liste des thèmes
      themeSelect.innerHTML = `<option value="">Sélectionnez une matière d'abord</option>`;
    }
  });

  // Déclenche le chargement initial si une matière est déjà sélectionnée
  if (matiereSelect.value) {
    loadThemes(matiereSelect.value);
  } else {
    themeSelect.innerHTML = `<option value="">Sélectionnez une matière d'abord</option>`;
  }
});

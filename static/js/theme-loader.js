document.addEventListener("DOMContentLoaded", () => {
  const matiereSelect = document.getElementById("matiere");
  const themeSelect = document.getElementById("theme");

  if (!matiereSelect || !themeSelect) return; // Sécurité si absent

  async function loadThemes(matiereId) {
    themeSelect.innerHTML = '<option value="">Chargement...</option>';
    if (!matiereId) {
      themeSelect.innerHTML =
        '<option value="">-- Choisir un thème --</option>';
      return;
    }
    try {
      const response = await fetch(
        `/admin/api/themes/${encodeURIComponent(matiereId)}`
      );
      if (!response.ok) throw new Error("Erreur lors du chargement des thèmes");
      const themes = await response.json();

      themeSelect.innerHTML =
        '<option value="">-- Choisir un thème --</option>';
      themes.forEach((theme) => {
        const option = document.createElement("option");
        option.value = theme._id;
        option.textContent = theme.nom;
        themeSelect.appendChild(option);
      });
    } catch (err) {
      console.error(err);
      themeSelect.innerHTML = '<option value="">Erreur de chargement</option>';
    }
  }

  matiereSelect.addEventListener("change", (e) => {
    loadThemes(e.target.value);
  });

  // Charger les thèmes si une matière est déjà sélectionnée (ex : formulaire en mode édition)
  if (matiereSelect.value) {
    loadThemes(matiereSelect.value);
  }
});

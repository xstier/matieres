document.addEventListener("DOMContentLoaded", () => {
  const matiereSelect = document.getElementById("matiere-select");
  const themeSelect = document.getElementById("theme-select");

  async function loadThemes(matiereId) {
    themeSelect.innerHTML = ""; // vide les options
    if (!matiereId) return;
    try {
      const response = await fetch(`/api/themes/${matiereId}`);
      if (!response.ok) throw new Error("Erreur lors du chargement des thèmes");
      const themes = await response.json();

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

  // Charge les thèmes au chargement si une matière est déjà sélectionnée
  if (matiereSelect.value) {
    loadThemes(matiereSelect.value);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  // Sélectionne tous les titres de leçon ayant contenu texte
  const lessonTitles = document.querySelectorAll(
    ".lesson-titre[data-has-content='true']"
  );

  lessonTitles.forEach((title) => {
    title.style.cursor = "pointer"; // Met un curseur pointer pour indiquer que c’est cliquable

    title.addEventListener("click", () => {
      const contentDiv = title.nextElementSibling;
      if (!contentDiv) return;

      if (contentDiv.style.display === "block") {
        contentDiv.style.display = "none";
      } else {
        contentDiv.style.display = "block";
      }
    });
  });
});

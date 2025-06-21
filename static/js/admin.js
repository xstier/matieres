document.addEventListener("DOMContentLoaded", () => {
  // Fonction qui gère le toggle du contenu de la leçon
  function toggleLessonContent(title) {
    const contentDiv = title.nextElementSibling;
    if (contentDiv && contentDiv.classList.contains("lesson-content")) {
      contentDiv.classList.toggle("visible");
    }
  }

  // Sélectionne tous les titres de leçon ayant contenu texte
  const lessonTitles = document.querySelectorAll(
    ".lesson-titre[data-has-content='true']"
  );

  lessonTitles.forEach((title) => {
    title.style.cursor = "pointer"; // Indique que c’est cliquable
    title.setAttribute("tabindex", "0"); // Permet la navigation clavier

    // Clic souris pour toggle
    title.addEventListener("click", () => toggleLessonContent(title));

    // Activation au clavier (touche Enter)
    title.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        toggleLessonContent(title);
      }
    });
  });
});

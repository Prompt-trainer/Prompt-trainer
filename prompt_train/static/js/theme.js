document.addEventListener("DOMContentLoaded", function () {

    const html = document.documentElement;
    const button = document.getElementById("themeToggle");

    // Якщо тема збережена в localStorage, використовуємо її, інакше за замовчуванням "dark"
    let theme = localStorage.getItem("theme") || "dark";

    html.setAttribute("data-bs-theme", theme);

    // Встановлюємо іконку відповідно до поточної теми
    setIcon(theme);

    button.addEventListener("click", function () {

        theme = html.getAttribute("data-bs-theme") === "dark"
            ? "light"
            : "dark";

        html.setAttribute("data-bs-theme", theme);
        localStorage.setItem("theme", theme);

        setIcon(theme);
    });

    function setIcon(theme) {
        if (theme === "dark") {
            button.innerHTML = '<i class="bi bi-sun-fill"></i>';
        } else {
            button.innerHTML = '<i class="bi bi-moon-fill"></i>';
        }
    }

});

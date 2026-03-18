(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // Construct the .html.md URL from the current page URL
    var pathname = window.location.pathname;
    var mdUrl;

    if (pathname.endsWith(".html")) {
      // Standard HTML builder: api_reference.html → api_reference.html.md
      mdUrl = pathname.replace(/\.html$/, ".html.md");
    } else if (pathname.endsWith("/")) {
      // dirhtml builder: api_reference/ → api_reference/index.html.md
      mdUrl = pathname + "index.html.md";
    } else {
      return; // Unknown URL format — skip
    }

    // Build a <li> item matching the existing download dropdown items
    var li = document.createElement("li");
    var a = document.createElement("a");
    a.href = mdUrl;
    a.className = "btn btn-sm btn-download-source-button dropdown-item";
    a.setAttribute("title", "Download Markdown (LLM-friendly)");
    a.setAttribute("data-bs-placement", "left");
    a.setAttribute("data-bs-toggle", "tooltip");
    a.setAttribute("download", "");

    var iconSpan = document.createElement("span");
    iconSpan.className = "btn__icon-container";
    var icon = document.createElement("i");
    icon.className = "fa-brands fa-markdown";
    iconSpan.appendChild(icon);

    var textSpan = document.createElement("span");
    textSpan.className = "btn__text-container";
    textSpan.textContent = ".md";

    a.appendChild(iconSpan);
    a.appendChild(textSpan);
    li.appendChild(a);

    // Inject as the first item in the download dropdown menu
    var menu = document.querySelector(".dropdown-download-buttons .dropdown-menu");
    if (menu) {
      menu.insertBefore(li, menu.firstChild);
    }
  });
})();

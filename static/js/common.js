export async function checkAuthAndShowNav() {
  try {
    const res = await fetch("/auth");
    if (!res.ok) {
      // Not authenticated? Send to splash/login
      window.location.href = "/ui/index.html";
      return;
    }

    // Build navigation
    const nav = document.createElement("nav");
    nav.innerHTML = `
      <a href="/ui/main.html">Main</a> |
      <a href="/ui/settings.html">Settings</a>
    `;
    nav.style.marginBottom = "1rem";
    nav.style.display = "block";
    nav.style.paddingBottom = "1rem";

    document.body.prepend(nav);
  } catch (error) {
    console.error("Error checking auth:", error);
    window.location.href = "/ui/index.html";
  }
}

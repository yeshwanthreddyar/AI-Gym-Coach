const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
document.head.insertAdjacentHTML("beforeend",
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap"><link rel="stylesheet" href="/static/style.css">');

function toast(m, ok = true) {
  const t = $("toast");
  if (!t) return;
  t.textContent = m;
  t.style.borderLeft = ok ? "4px solid var(--green)" : "4px solid #ff6b6b";
  t.style.display = "block";
  clearTimeout(t._h);
  t._h = setTimeout(() => (t.style.display = "none"), 2600);
}

async function fetchMe() {
  try {
    const r = await fetch("/auth/me");
    return r.ok ? await r.json() : null;
  } catch (e) {
    return null;
  }
}

async function logout() {
  await fetch("/auth/logout", { method: "POST" });
  location.href = "/home";
}

async function renderShell() {
  const here = location.pathname;
  const me = await fetchMe();
  const link = (href, label) => `<a href="${href}" class="${here === href ? "on" : ""}">${label}</a>`;
  const right = me
    ? `${link("/diet", "Diet")}${link("/tracker", "My progress")}${link("/profile", "My profile")}<a href="#" onclick="logout();return false">Log out</a>`
    : `${link("/diet", "Diet")}${link("/login", "Log in")}<a class="btn" href="/register">Register</a>`;
  if ($("nav")) $("nav").innerHTML = `<nav class="top"><div class="wrap">
    <a href="/home" class="logo disp">AI GYM COACH</a>
    <div class="links">${link("/home", "Home")}${link("/workouts", "Workouts")}${right}</div>
    </div></nav>`;
  if ($("footer")) $("footer").innerHTML = `<div class="wrap">AI Gym Coach gives general fitness guidance, not medical advice. Check with a doctor before starting a new programme, especially with an injury or health condition.</div>`;
}

// 3D background (loads as a module on every page)
(function () {
  const s = document.createElement("script");
  s.type = "module";
  s.src = window.BG3D_SRC || "/static/bg3d.js";
  document.body.appendChild(s);
})();

renderShell();

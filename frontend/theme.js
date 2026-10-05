/* ================================================================ theme
 *
 * The system preference sets the theme on load, and keeps setting it while
 * the reader has not chosen for themselves. Once they press the button,
 * their choice wins and the system stops overriding it, because following
 * the OS is not the same as being asked.
 *
 * The change is revealed outward from the button rather than cross-faded,
 * so it is obvious what caused it. That needs the View Transition API, and
 * it is skipped entirely where the API is missing or motion is unwelcome:
 * the theme still changes, it just arrives rather than wipes.
 */

const themeQuery = window.matchMedia("(prefers-color-scheme: dark)");

/* Read from the query directly rather than sharing a constant with the
 * companion script. Two files each declaring `reducedMotion` at top level
 * would be a duplicate declaration and would fail to parse, and depending
 * on load order to avoid that is worse than asking the question twice. */
const calm = window.matchMedia("(prefers-reduced-motion: reduce)");

const root = document.documentElement;
const themeButton = document.getElementById("theme");

function applyTheme(value) {
  root.dataset.theme = value;
  try {
    localStorage.setItem("meridian.theme", value);
  } catch (error) {
    /* Storage unavailable. The theme still applies for this page. */
  }
}

/* On first load the reader's stored choice wins; otherwise follow the
 * system. Reading localStorage can throw, so it is guarded rather than
 * assumed, or the whole script dies on a privacy setting. */
let initial = null;

try {
  initial = localStorage.getItem("meridian.theme");
} catch (error) {
  initial = null;
}

root.dataset.theme = initial === "dark" || initial === "light"
  ? initial
  : (themeQuery.matches ? "dark" : "light");

/* Only track the system while no explicit choice is stored. */
themeQuery.addEventListener("change", (event) => {
  let chosen = null;

  try {
    chosen = localStorage.getItem("meridian.theme");
  } catch (error) {
    chosen = null;
  }

  if (!chosen) root.dataset.theme = event.matches ? "dark" : "light";
});

if (themeButton) {
  themeButton.addEventListener("click", (event) => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";

    /* Where the wipe starts: the centre of the button that was pressed. */
    const box = event.currentTarget.getBoundingClientRect();
    const x = box.left + box.width / 2;
    const y = box.top + box.height / 2;

    const commit = () => applyTheme(next);

    if (calm.matches || !document.startViewTransition) {
      commit();
      return;
    }

    /* The radius needed to reach the furthest corner from the button. */
    const reach = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y),
    );

    document.startViewTransition(commit).ready.then(() => {
      root.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${reach}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 500,
          easing: "cubic-bezier(0.2, 0.7, 0.2, 1)",
          pseudoElement: "::view-transition-new(root)",
        },
      );
    });
  });
}
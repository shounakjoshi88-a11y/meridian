/* ============================================================= companion
 *
 * A small pixel creature that walks along the rows of a list. Drawn for a
 * prototype and kept because it earns something: a registry of 600 records
 * is otherwise a wall of near-identical lines, and this gives the eye a
 * moving point of reference and a reason to look at rows it would skip.
 *
 * It carries no information. It is aria-hidden, every action it responds to
 * is also available without it, and the header control switches it off for
 * good. Under prefers-reduced-motion it holds still and never wanders.
 *
 * Ported from the prototype with two changes worth naming. It reads its
 * rows from whichever view is on screen rather than one hardcoded list, and
 * it hides outside the browse views, because walking along a form or a
 * chart would be noise.
 */

const PIX = `<svg viewBox="0 0 16 13" aria-hidden="true">
<g class="lgs"><rect class="bd l1" x="3" y="9" width="2" height="3"/><rect class="bd l2" x="6" y="9" width="2" height="3"/><rect class="bd l3" x="9" y="9" width="2" height="3"/><rect class="bd l4" x="12" y="9" width="2" height="3"/></g>
<g class="bod"><rect class="bd" x="2" y="1" width="12" height="8"/><rect class="bd" x="0" y="4" width="2" height="2"/><rect class="bd" x="14" y="4" width="2" height="2"/>
<g class="eyes"><g class="look">
<g data-e="n"><rect class="ey" x="5" y="3" width="2" height="2"/><rect class="ey" x="9" y="3" width="2" height="2"/></g>
<path data-e="h" class="ey" d="M5 3h1v1H5zM6 4h1v1H6zM5 5h1v1H5zM10 3h1v1h-1zM9 4h1v1H9zM10 5h1v1h-1z"/>
<path data-e="s" class="ey" d="M5 4h2v1H5zM9 4h2v1H9zM9 2h2v1H9z"/>
<path data-e="z" class="ey" d="M5 5h2v1H5zM9 5h2v1H9z"/>
<path data-e="w" class="ey" d="M5 3h2v3H5zM9 3h2v3H9z"/>
</g></g>
<g class="sh"><rect class="ey" x="3" y="3" width="10" height="2"/><path class="gl" d="M4 3h1v1H4zM9 3h1v1H9z"/></g></g>
<path class="ht" d="M7 -7h1v1H7zM9 -7h1v1H9zM6 -6h5v1H6zM7 -5h3v1H7zM8 -4h1v1H8z"/>
<g class="zs"><path class="zq" d="M12 0h3l-3 3h3"/></g>
</svg>`;

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const companion = (() => {
  const el = document.getElementById("critter");
  const page = document.querySelector(".page");

  if (!el || !page) return { show() {}, hide() {}, set on(_v) {} };

  el.innerHTML = PIX;

  const SPEED = 55;
  let x = 0, y = 0, timer = null, hovering = false;
  let anchor = 0.8, rowIndex = 2, pointerX = -1, pointerY = -1, on = true;

  /* Only rows currently on screen, so it never walks off toward something
   * the reader cannot see. */
  const rowsOnScreen = () =>
    [...document.querySelectorAll(".rows .row")].filter((row) => {
      const top = row.getBoundingClientRect().top;
      return top > 56 && top < window.innerHeight - 48;
    });

  const face = (expression) => { el.dataset.x = expression; };

  const pose = (cls, ms) => {
    el.classList.add(cls);
    setTimeout(() => el.classList.remove(cls), ms);
  };

  const place = (nx, ny, ms) => {
    el.style.transitionDuration = `${ms}ms`;
    el.style.transform = `translate(${nx}px, ${ny}px)`;
    x = nx;
    y = ny;
  };

  /* A spot along a row, as an offset from the .page box the creature is
   * positioned against. 0 is the left edge, 1 the right. */
  const spot = (row, fraction) => {
    const a = row.getBoundingClientRect();
    const p = page.getBoundingClientRect();

    return [
      a.left - p.left + 8 + fraction * Math.max(0, a.width - 80),
      a.top - p.top - 40,
    ];
  };

  const rest = () => {
    face("n");
    timer = setTimeout(wander, 900 + Math.random() * 1800);
  };

  function step(row, fraction, jump, done) {
    const [nx, ny] = spot(row, fraction);
    const ms = jump ? 520 : Math.max(400, (Math.abs(nx - x) / SPEED) * 1000);

    el.style.setProperty("--f", nx < x - 2 ? -1 : 1);

    if (jump) pose("jump", ms);
    else el.classList.add("walk");

    place(nx, ny, ms);
    anchor = fraction;

    timer = setTimeout(() => {
      el.classList.remove("walk");

      if (jump) {
        row.classList.add("bump");
        setTimeout(() => row.classList.remove("bump"), 300);
      }

      (done || rest)();
    }, ms + 30);
  }

  function wander() {
    clearTimeout(timer);

    if (hovering || !on || reducedMotion.matches) return;

    const rows = rowsOnScreen();

    if (!rows.length) {
      timer = setTimeout(wander, 1500);
      return;
    }

    const here = Math.max(
      0,
      rows.findIndex((r) => Math.abs(spot(r, 0)[1] - y) < 4),
    );
    rowIndex = here;

    const roll = Math.random();

    /* Mostly it drifts to a nearby row. Occasionally it jumps, sulks, or
     * falls asleep, which is what stops the movement reading as a loop. */
    if (roll < 0.45) {
      step(rows[here], Math.random());
    } else if (roll < 0.7) {
      const k = Math.min(
        rows.length - 1,
        Math.max(0, here + (Math.random() < 0.5 ? -1 : 1) *
          (1 + (Math.random() * 2 | 0))),
      );
      rowIndex = k;
      step(rows[k], Math.random(), true);
    } else if (roll < 0.82) {
      face("s");
      timer = setTimeout(() => { face("n"); wander(); }, 1800);
    } else if (roll < 0.9) {
      face("z");
      timer = setTimeout(() => {
        face("n");
        pose("jump", 420);
        timer = setTimeout(wander, 900);
      }, 4500);
    } else if (pointerX >= 0) {
      /* Go and look at wherever the pointer last was. */
      const row = rows.reduce((a, b) =>
        Math.abs(b.getBoundingClientRect().top - pointerY) <
        Math.abs(a.getBoundingClientRect().top - pointerY) ? b : a);
      const box = row.getBoundingClientRect();
      rowIndex = rows.indexOf(row);
      face("s");

      step(row, Math.min(1, Math.max(0, (pointerX - box.left) / box.width)),
        Math.abs(spot(row, 0)[1] - y) > 4,
        () => {
          face("h");
          pose("jump", 420);
          timer = setTimeout(rest, 1000);
        });
    } else {
      step(rows[here], Math.random());
    }
  }

  /* Stop dead where it is. Reading the running transform back is the only
   * way to know where a CSS transition actually got to. */
  function freeze() {
    clearTimeout(timer);
    const matrix = new DOMMatrix(getComputedStyle(el).transform);
    x = matrix.m41;
    y = matrix.m42;
    el.style.transitionDuration = "0ms";
    el.style.transform = `translate(${x}px, ${y}px)`;
    el.classList.remove("walk", "jump");
  }

  el.addEventListener("pointerenter", () => {
    hovering = true;
    freeze();
    face("h");
  });

  el.addEventListener("pointerleave", () => {
    hovering = false;
    face("n");
    timer = setTimeout(wander, 900);
  });

  el.addEventListener("click", () => {
    el.classList.toggle("cool");
    face("w");
    pose("jump", 420);
    setTimeout(() => face(hovering ? "h" : "n"), 380);
  });

  /* Pupils follow the pointer. One whole pixel of travel, so the face stays
   * on the grid it was drawn on. */
  window.addEventListener("pointermove", (event) => {
    pointerX = event.clientX;
    pointerY = event.clientY;
    if (reducedMotion.matches) return;

    const clamp = (v) => Math.max(-1, Math.min(1, Math.round(v / 90)));

    document.querySelectorAll(".cr").forEach((critter) => {
      const r = critter.getBoundingClientRect();
      critter.style.setProperty("--lx",
        clamp(event.clientX - (r.left + r.width / 2)));
      critter.style.setProperty("--ly",
        clamp(event.clientY - (r.top + r.height / 2)));
    });
  }, { passive: true });

  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) freeze();
    /* Held still while reduced motion is on, released when it is turned
     * off. Below, because it needs the object this returns. */
    else setTimeout(() => companion.show(), 0);
  });

  return {
    get on() { return on; },
    set on(value) {
      on = value;
      /* this.show / this.hide, not bare calls. show and hide exist only as
       * methods on the returned object, so a bare hide() resolves against
       * the enclosing IIFE scope, where there is no such function. */
      if (value) this.show();
      else this.hide();
    },

    hide() {
      clearTimeout(timer);
      el.hidden = true;
    },

    /* Called on every view change and every list render. Re-places the
     * creature against whatever rows exist now, which is the only way it
     * survives a re-render replacing the rows underneath it. */
    show() {
      clearTimeout(timer);

      const rows = on ? rowsOnScreen() : [];

      if (!rows.length) {
        el.hidden = true;
        return;
      }

      el.hidden = false;
      el.classList.remove("walk", "jump");

      const [nx, ny] = spot(rows[Math.min(rowIndex, rows.length - 1)], anchor);
      place(nx, ny, 0);

      timer = setTimeout(wander, 1200);
    },
  };
})();

/* The header control. State persists, because a reader who switches this
 * off once should not be asked again on every page load. */
const buddyButton = document.getElementById("buddy");
let buddyOn = true;

try {
  buddyOn = localStorage.getItem("meridian.buddy") !== "0";
} catch (error) {
  /* Private browsing with storage disabled. The default still applies. */
}

function applyBuddy() {
  buddyButton.setAttribute("aria-pressed", buddyOn ? "true" : "false");
  companion.on = buddyOn;
}

if (buddyButton) {
  applyBuddy();

  buddyButton.addEventListener("click", () => {
    buddyOn = !buddyOn;
    buddyButton.setAttribute("aria-pressed", buddyOn ? "true" : "false");
    companion.on = buddyOn;

    try {
      localStorage.setItem("meridian.buddy", buddyOn ? "1" : "0");
    } catch (error) {
      /* Nothing to do; the choice holds for this page only. */
    }
  });

  window.addEventListener("resize", () => companion.show());
}
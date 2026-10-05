/* Meridian frontend.
 *
 * Plain ES modules free browser API. No framework, no build step: a
 * bundler would be a large concept outside the lab boundary, and the
 * backend already serves plain JSON.
 *
 * Views are rendered from real API data. Every view has an empty,
 * loading, error and no-results state.
 */

const API = "";

/* state.view exists to answer one question the DOM cannot: did this call
 * change the view, or is it the first one? state.dataset names the cohort
 * currently on screen. Nothing else is kept here; the lists live in
 * lastResults, next to the view they belong to. */
const state = {
  view: null,
  dataset: null,
};

/* Guards the one-off re-measure after the webfont loads. */
let fontsSettled = false;

/* ----------------------------------------------------------------- dom */

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;

    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }

  for (const child of [].concat(children)) {
    if (child === null || child === undefined || child === false) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }

  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

/* ----------------------------------------------------------------- api */

async function api(path, options = {}) {
  let response;

  try {
    response = await fetch(API + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (cause) {
    throw new Error("Cannot reach the Meridian API. Is the server running?");
  }

  let payload = null;

  try {
    payload = await response.json();
  } catch {
    throw new Error(`The API returned a malformed response (HTTP ${response.status}).`);
  }

  if (!response.ok) {
    throw new Error(payload.error || `Request failed with HTTP ${response.status}.`);
  }

  return payload;
}

/* --------------------------------------------------------------- states */

function skeletonRows(count = 4) {
  return el("div", {}, Array.from({ length: count }, () =>
    el("div", { class: "skeleton" }, [
      el("div", { class: "skeleton__bar skeleton__bar--title" }),
      el("div", { class: "skeleton__bar skeleton__bar--meta skeleton__bar--fill" }),
    ])
  ));
}

function emptyState({ title, body, action, art = "search", role = "status" }) {
  // Line art drawn from the same geometry as the interface: a list of
  // reported symptoms being matched against a reference set. One accent
  // detail, everything else neutral.
  const art_ = art === "search"
    ? el("svg", { class: "empty-art", viewBox: "0 0 96 72", width: "104",
                  height: "78", "aria-hidden": "true" }, [
        el("path", { class: "draw", pathLength: "1",
                     d: "M24 14h30M24 26h30M24 38h22" }),
        el("path", { class: "draw draw--2", pathLength: "1",
                     d: "M62 14h10M62 26h10M62 38h10" }),
        el("path", { class: "draw draw--3", pathLength: "1",
                     d: "M18 52h60M18 52l8 8M78 52l-8 8",
                     stroke: "var(--accent)" }),
      ])
    : el("svg", { class: "empty-art", viewBox: "0 0 96 72", width: "104",
                  height: "78", "aria-hidden": "true" }, [
        el("rect", { class: "draw", pathLength: "1", x: "20", y: "12",
                     width: "56", height: "46", rx: "4" }),
        el("path", { class: "draw draw--2", pathLength: "1",
                     d: "M20 26h56M32 38h32M32 47h20" }),
      ]);

  return el("div", { class: "state", role }, [
    art_,
    el("h2", { class: "state__title", text: title }),
    el("p", { class: "state__body", text: body }),
    action ? el("div", { class: "state__action" }, action) : null,
  ]);
}

function errorState(message, retry) {
  return emptyState({
    role: "alert",
    title: "Could not load this",
    body: message,
    action: retry ? el("button", { class: "btn btn--secondary",
                                   onclick: retry }, "Retry") : null,
  });
}

/* ------------------------------------------------------------ formatting */

/* A titled grid of record fields. Fields whose value is a sentence rather
 * than a figure are marked so they get the full width instead of being
 * split across a column gap. */
const WIDE_FACTS = new Set(["Address", "Notes", "Availability", "Languages"]);

function factGrid(caption, pairs) {
  return el("div", {}, [
    el("p", { class: "section-label", text: caption }),
    el("div", { class: "facts" }, pairs.map(([label, value]) =>
      el("div", { class: WIDE_FACTS.has(label) ? "fact fact--wide" : "fact" }, [
        el("p", { class: "fact__label", text: label }),
        el("p", { class: "fact__value", text: String(value) }),
      ])
    )),
  ]);
}

function formatDate(value) {
  if (!value) return "";
  const parts = value.split("-");
  if (parts.length !== 3) return value;
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[Number(parts[1]) - 1] || parts[1];
  return `${Number(parts[2])} ${month} ${parts[0]}`;
}

function orDash(value) {
  return value && value.trim() ? value : "—";
}

function severityClass(severity) {
  const value = (severity || "").toLowerCase();
  if (value === "severe") return "sev sev--severe";
  if (value === "high") return "sev sev--high";
  return "sev sev--quiet";
}

/* A score of zero means the condition explains none of what was reported,
 * which is a different statement from "low probability". Showing 0% next
 * to a name implies a measurement; it is actually an absence of evidence.
 * The engine already carries the evidence label, so the UI states it. */
function scoreClass(result) {
  return result.percent === 0 ? "rank__item-score rank__item-score--none" : "rank__item-score";
}

/* --------------------------------------------------------------- triage */

const triageForm = document.getElementById("triage-form");
const triageResults = document.getElementById("triage-results");
const triageSubmit = document.getElementById("triage-submit");

triageForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const symptoms = document.getElementById("triage-symptoms").value;
  const conditions = document.getElementById("triage-conditions").value;

  if (!symptoms.trim()) {
    clear(triageResults);
    triageResults.appendChild(emptyState({
      title: "No symptoms entered",
      body: "List at least one symptom so there is something to match against.",
    }));
    document.getElementById("triage-symptoms").focus();
    return;
  }

  triageSubmit.disabled = true;
  clear(triageResults);
  triageResults.appendChild(skeletonRows(3));

  try {
    const data = await api("/api/triage", {
      method: "POST",
      body: JSON.stringify({ symptoms, conditions }),
    });
    renderTriage(data);
  } catch (error) {
    clear(triageResults);
    triageResults.appendChild(errorState(error.message, () => triageForm.requestSubmit()));
  } finally {
    triageSubmit.disabled = false;
  }
});

function renderTriage(data) {
  clear(triageResults);

  if (!data.results.length) {
    triageResults.appendChild(emptyState({
      title: "Nothing matched",
      body: "No condition in the knowledge base shares at least two symptoms " +
            "with this report. Try fewer, more specific symptoms.",
    }));
    return;
  }

  const [lead, ...rest] = data.results;

  /* Medication is prose, not data, so it is deliberately not set in the
   * mono face. Only figures and record ids are. */
  const leadFacts = el("div", { class: "rank__facts" }, [
    el("span", { class: severityClass(lead.severity), text: lead.severity }),
    el("span", {}, [lead.medication, " ", lead.dosage]),
  ]);

  const block = [el("p", { class: "section-label", text: "Most likely" })];

  /* A zero score is an absence of evidence, not a measurement of zero
   * probability. Showing it in the focal position as "0%" would read as
   * a confident measurement of nothing, so it is stated in words. */
  const leadScore = lead.percent === 0
    ? el("p", { class: "rank__score rank__score--none", text: "No match" })
    : el("p", { class: "rank__score", text: `${lead.percent}%` });

  block.push(el("div", { class: "rank__lead" }, [
    el("div", { class: "rank__lead-top" }, [
      el("div", {}, [
        el("h2", { class: "rank__name", text: lead.name }),
        el("p", { class: "evidence",
                  text: `${lead.evidence} evidence · ` +
                        `${lead.matched_count} of ${lead.total_symptoms} symptoms matched` }),
      ]),
      leadScore,
    ]),
    leadFacts,
    lead.age_outside_range
      ? el("p", { class: "note",
                  text: `Usually affects ages ${lead.age_range}.` })
      : null,
    lead.warnings.length
      ? el("div", { class: "warn" }, lead.warnings.map(
          (w) => el("p", { text: w })))
      : null,
  ]));

  // Only rendered when there is something to put in it. An empty bordered
  // row leaves two orphan hairlines on screen.
  if (rest.length) {
    // A condition scoring zero is separated out. It is not a weak
    // candidate, it is one that explains none of the report, and listing
    // it inline implies a near miss rather than a non-match.
    const meaningful = rest.filter((r) => r.percent > 0);
    const noMatch = rest.filter((r) => r.percent === 0);

    // A lower score can sit above a higher one: conditions within a narrow
    // band are treated as tied and severity decides. Without saying so,
    // the list reads as mis-sorted.
    const inversions = [];
    for (let i = 0; i < meaningful.length; i += 1) {
      const above = lead;
      const item = meaningful[i];
      if (item.score > above.score) {
        inversions.push({ higher: item, lower: above });
      }
    }

    if (inversions.length) {
      const { higher, lower } = inversions[0];
      block.push(el("p", { class: "note note--quiet",
        text: `${higher.name} scores ${higher.percent}% against ` +
              `${lower.name} at ${lower.percent}%. Conditions within a narrow ` +
              `margin are treated as tied, and severity decides between them.` }));
    }

    if (meaningful.length) {
      block.push(el("p", { class: "section-label section-label--spaced",
                            text: "Also considered" }));
      block.push(el("div", { class: "rank__rest" }, meaningful.map((item) =>
        el("div", { class: "rank__item" }, [
          el("div", { class: "rank__item-top" }, [
            el("p", { class: "rank__item-name", text: item.name }),
            el("p", { class: scoreClass(item), text: `${item.percent}%` }),
          ]),
          el("p", { class: "evidence",
                    text: `${item.evidence} evidence · ` +
                          `${item.matched_count} of ${item.total_symptoms} matched` }),
          el("div", { class: "rank__facts" }, [
            el("span", { class: severityClass(item.severity), text: item.severity }),
            el("span", { text: item.medication }),
          ]),
          item.warnings.length
            ? el("div", { class: "warn" }, item.warnings.map(
                (w) => el("p", { text: w })))
            : null,
        ])
      )));
    }

    if (noMatch.length) {
      block.push(el("p", { class: "section-label section-label--spaced",
                            text: "Explains none of the report" }));

      block.push(el("ul", { class: "nonmatch" }, noMatch.map((item) =>
        el("li", { class: "nonmatch__item" }, [
          el("span", { text: item.name }),
          el("span", { class: "nonmatch__why",
                       text: item.unexplained_symptoms.length
                         ? `${item.unexplained_symptoms.join(", ")} not accounted for`
                         : "no shared symptoms" }),
        ])
      )));
    }
  }

  block.push(el("p", { class: "disclaimer",
    text: "Not a diagnosis. Triage guidance only. Verify with a clinician." }));

  triageResults.appendChild(el("div", { class: "rank" }, block));
}

/* ------------------------------------------------------- search helpers */

/* One entry per searchable registry, and the only place that knows how a
 * view is wired.
 *
 * The element ids are written out rather than built from the view name.
 * Building them, as "doctors" + "-search", produces doctors-search while
 * the markup says doctor-search, and the mismatch is invisible until
 * getElementById returns null and a whole view silently stops working.
 * Spelling them out here means a rename shows up as a missing id in one
 * table instead of a null dereference somewhere else. */
const SEARCH_VIEWS = {
  patients: {
    noun: "patients",
    endpoint: "/api/search/patients",
    searchId: "patient-search",
    containerId: "patient-results",
    label: "patient",
  },
  hospitals: {
    noun: "hospitals",
    endpoint: "/api/search/hospitals",
    searchId: "hospital-search",
    containerId: "hospital-results",
    label: "hospital",
  },
  doctors: {
    noun: "doctors",
    endpoint: "/api/search/doctors",
    searchId: "doctor-search",
    containerId: "doctor-results",
    label: "doctor",
  },
  medicines: {
    noun: "medicines",
    endpoint: "/api/search/medicines",
    searchId: "medicine-search",
    containerId: "medicine-results",
    label: "medicine",
  },
  stores: {
    noun: "stores",
    endpoint: "/api/search/stores",
    searchId: "store-search",
    containerId: "store-results",
    label: "store",
  },
  rare_conditions: {
    noun: "rare conditions",
    endpoint: "/api/search/rare_conditions",
    searchId: "rare-search",
    containerId: "rare-results",
    label: "condition",
  },
};

/* Each search view remembers its last query and its last results, so
 * opening a record and coming back does not lose the list. Without this
 * the detail view is a dead end. */
const lastResults = {};

/* Renderers for the list views, looked up by view name. Assigned once the
 * renderers are defined, further down. */
const ROW_RENDERERS = {};

/* One detail view is open at a time. */
let openDetail = null;

/* Every detail load takes a ticket. Backing out, or opening another
 * record, invalidates the ones in flight, so a slow response cannot
 * replace a screen the reader has already navigated away from. */
let detailTicket = 0;

/* Looking up a view's elements is the one place a typo becomes a dead
 * screen rather than a visible error, so a miss throws with the name of
 * the view instead of returning null and failing later somewhere else. */
function viewContainer(name) {
  const node = document.getElementById(SEARCH_VIEWS[name].containerId);
  if (!node) throw new Error(`no results container for the ${name} view`);
  return node;
}

function viewSearchInput(name) {
  const node = document.getElementById(SEARCH_VIEWS[name].searchId);
  if (!node) throw new Error(`no search input for the ${name} view`);
  return node;
}

function backLink() {
  return el("button", {
    class: "back", type: "button", onclick: () => closeDetail(),
  }, [
    el("span", { class: "back__mark", "aria-hidden": "true", text: "\u2190" }),
    el("span", { text: "Back to list" }),
  ]);
}

function closeDetail({ restoreFocus = true } = {}) {
  if (!openDetail) return;

  const name = openDetail;
  openDetail = null;
  detailTicket += 1;

  clear(viewContainer(name));

  /* Restore the rare registry summary on the way out, because
   * detailShell hid it. Done here rather than at each call site so there
   * is one place that knows the overview belongs to the list, not to a
   * record. */
  if (name === "rare_conditions") {
    const overview = document.getElementById("rare-overview");
    if (overview) overview.hidden = false;
  }

  const stored = lastResults[name];

  if (stored && stored.rows.length) renderList(stored.rows, name);
  else if (BROWSE_VIEWS[name]) renderBrowse(name);
  else showPrompt(name);

  if (restoreFocus) viewSearchInput(name)?.focus();
}

/* Replace a search view's contents with a detail screen.
 *
 * The heading takes focus so a keyboard or screen reader user lands on the
 * record they just opened rather than being left where the list used to
 * be. tabindex="-1" makes a heading focusable without adding it to the
 * tab order, so Tab from here still reaches the content below. */
function detailShell({ name, title, lead, children }) {
  const container = viewContainer(name);

  clear(container);
  openDetail = name;

  /* The rare overview is a summary of the registry. Once a single record
   * is open it is stale context sitting above the thing being read, and it
   * pushes the record off the screen. */
  if (name === "rare_conditions") {
    const overview = document.getElementById("rare-overview");
    if (overview) overview.hidden = true;
  }

  const heading = el("h2", { class: "page__title", tabindex: "-1", text: title });

  container.appendChild(el("div", {}, [
    backLink(),
    el("div", { class: "page__head page__head--detail" }, [
      heading,
      el("p", { class: "page__lead", text: lead }),
    ]),
    ...[].concat(children),
  ]));

  heading.focus();
}

function renderList(rows, name) {
  const container = viewContainer(name);
  clear(container);
  container.appendChild(el("div", { class: "rows" }, rows.map(ROW_RENDERERS[name])));
}

function showPrompt(name) {
  const container = viewContainer(name);
  const stored = lastResults[name];

  // The rare registry opens on an overview that already says what is in
  // it. Adding "No search yet" underneath tells the reader to do the one
  // thing they do not need to do.
  if (name === "rare_conditions" && document.getElementById("rare-overview")
      ?.dataset.loaded === "yes") {
    return;
  }

  clear(container);
  container.appendChild(emptyState({
    title: "No search yet",
    body: `Type a name, place or category to search ${SEARCH_VIEWS[name].noun}.` +
          (stored && stored.query ? ` Last search was “${stored.query}”.` : ""),
  }));
}

function searchView(name) {
  const config = SEARCH_VIEWS[name];
  const input = viewSearchInput(name);
  const container = viewContainer(name);
  let timer = null;
  // Each load gets a ticket. A slow response belonging to an abandoned
  // query must not overwrite the results of the query that replaced it.
  let ticket = 0;

  async function load(query) {
    if (!query.trim()) {
      lastResults[name] = { query: "", rows: [] };
      openDetail = null;

      /* A blank search box is not an empty state, it is the browse list.
       * The rare registry has its own overview and is left alone. */
      if (BROWSE_VIEWS[name]) renderBrowse(name);
      else showPrompt(name);
      return;
    }

    const mine = (ticket += 1);

    clear(container);
    container.appendChild(skeletonRows(4));

    try {
      const data = await api(`${config.endpoint}?q=${encodeURIComponent(query)}`);
      if (mine !== ticket) return;

      clear(container);
      openDetail = null;
      lastResults[name] = { query, rows: data.results };

      if (!data.count) {
        container.appendChild(emptyState({
          title: `No ${config.noun} matched`,
          body: `Nothing in the registry matches “${query}”. ` +
                `Try a shorter or more general term.`,
        }));
        return;
      }

      renderList(data.results, name);

      /* The rare registry matches thousands of rows to one word. Capping
       * the page without saying so would make a truncated list look
       * complete, so the true total is stated above it. */
      if (data.truncated) {
        container.appendChild(el("p", { class: "result-note" },
          `Showing the top ${data.count} of ${data.total_matched.toLocaleString()} ` +
          `matches. Narrow the search to see fewer.`));
      }
    } catch (error) {
      if (mine !== ticket) return;
      clear(container);
      container.appendChild(errorState(error.message, () => load(query)));
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => load(input.value.trim()), 220);
  });

  /* Escape backs out of a record. It has to clear any pending debounce
   * first, otherwise the keystroke also fires the search that is waiting
   * to run and the detail closes into a fresh list. */
  input.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !openDetail) return;
    clearTimeout(timer);
    event.preventDefault();
    closeDetail();
  });

  if (BROWSE_VIEWS[name]) renderBrowse(name);
  else showPrompt(name);

  load(input.value.trim());
}

/* ================================================================ browse
 *
 * A registry view used to render a search box and an invitation to type.
 * That was correct for eight patients and useless for six hundred, because
 * a reader who opens "Patients" is asking what is in there, not already
 * knowing a name to type.
 *
 * So each registry view now opens on the records themselves, with the
 * facets that matter as underlined tabs and a stated page range. Search is
 * unchanged and still refines whatever is on screen; clearing the field
 * returns to the browse list rather than to an empty prompt.
 *
 * One generic component drives all five views. A registry differs only in
 * its endpoint, its row renderer and its facets, and those three already
 * existed, so five bespoke implementations would be five places for the
 * same pagination bug to hide.
 */

const BROWSE_VIEWS = {
  patients: { endpoint: "/api/patients", limit: 50 },
  hospitals: { endpoint: "/api/hospitals", limit: 50 },
  doctors: { endpoint: "/api/doctors", limit: 50 },
  medicines: { endpoint: "/api/medicines", limit: 50 },
  stores: { endpoint: "/api/stores", limit: 50 },
};

/* Per-view browse state. Remembers the facet and the page so that opening a
 * record and coming back does not reset the reader to the top. */
const browseState = {};

function browseFor(name) {
  if (browseState[name]) return browseState[name];

  const state = { flag: "", offset: 0, ticket: 0, facets: [], total: 0 };
  browseState[name] = state;

  return state;
}

function facetUrl(name, state) {
  const { endpoint, limit } = BROWSE_VIEWS[name];
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(state.offset),
  });

  if (state.flag) query.set("flag", state.flag);

  return `${endpoint}?${query.toString()}`;
}

function browseCountLine(name, data, state) {
  const { noun } = SEARCH_VIEWS[name];
  const one = noun.replace(/s$/, "");

  if (state.flag) {
    const facet = state.facets.find((f) => f.flag === state.flag);
    const what = facet ? facet.label.toLowerCase() : state.flag;

    return data.total === 1
      ? `1 ${one} matches ${what}`
      : `${data.total.toLocaleString()} ${noun} match ${what}`;
  }

  return data.total === 1
    ? `1 ${one} on file`
    : `${data.total.toLocaleString()} ${noun} on file`;
}

function facetTabs(name, state, onPick) {
  const strip = el("div", {
    class: "tabs tabs--facets",
    role: "tablist",
    "aria-label": `Filter ${SEARCH_VIEWS[name].noun}`,
  });

  const all = el("button", {
    class: "tabs__btn",
    type: "button",
    role: "tab",
    "aria-selected": state.flag ? "false" : "true",
  }, [
    "All",
    el("span", { class: "tabs__count" }, state.total.toLocaleString()),
  ]);

  all.addEventListener("click", () => onPick(""));
  strip.appendChild(all);

  for (const facet of state.facets) {
    const active = state.flag === facet.flag;
    const empty = facet.count === 0 && !active;

    const button = el("button", {
      class: "tabs__btn",
      type: "button",
      role: "tab",
      "aria-selected": active ? "true" : "false",
      "aria-disabled": empty ? "true" : "false",
      title: facet.note,
    }, [
      facet.label,
      el("span", { class: "tabs__count" }, facet.count.toLocaleString()),
    ]);

    /* A facet with nothing in it is still worth showing, because "none are
     * missing a blood group" is an answer. It just is not clickable. */
    if (!empty) button.addEventListener("click", () => onPick(facet.flag));

    strip.appendChild(button);
  }

  return strip;
}

function buildPager(name, state, data, onGo) {
  const { limit } = BROWSE_VIEWS[name];
  const first = data.total === 0 ? 0 : state.offset + 1;
  const last = Math.min(state.offset + data.count, data.total);

  const prev = el("button", { class: "pager__btn", type: "button" }, "Previous");
  const next = el("button", { class: "pager__btn", type: "button" }, "Next");

  prev.disabled = state.offset === 0;
  next.disabled = !data.has_more;

  prev.addEventListener("click", () => onGo(-limit));
  next.addEventListener("click", () => onGo(limit));

  return el("div", { class: "pager" }, [
    el("span", { class: "pager__status data" },
      `${first.toLocaleString()}–${last.toLocaleString()} of ` +
      `${data.total.toLocaleString()}`),
    el("div", { class: "pager__nav" }, [prev, next]),
  ]);
}

/* Draw the browse list into a view's results container. */
async function renderBrowse(name) {
  const container = viewContainer(name);
  const state = browseFor(name);

  const mine = (state.ticket += 1);

  clear(container);
  container.appendChild(skeletonRows(6));

  try {
    const data = await api(facetUrl(name, state));
    if (mine !== state.ticket) return;

    state.facets = data.facets || [];
    state.total = data.total;

    clear(container);
    openDetail = null;

    const rows = data[name] || [];

    if (!rows.length) {
      /* Reachable when a page offset falls past the end, which is what a
       * reader on page 9 sees if records are deleted underneath them. The
       * action gets them back rather than leaving a dead end. */
      const past = state.offset > 0;

      container.appendChild(emptyState({
        title: past ? "Nothing on this page" : "No records here",
        body: past
          ? "This page is past the end of the list. Go back to see the records."
          : `No ${SEARCH_VIEWS[name].noun} match this filter.`,
        action: past
          ? {
              label: "Back to first page",
              run: () => {
                state.offset = 0;
                renderBrowse(name);
              },
            }
          : null,
      }));
      return;
    }

    const wrap = el("div", { class: "browse" });

    wrap.appendChild(el("div", { class: "browse__bar" }, [
      el("p", { class: "browse__count" }, browseCountLine(name, data, state)),
      facetTabs(name, state, (flag) => {
        if (state.flag === flag) return;
        state.flag = flag;
        state.offset = 0;
        renderBrowse(name);
      }),
    ]));

    wrap.appendChild(el("div", { class: "rows" }, rows.map(ROW_RENDERERS[name])));

    wrap.appendChild(buildPager(name, state, data, (delta) => {
      state.offset = Math.max(0, state.offset + delta);
      renderBrowse(name);
      window.scrollTo(0, 0);
    }));

    container.appendChild(wrap);

    /* New rows, new geometry. */
    if (typeof companion !== "undefined") {
      requestAnimationFrame(() => companion.show());
    }
  } catch (error) {
    if (mine !== state.ticket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => renderBrowse(name)));
  }
}/* ------------------------------------------------------------- patients */

function patientRow(p) {
  const seen = Number.isInteger(p.visit_count) ? p.visit_count : null;
  const never = seen === 0;
  const child = p.age !== "" && Number(p.age) < 18;

  const meta = [p.age ? `age ${p.age}` : "", p.gender,
                p.blood_group || "blood group not recorded",
                p.area]
    .filter(Boolean).join(", ");

  /* The rail marks the one thing on this record that is outstanding: a
   * patient who registered and never came back. A child is not flagged,
   * because being under 18 is not a problem to action, it is who they are.
   * The same fact is written in the trailing meta, so the colour is never
   * the only thing carrying it. */
  const classes = ["row"];

  if (never) classes.push("row--flagged");

  const trailing = never
    ? [el("span", { class: "row__trailing-note", text: "no consultation" }),
       el("span", { class: "data row__sub", text: p.patient_id })]
    : [
        el("span", { class: "row__trailing-note" },
          seen === null ? "" : `${seen} consultation${seen === 1 ? "" : "s"}`),
        el("span", { class: "data row__sub", text: p.patient_id }),
      ];

  return el("button", { class: classes.join(" "), onclick: () => showPatient(p) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: p.name }),
      el("span", { class: "row__meta", text: meta }),
      child ? el("span", { class: "flag" }, "Recorded with a guardian") : null,
    ].filter(Boolean)),
    el("span", { class: "row__trailing" }, trailing),
  ]);
}

function vitalsLine(v) {
  const parts = [];

  if (v.vitals_bp) parts.push(`BP ${v.vitals_bp}`);
  if (v.vitals_pulse) parts.push(`pulse ${v.vitals_pulse}`);
  if (v.vitals_temp) parts.push(`temp ${v.vitals_temp}`);
  if (v.vitals_spo2) parts.push(`SpO2 ${v.vitals_spo2}%`);

  const weight = weightFor(v);
  if (weight) parts.push(weight);

  return parts.join(", ");
}

function weightFor(v) {
  if (!v.vitals_weight) return "";
  if (!v.vitals_height) return `${v.vitals_weight} kg`;

  const height = Number(v.vitals_height) / 100;
  if (!height) return `${v.vitals_weight} kg`;

  const bmi = Number(v.vitals_weight) / (height * height);
  return `${v.vitals_weight} kg · BMI ${bmi.toFixed(1)}`;
}

function visitCard(v) {
  const facts = [
    el("span", { class: severityClass(v.severity), text: v.severity || "" }),
    el("span", { class: "data", text: v.status || "" }),
    el("span", { text: v.duration_minutes ? `${v.duration_minutes} min` : "" }),
  ].filter((n) => n.textContent.trim());

  return el("article", { class: "visit" }, [
    el("div", { class: "visit__head" }, [
      el("div", {}, [
        el("h3", { class: "visit__title",
                   text: v.diagnosis || "No diagnosis recorded" }),
        el("p", { class: "visit__reason", text: v.reason || "" }),
      ]),
      el("div", { class: "visit__when" }, [
        el("p", { class: "visit__date data", text: formatDate(v.scheduled_date) }),
        el("p", { class: "visit__time data", text: v.scheduled_time || "" }),
      ]),
    ]),

    el("div", { class: "visit__who" }, [
      el("p", { class: "visit__doctor" },
        [v.doctor?.name || "Doctor not recorded"]),
      el("p", { class: "visit__where",
                text: [v.doctor?.specialisation, v.hospital?.name]
                        .filter(Boolean).join(", ") }),
      el("p", { class: "visit__meta",
                text: [v.doctor?.department && `${v.doctor.department}, room ${v.doctor.room_no}`,
                       v.hospital?.area].filter(Boolean).join(", ") }),
    ]),

    v.symptoms
      ? el("p", { class: "visit__symptoms",
                  text: v.symptoms.split("|").join(", ") })
      : null,

    vitalsLine(v)
      ? el("div", { class: "visit__vitals" }, [
          el("span", { class: "visit__vitals-label", text: "Vitals" }),
          el("span", { class: "data", text: vitalsLine(v) }),
        ])
      : null,

    el("div", { class: "visit__facts" }, facts),

    v.notes ? el("p", { class: "visit__notes", text: v.notes }) : null,
  ]);
}

async function showPatient(p) {
  const mine = (detailTicket += 1);
  const container = viewContainer("patients");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/patients/${p.patient_id}`);
    if (mine !== detailTicket) return;
    const who = data.patient;

    const contact = [
      ["Registered", formatDate(who.registered_on)],
      ["Phone", who.phone ? `+91 ${who.phone}` : ""],
      ["Email", who.email],
      ["Blood group", who.blood_group || "not recorded"],
      ["Area", [who.area, who.pincode].filter(Boolean).join(" ")],
      ["City", [who.city, who.state].filter(Boolean).join(", ")],
      ["Emergency", who.emergency_contact
        ? `${who.emergency_contact}${who.emergency_phone ? `, +91 ${who.emergency_phone}` : ""}`
        : ""],
      ["Address", who.address_line],
      ["Notes", who.notes],
    ].filter(([, value]) => value);

    /* Address and notes span both columns: each is a single sentence that
     * does not survive being split across a gap. */
    const wide = new Set(["Address", "Notes"]);

    detailShell({
      name: "patients",
      title: who.name,
      lead: [who.patient_id,
             who.age ? `age ${who.age}` : "",
             who.gender,
             who.blood_group ? `${who.blood_group}` : ""]
             .filter(Boolean).join(", "),
      children: [
        el("div", { class: "detail-grid" }, [
          el("div", {}, [
            el("p", { class: "section-label", text: "Record" }),
            el("div", { class: "facts" }, contact.map(([label, value]) =>
              el("div", { class: wide.has(label) ? "fact fact--wide" : "fact" }, [
                el("p", { class: "fact__label", text: label }),
                el("p", { class: "fact__value", text: value }),
              ])
            )),
          ]),

          el("div", { class: "card" }, [
            el("p", { class: "section-label", text: "At a glance" }),
            el("div", { class: "glance" }, [
              ["Consultations", data.visit_count],
              ["Doctors seen", new Set(data.visits.map((v) => v.doctor_id)).size],
              ["Hospitals", new Set(data.visits.map((v) => v.hospital_id)).size],
              ["Still active", data.visits.filter((v) => v.status === "Active").length],
              ["Follow-ups due", data.visits.filter((v) => v.follow_up_days !== "").length],
            ].map(([label, value]) =>
              el("div", { class: "glance__row" }, [
                el("span", { class: "glance__label", text: label }),
                el("span", { class: "glance__value", text: String(value) }),
              ])
            )),
          ]),
        ]),

        el("p", { class: "section-label section-label--spaced",
                  text: "Consultation history" }),

        data.visits.length
          ? el("div", { class: "visits" }, data.visits.map(visitCard))
          : emptyState({
              title: "No consultations yet",
              body: "This patient has no visits on file. Search another name, " +
                    "or add a visit through the API.",
              art: "doc",
            }),
      ],
    });
  } catch (error) {
    if (mine !== detailTicket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => showPatient(p)));
  }
}

/* ------------------------------------------------------------ medicines */

function medicineRow(m) {
  const flags = [m.otc === "yes" ? "Over the counter" : "",
                 m.rx_required === "yes" ? "Prescription required" : ""]
    .filter(Boolean).join(", ");

  const price = m.price ? `₹${m.price}` : "";

  return el("button", { class: "row", onclick: () => showMedicine(m) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: m.name }),
      el("span", { class: "row__meta",
                   text: [m.generic, m.category, flags].filter(Boolean).join(", ") }),
    ]),
    el("span", { class: "row__trailing" }, [
      el("span", { class: "data", text: price }),
    ]),
  ]);
}

async function showMedicine(m) {
  const mine = (detailTicket += 1);
  const container = viewContainer("medicines");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/medicines/${m.medicine_id}`);
    if (mine !== detailTicket) return;
    const med = data.medicine;

    const facts = [
      ["Generic", med.generic],
      ["Category", med.category],
      ["Form", med.form],
      ["Strength", med.strength],
      ["Storage", med.storage],
      ["Manufacturer", med.manufacturer],
      ["Supply", med.rx_required === "yes"
        ? "Prescription required" : "Over the counter"],
      ["Price", med.price ? `₹${med.price}` : ""],
    ].filter(([, value]) => value);

    detailShell({
      name: "medicines",
      title: med.name,
      lead: [med.generic, med.category, med.strength].filter(Boolean).join(", "),
      children: [
        el("div", { class: "detail-grid" }, [
          factGrid("Catalogue entry", facts),
          el("div", { class: "card stock-card" }, [
            el("p", { class: "section-label", text: "Availability" }),
            el("p", { class: "stock-card__count data",
                      text: String(data.stocked_by.length) }),
            el("p", { class: "stock-card__unit",
                      text: data.stocked_by.length === 1
                        ? "store stocks this" : "stores stock this" }),
          ]),
        ]),

        el("p", { class: "section-label section-label--spaced",
                  text: "Stocked by" }),

        data.stocked_by.length
          ? el("div", { class: "rows" }, data.stocked_by.map((s) =>
              el("div", { class: "row row--static" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: s.name }),
                  el("span", { class: "row__meta",
                               text: [s.area, s.city, s.hours, s.phone && `+91 ${s.phone}`]
                                     .filter(Boolean).join(", ") }),
                ]),
                el("span", { class: "row__trailing data", text: s.store_id }),
              ])
            ))
          : emptyState({
              title: "No store records this",
              body: "No store in the registry lists this medicine in its " +
                    "recorded stock. That is an absence of data, not proof " +
                    "that no pharmacy nearby has it.",
            }),
      ],
    });
  } catch (error) {
    if (mine !== detailTicket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => showMedicine(m)));
  }
}

/* --------------------------------------------------------------- stores */

function storeRow(s) {
  const count = s.stock_csv ? s.stock_csv.split("|").length : 0;

  /* No stock on file is the same class of problem as a patient with no
   * consultation: the record exists but the useful part is missing. */
  const classes = count ? ["row"] : ["row", "row--flagged"];

  return el("button", { class: classes.join(" "), onclick: () => showStore(s) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: s.name }),
      el("span", { class: "row__meta",
                   text: [s.type, s.area, s.city, s.hours].filter(Boolean).join(", ") }),
    ]),
    el("span", { class: "row__trailing" }, [
      el("span", { class: count ? "data" : "row__trailing-note",
                   text: count ? `${count} stocked` : "stock not recorded" }),
    ]),
  ]);
}

async function showStore(s) {
  const mine = (detailTicket += 1);
  const container = viewContainer("stores");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/stores/${s.store_id}`);
    if (mine !== detailTicket) return;
    const store = data.store;

    const facts = [
      ["Type", store.type],
      ["Area", store.area],
      ["City", store.city],
      ["Phone", store.phone ? `+91 ${store.phone}` : ""],
      ["Hours", store.hours],
      ["Rating", store.rating],
    ].filter(([, value]) => value);

    const held = new Set((store.stock_csv || "").split("|").filter(Boolean));
    const known = data.medicines.length;

    detailShell({
      name: "stores",
      title: store.name,
      lead: [store.type, store.area, store.city].filter(Boolean).join(", "),
      children: [
        el("div", { class: "detail-grid" }, [
          factGrid("Store", facts),
          el("div", { class: "card stock-card" }, [
            el("p", { class: "section-label", text: "Recorded stock" }),
            el("p", { class: "stock-card__count data", text: String(known) }),
            el("p", { class: "stock-card__unit",
                      text: known === 1 ? "medicine listed" : "medicines listed" }),
          ]),
        ]),

        el("p", { class: "section-label section-label--spaced",
                  text: "Medicines listed" }),

        data.medicines.length
          ? el("div", { class: "rows" }, data.medicines.map((m) =>
              el("div", { class: "row row--static" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: m.name }),
                  el("span", { class: "row__meta",
                               text: [m.generic, m.category, m.strength]
                                     .filter(Boolean).join(", ") }),
                ]),
                el("span", { class: "row__trailing data",
                             text: m.price ? `₹${m.price}` : "" }),
              ])
            ))
          : emptyState({
              title: "Stock not recorded",
              body: "This store has no stock recorded. That is an absence of " +
                    "data, not an empty shelf.",
              art: "doc",
            }),
      ],
    });
  } catch (error) {
    if (mine !== detailTicket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => showStore(s)));
  }
}

/* ------------------------------------------------------------ hospitals */

function hospitalRow(h) {
  return el("button", { class: "row", onclick: () => showHospital(h) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: h.name }),
      el("span", { class: "row__meta",
                   text: [h.type, h.area, h.city,
                          h.beds ? `${h.beds} beds` : ""].filter(Boolean).join(", ") }),
    ]),
    el("span", { class: "row__trailing data", text: h.hospital_id }),
  ]);
}

async function showHospital(h) {
  const mine = (detailTicket += 1);
  const container = viewContainer("hospitals");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/hospitals/${h.hospital_id}`);
    if (mine !== detailTicket) return;
    const hosp = data.hospital;

    const facts = [
      ["Type", hosp.type],
      ["Address", hosp.address_line],
      ["Area", hosp.area],
      ["City", [hosp.city, hosp.state].filter(Boolean).join(", ")],
      ["PIN", hosp.pincode],
      ["Phone", hosp.phone ? `+91 ${hosp.phone}` : ""],
      ["Beds", hosp.beds],
      ["Established", hosp.established_year],
      ["Accreditation", hosp.accreditation && hosp.accreditation !== "none"
        ? hosp.accreditation.toUpperCase() : ""],
    ].filter(([, value]) => value && String(value).trim());

    detailShell({
      name: "hospitals",
      title: hosp.name,
      lead: [hosp.type, hosp.area, hosp.city].filter(Boolean).join(", "),
      children: [
        factGrid("Hospital", facts),

        el("p", { class: "section-label section-label--spaced",
                  text: `Doctors practising here (${data.doctors.length})` }),

        data.doctors.length
          ? el("div", { class: "rows" }, data.doctors.map((d) =>
              el("div", { class: "row row--static" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: d.name }),
                  el("span", { class: "row__meta",
                               text: [d.specialisation, d.qualification,
                                      `room ${d.room_no}`].filter(Boolean).join(", ") }),
                  el("span", { class: "row__sub",
                               text: d.availability || "" }),
                ]),
                el("span", { class: "row__trailing data",
                             text: d.consultation_fee ? `₹${d.consultation_fee}` : "" }),
              ])
            ))
          : emptyState({
              title: "No doctors listed",
              body: "No doctor is attached to this hospital in the registry.",
            }),
      ],
    });
  } catch (error) {
    if (mine !== detailTicket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => showHospital(h)));
  }
}

/* -------------------------------------------------------------- doctors */

function doctorRow(d) {
  return el("button", { class: "row", onclick: () => showDoctor(d) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: d.name }),
      el("span", { class: "row__meta",
                   text: [d.specialisation, d.qualification].filter(Boolean).join(", ") }),
      el("span", { class: "row__sub",
                   text: [d.hospital_name, d.department,
                          `room ${d.room_no}`].filter(Boolean).join(", ") }),
    ]),
    el("span", { class: "row__trailing data", text: d.doctor_id }),
  ]);
}

async function showDoctor(d) {
  const mine = (detailTicket += 1);
  const container = viewContainer("doctors");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/doctors/${d.doctor_id}`);
    if (mine !== detailTicket) return;
    const doc = data.doctor;

    const facts = [
      ["Specialisation", doc.specialisation],
      ["Qualification", doc.qualification],
      ["Registration", doc.registration_no],
      ["Hospital", doc.hospital_name],
      ["Department", doc.department],
      ["Room", doc.room_no],
      ["Phone", doc.phone ? `+91 ${doc.phone.replace("+91 ", "")}` : ""],
      ["Languages", doc.languages],
      ["Experience", doc.experience_years
        ? `${doc.experience_years} years` : ""],
      ["Consultation", doc.consultation_fee ? `₹${doc.consultation_fee}` : ""],
      ["Available", doc.availability],
    ].filter(([, value]) => value && String(value).trim());

    detailShell({
      name: "doctors",
      title: doc.name,
      lead: [doc.specialisation, doc.qualification].filter(Boolean).join(", "),
      children: [
        factGrid("Practitioner", facts),

        el("p", { class: "section-label section-label--spaced",
                  text: `Recent consultations (${data.visits.length})` }),

        data.visits.length
          ? el("div", { class: "rows" }, data.visits.map((v) =>
              el("div", { class: "row row--static" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title",
                               text: v.patient_name || v.patient_id }),
                  el("span", { class: "row__meta",
                               text: v.diagnosis || "No diagnosis recorded" }),
                ]),
                el("span", { class: "row__trailing data",
                             text: formatDate(v.scheduled_date) }),
              ])
            ))
          : emptyState({
              title: "No consultations yet",
              body: "No consultations are recorded for this doctor.",
            }),
      ],
    });
  } catch (error) {
    if (mine !== detailTicket) return;
    clear(container);
    container.appendChild(errorState(error.message, () => showDoctor(d)));
  }
}

/* -------------------------------------------------------------- rare */

const RARE_VIEW = {
  name: "rare_conditions",
  containerId: "rare-results",
  searchId: "rare-search",
};

function rareRow(c) {
  const findings = c.symptoms ? c.symptoms.split("|").length : 0;
  const mode = c.inheritance_mode ? c.inheritance_mode.replace(/-/g, " ") : "";

  return el("button", { class: "row", onclick: () => showRare(c) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: c.name }),
      el("span", { class: "row__meta",
                   text: `${findings} findings${mode ? ` · ${mode}` : ""}` }),
      el("span", { class: "row__sub", text: previewFindings(c.symptoms) }),
    ]),
    el("span", { class: "row__trailing data", text: c.mondo_id || c.condition_id }),
  ]);
}

function previewFindings(symptoms) {
  if (!symptoms) return "";
  const words = symptoms.split("|");
  return words.slice(0, 6).join(", ") + (words.length > 6 ? ` · +${words.length - 6} more` : "");
}

/* Shown before any search, so the page opens with the shape of the
 * corpus rather than an empty box telling you to type. A registry this
 * size is itself the interesting thing. */
async function loadRareOverview() {
  const panel = document.getElementById("rare-overview");

  if (!panel || panel.dataset.loaded === "yes") return;
  panel.dataset.loaded = "yes";

  clear(panel);
  panel.appendChild(skeletonRows(2));

  try {
    const data = await api("/api/rare-conditions");

    clear(panel);

    /* The prompt underneath is the thing the overview replaces, and it is
     * still on screen because the overview arrives after it. */
    clear(viewContainer(RARE_VIEW.name));

    const figures = [
      ["Diseases", data.total.toLocaleString()],
      ["Distinct findings", data.distinct_findings.toLocaleString()],
      ["With a MONDO id", data.with_mondo.toLocaleString()],
      ["With inheritance noted", data.with_inheritance.toLocaleString()],
    ];

    panel.appendChild(el("div", { class: "card" }, [
      el("p", { class: "section-label", text: "What is in this registry" }),
      el("div", { class: "figures" }, figures.map(([label, value]) =>
        el("div", { class: "figure" }, [
          el("p", { class: "figure__value data", text: value }),
          el("p", { class: "figure__label", text: label }),
        ])
      )),

      el("p", { class: "section-label section-label--spaced",
                text: "Most common findings" }),
      el("div", { class: "chips" }, data.common_findings.map((f) =>
        el("button", {
          class: "chip", type: "button",
          title: `Search for ${f.word}`,
          onclick: () => {
            const input = document.getElementById("rare-search");
            input.value = f.word;
            input.dispatchEvent(new Event("input"));
            input.focus();
          },
        }, [
          el("span", { class: "chip__word", text: f.word }),
          el("span", { class: "chip__count data", text: f.diseases.toLocaleString() }),
        ])
      )),

      el("p", { class: "section-label section-label--spaced",
                text: "Inheritance" }),
      el("div", { class: "chips" }, data.inheritance_modes.map((m) =>
        el("span", { class: "chip chip--static" }, [
          el("span", { class: "chip__word", text: m.mode }),
          el("span", { class: "chip__count data", text: m.diseases.toLocaleString() }),
        ])
      )),

      el("p", { class: "note note--quiet",
                text: "Derived from the Human Phenotype Ontology. Findings are " +
                      "clinical descriptors, not patient complaints, so this " +
                      "registry is browsed rather than used for outpatient triage." }),
    ]));
  } catch (error) {
    clear(panel);
    panel.appendChild(errorState(error.message, loadRareOverview));
  }
}

async function showRare(c) {
  const container = viewContainer(RARE_VIEW.name);
  clear(container);
  container.appendChild(skeletonRows(3));

  try {
    const data = await api(`/api/rare-conditions/${c.condition_id}`);
    const condition = data.condition;

    const facts = [
      ["MONDO id", condition.mondo_id],
      ["Source id", condition.condition_id],
      ["Inheritance", condition.inheritance_mode.replace(/-/g, " ")],
    ].filter(([, value]) => value && value.trim());

    detailShell({
      name: RARE_VIEW.name,
      title: condition.name,
      lead: [
        condition.mondo_id,
        `${condition.symptom_count} phenotypic findings`,
      ].filter(Boolean).join(", "),
      children: [
        el("div", { class: "detail-grid" }, [
          factGrid("Record", facts),

          el("div", { class: "card" }, [
            el("p", { class: "section-label", text: "Findings" }),
            el("div", { class: "glance" }, [
              ["Recorded", String(data.findings.length)],
              ["With lay wording", String(
                data.findings.filter((f) => f.is_lay_wording).length)],
              ["Inheritance modes", String(data.inheritance.length)],
            ].map(([label, value]) =>
              el("div", { class: "glance__row" }, [
                el("span", { class: "glance__label", text: label }),
                el("span", { class: "glance__value", text: value }),
              ])
            )),
          ]),
        ]),

        el("p", { class: "section-label section-label--spaced",
                  text: `Phenotypic findings (${data.findings.length})` }),

        el("div", { class: "rows" }, data.findings.map((f) =>
          el("div", { class: "row row--static" }, [
            el("span", { class: "row__main" }, [
              el("span", { class: "row__title", text: f.word }),
              /* The curator label is only worth a second line when it
               * differs from the lay word. Printing both when they are
               * the same text just repeats the row. */
              f.term && f.term.toLowerCase() !== f.word
                ? el("span", { class: "row__meta", text: f.term })
                : null,
            ]),
            el("span", { class: "row__trailing data", text: f.hpo_id }),
          ])
        )),

        el("p", { class: "note note--quiet",
                  text: "Terms come from the Human Phenotype Ontology. Words " +
                        "marked with a lay synonym are the wording a patient " +
                        "would recognise." }),
      ],
    });
  } catch (error) {
    clear(container);
    container.appendChild(errorState(error.message, () => showRare(c)));
  }
}

/* ------------------------------------------------------------ analytics */

const datasetTabs = document.getElementById("dataset-tabs");
const analyticsBody = document.getElementById("analytics-body");

/* See detailTicket. Same reasoning: a response for a dataset the reader
 * has already switched away from must not paint over the current one. */
let datasetTicket = 0;

async function loadDatasets() {
  clear(datasetTabs);
  clear(analyticsBody);
  analyticsBody.appendChild(skeletonRows(3));

  try {
    const data = await api("/api/analytics");

    if (!data.passing.length) {
      clear(analyticsBody);
      analyticsBody.appendChild(emptyState({
        title: "No datasets available",
        body: "Run scripts/fetch_datasets.py and scripts/profile_dataset.py " +
              "to download and score the clinical datasets.",
        art: "doc",
      }));
      return;
    }

    for (const name of data.passing) {
      datasetTabs.appendChild(el("button", {
        class: "tabs__btn", role: "tab", "aria-selected": "false",
        onclick: () => selectDataset(name),
      }, name.replace(".csv", "")));
    }

    selectDataset(data.passing[0]);
  } catch (error) {
    clear(analyticsBody);
    analyticsBody.appendChild(errorState(error.message, loadDatasets));
  }
}

function selectDataset(name) {
  state.dataset = name;

  for (const tab of datasetTabs.children) {
    tab.setAttribute("aria-selected",
      tab.textContent === name.replace(".csv", "") ? "true" : "false");
  }

  revealTab(name);

  clear(analyticsBody);
  analyticsBody.appendChild(skeletonRows(3));

  const mine = (datasetTicket += 1);

  (async () => {
    try {
      const [profile, bands] = await Promise.all([
        api(`/api/analytics/${name}`),
        api(`/api/analytics/${name}/risk-bands`).catch(() => null),
      ]);

      // Switching tabs faster than the requests return is normal. A
      // response for a tab the reader has already left must not paint.
      if (mine !== datasetTicket) return;

      const charts = profile.strongest_separators.slice(0, 3);

      clear(analyticsBody);

      analyticsBody.appendChild(el("div", { class: "panel" }, [
        el("p", { class: "section-label", text: "Strongest separators" }),
        el("table", { class: "kv" }, [
          el("tbody", {}, charts.map((s) =>
            el("tr", {}, [
              el("th", { class: "data", text: s.column }),
              el("td", { class: "data",
                         text: `${(s.relative_spread * 100).toFixed(0)}% spread` }),
            ])
          )),
        ]),
        el("p", { class: "field__hint",
                  text: `${profile.rows} rows · ${profile.cols} columns · ` +
                        `target ${profile.target}` }),
      ]));

      if (bands) {
        analyticsBody.appendChild(renderBands(name, bands));
      }

      loadCharts(name, mine);
    } catch (error) {
      if (mine !== datasetTicket) return;
      clear(analyticsBody);
      analyticsBody.appendChild(errorState(error.message, () => selectDataset(name)));
    }
  })();
}

function renderBands(name, bands) {
  const rows = [];

  for (const [column, data] of Object.entries(bands.columns || {})) {
    const entries = Object.entries(data.bands);
    const total = entries.reduce((sum, [, count]) => sum + count, 0);

    rows.push(el("tr", {}, [
      el("th", { class: "data", text: column }),
      el("td", {}, [
        el("div", { class: "bands__lines" },
          entries.map(([label, count]) =>
            el("span", { class: "bands__line" },
              `${label}: ${count} (${Math.round((count / total) * 100)}%)`))),
        data.unreachable_bands.length
          ? el("p", { class: "field__hint",
                      text: `No ${data.unreachable_bands.join(" or ")} band: ` +
                            `outside the range of this data.` })
          : null,
      ]),
    ]));
  }

  if (!rows.length) return null;

  return el("div", { class: "panel panel--spaced" }, [
    el("p", { class: "section-label", text: "Risk bands" }),
    el("table", { class: "kv" }, [el("tbody", {}, rows)]),
  ]);
}

/* The dataset tabs scroll sideways on a narrow screen, so the one that is
 * selected has to be brought back into view or the reader cannot see
 * which dataset they are looking at. Same reasoning as revealActiveNav. */
function revealTab(name) {
  const strip = document.getElementById("dataset-tabs");
  if (!strip) return;

  const wanted = name.replace(".csv", "");
  const tab = [...strip.children].find((t) => t.textContent === wanted);
  if (!tab) return;

  for (let pass = 0; pass < 3; pass += 1) {
    const stripBox = strip.getBoundingClientRect();
    const tabBox = tab.getBoundingClientRect();

    const hiddenLeft = tabBox.left < stripBox.left;
    const hiddenRight = tabBox.right > stripBox.right;

    if (!hiddenLeft && !hiddenRight) return;

    if (hiddenRight) strip.scrollLeft += tabBox.right - stripBox.right + 8;
    else strip.scrollLeft -= stripBox.left - tabBox.left + 8;
  }
}

async function loadCharts(name, ticket) {
  try {
    const data = await api(`/api/analytics/${name}/charts`);

    // Charts land last and slowest, so they need the same ticket check as
    // the rest. Without it, flipping between tabs leaves a grid of images
    // from every tab visited, stacked under whichever one loaded last.
    if (ticket !== datasetTicket) return;

    const target = document.getElementById("analytics-body");
    if (!target) return;

    const grid = el("div", { class: "charts charts--spaced" },
      data.charts.map((path) => {
        const file = path.split(/[\\/]/).pop();
        return el("figure", { class: "chart chart--flush" }, [
          el("img", { src: `/charts/${file}`, alt: `Chart for ${name}`,
                      loading: "lazy", width: "700", height: "420" }),
          el("figcaption", { class: "chart__caption",
                             text: file.replace(".png", "").replace(/_/g, " ") }),
        ]);
      }));

    target.appendChild(grid);
  } catch {
    /* Charts are supplementary. A failure here must not blank the page. */
  }
}

/* ------------------------------------------------------------- routing */

/* Row renderers, bound to the view names declared in SEARCH_VIEWS above.
 * Kept as a block here because each renderer is defined next to the
 * detail screen it opens. */
ROW_RENDERERS.patients = patientRow;
ROW_RENDERERS.hospitals = hospitalRow;
ROW_RENDERERS.doctors = doctorRow;
ROW_RENDERERS.medicines = medicineRow;
ROW_RENDERERS.stores = storeRow;
ROW_RENDERERS.rare_conditions = rareRow;

const VIEWS = ["triage", "patients", "hospitals", "doctors", "medicines",
               "stores", "rare_conditions", "analytics"];
const INITIALISED = new Set();

/* Seven sections do not fit across a phone, so the nav scrolls sideways
 * and fades at the cut edge. That makes the section you are in easy to
 * lose off the right of the screen, so it is brought back into view when
 * it changes.
 *
 * scrollLeft is adjusted directly rather than through scrollIntoView,
 * which would also scroll the page vertically to chase the link. */
function revealActiveNav(name) {
  const nav = document.querySelector(".nav");
  const link = nav && nav.querySelector(`.nav__link[data-view="${name}"]`);
  if (!nav || !link) return;

  /* scrollLeft is assigned rather than scrolled through scrollIntoView,
   * which would also scroll the page vertically chasing the link.
   *
   * Two passes, because the browser clamps scrollLeft at both ends and a
   * single pass can leave the link short of the edge it was pushed
   * towards. The loop stops as soon as the link is wholly inside. */
  for (let pass = 0; pass < 3; pass += 1) {
    const navBox = nav.getBoundingClientRect();
    const linkBox = link.getBoundingClientRect();

    const hiddenLeft = linkBox.left < navBox.left;
    const hiddenRight = linkBox.right > navBox.right;

    if (!hiddenLeft && !hiddenRight) return;

    if (hiddenRight) nav.scrollLeft += linkBox.right - navBox.right + 8;
    else nav.scrollLeft -= navBox.left - linkBox.left + 8;
  }
}

/* Changing the view is a navigation, so focus has to move with it. The
 * heading is made programmatically focusable rather than carrying
 * tabindex="-1" in the markup, which keeps the authored HTML readable and
 * puts the attribute only where it is needed. */
function focusHeading(viewName) {
  const heading = document.getElementById(`view-${viewName}`)?.querySelector("h1");
  if (!heading) return;

  heading.setAttribute("tabindex", "-1");
  heading.focus();
}

function show(name) {
  // Hashes read better with a hyphen, view keys cannot contain one.
  // "rare-conditions" and "rare_conditions" are the same view.
  name = String(name).replace(/-/g, "_");

  if (!VIEWS.includes(name)) name = "triage";

  // The first call is not a change. Treating it as one would move focus
  // to the heading on page load, which is never what anyone wants.
  const isChange = state.view !== null && state.view !== name;
  state.view = name;

  for (const view of VIEWS) {
    const node = document.getElementById(`view-${view}`);
    if (node) node.hidden = view !== name;
  }

  for (const link of document.querySelectorAll(".nav__link")) {
    if (link.dataset.view === name) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  // Leaving a view with a record open must not strand the reader. Focus is
  // not restored to the search box here, because the heading is about to
  // take it.
  if (openDetail && openDetail.name !== name) closeDetail({ restoreFocus: false });

  if (isChange) focusHeading(name);

  revealActiveNav(name);

  /* The companion walks on rows, so it has to be re-placed whenever
   * the screen under it changes. Deferred a frame because a view
   * rendering for the first time has not drawn its rows yet. */
  if (typeof companion !== "undefined") {
    if (BROWSE_VIEWS[name]) requestAnimationFrame(() => companion.show());
    else companion.hide();
  }

  /* The nav is measured with the fallback font first, then re-measured
   * when IBM Plex arrives and every item gets wider. The scroll position
   * chosen against the fallback is then short by however much the real
   * font added, which leaves the active item clipped again. One more pass
   * after the fonts settle closes the gap. */
  if (!fontsSettled) {
    fontsSettled = true;
    document.fonts?.ready.then(() => revealActiveNav(state.view));
  }

  if (INITIALISED.has(name)) return;

  /* Marked as done only after it has actually worked. Recording it first
   * means a view whose setup throws is remembered as initialised and is
   * then skipped forever, so it stays blank for the rest of the session
   * with no way back. */
  try {
    if (SEARCH_VIEWS[name]) searchView(name);
    if (name === "rare_conditions") loadRareOverview();
    if (name === "analytics") loadDatasets();
    INITIALISED.add(name);
  } catch (error) {
    reportBrokenView(name, error);
  }
}

/* A view that cannot start says so, in its own area, rather than leaving
 * a heading above nothing. */
function reportBrokenView(name, error) {
  console.error(`Meridian: the ${name} view failed to start`, error);

  const config = SEARCH_VIEWS[name];
  if (!config) return;

  const container = document.getElementById(config.containerId);
  if (!container) return;

  clear(container);
  container.appendChild(errorState(
    `${error.message}. This is a bug in the interface, not a data problem.`,
    () => location.reload(),
  ));
}

window.addEventListener("hashchange", () => show(location.hash.slice(1) || "triage"));
show(location.hash.slice(1) || "triage");
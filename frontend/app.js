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

const state = {
  view: "triage",
  dataset: null,
  datasetProfile: null,
};

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
      el("div", { class: "skeleton__bar skeleton__bar--meta", style: "flex:1" }),
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

let toastTimer = null;

function toast(message) {
  const node = document.getElementById("toast");
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, 2600);
}

/* ------------------------------------------------------------ formatting */

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
      block.push(el("p", { class: "section-label", style: "margin-top: var(--s-6)",
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
      block.push(el("p", { class: "section-label",
                            style: "margin-top: var(--s-6)",
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

/* Each search view remembers its last query and its last results, so
 * opening a record and coming back does not lose the list. Without this
 * the detail view is a dead end. */
const lastResults = {
  patients: { query: "", rows: [] },
  medicines: { query: "", rows: [] },
  stores: { query: "", rows: [] },
  hospitals: { query: "", rows: [] },
  doctors: { query: "", rows: [] },
};

/* Renderers for the five list views, looked up by view name. */
const ROW_RENDERERS = {
  patients: null,
  medicines: null,
  stores: null,
  hospitals: null,
  doctors: null,
};

/* One detail view is open at a time. */
let openDetail = null;

function backLink() {
  return el("button", {
    class: "back", type: "button", onclick: closeDetail,
  }, [
    el("span", { class: "back__mark", "aria-hidden": "true", text: "←" }),
    el("span", { text: "Back to list" }),
  ]);
}

function closeDetail() {
  if (!openDetail) return;

  const view = openDetail;
  openDetail = null;

  const container = document.getElementById(view.containerId);
  const stored = lastResults[view.name];

  clear(container);

  if (stored.rows.length) {
    renderList(stored.rows, view.name);
    toast(`Back to ${stored.rows.length} results`);
  } else {
    showPrompt(view.name);
  }

  document.getElementById(view.searchId)?.focus();
}

/* Replace a search view's contents with a detail screen. */
function detailShell({ view, title, lead, children }) {
  const container = document.getElementById(view.containerId);

  clear(container);
  openDetail = { name: view.name, containerId: view.containerId, searchId: view.searchId };

  container.appendChild(el("div", {}, [
    backLink(),
    el("div", { class: "page__head", style: "margin-top: var(--s-5)" }, [
      el("h2", { class: "page__title", text: title }),
      el("p", { class: "page__lead", text: lead }),
    ]),
    ...[].concat(children),
  ]));
}

function renderList(rows, viewName) {
  const container = document.getElementById(`${viewName}-results`);
  clear(container);
  container.appendChild(el("div", { class: "rows" }, rows.map(ROW_RENDERERS[viewName])));
}

function showPrompt(viewName) {
  const container = document.getElementById(`${viewName}-results`);
  const stored = lastResults[viewName];

  clear(container);
  container.appendChild(emptyState({
    title: "No search yet",
    body: `Type a name, place or category to search ${viewName}.` +
          (stored.query ? ` Last search was “${stored.query}”.` : ""),
  }));
}

function searchView({ view, endpoint, noun }) {
  const input = document.getElementById(`${view}-search`);
  const container = document.getElementById(`${view}-results`);
  let timer = null;

  async function load(query) {
    if (!query.trim()) {
      lastResults[view] = { query: "", rows: [] };
      showPrompt(view);
      return;
    }

    clear(container);
    container.appendChild(skeletonRows(4));

    try {
      const data = await api(`${endpoint}?q=${encodeURIComponent(query)}`);
      clear(container);

      lastResults[view] = { query, rows: data.results };

      if (!data.count) {
        container.appendChild(emptyState({
          title: `No ${noun} matched`,
          body: `Nothing in the registry matches “${query}”. ` +
                `Try a shorter or more general term.`,
        }));
        return;
      }

      renderList(data.results, view);
    } catch (error) {
      clear(container);
      container.appendChild(errorState(error.message, () => load(query)));
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => load(input.value.trim()), 220);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && openDetail) closeDetail();
  });

  load(input.value.trim());
}

/* ------------------------------------------------------------- patients */

const PATIENT_VIEW = {
  name: "patients", containerId: "patient-results", searchId: "patient-search",
};

function patientRow(p) {
  const meta = [p.age ? `age ${p.age}` : "", p.gender,
                p.blood_group || "blood group not recorded",
                p.area]
    .filter(Boolean).join(" · ");

  return el("button", { class: "row", onclick: () => showPatient(p) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: p.name }),
      el("span", { class: "row__meta", text: meta }),
    ]),
    el("span", { class: "row__trailing data", text: p.patient_id }),
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

  return parts.join(" · ");
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
  const waited = v.checked_in_at && v.scheduled_time
    ? null : null;

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
                        .filter(Boolean).join(" · ") }),
      el("p", { class: "visit__meta",
                text: [v.doctor?.department && `${v.doctor.department}, room ${v.doctor.room_no}`,
                       v.hospital?.area].filter(Boolean).join(" · ") }),
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
  const container = document.getElementById("patient-results");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/patients/${p.patient_id}`);
    const who = data.patient;

    const contact = [
      ["Registered", formatDate(who.registered_on)],
      ["Phone", who.phone ? `+91 ${who.phone}` : ""],
      ["Email", who.email],
      ["Blood group", who.blood_group || "not recorded"],
      ["Address", who.address_line],
      ["Area", [who.area, who.pincode].filter(Boolean).join(" ")],
      ["City", [who.city, who.state].filter(Boolean).join(", ")],
      ["Emergency", who.emergency_contact
        ? `${who.emergency_contact}${who.emergency_phone ? `, +91 ${who.emergency_phone}` : ""}`
        : ""],
    ].filter(([, value]) => value);

    detailShell({
      view: PATIENT_VIEW,
      title: who.name,
      lead: [who.patient_id,
             who.age ? `age ${who.age}` : "",
             who.gender,
             who.blood_group ? `${who.blood_group}` : ""]
             .filter(Boolean).join(" · "),
      children: [
        el("div", { class: "detail-grid" }, [
          el("table", { class: "kv" }, [
            el("caption", { class: "section-label", text: "Record" }),
            el("tbody", {}, contact.map(([key, value]) =>
              el("tr", {}, [
                el("th", { text: key }),
                el("td", { text: value }),
              ])
            )),
          ]),
          el("table", { class: "kv" }, [
            el("caption", { class: "section-label", text: "At a glance" }),
            el("tbody", {}, [
              el("tr", {}, [
                el("th", { text: "Consultations" }),
                el("td", { class: "data", text: String(data.visit_count) }),
              ]),
              el("tr", {}, [
                el("th", { text: "Doctors seen" }),
                el("td", { class: "data",
                           text: String(new Set(data.visits.map((v) => v.doctor_id)).size) }),
              ]),
              el("tr", {}, [
                el("th", { text: "Hospitals" }),
                el("td", { class: "data",
                           text: String(new Set(data.visits.map((v) => v.hospital_id)).size) }),
              ]),
              el("tr", {}, [
                el("th", { text: "Active" }),
                el("td", { class: "data",
                           text: String(data.visits.filter((v) => v.status === "Active").length) }),
              ]),
            ]),
          ]),
        ]),

        el("p", { class: "section-label", style: "margin-top: var(--s-6)",
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
    clear(container);
    container.appendChild(errorState(error.message, () => showPatient(p)));
  }
}

/* ------------------------------------------------------------ medicines */

function medicineRow(m) {
  const flags = [m.otc === "yes" ? "Over the counter" : "",
                 m.rx_required === "yes" ? "Prescription required" : ""]
    .filter(Boolean).join(" · ");

  const price = m.price ? `₹${m.price}` : "";

  return el("button", { class: "row", onclick: () => showMedicine(m) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: m.name }),
      el("span", { class: "row__meta",
                   text: [m.generic, m.category, flags].filter(Boolean).join(" · ") }),
    ]),
    el("span", { class: "row__trailing" }, [
      el("span", { class: "data", text: price }),
    ]),
  ]);
}

const MEDICINE_VIEW = {
  name: "medicines", containerId: "medicine-results", searchId: "medicine-search",
};

async function showMedicine(m) {
  const container = document.getElementById("medicine-results");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/medicines/${m.medicine_id}`);
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
      view: MEDICINE_VIEW,
      title: med.name,
      lead: [med.generic, med.category, med.strength].filter(Boolean).join(" · "),
      children: [
        el("div", { class: "detail-grid" }, [
          el("table", { class: "kv" }, [
            el("caption", { class: "section-label", text: "Catalogue entry" }),
            el("tbody", {}, facts.map(([key, value]) =>
              el("tr", {}, [
                el("th", { text: key }),
                el("td", { text: value }),
              ])
            )),
          ]),
          el("div", { class: "stock-card" }, [
            el("p", { class: "section-label", text: "Availability" }),
            el("p", { class: "stock-card__count data",
                      text: String(data.stocked_by.length) }),
            el("p", { class: "stock-card__unit",
                      text: data.stocked_by.length === 1
                        ? "store stocks this" : "stores stock this" }),
          ]),
        ]),

        el("p", { class: "section-label", style: "margin-top: var(--s-6)",
                  text: "Stocked by" }),

        data.stocked_by.length
          ? el("div", { class: "rows" }, data.stocked_by.map((s) =>
              el("div", { class: "row", style: "cursor: default" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: s.name }),
                  el("span", { class: "row__meta",
                               text: [s.area, s.city, s.hours, s.phone && `+91 ${s.phone}`]
                                     .filter(Boolean).join(" · ") }),
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
    clear(container);
    container.appendChild(errorState(error.message, () => showMedicine(m)));
  }
}

/* --------------------------------------------------------------- stores */

const STORE_VIEW = {
  name: "stores", containerId: "store-results", searchId: "store-search",
};

function storeRow(s) {
  const count = s.stock_csv ? s.stock_csv.split("|").length : 0;

  return el("button", { class: "row", onclick: () => showStore(s) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: s.name }),
      el("span", { class: "row__meta",
                   text: [s.type, s.area, s.city, s.hours].filter(Boolean).join(" · ") }),
    ]),
    el("span", { class: "row__trailing" }, [
      el("span", { class: count ? "data" : "row__trailing-note",
                   text: count ? `${count} stocked` : "stock not recorded" }),
    ]),
  ]);
}

async function showStore(s) {
  const container = document.getElementById("store-results");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/stores/${s.store_id}`);
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
      view: STORE_VIEW,
      title: store.name,
      lead: [store.type, store.area, store.city].filter(Boolean).join(" · "),
      children: [
        el("div", { class: "detail-grid" }, [
          el("table", { class: "kv" }, [
            el("caption", { class: "section-label", text: "Store" }),
            el("tbody", {}, facts.map(([key, value]) =>
              el("tr", {}, [
                el("th", { text: key }),
                el("td", { text: String(value) }),
              ])
            )),
          ]),
          el("div", { class: "stock-card" }, [
            el("p", { class: "section-label", text: "Recorded stock" }),
            el("p", { class: "stock-card__count data", text: String(known) }),
            el("p", { class: "stock-card__unit",
                      text: known === 1 ? "medicine listed" : "medicines listed" }),
          ]),
        ]),

        el("p", { class: "section-label", style: "margin-top: var(--s-6)",
                  text: "Medicines listed" }),

        data.medicines.length
          ? el("div", { class: "rows" }, data.medicines.map((m) =>
              el("div", { class: "row", style: "cursor: default" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: m.name }),
                  el("span", { class: "row__meta",
                               text: [m.generic, m.category, m.strength]
                                     .filter(Boolean).join(" · ") }),
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
    clear(container);
    container.appendChild(errorState(error.message, () => showStore(s)));
  }
}

/* ------------------------------------------------------------ hospitals */

const HOSPITAL_VIEW = {
  name: "hospitals", containerId: "hospital-results", searchId: "hospital-search",
};

function hospitalRow(h) {
  return el("button", { class: "row", onclick: () => showHospital(h) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: h.name }),
      el("span", { class: "row__meta",
                   text: [h.type, h.area, h.city,
                          h.beds ? `${h.beds} beds` : ""].filter(Boolean).join(" · ") }),
    ]),
    el("span", { class: "row__trailing data", text: h.hospital_id }),
  ]);
}

async function showHospital(h) {
  const container = document.getElementById("hospital-results");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/hospitals/${h.hospital_id}`);
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
      view: HOSPITAL_VIEW,
      title: hosp.name,
      lead: [hosp.type, hosp.area, hosp.city].filter(Boolean).join(" · "),
      children: [
        el("table", { class: "kv" }, [
          el("caption", { class: "section-label", text: "Hospital" }),
          el("tbody", {}, facts.map(([key, value]) =>
            el("tr", {}, [
              el("th", { text: key }),
              el("td", { text: String(value) }),
            ])
          )),
        ]),

        el("p", { class: "section-label", style: "margin-top: var(--s-6)",
                  text: `Doctors practising here (${data.doctors.length})` }),

        data.doctors.length
          ? el("div", { class: "rows" }, data.doctors.map((d) =>
              el("div", { class: "row", style: "cursor: default" }, [
                el("span", { class: "row__main" }, [
                  el("span", { class: "row__title", text: d.name }),
                  el("span", { class: "row__meta",
                               text: [d.specialisation, d.qualification,
                                      `room ${d.room_no}`].filter(Boolean).join(" · ") }),
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
    clear(container);
    container.appendChild(errorState(error.message, () => showHospital(h)));
  }
}

/* -------------------------------------------------------------- doctors */

const DOCTOR_VIEW = {
  name: "doctors", containerId: "doctor-results", searchId: "doctor-search",
};

function doctorRow(d) {
  return el("button", { class: "row", onclick: () => showDoctor(d) }, [
    el("span", { class: "row__main" }, [
      el("span", { class: "row__title", text: d.name }),
      el("span", { class: "row__meta",
                   text: [d.specialisation, d.qualification].filter(Boolean).join(" · ") }),
      el("span", { class: "row__sub",
                   text: [d.hospital_name, d.department,
                          `room ${d.room_no}`].filter(Boolean).join(" · ") }),
    ]),
    el("span", { class: "row__trailing data", text: d.doctor_id }),
  ]);
}

async function showDoctor(d) {
  const container = document.getElementById("doctor-results");
  clear(container);
  container.appendChild(skeletonRows(2));

  try {
    const data = await api(`/api/doctors/${d.doctor_id}`);
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
      view: DOCTOR_VIEW,
      title: doc.name,
      lead: [doc.specialisation, doc.qualification].filter(Boolean).join(" · "),
      children: [
        el("table", { class: "kv" }, [
          el("caption", { class: "section-label", text: "Practitioner" }),
          el("tbody", {}, facts.map(([key, value]) =>
            el("tr", {}, [
              el("th", { text: key }),
              el("td", { text: String(value) }),
            ])
          )),
        ]),

        el("p", { class: "section-label", style: "margin-top: var(--s-6)",
                  text: `Recent consultations (${data.visits.length})` }),

        data.visits.length
          ? el("div", { class: "rows" }, data.visits.map((v) =>
              el("div", { class: "row", style: "cursor: default" }, [
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
    clear(container);
    container.appendChild(errorState(error.message, () => showDoctor(d)));
  }
}

/* ------------------------------------------------------------ analytics */

const datasetTabs = document.getElementById("dataset-tabs");
const analyticsBody = document.getElementById("analytics-body");

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

  clear(analyticsBody);
  analyticsBody.appendChild(skeletonRows(3));

  (async () => {
    try {
      const [profile, bands] = await Promise.all([
        api(`/api/analytics/${name}`),
        api(`/api/analytics/${name}/risk-bands`).catch(() => null),
      ]);

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

      loadCharts(name);
    } catch (error) {
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
        el("div", { class: "row__meta", style: "margin-bottom: var(--s-2)" },
          entries.map(([label, count]) =>
            el("span", { style: "display:block" },
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

  return el("div", { class: "panel", style: "margin-top: var(--s-5)" }, [
    el("p", { class: "section-label", text: "Risk bands" }),
    el("table", { class: "kv" }, [el("tbody", {}, rows)]),
  ]);
}

async function loadCharts(name) {
  try {
    const data = await api(`/api/analytics/${name}/charts`);
    const target = document.getElementById("analytics-body");
    if (!target) return;

    const grid = el("div", { class: "charts", style: "margin-top: var(--s-5)" },
      data.charts.map((path) => {
        const file = path.split(/[\\/]/).pop();
        return el("figure", { class: "chart", style: "margin:0" }, [
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

/* Every searchable view: which registry to query, and what a row looks
 * like. Kept as one table so adding a registry is a single entry. */
ROW_RENDERERS.patients = patientRow;
ROW_RENDERERS.medicines = medicineRow;
ROW_RENDERERS.stores = storeRow;
ROW_RENDERERS.hospitals = hospitalRow;
ROW_RENDERERS.doctors = doctorRow;

const SEARCH_VIEWS = {
  patients: { view: "patients", endpoint: "/api/search/patients", noun: "patients" },
  medicines: { view: "medicines", endpoint: "/api/search/medicines", noun: "medicines" },
  stores: { view: "stores", endpoint: "/api/search/stores", noun: "stores" },
  hospitals: { view: "hospitals", endpoint: "/api/search/hospitals", noun: "hospitals" },
  doctors: { view: "doctors", endpoint: "/api/search/doctors", noun: "doctors" },
};

const VIEWS = ["triage", "patients", "hospitals", "doctors", "medicines",
               "stores", "analytics"];
const INITIALISED = new Set();

function show(name) {
  if (!VIEWS.includes(name)) name = "triage";
  state.view = name;

  for (const view of VIEWS) {
    const node = document.getElementById(`view-${view}`);
    if (node) node.hidden = view !== name;
  }

  for (const link of document.querySelectorAll(".nav__link")) {
    if (link.dataset.view === name) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }

  // Leaving a view with a record open must not strand the reader.
  if (openDetail && openDetail.name !== name) closeDetail();

  if (INITIALISED.has(name)) return;
  INITIALISED.add(name);

  if (SEARCH_VIEWS[name]) searchView(SEARCH_VIEWS[name]);
  if (name === "analytics") loadDatasets();
}

window.addEventListener("hashchange", () => show(location.hash.slice(1) || "triage"));
show(location.hash.slice(1) || "triage");
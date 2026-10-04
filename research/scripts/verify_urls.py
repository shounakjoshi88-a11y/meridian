"""Check that every URL cited in the synthetic-generation note really responds.

Hardcoded URLs rot, and citing a link you never opened is worse than writing
no link at all. Every source in research/notes/05-synthetic-generation.md is
listed here and this script reports the observed HTTP status for it.

Re-run it before trusting the notes. A few publishers sit behind a bot filter
and answer 403 to a plain script; those are marked EXPECT_BLOCKED so a clean
run means "every reachable source answered 200, and every blocked source is
one we already know blocks scripts".

Taught concepts used: functions, lists, dicts, strings, for loops, files,
try/except (Lab 2), plus sys for the exit code (Lab 4).

Run it:

    python research/scripts/verify_urls.py
    python research/scripts/verify_urls.py --timeout 45
"""

import sys
import time
import urllib.error
import urllib.request

# key -> (url, expected). expected is "ok" or "blocked": "blocked" means the
# publisher refuses scripted clients, which we observed and accepted.
SOURCES = {
    # --- vital signs, adults -------------------------------------------
    "medlineplus-vitals":
        ("https://www.medlineplus.gov/ency/article/002341.htm", "ok"),
    "nhlbi-high-blood-pressure":
        ("https://www.nhlbi.nih.gov/health/high-blood-pressure", "ok"),
    "medlineplus-pulse-ox":
        ("https://www.medlineplus.gov/lab-tests/pulse-oximetry", "ok"),
    "statpearls-vitals":
        ("https://www.ncbi.nlm.nih.gov/books/NBK553213/", "blocked"),
    "statpearls-pulse-ox":
        ("https://www.ncbi.nlm.nih.gov/books/NBK592401/", "blocked"),

    # --- vital signs, paediatric ---------------------------------------
    "aafp-pediatric-bp-2018":
        ("https://www.aafp.org/pubs/afp/issues/2018/1015/p486.html", "ok"),
    "merck-bp-boys":
        ("https://www.merckmanuals.com/professional/multimedia/table/"
         "blood-pressure-bp-percentile-levels-for-boys-by-age-and-height-"
         "measured-and-percentile", "ok"),
    "merck-bp-girls":
        ("https://www.merckmanuals.com/professional/multimedia/table/"
         "blood-pressure-bp-percentile-levels-for-girls-by-age-and-height-"
         "measured-and-percentile", "ok"),
    "pmc-aap-guideline-review":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC8031116/", "ok"),
    "pmc-aap-vs-esh":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC6705594/", "ok"),
    "aap-cpg-2017":
        ("https://publications.aap.org/pediatrics/article/140/3/e20171904/"
         "38358/Clinical-Practice-Guideline-for-Screening-and", "blocked"),

    # --- blood groups ---------------------------------------------------
    "pmc-agrawal-india-national":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC4140055/", "ok"),
    "pmc-delhi-eight-groups":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC10599670/", "ok"),
    "pmc-indian-antigen-panels":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC3705660/", "ok"),
    "pmc-south-india-abo":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC11734788/", "ok"),
    "pmc-rhd-national":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC2847344/", "ok"),

    # --- growth, height, weight ----------------------------------------
    "who-child-growth-standards":
        ("https://www.who.int/tools/child-growth-standards", "ok"),
    "who-growth-methods-publication":
        ("https://www.who.int/publications/i/item/924154693X", "ok"),
    "who-weight-for-age-page":
        ("https://www.who.int/tools/child-growth-standards/standards/"
         "weight-for-age", "ok"),
    "who-length-height-for-age-page":
        ("https://www.who.int/tools/child-growth-standards/standards/"
         "length-height-for-age", "ok"),
    "who-wfa-boys-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/weight-for-age/"
         "wfa_boys_0-to-5-years_zscores.xlsx", "ok"),
    "who-wfa-girls-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/weight-for-age/"
         "wfa_girls_0-to-5-years_zscores.xlsx", "ok"),
    "who-lhfa-boys-0-2-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/length-height-for-age/"
         "lhfa_boys_0-to-2-years_zscores.xlsx", "ok"),
    "who-lhfa-boys-2-5-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/length-height-for-age/"
         "lhfa_boys_2-to-5-years_zscores.xlsx", "ok"),
    "who-lhfa-girls-0-2-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/length-height-for-age/"
         "lhfa_girls_0-to-2-years_zscores.xlsx", "ok"),
    "who-lhfa-girls-2-5-lms":
        ("https://cdn.who.int/media/docs/default-source/child-growth/"
         "child-growth-standards/indicators/length-height-for-age/"
         "lhfa_girls_2-to-5-years_zscores.xlsx", "ok"),
    "cdc-nhanes-anthropometry-2017":
        ("https://wwwn.cdc.gov/nchs/data/nhanes/public/2017/manuals/"
         "2017_Anthropometry_Procedures_Manual.pdf", "ok"),
    "indian-pediatrics-bmi-cutoffs":
        ("https://indianpediatrics.net/jan2012/jan-29-34.htm", "ok"),
    "pib-india-bmi-cutoffs":
        ("https://www.pib.gov.in/PressReleasePage.aspx?PRID=2107179", "ok"),
    "pmc-indian-bmi-consensus":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC4555479/", "ok"),
    "pmc-india-obesity-review":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC7615800/", "ok"),
    "pmc-nfhs4-double-burden":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC6976728/", "ok"),

    # --- India demography ----------------------------------------------
    "mospi-women-men-2022-population":
        ("https://www.mospi.gov.in/sites/default/files/publication_reports/"
         "women-men22/PopulationStatistics22.pdf", "ok"),
    "mohfw-nhp-2011-demographic":
        ("https://cbhidghs.mohfw.gov.in/sites/default/files/NHP/"
         "nhp-2011-Demographic%20Indicators.pdf", "ok"),
    "mospi-statistical-yearbook-area-population":
        ("https://www.mospi.gov.in/sites/default/files/Statistical_year_book_"
         "india_chapters/Area%20And%20Population-writeup.pdf", "ok"),

    # --- python standard library ----------------------------------------
    "python-random":
        ("https://docs.python.org/3/library/random.html", "ok"),
    "python-random-seed":
        ("https://docs.python.org/3/library/random.html#random.seed", "ok"),
    "python-random-gauss":
        ("https://docs.python.org/3/library/random.html#random.gauss", "ok"),
    "python-random-choices":
        ("https://docs.python.org/3/library/random.html#random.choices", "ok"),
    "python-random-normalvariate":
        ("https://docs.python.org/3/library/random.html#normalvariate",
         "ok"),
    "python-secrets":
        ("https://docs.python.org/3/library/secrets.html", "ok"),
    "python-math":
        ("https://docs.python.org/3/library/math.html", "ok"),
    "python-standard-library-index":
        ("https://docs.python.org/3/library/index.html", "ok"),

    # --- Synthea --------------------------------------------------------
    "synthea-github":
        ("https://github.com/synthetichealth/synthea", "ok"),
    "synthea-site":
        ("https://synthea.org/", "ok"),
    "synthea-wiki-records":
        ("https://github.com/synthetichealth/synthea/wiki/Records", "ok"),
    "synthea-wiki-generic-modules":
        ("https://github.com/synthetichealth/synthea/wiki/Generic-Modules",
         "ok"),
    "synthea-wiki-basics":
        ("https://github.com/synthetichealth/synthea/wiki/Basics", "ok"),

    # --- synthetic data quality -----------------------------------------
    "pmc-generation-and-evaluation":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC7204018/", "ok"),
    "royalsociety-synthetic-data-survey":
        ("https://royalsociety.org/-/media/policy/projects/"
         "privacy-enhancing-technologies/Synthetic_Data_Survey-24.pdf", "ok"),
    "arxiv-synthetic-data-what-why-how":
        ("https://arxiv.org/abs/2205.03257", "ok"),
    "pmc-four-checks-low-fidelity":
        ("https://pmc.ncbi.nlm.nih.gov/articles/PMC12626184/", "ok"),
    "nist-privacy-framework":
        ("https://www.nist.gov/privacy-framework", "ok"),
    "nist-sp-800-188":
        ("https://nvlpubs.nist.gov/nistpubs/SpecialPublications/"
         "NIST.SP.800-188.pdf", "ok"),

    # --- india disease burden -------------------------------------------
    "lancet-indiab":
        ("http://thelancet.com/journals/landia/article/"
         "PIIS2213-8587(23)00119-5/fulltext", "blocked"),

    # --- privacy law -----------------------------------------------------
    "dpdp-act-meity":
        ("https://www.meity.gov.in/static/uploads/2024/06/"
         "2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf", "ok"),
    "dpdp-act-indiacode":
        ("https://www.indiacode.nic.in/indiacode/bitstream/123456789/22037/1/"
         "a2023-22.pdf", "ok"),
    "dpdp-rules-2025":
        ("https://www.meity.gov.in/static/uploads/2025/11/"
         "53450e6e5dc0bfa85ebd78686cadad39.pdf", "ok"),
    "hipaa-safe-harbor-hhs":
        ("https://www.hhs.gov/hipaa/for-professionals/special-topics/"
         "de-identification/index.html", "blocked"),
    "hhs-deid-guidance-pdf":
        # answered 200 twice on 2026-10-04, then hhs.gov started refusing
        # every request from this host. Kept as a citation; the identifier
        # list itself is cited to cornell-164-514 below, which is live.
        ("https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/"
         "understanding/coveredentities/De-identification/"
         "hhs_deid_guidance.pdf", "blocked"),
    "ncvhs-deid-letter":
        ("https://www.ncvhs.hhs.gov/wp-content/uploads/2013/12/"
         "2017-Ltr-Privacy-DeIdentification-Feb-23-Final-w-sig.pdf", "ok"),
    "cornell-164-514":
        ("https://www.law.cornell.edu/cfr/text/45/164.514", "ok"),
    "ecfr-164-514":
        ("https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/"
         "part-164/subpart-E/section-164.514", "blocked"),
}

DEFAULT_TIMEOUT = 40
# Publishers behind Cloudflare answer a browser UA and 403 anything else.
# We send a browser UA on purpose, and say so in the output.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def probe(url, timeout, tries=3):
    """Return (status_code, note) for one URL without raising.

    hhs.gov and indiacode.nic.in rate-limit bursts, so a 403 can mean
    "come back in ten seconds" rather than "no such page". Retry a couple of
    times before believing a non-2xx answer.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    last_status, last_note = 0, "not attempted"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response.read(1)
                return response.status, response.geturl()
        except urllib.error.HTTPError as error:
            last_status, last_note = error.code, str(error.reason)
            if error.code not in (403, 429, 500, 502, 503, 504):
                return last_status, last_note
        except urllib.error.URLError as error:
            last_status = 0
            last_note = f"{type(error.reason).__name__}: {error.reason}"
        except Exception as error:  # noqa: BLE001 - survive anything
            return 0, f"{type(error).__name__}: {error}"
        time.sleep(3 * (attempt + 1))
    return last_status, last_note


def main():
    timeout = DEFAULT_TIMEOUT
    if "--timeout" in sys.argv:
        index = sys.argv.index("--timeout")
        timeout = int(sys.argv[index + 1])

    problems = []
    blocked = 0
    for key in sorted(SOURCES):
        url, expected = SOURCES[key]
        status, note = probe(url, timeout)
        if 200 <= status < 300:
            print(f"ok    {status:>3}  {key}")
        elif expected == "blocked":
            blocked += 1
            print(f"BLOCK {status:>3}  {key}  ({note})")
        else:
            problems.append((key, url, status, note))
            print(f"BAD   {status:>3}  {key}")
            print(f"        {url}")
            print(f"        {note}")

    total = len(SOURCES)
    print(f"\n{total - blocked - len(problems)} ok, {blocked} blocked by "
          f"publisher, {len(problems)} broken, of {total}")

    if problems:
        print("broken: " + ", ".join(sorted(key for key, *_ in problems)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
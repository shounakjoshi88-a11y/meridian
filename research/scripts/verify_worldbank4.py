"""Round ten: build a real World Bank health panel with verified indicator codes.

Research helper only. Nothing here is imported by the app.

The earlier attempt used SH.DYN.LE00.M4, which is not a World Bank code; the API
answered 200 with an error object rather than a 4xx, which is exactly the trap
this project keeps hitting. So: pull the real indicator list first, then only
use codes that were observed in it.
"""

import pandas as pd
import requests

TIMEOUT = 240
UA = {"User-Agent": "meridian-dataset-research/1.0 (student project; non-commercial)"}


def get_json(url):
    r = requests.get(url, timeout=TIMEOUT, headers=UA)
    r.raise_for_status()
    return r.json()


def fetch_all_indicator_rows(code, source=2, per=1000):
    """Page through country/all for one indicator and return a tidy frame."""
    base = f"https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&source={source}&per_page={per}"
    p = get_json(base + "&page=1")
    if not (isinstance(p, list) and len(p) == 2 and "total" in p[0]):
        raise RuntimeError(f"{code}: unexpected payload {str(p)[:120]}")
    pages, rows = p[0]["pages"], list(p[1])
    for page in range(2, pages + 1):
        rows.extend(get_json(f"{base}&page={page}")[1])
    return p[0], pd.DataFrame(
        [{"country": x["country"]["value"], "iso3": x["countryiso3code"],
          "year": x["date"], "value": x["value"]} for x in rows]
    )


def main():
    print("=" * 100)
    print("STEP 1 - pull the real World Bank indicator list (source 2 = WDI)")
    print("=" * 100)
    rows = []
    page = 1
    while True:
        p = get_json(f"https://api.worldbank.org/v2/indicator?format=json&source=2&per_page=1000&page={page}")
        if not (isinstance(p, list) and len(p) == 2 and "total" in p[0]):
            break
        rows.extend([{"id": x["id"], "name": x["name"], "source": x["source"]["value"]}
                     for x in p[1]])
        if page >= p[0]["pages"]:
            break
        page += 1
    ind = pd.DataFrame(rows).drop_duplicates(subset=["id"])
    print(f"  fetched {len(ind):,} distinct indicators")

    wanted = ["SP.DYN.LE00.IN", "SP.DYN.MORT", "SP.DYN.TOTL.IN",
              "SH.DTH.COMM.ZS", "SH.DTH.NCOM.ZS", "SH.DTH.INJR.ZS",
              "SP.DYN.TFRT.IN", "SH.XPD.CHEX.GD.ZS", "SH.MED.PHYS.ZS",
              "SH.IMM.MEAS", "SH.IMM.IDPT", "SP.ADO.TFRT", "SH.STA.MMRT",
              "SH.DYN.AIDS.ZS", "SH.STA.DIAB.ZS", "SH.STA.BRTC.ZS"]
    print("\n  codes present in the live list:")
    good = []
    for code in wanted:
        hit = ind[ind["id"] == code]
        if len(hit):
            print(f"    OK   {code:<18} {hit.iloc[0]['name'][:78]}")
            good.append(code)
        else:
            print(f"    MISS {code:<18} (not in list)")

    print("\n  grepping the list for other mortality / burden indicators:")
    mask = ind["name"].str.contains("mortality|Cause of death", case=False, na=False)
    for _, r in ind[mask].head(28).iterrows():
        print(f"    {r['id']:<18} {r['name'][:92]}")
    print()

    print("=" * 100)
    print("STEP 2 - build a multi-indicator country-year panel")
    print("=" * 100)
    frames = []
    for code in good[:8]:
        try:
            meta, df = fetch_all_indicator_rows(code)
        except Exception as e:  # noqa: BLE001
            print(f"  {code:<18} FAILED {type(e).__name__}: {str(e)[:60]}")
            continue
        nn = df.dropna(subset=["value"])
        print(f"  {code:<18} api_total={meta['total']:>6}  pages={meta['pages']:<3} "
              f"raw={len(df):>6,}  non-null={len(nn):>6,}  "
              f"countries={nn['iso3'].nunique():>3}  years {nn['year'].min()}-{nn['year'].max()}")
        nn = nn.copy()
        nn["indicator"] = code
        frames.append(nn[["iso3", "country", "year", "value", "indicator"]])

    panel = pd.concat(frames, ignore_index=True)
    panel.to_csv("world_bank_health_panel.csv", index=False)
    print(f"\n  combined panel: {len(panel):,} rows x {len(panel.columns)} cols "
          f"({panel['indicator'].nunique()} indicators, {panel['iso3'].nunique()} countries)")
    print("  saved world_bank_health_panel.csv")

    ind_df = panel[panel["iso3"] == "IND"].copy()
    ind_df["year"] = ind_df["year"].astype(int)
    print(f"\n  INDIA slice: {len(ind_df):,} rows across {ind_df['indicator'].nunique()} indicators")
    le = ind_df[(ind_df["indicator"] == "SP.DYN.LE00.IN")].sort_values("year")
    if len(le):
        print(f"    life expectancy {le['year'].min()}-{le['year'].max()}: "
              f"{le.iloc[0]['value']} -> {le.iloc[-1]['value']}")
    print("\n  VERDICT: no key, no login, no DUA. JSON only -> flatten to CSV locally.")


if __name__ == "__main__":
    main()

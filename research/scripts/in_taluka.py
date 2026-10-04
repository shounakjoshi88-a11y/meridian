"""List real Nagpur CD blocks (tehsils) and towns from the verified Census 2011
CD-block workbook for district Nagpur.

Source URL was read out of the NADA catalogue page for catalog/41183.

Usage: python in_taluka.py
"""

import io
import re
import ssl
import sys
import urllib.request
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

URL = (
    "https://censusindia.gov.in/nada/index.php/catalog/41183/download/44814/"
    "PCA_CDB-2709-F-Census.xlsx"
)


def colkey(c):
    n = 0
    for ch in c:
        n = n * 26 + (ord(ch) - 64)
    return n


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300, context=CTX) as r:
        raw = r.read()
    print(f"GET {URL}\n  status=200 bytes={len(raw):,}")

    zf = zipfile.ZipFile(io.BytesIO(raw))
    names = zf.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        xml = zf.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        for si in re.findall(r"<si>(.*?)</si>", xml, re.S):
            shared.append(
                "".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))
                .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            )

    rows = []
    for n in sorted(x for x in names if re.match(r"xl/worksheets/sheet\d+\.xml$", x)):
        xml = zf.read(n).decode("utf-8", "replace")
        for rm in re.finditer(r'<row[^>]*?>(.*?)</row>', xml, re.S):
            cells = {}
            for cm in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*)(?:/>|>(.*?)</c>)',
                                  rm.group(1), re.S):
                body = cm.group(3) or ""
                v = re.search(r"<v>(.*?)</v>", body, re.S)
                if not v:
                    continue
                val = v.group(1)
                if 't="s"' in cm.group(2):
                    try:
                        val = shared[int(val)]
                    except (ValueError, IndexError):
                        pass
                cells[cm.group(1)] = val
            rows.append(cells)

    hdr = [rows[0][k] for k in sorted(rows[0], key=colkey)]
    idx = {h: i for i, h in enumerate(hdr)}
    print("  header:", ", ".join(hdr[:12]), "...")

    def cell(r, name):
        i = idx.get(name)
        if i is None:
            return ""
        ks = sorted(r, key=colkey)
        return r[ks[i]] if i < len(ks) else ""

    blocks, towns = {}, {}
    for r in rows[1:]:
        lvl = cell(r, "Level")
        nm = cell(r, "Name")
        cd = cell(r, "CD Block")
        if lvl == "CD BLOCK" and nm:
            blocks[cd] = nm
        elif lvl == "TOWN" and nm:
            towns[nm] = blocks.get(cd, "?")

    print(f"\nCD BLOCKS / tehsils in Nagpur district ({len(blocks)}):")
    for cd in sorted(blocks):
        print(f"   {cd}  {blocks[cd]}")

    print(f"\nTOWNS in Nagpur district ({len(towns)}):")
    for t in sorted(towns):
        print(f"   {t:<38} block={towns[t]}")


if __name__ == "__main__":
    main()
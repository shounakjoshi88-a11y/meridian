"""Pull the India age-distribution table out of a government PDF.

There is no PDF library here, so this reads only what a PDF makes easy:
uncompressed FlateDecode streams, searched for readable text. That is enough
for the National Health Profile demographic tables, which are ordinary text.

Taught concepts used: functions, strings, lists, for loops, bytes slicing,
imports (Lab 1-2). Research helper only.

Run it:

    python research/scripts/pdf_text_scrape.py <url> <first needle>
"""

import re
import ssl
import sys
import urllib.error
import urllib.request
import zlib

TIMEOUT = 90
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# PDF text operators we care about. A show-text operator is one of Tj, TJ or
# ' / ". Everything between parentheses is literal text, and hex strings
# <...> hold two-byte or one-byte glyph codes.
SHOW_TEXT = re.compile(rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>")


def download(url):
    """GET a URL and return (status, bytes), or (None, None)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.URLError as error:
        # censusindia.gov.in serves an incomplete certificate chain, so the
        # system bundle rejects it. certifi usually fixes it; if not, fall
        # back to an unverified context and say so loudly, because that
        # means we are no longer proving who we are talking to.
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
        except Exception:  # noqa: BLE001
            context = None
        if context is not None:
            try:
                with urllib.request.urlopen(
                    request, timeout=TIMEOUT, context=context
                ) as response:
                    return response.status, response.read()
            except Exception as retry_error:  # noqa: BLE001
                print(f"certifi retry failed: {type(retry_error).__name__}: "
                      f"{retry_error}")
        print("WARNING: certificate verification disabled for this fetch")
        loose = ssl._create_unverified_context()  # noqa: SLF001
        try:
            with urllib.request.urlopen(
                request, timeout=TIMEOUT, context=loose
            ) as response:
                return response.status, response.read()
        except Exception as error:  # noqa: BLE001
            print(f"FAIL  {type(error).__name__}: {error}")
            return None, None


def inflate_streams(blob):
    """Yield the decompressed body of every FlateDecode stream in a PDF."""
    marker = b"stream"
    position = 0
    while True:
        start = blob.find(marker, position)
        if start < 0:
            return
        # the keyword can be preceded by 'endstream' letters, so skip the
        # EOL that follows the keyword before the data begins
        head = start + len(marker)
        while head < len(blob) and blob[head] in (13, 10):
            head += 1
        tail = blob.find(b"endstream", head)
        if tail < 0:
            return
        chunk = blob[head:tail]
        position = tail + len(b"endstream")
        try:
            yield zlib.decompress(chunk)
        except zlib.error:
            # not every stream is flate, and some are truncated; skip them
            continue


def unescape(raw):
    """Turn the bytes inside a PDF literal string into text."""
    out = bytearray()
    index = 0
    while index < len(raw):
        byte = raw[index]
        if byte == 0x5C and index + 1 < len(raw):   # backslash
            nxt = raw[index + 1]
            mapping = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
            if nxt in mapping:
                out.append(mapping[nxt])
                index += 2
                continue
            if 0x30 <= nxt <= 0x37:                # octal escape
                digits = raw[index + 1:index + 4]
                digits = bytes(d for d in digits if 0x30 <= d <= 0x37)
                out.append(int(digits, 8) & 0xFF)
                index += 1 + len(digits)
                continue
            out.append(nxt)
            index += 2
            continue
        out.append(byte)
        index += 1
    return bytes(out)


def stream_to_text(data):
    """Extract visible text from one decompressed content stream."""
    pieces = []
    for match in SHOW_TEXT.finditer(data):
        token = match.group(0)
        if token.startswith(b"<"):
            digits = re.sub(rb"\s", b"", token[1:-1])
            if len(digits) % 4 == 0:      # two-byte glyph codes
                codes = [
                    int(digits[i:i + 4], 16) for i in range(0, len(digits), 4)
                ]
                pieces.append(
                    "".join(chr(c) for c in codes if 32 <= c < 0x2FF80)
                )
            elif len(digits) % 2 == 0:    # one-byte glyph codes
                codes = [
                    int(digits[i:i + 2], 16) for i in range(0, len(digits), 2)
                ]
                pieces.append(
                    "".join(chr(c) for c in codes if 32 <= c < 0x2FF80)
                )
            continue
        pieces.append(unescape(token[1:-1]).decode("latin-1", "replace"))
        pieces.append(" ")
    return "".join(pieces)


def readable_page(text):
    """Keep the parts that look like prose or a table, not font noise."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9.,%()/:-]{1,40}", text)
    return " ".join(words)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    url = sys.argv[1]
    needles = sys.argv[2:]

    status, blob = download(url)
    if blob is None:
        return 1
    print(f"HTTP {status}  {len(blob)} bytes  {url}")

    pages = []
    for data in inflate_streams(blob):
        text = readable_page(stream_to_text(data))
        if len(text) > 40:
            pages.append(text)

    print(f"pages with text: {len(pages)}")
    for number, text in enumerate(pages, start=1):
        if not needles:
            if number <= 3:
                print(f"\n--- page {number} ---\n{text[:1500]}")
            continue
        low = text.lower()
        if any(needle.lower() in low for needle in needles):
            print(f"\n--- page {number} ---\n{text[:4000]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
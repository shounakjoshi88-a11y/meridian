"""Check that every out-of-syllabus import has an explainer in docs/concepts.

Taught concepts: os (Lab 4), string methods (Lab 2), loops and dicts.

Run from the project root:  python scripts/check_concept_coverage.py
Exits 1 if any import lacks documentation.
"""

import os
import re

BACKEND = "backend"
SCRIPTS = "scripts"
DOCS = os.path.join("docs", "concepts")

# Standard library modules. csv, shutil, zipfile, random and math are
# documented because the labs did not cover them; the rest need no
# explainer.
STDLIB_NEEDS_DOC = {"csv", "shutil", "zipfile", "random", "math"}

# Documented by a file in docs/concepts/. Keys are imported module names.
# Values are file stems. A module may map to several docs when one library
# needed more than one explainer, e.g. pandas needed both select_dtypes
# and na_values explained separately.
DOCUMENTED = {
    "flask": ["flask"],
    "csv": ["csv-module"],
    "shutil": ["shutil-and-zipfile"],
    "zipfile": ["shutil-and-zipfile"],
    "random": ["random-and-math"],
    "math": ["random-and-math"],
    "matplotlib": ["matplotlib-basics"],
    "pyplot": ["matplotlib-basics"],
    "requests": ["requests"],
    "json": ["json"],
    # Lab 6 covered the pandas basics. These two docs cover the parts
    # the lab did not reach.
    "pandas": ["pandas-select-dtypes", "pandas-missing-values"],
    "pd": ["pandas-select-dtypes", "pandas-missing-values"],
    "select_dtypes": ["pandas-select-dtypes"],
    "na_values": ["pandas-missing-values"],
    "keep_default_na": ["pandas-missing-values"],
}

# Modules that are our own code, not third party.
LOCAL = {"store", "triage", "registry", "analytics", "models", "app"}

# Ignored: typing, testing plumbing, and standard library modules the labs
# never name. colorsys arrived with check_contrast.py, which needs it to
# turn the HSL design tokens into RGB before measuring contrast. It is
# stdlib and belongs here rather than in a concept explainer.
SKIP = {"typing", "unittest", "__future__", "io", "sys", "os", "re",
        "datetime", "colorsys", "tokenize", "atexit", "hashlib", "time"}

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w]*)")


def imports_in(source):
    """Yield (module_name, line_number) for each real import statement.

    Uses the tokenizer rather than a regular expression over the text. A
    regex cannot tell an import from a line of English that happens to start
    with "from", which is not a hypothetical: a docstring here contained the
    sentence "from the same pass over the same rows" and it was reported as
    an import of a module named "the".

    tokenize labels that sentence as string content and a real import as a
    NAME token, so the two cannot be confused.
    """
    import io
    import tokenize

    found = []
    mode = None          # None, "from" or "import"
    want_name = False

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # An unreadable file still gets scanned as text. Reporting a few
        # spurious imports beats reporting none at all.
        for number, line in enumerate(source.splitlines(), start=1):
            match = IMPORT_RE.match(line)

            if match:
                found.append((match.group(1), number))

        return found

    for token in tokens:
        # A statement ends at the newline. Everything inside it is one of
        # the forms below, so nothing after it is considered.
        if token.type in (tokenize.NEWLINE, tokenize.NL) and token.line.strip():
            mode = None
            want_name = False
            continue

        if token.type != tokenize.NAME:
            # A comma means another name in the same statement: "import a, b"
            if token.type == tokenize.OP and token.string == "," and mode:
                want_name = True
            continue

        if token.string == "from" and not mode:
            mode = "from"
            want_name = True
            continue

        if token.string == "import" and not mode:
            mode = "import"
            # "import x" names x next. "from x import y" has already named
            # x, so this import keyword ends the module part.
            want_name = True
            continue

        if want_name:
            # For "from x import y", only x is a module. y is a name inside
            # x, and recording it would report jsonify and Flask as modules
            # in their own right.
            if mode == "from":
                found.append((token.string, token.start[0]))
                mode = "names"
                want_name = False
            elif mode == "import":
                found.append((token.string, token.start[0]))
                want_name = False
            else:
                want_name = False

    return found


def scan(directory):
    """Yield (module_name, relative_path) for each import found."""
    found = {}

    if not os.path.isdir(directory):
        return found

    for name in sorted(os.listdir(directory)):
        if not name.endswith(".py"):
            continue

        path = os.path.join(directory, name)

        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        for module, number in imports_in(source):
            if module in LOCAL or module in SKIP:
                continue

            found.setdefault(module, []).append(f"{path}:{number}")

    return found


def main():
    doc_dir = DOCS

    if not os.path.isdir(doc_dir):
        print(f"no such directory: {doc_dir}")
        return 1

    imports = {}
    for directory in (BACKEND, SCRIPTS):
        for module, places in scan(directory).items():
            imports.setdefault(module, []).extend(places)

    print("=" * 66)
    print("Concept coverage check")
    print("=" * 66)

    undocumented = []
    noted = []

    for module in sorted(imports):
        places = imports[module]
        docs = DOCUMENTED.get(module)

        if docs:
            missing = [d for d in docs
                       if not os.path.exists(os.path.join(doc_dir, f"{d}.md"))]

            if missing:
                listed = ", ".join(f"{d}.md" for d in missing)
                print(f"[FAIL] {module:<16} -> {listed} MISSING")
                undocumented.append(module)
            else:
                listed = ", ".join(f"{d}.md" for d in docs)
                print(f"[ok  ] {module:<16} -> {listed}")
        elif module in STDLIB_NEEDS_DOC:
            print(f"[FAIL] {module:<16} -> stdlib, but no doc mapped")
            undocumented.append(module)
        else:
            print(f"[??  ] {module:<16} -> not in the documented map")
            noted.append(module)

    print()
    print(f"{len(imports)} distinct modules imported")
    print(f"documented     : {len(imports) - len(undocumented) - len(noted)}")
    print(f"unmapped       : {len(noted)}")
    print(f"undocumented   : {len(undocumented)}")

    if noted:
        print()
        print("Unmapped modules. If these are stdlib or project-local, add them")
        print("to SKIP in this script. If they are genuinely new, add a doc:")
        for module in noted:
            places = imports[module]
            print(f"  - {module}  (first used at {places[0]})")

    if undocumented:
        print()
        print("Add an explainer for each of these before submitting:")
        for module in undocumented:
            print(f"  - {module}  (used at {', '.join(imports[module])})")
        print("=" * 66)
        return 1

    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Re-probe every URL cited in 02-symptom-disease.md and print a dated table.

Run this before trusting the notes. Any row with a non-200 status or an
ERROR line must be marked UNVERIFIED in the notes.

Usage: python verify_all_urls.py
"""

from __future__ import annotations

import datetime
import sys

from probe import probe

URLS = [
    # (label, url, method) -- method defaults to HEAD. Monarch's API answers
    # 405 Method Not Allowed to HEAD but 200 to GET, so it is probed with GET.
    # ---- HPO ontology ----
    ("HPO ontology (OBO Foundry PURL)", "https://purl.obolibrary.org/obo/hp.obo", "HEAD"),
    ("HPO ontology (GitHub release, same bytes)",
     "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/hp.obo", "HEAD"),
    ("HPO ontology (OWL)", "https://purl.obolibrary.org/obo/hp.owl", "HEAD"),
    # ---- HPO annotations ----
    ("HPOA annotations (phenotype.hpoa)",
     "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype.hpoa", "HEAD"),
    ("HPOA gene xref (genes_to_phenotype.txt)",
     "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/genes_to_phenotype.txt", "HEAD"),
    ("HPOA phenotype xref (phenotype_to_genes.txt)",
     "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype_to_genes.txt", "HEAD"),
    ("HPO licence pointer cited inside hp.obo (expected DEAD)",
     "https://hpo.jax.org/app/license", "HEAD"),
    ("HPO project homepage", "http://www.human-phenotype-ontology.org", "HEAD"),
    ("HPO repo LICENSE.md", "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md", "HEAD"),
    ("OBO Foundry entry for HPO", "http://obofoundry.org/ontology/hp.html", "HEAD"),
    ("Open Targets data-source licence table",
     "https://platform-docs.opentargets.org/licence.md", "HEAD"),
    # ---- Monarch (GET only: returns 405 to HEAD) ----
    ("Monarch v3 entity endpoint",
     "https://api.monarchinitiative.org/v3/api/entity/MONDO:0005148", "GET"),
    ("Monarch v3 disease->phenotype associations",
     "https://api.monarchinitiative.org/v3/api/association?category=biolink:DiseaseToPhenotypicFeatureAssociation&limit=1", "GET"),
    # ---- MONDO ----
    ("MONDO ontology", "https://purl.obolibrary.org/obo/mondo.obo", "HEAD"),
    # ---- MedGen ----
    ("MedGen FTP root", "https://ftp.ncbi.nlm.nih.gov/pub/medgen/", "HEAD"),
    ("MedGen disease-concept source list",
     "https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGen_Sources.txt", "HEAD"),
    ("MedGen file README", "https://ftp.ncbi.nlm.nih.gov/pub/medgen/README.txt", "HEAD"),
    ("MedGen HPO <-> CUI mapping",
     "https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGen_HPO_Mapping.txt.gz", "HEAD"),
    ("MedGen HPO <-> OMIM mapping",
     "https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGen_HPO_OMIM_Mapping.txt.gz", "HEAD"),
    ("MedGen ID mappings", "https://ftp.ncbi.nlm.nih.gov/pub/medgen/MedGenIDMappings.txt.gz", "HEAD"),
    ("NCBI policies / copyright status",
     "https://www.ncbi.nlm.nih.gov/home/about/policies/", "HEAD"),
    # ---- Orphanet ----
    ("Orphadata homepage", "https://www.orphadata.com", "HEAD"),
    ("Orphadata Science file catalogue",
     "https://sciences.orphadata.com/orphanet-scientific-knowledge-files", "HEAD"),
    ("Orphadata Science portal", "https://sciences.orphadata.com/", "HEAD"),
    ("Orphanet product4, Git LFS media endpoint (real bytes)",
     "https://media.githubusercontent.com/media/Orphanet/Orphadata_aggregated/master/Rare%20diseases%20with%20associated%20phenotypes/en_product4.xml", "HEAD"),
    ("Orphanet product4, raw endpoint (LFS POINTER only, 133 B)",
     "https://raw.githubusercontent.com/Orphanet/Orphadata_aggregated/master/Rare%20diseases%20with%20associated%20phenotypes/en_product4.xml", "HEAD"),
    ("Orphanet HOOM module",
     "https://raw.githubusercontent.com/Orphanet/Orphadata_aggregated/refs/heads/master/Orphanet%20Ontologies/HOOM/hoom_orphanet_2.5..zip", "HEAD"),
    ("Orphanet aggregated repo", "https://github.com/Orphanet/Orphadata_aggregated", "HEAD"),
    # ---- UMLS ----
    ("UMLS Metathesaurus licence agreement (HTML)",
     "https://www.nlm.nih.gov/research/umls/knowledge_sources/metathesaurus/release/license_agreement.html", "HEAD"),
    ("UMLS Metathesaurus licence agreement (2026AA PDF)",
     "https://uts.nlm.nih.gov/uts/assets/LicenseAgreement.pdf", "HEAD"),
    ("UMLS how to license and access",
     "https://www.nlm.nih.gov/databases/umls.html", "HEAD"),
    ("UMLS Terminology Services (login wall)",
     "https://uts.nlm.nih.gov/uts/", "HEAD"),
    # ---- DisGeNET ----
    ("DisGeNET plans", "https://disgenet.com/plans", "HEAD"),
    ("DisGeNET legal / data sources", "https://disgenet.com/Legal", "HEAD"),
    ("DisGeNET commercial licence + redistribution FAQ",
     "https://support.disgenet.com/support/solutions/articles/202000087487-do-i-need-a-commercial-license-can-i-use-disgenet-data-in-my-product-", "HEAD"),
]


def main() -> int:
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"URL verification run: {stamp}\n")
    hdr = (f"{'label':<52} {'m':<5} {'code':<5} {'bytes':>12}  {'content-type':<28}")
    print(hdr)
    print("-" * len(hdr))
    bad = 0
    for label, url, method in URLS:
        o = probe(url, method, timeout=90)
        code = o["status"] or "ERR"
        if code != "200":
            bad += 1
        size = o["content_length"] or "-"
        print(f"{label:<52} {method:<5} {code:<5} {size:>12}  "
              f"{o['content_type'][:28]:<28}")
        if o["error"]:
            print(f"{'':<52} {o['error']}")
    print(f"\n{bad} of {len(URLS)} URLs did not return 200.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
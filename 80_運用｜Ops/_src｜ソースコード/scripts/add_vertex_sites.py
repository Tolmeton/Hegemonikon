#!/usr/bin/env python3
"""Add target sites to Vertex AI Search Data Store via Discovery Engine API.

Adds the domains from deep_research_synthesis R01/R04/R08 to the
specified data store for comprehensive search coverage.

Usage:
    # Default (makaron8426):
    python scripts/add_vertex_sites.py

    # Tolmeton:
    python scripts/add_vertex_sites.py \
        --account Tolmetes@hegemonikon.org \
        --project 97057192576 \
        --data-store periskope-web-ds

    # movement8426:
    python scripts/add_vertex_sites.py \
        --account movement8426@gmail.com \
        --project 1003263550004 \
        --data-store periskope-web-ds_1771922691888
"""

import argparse
import subprocess
import json
import time
import sys

import httpx

# === Defaults (makaron8426) ===
DEFAULT_PROJECT = "951023173830"
DEFAULT_LOCATION = "global"
DEFAULT_DATA_STORE = "hgk-data-store_1771900430858"

# === Domain list from deep_research_synthesis R01/R04/R08 ===

DOMAINS = {
    # R08: Academic — Active Inference
    "activeinference.institute": "Active Inference Institute",
    "verses.ai": "VERSES AI (active inference)",

    # R08: Academic — Computational Psychiatry
    "gatsby.ucl.ac.uk": "UCL Gatsby Unit",

    # R08: Academic — Category Theory / ACT
    "appliedcategorytheory.org": "Applied Category Theory",
    "ncatlab.org": "nLab (category theory wiki)",

    # R08: Academic — Open Access Search
    "doaj.org": "Directory of Open Access Journals",
    "core.ac.uk": "CORE (open access aggregator)",
    "base-search.net": "BASE (Bielefeld Academic Search)",

    # R08: Academic — Preprints
    "arxiv.org": "arXiv",
    "biorxiv.org": "bioRxiv",
    "medrxiv.org": "medRxiv",
    "philpapers.org": "PhilPapers",

    # R08: Academic — Journals & Proceedings
    "nature.com": "Nature",
    "science.org": "Science",
    "pnas.org": "PNAS",
    "frontiersin.org": "Frontiers",
    "plos.org": "PLOS",
    "mdpi.com": "MDPI",

    # R08: Academic — FEP / Neuroscience
    "fil.ion.ucl.ac.uk": "UCL FIL (Karl Friston)",
    "neuralcorrelates.com": "Neural Correlates",

    # R04: English Niche — AI Safety / Rationality
    "lesswrong.com": "LessWrong",
    "alignmentforum.org": "Alignment Forum",
    "distill.pub": "Distill (ML explainability)",

    # R04: English Niche — Long-form Thought
    "substack.com": "Substack",

    # R04: English Niche — Technical
    "mlst.tv": "Machine Learning Street Talk",

    # R01: Japanese Niche — Tech
    "qiita.com": "Qiita",
    "zenn.dev": "Zenn",
    "crieit.net": "Crieit",
    "scrapbox.io": "Scrapbox (public projects)",

    # HGK Core
    "modelcontextprotocol.io": "Model Context Protocol",

    # Developer Documentation
    "docs.anthropic.com": "Anthropic Docs",
    "docs.google.com": "Google Docs",
    "cloud.google.com": "Google Cloud Docs",
    "huggingface.co": "Hugging Face",

    # AI/ML Research
    "openreview.net": "OpenReview",
    "paperswithcode.com": "Papers With Code",
    "semanticscholar.org": "Semantic Scholar",
}

def get_token(account: str = "") -> str:
    """Get gcloud access token, optionally for a specific account."""
    cmd = ["gcloud", "auth", "print-access-token"]
    if account:
        cmd.append(f"--account={account}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        print(f"ERROR: gcloud auth failed: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Add target sites to Vertex AI Search Data Store"
    )
    parser.add_argument(
        "--account", default="",
        help="GCP account email (e.g., Tolmetes@hegemonikon.org)"
    )
    parser.add_argument(
        "--project", default=DEFAULT_PROJECT,
        help=f"GCP project number (default: {DEFAULT_PROJECT})"
    )
    parser.add_argument(
        "--data-store", default=DEFAULT_DATA_STORE,
        help=f"Data store ID (default: {DEFAULT_DATA_STORE})"
    )
    parser.add_argument(
        "--location", default=DEFAULT_LOCATION,
        help=f"Location (default: {DEFAULT_LOCATION})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List domains without adding"
    )
    args = parser.parse_args()

    # Build base URL
    base_url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{args.project}"
        f"/locations/{args.location}/collections/default_collection"
        f"/dataStores/{args.data_store}/siteSearchEngine"
    )

    print(f"=== Configuration ===")
    print(f"  Account:    {args.account or '(default/ADC)'}")
    print(f"  Project:    {args.project}")
    print(f"  Data Store: {args.data_store}")
    print(f"  Location:   {args.location}")
    print(f"  Domains:    {len(DOMAINS)}")

    if args.dry_run:
        print("\n=== Dry Run — Domains to add ===")
        for domain, desc in DOMAINS.items():
            print(f"  {domain} — {desc}")
        return

    token = get_token(args.account)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    # Add quota project header for user-account tokens
    if args.account:
        # Derive project ID from project number — need the actual project ID
        # For now, use the project number itself (works for most APIs)
        headers["x-goog-user-project"] = args.project

    client = httpx.Client(timeout=15.0)

    # Step 1: List existing target sites
    print("\n=== Existing target sites ===")
    existing_uris = set()
    try:
        resp = client.get(f"{base_url}/targetSites", headers=headers)
        resp.raise_for_status()
        existing = resp.json()
        for site in existing.get("targetSites", []):
            uri = site.get("providedUriPattern", "")
            existing_uris.add(uri)
            print(f"  ✓ {uri}")
        print(f"  Total existing: {len(existing_uris)}")
    except Exception as e:
        print(f"  Warning: Could not list existing sites: {e}")

    # Step 2: Add new domains
    print("\n=== Adding new domains ===")
    added = 0
    skipped = 0
    failed = 0

    for domain, description in DOMAINS.items():
        uri_pattern = f"{domain}/*"

        if uri_pattern in existing_uris:
            print(f"  → {domain} (already exists, skipping)")
            skipped += 1
            continue

        payload = {
            "providedUriPattern": uri_pattern,
            "type": "INCLUDE",
        }

        try:
            resp = client.post(
                f"{base_url}/targetSites",
                headers=headers,
                json=payload,
            )
            if resp.status_code in (200, 201):
                print(f"  ✓ {domain} — {description}")
                added += 1
            elif resp.status_code == 409:
                print(f"  → {domain} (already exists)")
                skipped += 1
            else:
                error_msg = resp.json().get("error", {}).get("message", resp.text[:100])
                print(f"  ✗ {domain} — HTTP {resp.status_code}: {error_msg}")
                failed += 1
        except Exception as e:
            print(f"  ✗ {domain} — {e}")
            failed += 1

        # Rate limiting: 0.5s between requests
        time.sleep(0.5)

    # Summary
    print(f"\n=== Summary ===")
    print(f"  Added:   {added}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print(f"  Total domains in list: {len(DOMAINS)}")

    client.close()


if __name__ == "__main__":
    main()

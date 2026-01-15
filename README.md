XML Clone Tool
=================

This repository contains a minimal tool to clone two supplier XML feeds and produce two output files without any schema transformation or data loss. Only a fixed prefix is added to barcode/SKU fields.

Outputs
- ebi_out.xml
- tkt_out.xml

These files are committed to the repository and can be published via GitHub Pages. The URLs will be:

- https://<github_user>.github.io/<repo_name>/ebi_out.xml
- https://<github_user>.github.io/<repo_name>/tkt_out.xml

How it works
- The `make_clone_xmls.py` script fetches the supplier feeds, prefixes barcode/Sku values with `isteburada_`, and writes `ebi_out.xml` and `tkt_out.xml` in the repository root. Writes are atomic (temp file + rename) so partial files are never published.
- A GitHub Action (`.github/workflows/clone.yml`) runs the script on schedule and commits+pushes changed output files.

Schedule (Turkey time)
- Runs at: 07:50, 11:50, 16:50, 20:50, 23:30 (TR = UTC+3). The workflow cron uses UTC times accordingly.

Local testing
- Install dependencies:
  python -m pip install -r requirements.txt
- Run locally:
  python make_clone_xmls.py --config config.yaml

Notes
- This repo contains only the clone tool and the GitHub Actions workflow. Other tools (e.g., `update_xml.py`, `validate_output.py`) are intentionally not part of the default workflow.
- Make sure GitHub Pages is enabled (Settings -> Pages -> main branch / root) to publish the outputs.

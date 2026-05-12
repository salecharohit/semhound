import argparse
import shutil
import sys

from .ai_client import get_ai_client
from .scanner import discover_repos, download_rules, run_preflight, run_scan


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="semhound",
        description=(
            "Scan every repository across one or more GitHub organisations or users "
            "using Semgrep rules."
        ),
    )
    parser.add_argument(
        "github_targets",
        nargs="*",
        metavar="ORG_OR_USER",
        help=(
            "One or more GitHub organization or username targets to scan "
            "(e.g. my-org another-org someuser)"
        ),
    )
    parser.add_argument(
        "--orgs-file",
        default=None,
        metavar="PATH",
        help=(
            "Path to a text file listing GitHub org names to scan, one per line. "
            "Blank lines and lines starting with '#' are ignored. "
            "Can be combined with inline ORG_OR_USER arguments."
        ),
    )
    parser.add_argument(
        "--rules-dir",
        default=None,
        metavar="PATH",
        help="Path to a local folder containing Semgrep .yaml rule files",
    )
    parser.add_argument(
        "--rules-url",
        action="append",
        default=[],
        metavar="URL",
        help=(
            "HTTPS URL of a Semgrep .yaml rule file to download before scanning. "
            "Can be specified multiple times to download several rules."
        ),
    )
    parser.add_argument(
        "--ai-config",
        default=None,
        metavar="PATH",
        help="Path to AI config file (ai.config). Omit to skip AI analysis.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=5,
        metavar="N",
        help="Number of parallel worker threads (default: 5)",
    )
    parser.add_argument(
        "--sarif",
        action="store_true",
        default=False,
        help="Also write a SARIF 2.1.0 report (<target>_scan.sarif) alongside the CSV",
    )
    args = parser.parse_args()

    targets: list[str] = list(args.github_targets)

    if args.orgs_file:
        try:
            with open(args.orgs_file, encoding="utf-8") as fh:
                for line in fh:
                    name = line.strip()
                    if name and not name.startswith("#"):
                        targets.append(name)
        except OSError as exc:
            parser.error(f"Cannot read --orgs-file: {exc}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_targets: list[str] = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            unique_targets.append(t)
    targets = unique_targets

    if not targets:
        parser.error(
            "At least one GitHub org or username must be provided "
            "(inline or via --orgs-file)."
        )

    if not args.rules_dir and not args.rules_url:
        parser.error("At least one of --rules-dir or --rules-url must be provided.")

    for url in args.rules_url:
        if not url.lower().startswith("https://"):
            parser.error(f"--rules-url only accepts HTTPS URLs: {url}")

    run_preflight()

    rules_sources: list[str] = []
    if args.rules_dir:
        rules_sources.append(args.rules_dir)

    downloaded_tmpdir: str | None = None
    if args.rules_url:
        try:
            downloaded_tmpdir = download_rules(args.rules_url)
            rules_sources.append(downloaded_tmpdir)
        except (ValueError, RuntimeError) as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)

    try:
        ai_client = get_ai_client(args.ai_config)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    if ai_client is None:
        print("[info] No --ai-config provided; AI analysis will be skipped.")

    try:
        for target in targets:
            print(f"\n[info] Discovering repositories for '{target}' ...")
            repos = discover_repos(target)
            print(f"[info] Found {len(repos)} repository/repositories.")
            run_scan(repos, target, rules_sources, ai_client, args.threads, output_sarif=args.sarif)
    finally:
        if downloaded_tmpdir:
            shutil.rmtree(downloaded_tmpdir, ignore_errors=True)

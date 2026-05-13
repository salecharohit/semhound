import csv
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .ai_client import BaseAIClient

_MAX_RETRIES = 3


_TOOL_INSTALL = {
    "gh": {
        "name": "GitHub CLI",
        "url": "https://cli.github.com",
        "mac": "brew install gh",
        "linux": "sudo apt install gh          # Debian/Ubuntu (apt.cli.github.com)\n"
                 "             sudo dnf install gh          # Fedora/RHEL\n"
                 "             See https://github.com/cli/cli/blob/trunk/docs/install_linux.md",
        "windows": "winget install --id GitHub.cli\n"
                   "             # or: choco install gh",
    },
    "git": {
        "name": "Git",
        "url": "https://git-scm.com",
        "mac": "brew install git",
        "linux": "sudo apt install git         # Debian/Ubuntu\n"
                 "             sudo dnf install git         # Fedora/RHEL",
        "windows": "winget install --id Git.Git\n"
                   "             # or: choco install git  — then restart your terminal",
    },
    "semgrep": {
        "name": "Semgrep",
        "url": "https://semgrep.dev",
        "mac": "brew install semgrep\n"
               "             # or: pip install semgrep",
        "linux": "pip install semgrep",
        "windows": "pip install semgrep",
    },
    "ssh": {
        "name": "OpenSSH client",
        "url": "https://www.openssh.com",
        "mac": "ssh ships with macOS — no install needed",
        "linux": "sudo apt install openssh-client   # Debian/Ubuntu\n"
                 "             sudo dnf install openssh              # Fedora/RHEL",
        "windows": "# OpenSSH ships with Windows 10/11. If missing, run in PowerShell (Admin):\n"
                   "             Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0",
    },
}


def _print_install_hint(tool: str, system: str) -> None:
    info = _TOOL_INSTALL.get(tool, {"name": tool, "url": "", "mac": "", "linux": "", "windows": ""})
    if system == "Darwin":
        cmd = info.get("mac", "")
    elif system == "Windows":
        cmd = info.get("windows", "")
    else:
        cmd = info.get("linux", "")
    print(f"\n  {info['name']} — {info['url']}", file=sys.stderr)
    print(f"  Install: {cmd}", file=sys.stderr)


def run_preflight() -> None:
    import platform
    system = platform.system()

    missing = [t for t in ("gh", "git", "semgrep", "ssh") if shutil.which(t) is None]
    if missing:
        print("[error] The following required tools are missing from PATH:", file=sys.stderr)
        for tool in missing:
            _print_install_hint(tool, system)
        print(file=sys.stderr)
        print("  Install the tools above, then re-run semhound.", file=sys.stderr)
        sys.exit(1)

    auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if auth.returncode != 0:
        print("[error] GitHub CLI is not authenticated.", file=sys.stderr)
        print("  Run:  gh auth login", file=sys.stderr)
        print("  Docs: https://cli.github.com/manual/gh_auth_login", file=sys.stderr)
        sys.exit(1)

    # Warn if the token is visibly missing scopes semhound needs.
    # Fine-grained PATs may not list scopes, so only warn when we can
    # positively confirm scopes are present but the required ones are absent.
    auth_output = auth.stdout + auth.stderr
    if "Token scopes:" in auth_output:
        missing_scopes = [s for s in ("repo", "read:org") if f"'{s}'" not in auth_output]
        if missing_scopes:
            print(
                f"[warn] GitHub token may be missing scopes: {', '.join(missing_scopes)}",
                file=sys.stderr,
            )
            print(
                "  Private repos and org membership require these scopes.",
                file=sys.stderr,
            )
            print(
                f"  Re-authenticate if needed:  gh auth login --scopes {','.join(missing_scopes)}",
                file=sys.stderr,
            )

    result = subprocess.run(
        ["ssh", "-T", "-o", "StrictHostKeyChecking=no", "git@github.com"],
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    if "Hi " not in combined:
        print("[error] GitHub SSH authentication failed.", file=sys.stderr)
        if "Permission denied" in combined:
            print(
                "  Your SSH key is not registered with GitHub or does not have access.",
                file=sys.stderr,
            )
            print("  Add your public key at: https://github.com/settings/keys", file=sys.stderr)
        elif "Connection refused" in combined or "timed out" in combined.lower():
            print(
                "  Could not reach GitHub over SSH — port 22 may be blocked by your network.",
                file=sys.stderr,
            )
            print(
                "  Try SSH over HTTPS port 443: "
                "https://docs.github.com/en/authentication/troubleshooting-ssh/using-ssh-over-the-https-port",
                file=sys.stderr,
            )
        else:
            print(
                "  Ensure an SSH key is added to your GitHub account:",
                file=sys.stderr,
            )
            print(
                "  https://docs.github.com/en/authentication/connecting-to-github-with-ssh",
                file=sys.stderr,
            )
        print(f"  SSH output: {combined.strip()}", file=sys.stderr)
        sys.exit(1)


def discover_repos(target: str) -> list[dict]:
    result = subprocess.run(
        ["gh", "repo", "list", target, "--limit", "1000", "--json", "sshUrl,name,defaultBranchRef"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout).strip()
        err_lower = err.lower()
        if "could not resolve" in err_lower or "not found" in err_lower:
            print(
                f"[error] '{target}' was not found on GitHub. "
                "Check the org name or username spelling.",
                file=sys.stderr,
            )
        elif (
            "must have admin rights" in err_lower
            or "permission" in err_lower
            or "403" in err
            or "forbidden" in err_lower
        ):
            print(
                f"[error] Permission denied when listing repositories for '{target}'.",
                file=sys.stderr,
            )
            print(
                "  Your GitHub token may be missing the 'repo' or 'read:org' scope.",
                file=sys.stderr,
            )
            print(
                "  Re-authenticate:  gh auth login --scopes repo,read:org",
                file=sys.stderr,
            )
        elif "token" in err_lower and ("scope" in err_lower or "grant" in err_lower):
            print(
                f"[error] GitHub token lacks the required scopes to list repositories for '{target}'.",
                file=sys.stderr,
            )
            print(
                "  Re-authenticate:  gh auth login --scopes repo,read:org",
                file=sys.stderr,
            )
        elif "rate limit" in err_lower or "429" in err:
            print(
                "[error] GitHub API rate limit exceeded. Wait a few minutes and retry.",
                file=sys.stderr,
            )
        else:
            print(
                f"[error] Failed to list repositories for '{target}': {err}",
                file=sys.stderr,
            )
        sys.exit(1)

    raw = json.loads(result.stdout)
    repos = []
    for r in raw:
        branch_ref = r.get("defaultBranchRef") or {}
        repos.append({
            "name": r["name"],
            "sshUrl": r["sshUrl"],
            "defaultBranch": branch_ref.get("name", "main"),
        })
    return repos


def download_rules(urls: list[str]) -> str:
    """Download semgrep rule files from HTTPS URLs into a new temp directory.

    Returns the temp directory path. Caller is responsible for cleanup.
    """
    tmpdir = tempfile.mkdtemp(prefix="semhound_rules_")
    for url in urls:
        if not url.lower().startswith("https://"):
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise ValueError(f"Only HTTPS URLs are allowed for rule downloads: {url}")
        filename = Path(url.split("?")[0]).name or "rule.yaml"
        dest = Path(tmpdir) / filename
        counter = 1
        while dest.exists():
            dest = Path(tmpdir) / f"{dest.stem}_{counter}{dest.suffix}"
            counter += 1
        print(f"[info] Downloading rule: {url}")
        try:
            urllib.request.urlretrieve(url, dest)  # noqa: S310 – URL validated above
        except urllib.error.URLError as exc:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise RuntimeError(f"Failed to download rule from {url}: {exc}") from exc
    return tmpdir


def _run_cmd(
    args: list,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, returncode=-1, stdout="", stderr="timed out")


def _analyze_with_retry(
    ai_client: BaseAIClient,
    snippet: str,
    message: str,
    name: str,
    rule_id: str,
) -> tuple[str, str]:
    for attempt in range(_MAX_RETRIES):
        try:
            confidence, true_positive = ai_client.analyze(snippet, message)
            if confidence != "ERROR":
                return confidence, true_positive
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** attempt
                tqdm.write(f"  [retry]   {name} — {rule_id} (attempt {attempt + 1}, retrying in {wait}s)")
                time.sleep(wait)
        except Exception as exc:
            if attempt < _MAX_RETRIES - 1:
                wait = 2 ** attempt
                tqdm.write(f"  [retry]   {name} — {rule_id} (attempt {attempt + 1}, error: {str(exc)[:60]}, retrying in {wait}s)")
                time.sleep(wait)
            else:
                return "ERROR", str(exc)[:80]
    return "ERROR", "ERROR"


def _write_sarif(results: list[dict], output_file: str) -> None:
    rules_seen: dict[str, str] = {}
    for r in results:
        rules_seen.setdefault(r["rule_id"], r["message"])

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "semhound",
                    "version": "0.1.0",
                    "rules": [
                        {
                            "id": rid,
                            "shortDescription": {"text": msg[:200]},
                            "fullDescription": {"text": msg},
                        }
                        for rid, msg in rules_seen.items()
                    ],
                }
            },
            "results": [
                {
                    "ruleId": r["rule_id"],
                    "message": {"text": r["message"]},
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": r["permalink"]},
                            "region": {"startLine": r["line"]},
                        }
                    }],
                    "properties": {
                        "repository": r["repo"],
                        "confidence": r["confidence"],
                        "truePositive": r["true_positive"],
                    },
                }
                for r in results
            ],
        }],
    }

    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(sarif, fh, indent=2)
    print(f"SARIF report written to:  {output_file}")


def _scan_repo(
    repo: dict,
    org: str,
    rules_sources: list[str],
    ai_client: Optional[BaseAIClient],
    csv_writer: "csv.writer",
    csv_lock: threading.Lock,
    sarif_results: list,
    sarif_lock: threading.Lock,
    progress: tqdm,
) -> None:
    name = repo["name"]
    ssh_url = repo["sshUrl"]

    tempdir = tempfile.mkdtemp(prefix=f"semhound_{name}_")
    try:
        tqdm.write(f"  [clone]   {name}")
        clone = _run_cmd([
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            "--no-tags",
            "--filter=blob:limit=1m",
            ssh_url,
            tempdir,
        ], timeout=300)
        if clone.returncode != 0:
            err = clone.stderr.strip()
            if clone.returncode == -1:
                tqdm.write(f"  [skip]    {name} — clone timed out after 5 minutes")
            elif "Permission denied (publickey)" in err:
                tqdm.write(
                    f"  [skip]    {name} — SSH key rejected by GitHub. "
                    "Ensure your key has read access to this repository."
                )
            elif "Repository not found" in err or "Could not read from remote repository" in err:
                tqdm.write(
                    f"  [skip]    {name} — repository not found or your account lacks read access."
                )
            else:
                tqdm.write(f"  [skip]    {name} — clone failed: {err[:200]}")
            return

        rev = _run_cmd(["git", "rev-parse", "HEAD"], cwd=tempdir)
        commit_id = rev.stdout.strip() if rev.returncode == 0 else "HEAD"

        tqdm.write(f"  [scan]    {name}")
        semgrep_cmd = ["semgrep", "--jobs", "1"]
        for src in rules_sources:
            semgrep_cmd += ["--config", src]
        semgrep_cmd += ["--json", "--quiet", tempdir]
        semgrep = _run_cmd(semgrep_cmd, timeout=1200)

        if semgrep.returncode == -1:
            tqdm.write(f"  [warn]    {name} — semgrep timed out after 20 minutes")
        elif semgrep.returncode not in (0, 1):
            tqdm.write(f"  [warn]    {name} — semgrep exited {semgrep.returncode}")

        try:
            raw_findings = json.loads(semgrep.stdout).get("results", [])
        except json.JSONDecodeError:
            tqdm.write(f"  [warn]    {name} — could not parse semgrep output")
            raw_findings = []

        sarif_batch: list[dict] = []

        for finding in raw_findings:
            rel_path = Path(finding["path"]).relative_to(tempdir)
            line = finding["start"]["line"]
            rule_id = finding.get("check_id", "unknown")
            message = finding.get("extra", {}).get("message", rule_id)
            snippet = finding.get("extra", {}).get("lines", "").strip()
            permalink = f"https://github.com/{org}/{name}/blob/{commit_id}/{rel_path}#L{line}"

            confidence, true_positive = "", ""
            if ai_client is not None:
                tqdm.write(f"  [analyze] {name} — {rule_id}")
                confidence, true_positive = _analyze_with_retry(
                    ai_client, snippet, message, name, rule_id
                )
                tqdm.write(
                    f"  [ai]      {name} — {rule_id} | "
                    f"confidence={confidence} true_positive={true_positive}"
                )

            with csv_lock:
                csv_writer.writerow([name, rule_id, message, permalink, confidence, true_positive])

            sarif_batch.append({
                "repo": name,
                "rule_id": rule_id,
                "message": message,
                "permalink": permalink,
                "line": line,
                "confidence": confidence,
                "true_positive": true_positive,
            })

        with sarif_lock:
            sarif_results.extend(sarif_batch)

        tqdm.write(f"  [done]    {name} — {len(raw_findings)} finding(s)")

    finally:
        shutil.rmtree(tempdir, ignore_errors=True)
        progress.update(1)


def run_scan(
    repos: list,
    org: str,
    rules_sources: list[str],
    ai_client: Optional[BaseAIClient],
    threads: int,
    output_sarif: bool = False,
) -> None:
    if not repos:
        print("[info] No repositories found for this organization.")
        return

    output_file = f"{org}_scan.csv"
    csv_lock = threading.Lock()
    sarif_results: list[dict] = []
    sarif_lock = threading.Lock()

    with open(output_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "Repository", "Rule", "Issue Description", "Location",
            "Confidence Score (AI)", "True Positive (AI)",
        ])

        progress = tqdm(total=len(repos), desc=f"Scanning {org}", unit="repo")
        pool = ThreadPoolExecutor(max_workers=threads)
        futures = {
            pool.submit(
                _scan_repo, repo, org, rules_sources, ai_client,
                writer, csv_lock, sarif_results, sarif_lock, progress,
            ): repo["name"]
            for repo in repos
        }
        interrupted = False
        try:
            for future in as_completed(futures):
                exc = future.exception()
                if exc:
                    tqdm.write(f"  [error]   {futures[future]} — {exc}")
        except KeyboardInterrupt:
            interrupted = True
            tqdm.write("\n[interrupted] Cancelling remaining tasks...")
            for f in futures:
                f.cancel()
        finally:
            pool.shutdown(wait=not interrupted, cancel_futures=interrupted)
            progress.close()

    if interrupted:
        print(f"\nScan interrupted. Partial results written to: {output_file}")
        return

    print(f"\nResults written to:       {output_file}")

    if output_sarif:
        _write_sarif(sarif_results, f"{org}_scan.sarif")

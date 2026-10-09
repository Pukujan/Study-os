#!/usr/bin/env python3
"""Run the real ACS installer against the certified four-component release train.

Use only on the dedicated issue #202 task branch, in a clean Study OS checkout.
The installer fails closed; this wrapper never marks a partial install READY.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "task/SOS-0202-install-acs-hotloader"
REPOS = "https://github.com/Pukujan/"
ACS_PATH = ROOT / "third_party/agent-custom-setup"
PACK = "modules/coordination/multi-agent-hotload/v0.1.0"
OLD = {
    "pcm": "c18bfd6064d1249996bc00c45dbbc6721ec5dfd9",
    "cgm": "c069613ca8b3e02bcf5aba1960160583537f8a3a",
    "acs": "f9650936fd5fd66be3b0e2cf04e653f0a3cbb7e4",
}


def run(*args, cwd=ROOT):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=cwd, check=True)


def output(*args, cwd=ROOT):
    return subprocess.check_output(list(map(str, args)), cwd=cwd, text=True).strip()


def fetch_pinned(name, commit, parent):
    dest = parent / name
    run("git", "init", "-q", dest)
    run("git", "fetch", "-q", "--depth", "1", REPOS + name + ".git", commit, cwd=dest)
    run("git", "checkout", "-q", "--detach", "FETCH_HEAD", cwd=dest)
    if output("git", "rev-parse", "HEAD", cwd=dest) != commit:
        raise RuntimeError("Fetched a different commit for " + name)
    return dest


def replace_file(path, replacements):
    text = path.read_text(encoding="utf-8")
    for former, current in replacements.items():
        if former not in text and current not in text:
            raise RuntimeError("Missing pin in " + str(path) + ": " + former)
        text = text.replace(former, current)
    path.write_text(text, encoding="utf-8")


def reconcile_adopter(release, pcm_root):
    certified = release["certified"]
    pcm = certified["project-continuity-modules"]["commit"]
    cgm = certified["content-generation-modules"]["commit"]
    acs = certified["agent-custom-setup"]["commit"]
    adapter = ROOT / ".content-system/system-version.json"
    data = json.loads(adapter.read_text(encoding="utf-8"))
    if data["helper_commit"] not in (OLD["cgm"], cgm):
        raise RuntimeError("Unknown CGM adapter revision: refusing migration")
    data["helper_commit"] = cgm
    data["helper_version"] = certified["content-generation-modules"]["version"]
    data["helper_pin_note"] = "Certified release-train CGM, all eight modules; writing routing and filename naming remain mandatory."
    data["adoption_status"] = "CGM 0.5.12 adapter, pending/full ACS validation"
    adapter.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replaces = {OLD["pcm"]: pcm, OLD["cgm"]: cgm}
    replace_file(ROOT / "PROJECT_MANIFEST.yaml", replaces)
    replace_file(ROOT / "tests/test_helper_adoption.py", replaces)
    replace_file(ROOT / "AGENTS.md", {**replaces, OLD["acs"]: acs})
    replace_file(ROOT / ".github/workflows/ci.yml", {OLD["pcm"]: pcm})
    replace_file(ROOT / "PROJECT_MANIFEST.yaml", {'cli_version: "0.6.0"': 'cli_version: "0.7.0"', 'helper_version: "0.5.7"': 'helper_version: "0.5.12"'})
    agent = ROOT / "AGENTS.md"
    text = agent.read_text(encoding="utf-8").replace("0.5.7", "0.5.12").replace("0.6.0", "0.7.0")
    text = text.replace("(ACS PR #12 tip until merged to ACS \x60main\x60)", "(certified ACS release)")
    agent.write_text(text, encoding="utf-8")

    # Study OS has an exact-copy PCM schemas invariant; keep hashes in sync.
    source = pcm_root / "schemas/v1"
    target = ROOT / "schemas/v1"
    if not source.is_dir():
        raise RuntimeError("The certified PCM release has no schemas/v1")
    shutil.rmtree(target)
    shutil.copytree(source, target)
    tests = ROOT / "tests/test_helper_adoption.py"
    code = tests.read_text(encoding="utf-8")
    for file in target.iterdir():
        if not file.is_file():
            continue
        digest = hashlib.sha256(file.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        pattern = r'("' + re.escape(file.name) + r'": ")[0-9a-f]{64}(")'
        code, n = re.subn(pattern, lambda m: m.group(1) + digest + m.group(2), code)
        if n != 1:
            raise RuntimeError("Unexpected PCM schema inventory: " + file.name)
    tests.write_text(code, encoding="utf-8")


def main():
    if output("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError("Refusing to install outside " + BRANCH)
    if output("git", "status", "--porcelain"):
        raise RuntimeError("Start from a clean task branch checkout")
    cache = Path(os.getenv("ACS_CACHE_DIR", tempfile.gettempdir()))
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="study-os-acs-", dir=cache) as temp:
        tmp = Path(temp)
        train_head = output("git", "ls-remote", REPOS + "agent-stack-train.git", "refs/heads/main").split()[0]
        train = fetch_pinned("agent-stack-train", train_head, tmp)
        release = json.loads((train / "stack-releases.json").read_text(encoding="utf-8"))
        if release.get("status") != "certified":
            raise RuntimeError("Train release is not certified")
        pins = release["certified"]
        pcm = fetch_pinned("project-continuity-modules", pins["project-continuity-modules"]["commit"], tmp)
        cgm = fetch_pinned("content-generation-modules", pins["content-generation-modules"]["commit"], tmp)
        oio = fetch_pinned("observational-issue-ops", pins["observational-issue-ops"]["commit"], tmp)
        run("git", "submodule", "update", "--init", "--recursive", "third_party/agent-custom-setup")
        acs_commit = pins["agent-custom-setup"]["commit"]
        run("git", "fetch", "-q", "--depth", "1", "origin", acs_commit, cwd=ACS_PATH)
        run("git", "checkout", "-q", "--detach", "FETCH_HEAD", cwd=ACS_PATH)
        if output("git", "rev-parse", "HEAD", cwd=ACS_PATH) != acs_commit:
            raise RuntimeError("ACS submodule is not at the certified release")
        reconcile_adopter(release, pcm)
        run(sys.executable, ACS_PATH / PACK / "scripts/acs_install.py",
            "--adopter-root", ROOT, "--pcm-root", pcm, "--cgm-root", cgm,
            "--oio-root", oio, "--project-id", "Pukujan/Study-os",
            "--project-name", "Study OS")
        run(sys.executable, ACS_PATH / PACK / "scripts/hotload_check.py",
            "--adopter-root", ROOT, "--cgm-root", cgm)
        run(sys.executable, oio / ".github/scripts/oio_installer.py",
            "--target", ROOT, "--project-id", "Pukujan/Study-os", "--check")
        run(sys.executable, train / "scripts/check_manifest.py",
            "--manifest", ROOT / "stack-manifest.json",
            "--train", train / "stack-releases.json")
        lock = json.loads((ROOT / ".coord/hotload.lock.json").read_text(encoding="utf-8"))
        if lock["state"] != "READY":
            raise RuntimeError("ACS installer did not report READY")
        run(sys.executable, "-m", "unittest", "tests.test_helper_adoption", "-v")
        run(sys.executable, "tools/validate_repo.py")
        print("ACS install is READY and locally validated. Review the diff before committing.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print("ACS install failed closed:", error, file=sys.stderr)
        sys.exit(1)

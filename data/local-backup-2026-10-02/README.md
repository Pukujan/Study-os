# Local data backup, 2026-10-02

This folder is a copy of Study OS data that until now only lived on my Windows PC (Teresa-Pujan). It was taken on 2026-10-02/03 so the local copies can be deleted. I've decided the study transcripts and data are fine to be public. See D021 in `docs/DECISIONS.md`.

Nothing here is used by the code or the tests. It's an archive.

| Folder | What it is | Source on the PC | Files | Size |
|---|---|---|---|---|
| `wsl-root-study-os/` | The main local Study OS store: `db/study-os.sqlite3`, the dated `backups/` (each with its own DB, manifest and evidence), and `evidence/` blobs | WSL Ubuntu `/root/.study-os` | 394 | 3.5 MB |
| `windows-user-study-os/` | The Windows-side Study OS DB (its `backups/`, `evidence/` and `exports/` folders were empty) | `C:\Users\pujan\.study-os` | 1 | 0.36 MB |
| `artifacts/` | Gate and debugging output: Playwright reports, screenshots, vision-gate runs, the UX defect scratch scripts | `D:\claude\Study-os\artifacts\` | 276 | 25.0 MB |
| `evals-out/` | Player eval scorecards | `D:\claude\Study-os\evals\out\` | 2 | 0.30 MB |
| `pcm-worktree-artifacts/` | UX defect Playwright/ultrafast output from two PCM worktrees, one subfolder each | `D:\claude\Study-os\pcm\worktree\SOS-126-sw-multirep\artifacts\` and `...\SOS-161-big-o-4class\artifacts\` | 50 | 4.2 MB |
| `private-service-files/` | The WSL start script and the `study-os.service` systemd unit. Neither holds a secret; the unit only points at `runtime.env`, which isn't included | `D:\Study-os\.study-os-private\` | 2 | <1 KB |
| `wip-patches/` | Unfinished work, saved as patches only (see below) | see below | 4 | 49 KB |

## wip-patches

- `checkpoint-wip.patch`: `git -C D:\Study-os-main diff`, the uncommitted checkpoint work from around Sep 8 (HEAD was `151c819`).
- `staged-task-docs.patch`: `git -C D:\claude\Study-os diff --cached`, the staged PCM task docs (HEAD was `4197627`).
- `TASK-SOS-0019-pcm-issue-log-format.md`: an untracked task file from the same checkout, copied as is.
- `player-arrows-stash.patch`: `git stash show -p --include-untracked stash@{3}` from `D:\claude\Study-os`, the WIP on `task/SOS-player-arrows-explain-2026-09-26`. Stashes 0-2 were junk and were skipped.

These are kept for reference only. They aren't going to be built out.

## Left out on purpose

- `cloudflared-study-os.service` from `.study-os-private\systemd\`. It has no token in it, but it names the tunnel and the token file, so it stays off a public repo.
- Any `.env`, `runtime.env`, `~/.config/study-os/*`, cloudflared tokens and API keys. None of these were copied.

Everything here went through a secret scan (OpenAI-style, GitHub, AWS and Google key formats, Bearer tokens, private keys, JWTs, and the words token/secret/password/cloudflared, including inside the Playwright trace zips) before it was committed. Nothing real turned up.

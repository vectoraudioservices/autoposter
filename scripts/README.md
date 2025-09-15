# Autoposter (Vector Management)

A Windows-friendly, multi-client Instagram autoposter with:
- folder watcher → queue → runner pipeline
- per-client sessions & caption styles
- safe mode (dry-run) vs live mode
- batch helpers (start/stop/status)

## Local folders
- `content/` (client subfolders; media dropped here)
- `logs/` (runtime logs; ignored from git)
- `exports/` (dry-run copies; ignored)
- `config/` (non-secret config)
- `config/clients/<ClientKey>/secrets.env` (ignored)

## Safety
Secrets, sessions, logs, and media are **not** tracked by git via `.gitignore`.

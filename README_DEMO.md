# Demo Helpers (Dry-Run & Safe Live Harness)

- \scripts\demo_main_runner.ps1\ — Dry-run, uses MAIN runner with IGNORE_QUOTA for smooth demo.
- \scripts\pre_demo_quickcheck.py\ — Validates folders, session file, client.json (no posting).
- \scripts\run_dry_tests.py\ — Enqueues 3 dry jobs and processes them (DRY).
- \scripts\post_one_live.ps1\ — **Posts exactly one feed item** after you type **POST**.
- \scripts\cancel_live_enqueue.py\ — Freezes any accidental live enqueue (eta -> 2100-01-01).

**Tip:** Keep \.gitignore\ entries for \content/\, \env/\, \*.db\, and logs to avoid leaking local data.

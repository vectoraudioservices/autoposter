# demo_main_runner.ps1 — full dry-run showcase using the MAIN runner
function Log($m) { "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m }

Log "=== MAIN RUNNER DEMO (DRY) START ==="

# 0) Quick health check
Log "Quick check..."
.\venv\Scripts\python.exe .\scripts\pre_demo_quickcheck.py

# 1) Start watcher in dry-run (minimized)
Log "Starting watcher (dry-run)..."
$watcher = Start-Process -FilePath ".\venv\Scripts\python.exe" -ArgumentList "main.py","--dry-run" -PassThru -WindowStyle Minimized
Start-Sleep -Seconds 2

# 2) Prepare demo assets (tiny placeholders if missing)
$feed   = "C:\content\Luchiano\feed\main_demo_feed.jpg"
$reels  = "C:\content\Luchiano\reels\main_demo_reel.mp4"
$story  = "C:\content\Luchiano\stories\main_demo_story.jpg"

New-Item -ItemType Directory -Force -Path (Split-Path $feed)  | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $reels) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $story) | Out-Null

if (!(Test-Path $feed))  { fsutil file createnew $feed  4096  | Out-Null }
if (!(Test-Path $reels)) { fsutil file createnew $reels 8192  | Out-Null }
if (!(Test-Path $story)) { fsutil file createnew $story 4096  | Out-Null }

# Touch so watcher sees them
(Get-Item $feed).LastWriteTime  = Get-Date
(Get-Item $reels).LastWriteTime = Get-Date
(Get-Item $story).LastWriteTime = Get-Date
Log "Dropped & touched demo assets."
Start-Sleep -Seconds 2

# 3) Force all queued jobs to be due now
Log "Forcing ETA=now for queued jobs..."
.\venv\Scripts\python.exe .\scripts\force_eta_now.py Luchiano

# 4) Run MAIN runner three times (feed -> reels -> story), DRY, IGNORE_QUOTA=1
$env:IGNORE_QUOTA = '1'
for ($i=1; $i -le 3; $i++) {
  Log "Main runner pass $i (DRY, IGNORE_QUOTA=1)..."
  .\venv\Scripts\python.exe .\scripts\queue_runner.py --client Luchiano --dry-run --once
}

# 5) Summary
Log "Recent jobs summary:"
.\venv\Scripts\python.exe .\scripts\list_jobs.py --client Luchiano --limit 10

# 6) Stop watcher
Log "Stopping watcher..."
try { Stop-Process -Id $watcher.Id -Force -ErrorAction SilentlyContinue } catch {}

Log "=== MAIN RUNNER DEMO (DRY) END ==="

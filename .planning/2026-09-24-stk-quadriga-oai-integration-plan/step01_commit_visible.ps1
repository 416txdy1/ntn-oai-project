$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = "E:\jingwenpeng\2026autumn\ntn-oai-project"
$planRoot = Join-Path $projectRoot ".planning\2026-09-24-stk-quadriga-oai-integration-plan"
$logPath = Join-Path $planRoot "step01-commit-transcript.txt"
$resultPath = Join-Path $planRoot "STEP01_COMMITTED.json"

Set-Location $projectRoot
$Host.UI.RawUI.WindowTitle = "Step 1 - commit QDCHANNEL1"
Start-Transcript -LiteralPath $logPath -Force | Out-Null

try {
    Write-Host "Step 1：审查并提交 QDCHANNEL1 到 zky" -ForegroundColor Cyan
    $branch = (git branch --show-current).Trim()
    if ($branch -ne "zky") { throw "当前分支不是 zky: $branch" }
    git config user.name zky
    git config user.email 1119045132@qq.com

    $files = @(
        "README.md",
        "quadriga/__init__.py",
        "quadriga/README.md",
        "quadriga/schema/channel_bundle_v1.schema.json",
        "quadriga/tools/__init__.py",
        "quadriga/tools/create_example_bundle.py",
        "quadriga/tools/validate_bundle.py",
        "quadriga/tests/__init__.py",
        "quadriga/tests/test_validate_bundle.py",
        "quadriga/examples/siso_two_path/manifest.json",
        "quadriga/examples/siso_two_path/times.f64",
        "quadriga/examples/siso_two_path/delays.f64",
        "quadriga/examples/siso_two_path/coefficients.cf32",
        "quadriga/examples/siso_two_path/residual_gain_db.f32",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/task_plan.md",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/findings.md",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/progress.md",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_discovery.ps1",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_verify_visible.ps1",
        ".planning/2026-09-24-stk-quadriga-oai-integration-plan/step01_commit_visible.ps1"
    )
    foreach ($file in $files) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "缺少提交文件: $file" }
    }

    Write-Host "PS> python -m json.tool quadriga/schema/channel_bundle_v1.schema.json" -ForegroundColor DarkGray
    python -m json.tool quadriga/schema/channel_bundle_v1.schema.json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "JSON schema syntax check failed" }

    Write-Host "PS> python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path" -ForegroundColor DarkGray
    python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path
    if ($LASTEXITCODE -ne 0) { throw "example validation failed" }

    Write-Host "PS> git add -- <Step 1 allowlist>" -ForegroundColor DarkGray
    git add -- $files
    if ($LASTEXITCODE -ne 0) { throw "git add failed" }

    Write-Host "PS> git diff --cached --name-status" -ForegroundColor DarkGray
    git diff --cached --name-status
    Write-Host "PS> git diff --cached --stat" -ForegroundColor DarkGray
    git diff --cached --stat
    Write-Host "PS> git diff --cached --check" -ForegroundColor DarkGray
    git diff --cached --check
    if ($LASTEXITCODE -ne 0) { throw "staged diff check failed" }

    $staged = @(git diff --cached --name-only)
    if ($staged.Count -ne $files.Count) { throw "暂存文件数不等于允许列表: $($staged.Count) != $($files.Count)" }
    $diff = (git diff --cached --no-ext-diff --unified=0) -join "`n"
    $patterns = @(
        "-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "(?i)\b(?:opc|ki|password)\s*[:=]\s*[`"']?[0-9a-f]{32,}",
        "(?i)\b(?:mysql|postgres(?:ql)?)://[^\s]+:[^\s]+@"
    )
    foreach ($pattern in $patterns) {
        if ($diff -match $pattern) { throw "敏感信息扫描命中: $pattern" }
    }
    Write-Host "敏感信息扫描：PASS" -ForegroundColor Green

    Write-Host "PS> git commit -m feat: define QDCHANNEL1 offline channel contract" -ForegroundColor DarkGray
    git commit -m "feat: define QDCHANNEL1 offline channel contract"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
    $commit = (git rev-parse HEAD).Trim()
    git show --stat --oneline --decorate -1

    [ordered]@{
        status = "success"
        timestamp = (Get-Date).ToString("o")
        branch = "zky"
        commit = $commit
        author = "zky <1119045132@qq.com>"
        files = $files.Count
        transcript = $logPath
    } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "Step 1 committed: $commit" -ForegroundColor Green
}
catch {
    [ordered]@{
        status = "failed"
        timestamp = (Get-Date).ToString("o")
        error = $_.Exception.Message
        transcript = $logPath
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "提交失败：$($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Stop-Transcript | Out-Null
    Read-Host "按 Enter 关闭窗口"
}

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = "E:\jingwenpeng\2026autumn\ntn-oai-project"
$planRoot = Join-Path $projectRoot ".planning\2026-09-24-stk-quadriga-oai-integration-plan"
$logPath = Join-Path $planRoot "step01-verification-transcript.txt"
$resultPath = Join-Path $planRoot "STEP01_VERIFIED.json"

Set-Location $projectRoot
$Host.UI.RawUI.WindowTitle = "Step 1 - QDCHANNEL1 verification"
Start-Transcript -LiteralPath $logPath -Force | Out-Null

function Invoke-Checked {
    param([string]$Display, [scriptblock]$Command)
    Write-Host "PS> $Display" -ForegroundColor DarkGray
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Display failed with exit code $LASTEXITCODE"
    }
}

try {
    Write-Host "Step 1：QDCHANNEL1 接口、示例和回归验证" -ForegroundColor Cyan
    Write-Host "PS> Get-Command python; python --version; conda info --envs" -ForegroundColor DarkGray
    Get-Command python | Select-Object Source
    python --version
    if (Get-Command conda -ErrorAction SilentlyContinue) {
        conda info --envs
    } else {
        Write-Host "conda command is not on this PowerShell PATH; no dependency installation is required." -ForegroundColor Yellow
    }

    Invoke-Checked "python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path" {
        python -m quadriga.tools.create_example_bundle quadriga/examples/siso_two_path
    }
    Invoke-Checked "python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path" {
        python -m quadriga.tools.validate_bundle quadriga/examples/siso_two_path
    }
    Invoke-Checked "python -m unittest -v quadriga.tests.test_validate_bundle" {
        python -m unittest -v quadriga.tests.test_validate_bundle
    }
    Invoke-Checked "python -m json.tool quadriga/schema/channel_bundle_v1.schema.json" {
        python -m json.tool quadriga/schema/channel_bundle_v1.schema.json | Out-Null
    }
    Invoke-Checked "python -m py_compile quadriga tools and tests" {
        python -m py_compile quadriga/tools/validate_bundle.py quadriga/tools/create_example_bundle.py quadriga/tests/test_validate_bundle.py
    }

    Invoke-Checked "WSL: bash local_ntn/run_regressions.sh" {
        wsl.exe -d Ubuntu-22.04 -- bash -lc "cd /mnt/e/jingwenpeng/2026autumn/ntn-oai-project && GIT_PAGER=cat bash local_ntn/run_regressions.sh"
    }
    Invoke-Checked "git diff --check" {
        $env:GIT_PAGER = "cat"
        git diff --check
    }

    [ordered]@{
        status = "success"
        timestamp = (Get-Date).ToString("o")
        tests = @(
            "QDCHANNEL1 example generation",
            "QDCHANNEL1 example validation",
            "5 QDCHANNEL1 unit tests",
            "JSON syntax",
            "Python syntax",
            "trace parser and IQ regression suite",
            "git diff --check"
        )
        transcript = $logPath
    } | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "Step 1 verification passed: $resultPath" -ForegroundColor Green
}
catch {
    [ordered]@{
        status = "failed"
        timestamp = (Get-Date).ToString("o")
        error = $_.Exception.Message
        transcript = $logPath
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Host "验证失败：$($_.Exception.Message)" -ForegroundColor Red
}
finally {
    Stop-Transcript | Out-Null
    Read-Host "按 Enter 关闭窗口"
}

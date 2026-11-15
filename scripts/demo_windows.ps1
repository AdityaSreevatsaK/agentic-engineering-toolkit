# Self-contained native Windows AET demo. Default flows use synthetic data and mock inference.
[CmdletBinding()]
param(
    [ValidateSet("all", "tool-agent", "langgraph-rag", "strands-agent", "llamaindex-rag", "ingestion", "cloud-config", "ollama", "docker")]
    [string]$Flow = "all",
    [ValidateSet("tool-agent", "langgraph-rag", "strands-agent", "llamaindex-rag")]
    [string]$Template = "langgraph-rag",
    [ValidateSet("mock", "ollama", "openai", "azure-openai", "anthropic", "bedrock")]
    [string]$Provider = "openai",
    [switch]$KeepOutput
)
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OldDirectory = (Get-Location).Path
$OldProvider = $env:AET_PROVIDER
$OldKnowledge = $env:AET_KNOWLEDGE_PATH
$OutputRoot = Join-Path $env:TEMP ("aet-demo-" + [guid]::NewGuid().ToString("N").Substring(0, 12))
$Completed = $false
function Assert-Exit([string]$Task) {
    if ($LASTEXITCODE -ne 0) { throw "$Task failed (exit status $LASTEXITCODE)." }
}
function Initialise-Aet {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "Install Python 3.11 or 3.12 with the Windows 'py' launcher."
    }
    $Available = & py -0p | Out-String
    Assert-Exit "Python launcher"
    if ($Available -match '3\.12') { $script:PythonVersion = "-3.12" }
    elseif ($Available -match '3\.11') { $script:PythonVersion = "-3.11" }
    else { throw "Python 3.11 or 3.12 not found by the Windows py launcher." }
    $script:RootPython = Join-Path $Repo ".venv\Scripts\python.exe"
    $script:AgentKit = Join-Path $Repo ".venv\Scripts\agentkit.exe"
    if (-not (Test-Path $RootPython)) {
        & py $PythonVersion -m venv (Join-Path $Repo ".venv") | Out-Host
        Assert-Exit "Create root Python environment"
    }
    & $RootPython -m pip install --quiet -e $Repo | Out-Host
    Assert-Exit "Install AET"
    & $AgentKit list | Out-Host
    Assert-Exit "List templates"
}
function New-DemoProject {
    param([string]$ProjectTemplate, [string]$ProjectProvider = "mock",
          [string]$Name = "", [string]$Extra = "dev", [switch]$GenerateOnly)
    if (-not $Name) { $Name = "demo-" + $ProjectTemplate }
    $Folder = Join-Path $OutputRoot $Name
    Write-Host ("STEP: Generate " + $ProjectTemplate + " (" + $ProjectProvider + ")")
    & $AgentKit new $Name --template $ProjectTemplate --provider $ProjectProvider --output-dir $OutputRoot | Out-Host
    Assert-Exit "Generate $Name"
    & $AgentKit doctor $Folder | Out-Host
    Assert-Exit "Doctor $Name"
    if ($GenerateOnly) { return @{ Path = $Folder; Name = $Name; Template = $ProjectTemplate } }
    $Python = Join-Path $Folder ".venv\Scripts\python.exe"
    & py $PythonVersion -m venv (Join-Path $Folder ".venv") | Out-Host
    Assert-Exit "Create isolated app environment"
    Push-Location $Folder
    try {
        & $Python -m pip install --quiet -e ".[$Extra]" | Out-Host
        Assert-Exit "Install app dependencies"
        & $Python -m pip check | Out-Host
        Assert-Exit "Check app dependencies"
        & $Python -m pytest -q | Out-Host
        Assert-Exit "Run generated tests"
    } finally { Pop-Location }
    return @{ Path = $Folder; Name = $Name; Template = $ProjectTemplate; Python = $Python }
}
function Start-DemoServer {
    param([hashtable]$Project, [switch]$LiveProvider)
    $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $Listener.Start()
    $Port = $Listener.LocalEndpoint.Port
    $Listener.Stop()
    $Stderr = Join-Path $Project.Path "server-errors.log"
    $P = Start-Process -FilePath $Project.Python -WorkingDirectory $Project.Path -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","$Port") -RedirectStandardOutput (Join-Path $Project.Path "server-output.log") -RedirectStandardError $Stderr -PassThru
    $Base = "http://127.0.0.1:$Port"
    try {
        $Healthy = $false
        for ($I = 0; $I -lt 30; $I++) {
            if ($P.HasExited) { break }
            try {
                $H = Invoke-RestMethod -Uri ($Base + "/health") -TimeoutSec 2
                if ($H.status -ne "ok") { throw "Bad health response" }
                if (-not $LiveProvider) {
                    $Ready = Invoke-RestMethod -Uri ($Base + "/ready") -TimeoutSec 2
                    if ($Ready.status -ne "ready") { throw "Bad readiness response" }
                }
                $Healthy = $true
                break
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $Healthy -or $P.HasExited) { throw "API failed to start. Check $Stderr" }
        return @{ Process = $P; Base = $Base }
    } catch {
        Stop-Process -Id $P.Id -ErrorAction SilentlyContinue
        throw
    }
}
function Ask-Api([string]$Url, [string]$Question) {
    $Body = @{ question = $Question } | ConvertTo-Json -Compress
    return Invoke-RestMethod -Method Post -Uri $Url -Body $Body -ContentType "application/json" -TimeoutSec 60
}
function Test-Project {
    param([hashtable]$Project, [switch]$Ingest, [switch]$UseOllama)
    if ($Ingest) {
        $Docs = Join-Path $Project.Path "synthetic-documents"
        New-Item -ItemType Directory -Path $Docs | Out-Null
        Set-Content -LiteralPath (Join-Path $Docs "violet-guide.txt") -Encoding UTF8 -Value "Violet reference manuals are indexed every Thursday for the fictional archive."
        Push-Location $Project.Path
        try {
            & $Project.Python -m app.ingest --input synthetic-documents --output data/violet-knowledge.jsonl | Out-Host
            Assert-Exit "Ingest synthetic document"
        } finally { Pop-Location }
        $env:AET_KNOWLEDGE_PATH = "data/violet-knowledge.jsonl"
    }
    $Server = $null
    try {
        $Server = Start-DemoServer -Project $Project -LiveProvider:$UseOllama
        if ($Project.Template -in @("langgraph-rag", "llamaindex-rag")) {
            if ($Ingest) {
                $R = Ask-Api ($Server.Base + "/ask") "When are violet reference manuals indexed?"
                if ($R.source_ids -notcontains "violet-guide-001" -or $R.answer -notmatch "Thursday") { throw "Ingested text not found" }
                Write-Host "PASS: text ingestion and live API retrieval"
            } else {
                $R = Ask-Api ($Server.Base + "/ask") "What is the sample return policy?"
                if ($R.source_ids -notcontains "returns" -or $R.answer -notmatch "30 days") { throw "Original RAG query failed" }
                Add-Content -LiteralPath (Join-Path $Project.Path "data\knowledge.jsonl") -Encoding UTF8 -Value '{"id":"violet-manual","text":"Violet reference manuals are indexed on Thursday."}'
                $R = Ask-Api ($Server.Base + "/ask") "Which day are violet reference manuals indexed?"
                if ($R.source_ids -notcontains "violet-manual" -or $R.answer -notmatch "Thursday") { throw "Live corpus update failed" }
                Write-Host "PASS: RAG before and after corpus change (no server restart)"
            }
        } elseif ($Project.Template -eq "tool-agent") {
            if ($UseOllama) {
                $R = Ask-Api ($Server.Base + "/invoke") "hello"
                if (-not $R.answer) { throw "Ollama produced no answer" }
                Write-Host "PASS: Ollama local inference"
            } else {
                $R = Ask-Api ($Server.Base + "/invoke") "order status ORD-1001"
                if ($R.tool_used -ne "get_order_status" -or $R.answer -notmatch "shipped") { throw "Order-status tool failed" }
                $R = Ask-Api ($Server.Base + "/invoke") "hello"
                if (-not $R.answer -or $null -ne $R.tool_used) { throw "Mock response failed" }
                Write-Host "PASS: LangGraph tool routing and default mock response"
            }
        } else {
            $R = Ask-Api ($Server.Base + "/invoke") "order status ORD-1001"
            if ($R.provider -ne "mock" -or $R.tool_used -ne $true -or $R.answer -notmatch "shipped") { throw "Strands tool loop failed" }
            Write-Host "PASS: real Strands SDK tool loop (scripted model)"
        }
    } finally {
        if ($null -ne $Server) {
            Stop-Process -Id $Server.Process.Id -ErrorAction SilentlyContinue
            Wait-Process -Id $Server.Process.Id -Timeout 10 -ErrorAction SilentlyContinue
        }
        if ($Ingest) { $env:AET_KNOWLEDGE_PATH = "data/knowledge.jsonl" }
    }
}
try {
    New-Item -ItemType Directory -Path $OutputRoot | Out-Null
    $env:AET_PROVIDER = "mock"
    $env:AET_KNOWLEDGE_PATH = "data/knowledge.jsonl"
    Initialise-Aet
    Write-Host "Output folder: $OutputRoot"
    if ($Flow -eq "docker") {
        & docker version | Out-Host
        Assert-Exit "Docker daemon"
        $Names = @{
            "tool-agent" = "mock-demo"; "langgraph-rag" = "rag-demo"
            "strands-agent" = "strands-demo"; "llamaindex-rag" = "llamaindex-demo"
        }
        foreach ($T in @("tool-agent","langgraph-rag","strands-agent","llamaindex-rag")) {
            $null = New-DemoProject -ProjectTemplate $T -Name $Names[$T] -GenerateOnly
        }
        Push-Location $OutputRoot
        try {
            & $RootPython (Join-Path $Repo "scripts\docker_smoke.py") --json-out "docker-evidence.json" | Out-Host
            Assert-Exit "Four-image Docker smoke"
        } finally { Pop-Location }
    } elseif ($Flow -eq "cloud-config") {
        if ($Provider -eq "mock" -or ($Template -eq "strands-agent" -and $Provider -eq "ollama")) { throw "Select a supported non-mock provider." }
        $Extra = "dev"
        if ($Provider -in @("openai","azure-openai","anthropic","bedrock")) {
            if (-not ($Template -eq "strands-agent" -and $Provider -eq "bedrock")) { $Extra = "dev,$Provider" }
        } elseif ($Template -eq "llamaindex-rag" -and $Provider -eq "ollama") { $Extra = "dev,ollama" }
        $null = New-DemoProject -ProjectTemplate $Template -ProjectProvider $Provider -Name "cloud-config-demo" -Extra $Extra
        Write-Host "PASS: cloud-configured app installed and tested offline. No model was contacted."
    } elseif ($Flow -eq "ollama") {
        & ollama list | Out-Host
        Assert-Exit "Local Ollama availability"
        $Models = & ollama list | Out-String
        Assert-Exit "Ollama model list"
        if ($Models -notmatch 'llama3\.2:1b') {
            Write-Host "Downloading optional Ollama model llama3.2:1b..."
            & ollama pull llama3.2:1b | Out-Host
            Assert-Exit "Download Ollama model"
        }
        $P = New-DemoProject -ProjectTemplate "tool-agent" -ProjectProvider "ollama" -Name "demo-ollama"
        $env:AET_PROVIDER = "ollama"
        Test-Project -Project $P -UseOllama
    } else {
        $Selected = if ($Flow -eq "all") {
            @("tool-agent","langgraph-rag","strands-agent","llamaindex-rag")
        } elseif ($Flow -eq "ingestion") { @("langgraph-rag") } else { @($Flow) }
        foreach ($T in $Selected) {
            $P = New-DemoProject -ProjectTemplate $T
            if ($Flow -eq "ingestion") { Test-Project -Project $P -Ingest }
            else { Test-Project -Project $P }
            if ($Flow -eq "all" -and $T -eq "langgraph-rag") { Test-Project -Project $P -Ingest }
        }
    }
    $Completed = $true
} catch {
    Write-Host "FAILED: $Flow. Temporary projects and server logs were kept in $OutputRoot."
    throw
} finally {
    $env:AET_PROVIDER = $OldProvider
    $env:AET_KNOWLEDGE_PATH = $OldKnowledge
    Set-Location $OldDirectory
    if ($Completed -and -not $KeepOutput) {
        # Python handles long nested dependency paths reliably on Windows.
        & $RootPython -c "import shutil, sys; shutil.rmtree(sys.argv[1])" $OutputRoot
        Assert-Exit "Remove temporary demo projects"
        if (Test-Path -LiteralPath $OutputRoot) { throw "Temporary demo folder still exists: $OutputRoot" }
        Write-Host "PASS: temporary demo projects removed. Use -KeepOutput to retain them."
    } elseif ($Completed) {
        Write-Host "PASS: demo projects retained at $OutputRoot"
    }
}
if ($Completed) { Write-Host "SUCCESS: $Flow completed." }

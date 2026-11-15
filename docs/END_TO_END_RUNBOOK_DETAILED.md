# AET: full end-to-end execution runbook

**Purpose:** Exact, self-contained steps for every important AET flow. **Primary platform:** native Windows PowerShell, Python 3.11/3.12, no WSL. **Default demos:** synthetic data and mock inference, no credentials, Ollama, cloud services or billable calls. These are local developer applications, **not** production deployments.

**Contents:** (1) one-time bootstrap; (2) automated four-project verification; (3) LangGraph Tool Agent; (4) LangGraph RAG; (5) AWS Strands; (6) LlamaIndex RAG; (7) text ingestion; (8) cloud/Ollama options; (9) Docker; (10) tests, CI and presentation; (11) troubleshooting.

**How to follow:** Copy the complete PowerShell blocks in order **in one PowerShell session**. Section 1 defines two helpers that remove repeated setup and server-management steps. Each app is independently installed, tested, started on loopback, queried over actual HTTP and stopped. Do not skip section 1 before using sections 3–7.

## 1. One-time native Windows bootstrap

Prerequisites: Git, Windows Python launcher (**py**) with Python 3.11 or 3.12, and permission to download packages from your Python package index. No virtualenv activation or PowerShell execution-policy change is needed.

### Step 1A: fresh clone and AET installation

~~~powershell
$ErrorActionPreference = "Stop"
git --version
py -0p
$InstalledPython = (py -0p | Out-String)
if ($InstalledPython -match '3\.12') { $PythonVersion = "-3.12" }
elseif ($InstalledPython -match '3\.11') { $PythonVersion = "-3.11" }
else { throw "Install Python 3.11 or 3.12 and the Windows py launcher." }

$Workspace = Join-Path $HOME ("AET-Demo-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Path $Workspace | Out-Null
Set-Location $Workspace
git clone https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit.git
if ($LASTEXITCODE -ne 0) { throw "Git clone failed." }
Set-Location .\agentic-engineering-toolkit
$Repo = (Get-Location).Path
py $PythonVersion -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Root virtualenv creation failed." }
$RootPython = Join-Path $Repo ".venv\Scripts\python.exe"
$AgentKit = Join-Path $Repo ".venv\Scripts\agentkit.exe"
& $RootPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "AET installation failed." }
& $AgentKit --version
& $AgentKit list
if ($LASTEXITCODE -ne 0) { throw "AET CLI listing failed." }
$env:AET_PROVIDER = "mock"
$env:AET_KNOWLEDGE_PATH = "data/knowledge.jsonl"
Write-Host "PASS: AET ready in $Repo"
~~~

**Pass criteria:** The CLI lists **tool-agent**, **langgraph-rag**, **strands-agent** and **llamaindex-rag** with their allowed providers. A unique directory prevents collisions with earlier projects; AET intentionally refuses overwriting generated paths.

### Step 1B: paste two reusable walkthrough helpers

~~~powershell
function New-VerifiedAetProject {
    param([string]$Name, [string]$Template)
    & $AgentKit new $Name --template $Template --provider mock --output-dir $Repo
    if ($LASTEXITCODE -ne 0) { throw "Generation failed: $Name" }
    & $AgentKit doctor (Join-Path $Repo $Name)
    if ($LASTEXITCODE -ne 0) { throw "Doctor failed: $Name" }
    Push-Location (Join-Path $Repo $Name)
    try {
        py $PythonVersion -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Virtualenv failed: $Name" }
        & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "Installation failed: $Name" }
        & .\.venv\Scripts\python.exe -m pip check
        if ($LASTEXITCODE -ne 0) { throw "pip check failed: $Name" }
        & .\.venv\Scripts\python.exe -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw "Generated pytest failed: $Name" }
    } finally { Pop-Location }
    Write-Host "PASS: $Name generated, checked, installed and tested"
}

function Start-AetLocalServer {
    param([string]$Name, [int]$Port)
    $Project = Join-Path $Repo $Name
    $Python = Join-Path $Project ".venv\Scripts\python.exe"
    $Stdout = Join-Path $Project "server-stdout.log"
    $Stderr = Join-Path $Project "server-stderr.log"
    $Process = Start-Process -FilePath $Python -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port","$Port") -WorkingDirectory $Project -PassThru -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
    $Healthy = $false
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        if ($Process.HasExited) { break }
        try {
            $Health = Invoke-RestMethod -Method Get -TimeoutSec 2 -Uri "http://127.0.0.1:$Port/health"
            $Ready = Invoke-RestMethod -Method Get -TimeoutSec 2 -Uri "http://127.0.0.1:$Port/ready"
            if ($Health.status -eq "ok" -and $Ready.status -eq "ready") { $Healthy = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $Healthy -or $Process.HasExited) {
        Stop-Process -Id $Process.Id -ErrorAction SilentlyContinue
        throw "API failed on port $Port. Check $Stderr or port conflicts."
    }
    Write-Host "PASS: $Name listening only on 127.0.0.1:$Port"
    return $Process
}
~~~

These helpers always create a **separate virtualenv for every generated project**. Each generated Python package is named **app**, so the project environments must not be merged. Real HTTP servers are started as child processes and stopped explicitly in a **finally** block.

## 2. Flow A: automatically verify all four independent projects

This is the shortest full engineering acceptance check. It automatically generates, installs, runs the generated tests and performs mock ASGI API requests for every registered template.

~~~powershell
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
& $RootPython -m scripts.isolated_install_smoke --json-out "isolated-apps-$Stamp.json" --versions-dir "isolated-versions-$Stamp" --jobs 1
if ($LASTEXITCODE -ne 0) { throw "Four-template isolated acceptance FAILED." }
Get-Content "isolated-apps-$Stamp.json"
Get-ChildItem "isolated-versions-$Stamp"
~~~

**Expected:** Four named **PASS isolated install** messages, one JSON report with four successful applications and four per-app pip-resolution files. This uses temporary generated projects and mock ASGI clients, not externally reachable network services or human performance measurements.

## 3. Flow B: LangGraph Tool Agent, real HTTP + synthetic tool call

### Step 3A: scaffold, Doctor, own virtualenv, pip consistency and full tests

~~~powershell
New-VerifiedAetProject -Name "demo-tool-agent" -Template "tool-agent"
~~~

### Step 3B: run actual localhost API requests and stop cleanly

~~~powershell
$Server = Start-AetLocalServer -Name "demo-tool-agent" -Port 18001
try {
    $Tool = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18001/invoke" -ContentType "application/json" -Body '{"question":"order status ORD-1001"}'
    if ($Tool.tool_used -ne "get_order_status" -or $Tool.answer -notmatch "shipped") { throw "Synthetic order tool failed." }
    $Mock = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18001/invoke" -ContentType "application/json" -Body '{"question":"hello"}'
    if (-not $Mock.answer -or $null -ne $Mock.tool_used) { throw "Mock response route failed." }
    $Tool
    $Mock
    Write-Host "PASS: Tool Agent order lookup and default mock response"
} finally { Stop-Process -Id $Server.Id -ErrorAction SilentlyContinue }
~~~

**Expected:** **ORD-1001 shipped**, **tool_used = get_order_status**, plus an ordinary deterministic reply with no tool. This example uses deterministic LangGraph routing, **not** autonomous tool selection.

## 4. Flow C: LangGraph BM25 RAG, HTTP before and after corpus change

### Step 4A: scaffold, Doctor, isolated install and full tests

~~~powershell
New-VerifiedAetProject -Name "demo-langgraph-rag" -Template "langgraph-rag"
~~~

### Step 4B: exercise source-backed retrieval and hot corpus update

~~~powershell
$Server = Start-AetLocalServer -Name "demo-langgraph-rag" -Port 18002
try {
    $First = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18002/ask" -ContentType "application/json" -Body '{"question":"What is the sample return policy?"}'
    if ($First.source_ids -notcontains "returns" -or $First.answer -notmatch "30 days") { throw "Initial BM25 retrieval failed." }

    $Corpus = Join-Path $Repo "demo-langgraph-rag\data\knowledge.jsonl"
    Add-Content -LiteralPath $Corpus -Encoding UTF8 -Value '{"id":"violet-manual","text":"Violet reference manuals are indexed on Thursday."}'

    $Second = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18002/ask" -ContentType "application/json" -Body '{"question":"Which day are violet reference manuals indexed?"}'
    if ($Second.source_ids -notcontains "violet-manual" -or $Second.answer -notmatch "Thursday") { throw "Updated BM25 corpus not visible." }
    $First
    $Second
    Write-Host "PASS: LangGraph BM25 RAG and live source update"
} finally { Stop-Process -Id $Server.Id -ErrorAction SilentlyContinue }
~~~

**Expected:** **returns / 30 days**, then **violet-manual / Thursday** *without restarting the server*. This is BM25 lexical retrieval with mock evidence responses, not a vector store or hosted LLM.

## 5. Flow D: Strands SDK Agent, actual synthetic tool loop

### Step 5A: scaffold, Doctor, isolated install and tests

~~~powershell
New-VerifiedAetProject -Name "demo-strands-agent" -Template "strands-agent"
~~~

### Step 5B: verify mock Strands tool execution and stop

~~~powershell
$Server = Start-AetLocalServer -Name "demo-strands-agent" -Port 18003
try {
    $Result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18003/invoke" -ContentType "application/json" -Body '{"question":"order status ORD-1001"}'
    if ($Result.provider -ne "mock" -or $Result.tool_used -ne $true -or $Result.answer -notmatch "shipped") { throw "Strands SDK tool loop failed." }
    $Result
    Write-Host "PASS: real Strands SDK tool invocation (scripted offline model)"
} finally { Stop-Process -Id $Server.Id -ErrorAction SilentlyContinue }
~~~

**Expected:** **provider = mock**, **tool_used = true**, and a shipped-status answer. This uses the real Strands SDK loop, but a scripted offline model rather than Bedrock or an LLM.

## 6. Flow E: native LlamaIndex keyword RAG, HTTP + corpus change

### Step 6A: scaffold, Doctor, isolated install and tests

~~~powershell
New-VerifiedAetProject -Name "demo-llamaindex-rag" -Template "llamaindex-rag"
~~~

### Step 6B: source-backed response, edit JSONL while running, verify again

~~~powershell
$Server = Start-AetLocalServer -Name "demo-llamaindex-rag" -Port 18004
try {
    $First = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18004/ask" -ContentType "application/json" -Body '{"question":"What is the sample return policy?"}'
    if ($First.source_ids -notcontains "returns" -or $First.answer -notmatch "30 days") { throw "Initial LlamaIndex retrieval failed." }

    $Corpus = Join-Path $Repo "demo-llamaindex-rag\data\knowledge.jsonl"
    Add-Content -LiteralPath $Corpus -Encoding UTF8 -Value '{"id":"violet-manual","text":"Violet reference manuals are indexed on Thursday."}'

    $Second = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18004/ask" -ContentType "application/json" -Body '{"question":"Which day are violet reference manuals indexed?"}'
    if ($Second.source_ids -notcontains "violet-manual" -or $Second.answer -notmatch "Thursday") { throw "Updated LlamaIndex corpus not visible." }
    $First
    $Second
    Write-Host "PASS: native LlamaIndex keyword RAG and live source update"
} finally { Stop-Process -Id $Server.Id -ErrorAction SilentlyContinue }
~~~

**Expected:** **returns / 30 days**, then **violet-manual / Thursday** without a server restart. This uses native LlamaIndex keyword indexing, **not** LangGraph, BM25 or semantic vectors.

## 7. Flow F: ingest an entirely new local document and query it

The generated **LangGraph RAG** app has an explicit text/Markdown ingestion CLI. LlamaIndex accepts validated JSONL via AET_KNOWLEDGE_PATH, but does **not** include this ingestion CLI.

### Step 7A: create a synthetic text document and a NEW JSONL corpus

~~~powershell
$Project = Join-Path $Repo "demo-langgraph-rag"
$Documents = Join-Path $Project "synthetic-documents"
New-Item -ItemType Directory -Path $Documents | Out-Null
Set-Content -LiteralPath (Join-Path $Documents "violet-guide.txt") -Encoding UTF8 -Value "Violet reference manuals are indexed every Thursday for the fictional archive."
Push-Location $Project
try {
    & .\.venv\Scripts\python.exe -m app.ingest --input synthetic-documents --output data/violet-knowledge.jsonl
    if ($LASTEXITCODE -ne 0) { throw "Ingestion failed." }
    Get-Content .\data\violet-knowledge.jsonl
} finally { Pop-Location }
~~~

**Expected:** A new corpus containing **violet-guide-001**. Existing corpora are intentionally never overwritten.

### Step 7B: switch to this corpus for one server session and verify it

~~~powershell
$env:AET_KNOWLEDGE_PATH = "data/violet-knowledge.jsonl"
try {
    $Server = Start-AetLocalServer -Name "demo-langgraph-rag" -Port 18005
    try {
        $Result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18005/ask" -ContentType "application/json" -Body '{"question":"When are violet reference manuals indexed?"}'
        if ($Result.source_ids -notcontains "violet-guide-001" -or $Result.answer -notmatch "Thursday") { throw "New corpus was not used." }
        $Result
        Write-Host "PASS: file ingestion through independent JSONL to live RAG HTTP"
    } finally { Stop-Process -Id $Server.Id -ErrorAction SilentlyContinue }
} finally { $env:AET_KNOWLEDGE_PATH = "data/knowledge.jsonl" }
~~~

## 8. Flow G: additional inference providers

These flows are **optional**. Mock mode above is fully executable without cloud accounts. Real cloud inference **requires the user's own authorised account, model entitlement, credentials and possibly billed calls**. Never put live secrets in Git or use customer data in these unauthenticated demos.

### Step 8A: verify cloud configuration WITHOUT credentials or paid inference

This tests generation, Doctor, SDK installation and offline provider contract tests for one explicit provider. It **does not** send a live OpenAI request.

~~~powershell
& $AgentKit new demo-cloud-config --template langgraph-rag --provider openai --output-dir $Repo
if ($LASTEXITCODE -ne 0) { throw "Cloud project generation failed." }
& $AgentKit doctor (Join-Path $Repo "demo-cloud-config")
if ($LASTEXITCODE -ne 0) { throw "Cloud project Doctor failed." }
Push-Location (Join-Path $Repo "demo-cloud-config")
try {
    py $PythonVersion -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -e ".[dev,openai]"
    if ($LASTEXITCODE -ne 0) { throw "Cloud extra installation failed." }
    & .\.venv\Scripts\python.exe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Offline provider tests failed." }
} finally { Pop-Location }
Write-Host "PASS: cloud-configured starter tested without hosted model inference"
~~~

### Step 8B: full available provider matrix

Use the **same** generation, Doctor, isolated environment, extra installation and generated tests as in Step 8A with the chosen compatible template/provider. Each generated **.env.example** and README lists the exact live settings. **.[dev,PROVIDER]** is the normal SDK-extra installation, except Strands Bedrock already has its base SDK.

| Template | mock | ollama | openai | azure-openai | anthropic | bedrock |
| --- | --- | --- | --- | --- | --- | --- |
| tool-agent | Yes | Yes, base deps | Yes | Yes | Yes | Yes |
| langgraph-rag | Yes | Yes, base deps | Yes | Yes | Yes | Yes |
| strands-agent | Yes | **Unsupported** | Yes | Yes | Yes | Yes, base deps |
| llamaindex-rag | Yes | Yes, install .[dev,ollama] | Yes | Yes | Yes | Yes |

For live provider tests, securely provision your approved environment's settings: **OPENAI_API_KEY / AET_OPENAI_MODEL**, **ANTHROPIC_API_KEY / AET_ANTHROPIC_MODEL**, or an Azure HTTPS endpoint, deployment, API version and authorised Azure credentials. LlamaIndex's Azure integration also needs **AET_AZURE_OPENAI_MODEL**. Bedrock requires an authorised AWS identity, region, and **AET_BEDROCK_MODEL_ID**. These inputs cannot be generated or validated by AET offline; real model access is an explicit external prerequisite. **/ready = 503 in live-provider mode is expected**, not proof that the cloud provider is down.

### Step 8C: optionally try local Ollama (requires a model download)

This is **not** needed for any default demo. If Ollama is installed and its local service is running, execute:

~~~powershell
ollama --version
ollama pull llama3.2:1b
& $AgentKit new demo-ollama --template tool-agent --provider ollama --model llama3.2:1b --output-dir $Repo
& $AgentKit doctor (Join-Path $Repo "demo-ollama")
Push-Location (Join-Path $Repo "demo-ollama")
try {
    py $PythonVersion -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    & .\.venv\Scripts\python.exe -m pytest -q
    & .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18006
} finally { Pop-Location }
~~~

While that server runs, in a **second PowerShell terminal**, submit:

~~~powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18006/invoke" -ContentType "application/json" -Body '{"question":"hello"}'
~~~

Then press **Ctrl+C** in the server terminal. This model-based path is intentionally different from the mock server helper: Ollama/cloud configurations return **503 for /ready** until separately operationally verified.

### Step 8D: optional *live* OpenAI HTTP request, only with prior authorisation

This is the complete server/request procedure for the cloud starter generated in step 8A. **It is deliberately not executed by the no-key runbook or CI.** Before starting, your approved secret-management process must have injected **OPENAI_API_KEY** and you must supply the exact, permitted **AET_OPENAI_MODEL** for your account. A valid authorised model, credentials, network access and paid usage permission are mandatory. The generated application has no public authentication.

In the **server PowerShell terminal**, with the cloud starter from step 8A:

~~~powershell
if (-not $env:OPENAI_API_KEY -or -not $env:AET_OPENAI_MODEL) {
    throw "Approved OPENAI_API_KEY and AET_OPENAI_MODEL must already be configured."
}
$env:AET_PROVIDER = "openai"
Push-Location (Join-Path $Repo "demo-cloud-config")
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18007
~~~

While that terminal is serving, in a **second terminal**, submit a **synthetic-only** question:

~~~powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:18007/ask" -ContentType "application/json" -Body '{"question":"What is the sample return policy?"}'
~~~

A success is HTTP 200 with an answer and **source_ids**. A 503 means the selected provider or configuration was unavailable; do not infer the exact upstream failure from the sanitised API response. Press **Ctrl+C** in the server terminal and then run the following there to restore the safe default:

~~~powershell
Pop-Location
$env:AET_PROVIDER = "mock"
~~~

For other supported cloud combinations, the equivalent verified **scaffolding** contract is shown in the section-8B registry table, and each generated README specifies its provider-specific settings. Live model-specific behaviour is **not** verified by mock CI; it requires separate authorised integration evidence.

## 9. Flow H: build and probe all four development Docker images (optional)

Requires a running Docker daemon, but still no cloud credentials. Run sections 3–6 first so each project directory exists.

~~~powershell
docker version
if ($LASTEXITCODE -ne 0) { throw "Docker unavailable." }
$DockerApps = @(
    @{ Name = "demo-tool-agent"; Path = "invoke"; Port = 18101 },
    @{ Name = "demo-langgraph-rag"; Path = "ask"; Port = 18102 },
    @{ Name = "demo-strands-agent"; Path = "invoke"; Port = 18103 },
    @{ Name = "demo-llamaindex-rag"; Path = "ask"; Port = 18104 }
)
foreach ($Item in $DockerApps) {
    $Project = Join-Path $Repo $Item.Name
    $Image = "aet-" + $Item.Name
    docker build -t $Image $Project
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $Image" }
    $Port = $Item.Port
    $Binding = "127.0.0.1:" + $Port + ":8000"
    docker run -d --rm --name $Image -p $Binding $Image
    if ($LASTEXITCODE -ne 0) { throw "Container start failed: $Image" }
    try {
        $ContainerHealthy = $false
        for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
            try {
                $Health = Invoke-RestMethod -Method Get -TimeoutSec 2 -Uri "http://127.0.0.1:$Port/health"
                if ($Health.status -eq "ok") { $ContainerHealthy = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $ContainerHealthy) { throw "Container health failed: $Image" }
        $Endpoint = $Item.Path
        if ($Endpoint -eq "ask") { $Payload = '{"question":"What is the sample return policy?"}' }
        else { $Payload = '{"question":"order status ORD-1001"}' }
        $Result = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/$Endpoint" -ContentType "application/json" -Body $Payload
        if (-not $Result.answer) { throw "Container API failed: $Image" }
        Write-Host "PASS Docker: $Image"
    } finally { docker stop $Image | Out-Null }
}
~~~

**Expected:** Four Docker PASS lines, four loopback-only real HTTP probes, and no running containers left behind. These are **development-only**, unauthenticated images.

## 10. Flow I: local root tests, GitHub CI and presentation evidence

### Step 10A: root tests (different from generated-project tests)

~~~powershell
& $RootPython -m pip install pytest
if ($LASTEXITCODE -ne 0) { throw "Root pytest installation failed." }
& $RootPython -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "Root tests failed." }
~~~

Run generated-app tests with **each generated project's own** .venv\Scripts\python.exe, not the root interpreter. Never install all four generated projects into the same environment because all four use Python package name **app**.

### Step 10B: inspect the exact evidence for the reviewed commit

Open [AET GitHub Actions](https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit/actions). Select the **ci** run for the reviewed SHA and confirm **all five** status checks:

- quality (ruff, mypy, bandit)
- smoke (windows-2025, 3.11)
- smoke (windows-2025, 3.12)
- smoke (ubuntu-24.04, 3.11)
- smoke (ubuntu-24.04, 3.12)

Inspect the run's **isolated-install** artifacts (four independent apps per runner), **comprehensive-matrix** artifacts (all 23 supported pairings per runner), **deep-event** artifacts (716 synthetic scenarios per runner), Ubuntu's four Docker checks, and Windows 3.12's 16-trial RAG corpus-race stress. Artifacts expire: never describe historical outcomes as a newly completed run.

The [leadership-readiness report](release/leadership-readiness-2026-11-15.md) supplies the evidence links, risks, architecture-review argument and remaining KRA gates. The [independent fresh-user checklist](release/fresh-user-walkthrough.md) and [matched productivity study](benchmarks/study_protocol.md) are not completed human trials.

### Step 10C: a precise technical leadership demo

1. Show **agentkit list** and **agentkit doctor** from section 1.
2. Run section 3: tool routing and synthetic order response.
3. Run sections 4 and 6: two different RAG frameworks that update evidence without server restart.
4. Run section 5: real Strands SDK loop with mock model.
5. Show the latest green run and [leadership-readiness report](release/leadership-readiness-2026-11-15.md). State that human setup-time improvement, formal stakeholder approval, and multiple-team adoption remain **unverified**.

## 11. Exact recovery and limitations

| Problem | Recovery |
| --- | --- |
| Missing git or py | Install Git and Python 3.11/3.12 with the Windows launcher, reopen PowerShell, start section 1 afresh |
| PowerShell denies Activate.ps1 | No activation is needed. Always invoke the full .venv\Scripts\python.exe path |
| AET command not found | Use the stored **$AgentKit** variable from section 1 |
| Output folder already exists | AET refuses overwrite; use a fresh timestamped workspace, do not delete any existing user project |
| pip installation fails | Check your package index/network and retry inside the same project's own virtualenv; do not put credentials in logs |
| Mock /health or /ready fails | Inspect the generated project's **server-stderr.log**, check local corpus, port, and **AET_PROVIDER=mock** |
| Live provider /ready returns 503 | Expected; live connectivity is not checked by local mock readiness |
| App import points at the wrong project | Run commands with that generated app's own .venv Python and project working directory |
| Corpus edits have no effect | Edit the **generated project's** data/knowledge.jsonl, not AET's source template; verify AET_KNOWLEDGE_PATH and the running project |
| Port is occupied | Stop the earlier server/container, or change both the server's localhost port and request URLs |
| Original PowerShell session was closed | Section 1 variables and functions were session-local; rerun it in a new timestamped workspace |
| Docker unavailable | Skip section 9. The complete default native Python flows require no Docker |

**Evidence boundary:** These steps demonstrate scaffold and synthetic local API correctness, *not* live hosted-provider performance, security approval, independent developer usability, actual developer hours saved or adoption by more than one team. No additional AET feature development is necessary to execute the four default mock flows; approved cloud credentials and optional external tooling are environmental prerequisites for those separate paths.

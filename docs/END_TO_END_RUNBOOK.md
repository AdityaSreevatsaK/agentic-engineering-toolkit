# AET: Run it step by step (Windows)

## Before you begin

You only need:

- **Windows 10/11** and **PowerShell** (already included with Windows). Use PowerShell, **not Command Prompt**, for these commands.
- **Git:** [Install Git](https://git-scm.com/downloads/win).
- **Python 3.11 or 3.12:** [Install Python](https://www.python.org/downloads/windows/). Include the Windows **py launcher** during installation.
- **Internet access** to download free Python packages during setup.

**Not needed for the normal demos:** WSL, Docker, a cloud account, API keys, a local AI model or paid services.

## Step 1. Open PowerShell

Press the Windows key, search for **PowerShell**, and open it.

Copy and paste these two commands:

~~~powershell
git clone https://github.com/AdityaSreevatsaK/agentic-engineering-toolkit.git
cd agentic-engineering-toolkit
~~~

You are now inside the AET folder. **You only need to do this once.**

## Step 2. Try everything (recommended)

In the same PowerShell window, paste:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow all
~~~

**What happens automatically:**

1. Installs AET.
2. Creates all **four** projects, each with its own Python environment.
3. Runs Project Doctor, package checks and each project's tests.
4. Starts each app on your computer, makes actual HTTP requests, checks the results and shuts it down.
5. Changes sample RAG data and checks that both RAG workflows return the new answer. Also tests text-file ingestion.

**What you should see:** several **PASS** messages and a final **SUCCESS: all completed** message. No need to open a second terminal or edit files manually.

After a successful run, the script **deletes the temporary demo projects** to save disk space. To inspect the generated projects yourself, add `-KeepOutput` to the end of any demo command. If a run fails, the script **keeps the projects and server logs** and prints their folder so you can investigate.

## Step 3. Try one flow instead

You can run just one of these. **Paste the command for the flow you want** into PowerShell while inside the AET folder.

### A. LangGraph Tool Agent

Checks an example order-status tool and a normal mock response.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow tool-agent
~~~

Expected: **PASS: LangGraph tool routing and default mock response**.

### B. LangGraph RAG

Asks a question, adds a sample document and confirms that the answer changes.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow langgraph-rag
~~~

Expected: **PASS: RAG before and after corpus change**.

### C. AWS Strands Agent

Runs the real Strands SDK agent loop with a local sample tool. No AWS account needed.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow strands-agent
~~~

Expected: **PASS: real Strands SDK tool loop**.

### D. LlamaIndex RAG

Runs LlamaIndex keyword search, adds sample knowledge and checks the result again.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow llamaindex-rag
~~~

Expected: **PASS: RAG before and after corpus change**.

### E. Load a text document into RAG

Creates a sample text file, imports it into LangGraph RAG and checks the new answer.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow ingestion
~~~

Expected: **PASS: text ingestion and live API retrieval**.

## Step 4. Other flows (optional)

These are **not required** to complete the normal demos.

**Check cloud-provider setup without making a paid call.** This creates an OpenAI-configured LangGraph RAG project, installs its provider package and runs offline tests. **No API key needed.**

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow cloud-config -Template langgraph-rag -Provider openai
~~~

To check a different supported combination, replace the template and provider values. For the full provider compatibility table and approved live-inference setup, see the [detailed technical guide](END_TO_END_RUNBOOK_DETAILED.md). Live cloud inference requires **your own approved credentials, model and possibly paid usage**. It cannot be performed automatically without them.

**Try a local Ollama model.** First, install and start [Ollama](https://ollama.com/download/windows). The command below will download **llama3.2:1b** if you do not already have it.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow ollama
~~~

Expected: **PASS: Ollama local inference**. This optional download needs internet access and disk space.

**Test all four Docker images.** First, install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_windows.ps1 -Flow docker
~~~

Expected: **four PASS docker smoke** messages. This is a local development test only.

## If something goes wrong

- **git is not recognised:** install Git, reopen PowerShell and repeat Step 1.
- **py launcher / Python not found:** install Python 3.11 or 3.12 with the Windows launcher, reopen PowerShell and repeat.
- **pip cannot download packages:** check your internet connection and whether your network permits Python package downloads.
- **You already cloned AET:** open PowerShell, run cd to your existing AET folder, then use any Step 2, 3 or 4 command.
- **A demo fails:** read the error shown in PowerShell. The output folder is printed near the start and kept after a failure; generated server error logs are inside its project folders.

The PowerShell option **-ExecutionPolicy Bypass** applies only to that new PowerShell process. It does not permanently change your computer's PowerShell policy.

## More information

- [Detailed command-by-command technical reference](END_TO_END_RUNBOOK_DETAILED.md) for manual server operation, request payloads, configuration and troubleshooting.
- [Supported templates and provider wiring](../PROJECT_DEEP_DIVE.md).
- [Leadership readiness and evidence](release/leadership-readiness-2026-11-15.md).

**Reminder:** These demos use synthetic examples. Passing them does not make generated apps production-secure or prove real developer time savings or adoption by other teams.

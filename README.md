# QuotaPilot

**A local-first AI coding context optimizer for large codebases.**

QuotaPilot helps developers prepare focused, task-specific code context instead of repeatedly supplying information from an entire repository to an AI coding assistant.

It scans a workspace, estimates token usage, searches for relevant files, and prepares a context brief within a configurable token budget.

## Features

- **Local-first processing:** Runs locally without requiring a paid AI API.
- **Workspace scanning:** Indexes project files while excluding common generated directories and sensitive files.
- **Relevance-based search:** Finds files related to a coding task.
- **Context preparation:** Selects relevant files under a target token budget.
- **MCP integration:** Exposes tools to compatible AI clients through the Model Context Protocol.
- **Automated tests:** Includes pytest tests for core functionality.

## Architecture

```text
Developer task
      |
      v
QuotaPilot
      |
      +--> Scan workspace
      |
      +--> Search relevant files
      |
      +--> Estimate token usage
      |
      v
Focused context brief
      |
      v
Compatible AI coding assistant
```

## Requirements

- Python 3.11 or newer
- Windows, macOS, or Linux
- Git (optional, for cloning the repository)

## Installation

Clone the repository and enter its directory:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd QuotaPilot
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the package and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Run the tests

```bash
python -m pytest -v
```

## Local usage

Set the workspace that QuotaPilot should scan.

Windows PowerShell:

```powershell
$env:QUOTAPILOT_ROOT = "C:\path\to\your\project"
```

Set the Python source path when running from a source checkout:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

Check workspace status:

```powershell
python -c "from quotapilot.mcp_server import qp_status; print(qp_status())"
```

Search for relevant files:

```powershell
python -c "from quotapilot.mcp_server import qp_search; print(qp_search('privacy deletion endpoint'))"
```

Prepare a task-specific context brief:

```powershell
python -c "from quotapilot.mcp_server import qp_prepare_task; print(qp_prepare_task('Add a privacy deletion endpoint', 6000))"
```

The token figures are estimates and may differ from the actual tokenization used by an AI provider.

## MCP integration

QuotaPilot exposes these tools through its MCP server:

| Tool | Purpose |
|---|---|
| `qp_status` | Reports workspace status and scan statistics |
| `qp_search` | Searches for task-relevant files |
| `qp_get_file` | Retrieves an eligible project file |
| `qp_prepare_task` | Prepares focused context for a coding task |

Start the server using:

```bash
quotapilot-mcp
```

Compatible MCP clients can launch the server as a local process using the installed Python environment and the module `quotapilot.mcp_server`.

Configure the workspace root for the target project before connecting the client.

## Security considerations

- Keep API keys, passwords, and other secrets out of source control.
- Review files before sharing their contents with an AI assistant.
- Use an appropriate workspace root and test path restrictions.
- Treat generated context briefs as potentially sensitive if they contain proprietary source code.

## Current status

The core project has three automated tests covering token estimation, secret-file exclusion, and relevant-file selection. Additional integration and security tests are recommended before relying on the tool in production.

## License

No license has been selected yet. Add a `LICENSE` file before presenting the project as open source.

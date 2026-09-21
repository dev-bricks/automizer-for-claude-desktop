# Third-Party Licenses & Software Inventory

> **Project:** `dev-bricks/automizer-for-claude-desktop`<br>
> **Repository License:** [MIT License](LICENSE)<br>
> **Audited:** 2026-09-21<br>
> **Status:** Invariant Confirmed — Zero External Runtime Dependencies (`INV-ACD-02`)<br>
> **Architecture & Security:** 100% Local-First, Zero-Egress, Atomic File Swap Protocol, Windows Local AppData Sandbox

---

## 1. Executive Summary & Zero-Copyleft Isolation Guarantee

`automizer-for-claude-desktop` is engineered to reliably inspect, queue, modify, and apply scheduled tasks for the Claude Desktop App on Windows environments without file-lock contention or data corruption. To preserve maximum operational reliability across multi-agent environments (Claude Code CLI, OpenAI Codex CLI, Google Antigravity / AGY CLI, Kimi Code CLI), ensure deterministic local execution, and eliminate external supply-chain attack vectors, `automizer-for-claude-desktop` strictly enforces the **Zero External Runtime Dependencies** invariant (**INV-ACD-02**).

- **100% Permissive / Standard Library:** Core execution uses exclusively the Python Standard Library distributed under the Python Software Foundation License (PSFL-2.0).
- **Zero-Copyleft Isolation Guarantee:** No GPL, AGPL, or viral copyleft dependencies are incorporated into the runtime distribution.
- **Unprivileged User-Mode Execution:** Operates strictly within user-space directories (`%APPDATA%`, `%LOCALAPPDATA%`) without requesting root or administrator privileges.

---

## 2. Invariant Cross-Reference Matrix (INV-ACD-01 .. INV-ACD-08)

| Invariant ID | Guarantee & Scope | Enforcing Subsystem / Module | Compliance Assurance |
|---|---|---|---|
| **INV-ACD-01** | **Atomic Swap Protocol** | `tools/apply_pending_tasks.py` | Queue files and task state are replaced via atomic filesystem operations, preventing partial writes. |
| **INV-ACD-02** | **Zero External Runtime Dependencies** | `pyproject.toml`, `tools/` | Zero external runtime wheels; 100% pure Python standard library (`json`, `pathlib`, `os`, `sys`, `shutil`, `argparse`). |
| **INV-ACD-03** | **Pre-Mutation Backup Rotation** | `tools/apply_pending_tasks.py` | Automated pre-modification backups (`*.backup-<timestamp>`) with bounded retention before any write operation. |
| **INV-ACD-04** | **Strict Validation Before Apply** | `tools/apply_pending_tasks.py` | Payload syntax, required fields, and JSON structure are validated before touching production task storage. |
| **INV-ACD-05** | **Decoupled Queue Architecture** | `tools/queue_request.py` | Safe request enqueuing decouples agent write operations from Desktop App memory-lock lifecycles. |
| **INV-ACD-06** | **Transparent Windowless Background Runner** | `tools/run_apply_pending_hidden.vbs` | Zero intrusive console popup windows during scheduled merge executions. |
| **INV-ACD-07** | **Zero-Egress Local-First Privacy** | `tools/` | Strictly offline operation; zero outbound HTTP/HTTPS telemetric or analytical connections. |
| **INV-ACD-08** | **48h Security & Governance SLA** | `SECURITY.md`, `dev-bricks` | Committed 48-hour response SLA and 5-business-day vulnerability triage for all reported security hazards. |

---

## 3. Level 1 Software Bill of Materials (SBOM) & SPDX Package Inventory

### Runtime Dependencies

| Package | Version Spec | SPDX Identifier | Scope | Upstream / Repository | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Python Standard Library** | `>=3.8` | `Python-2.0` | `runtime` | [python/cpython](https://github.com/python/cpython) | JSON parsing, filesystem I/O, process handling, logging |
| *(External Wheels)* | `None` | `N/A` | `runtime` | `N/A` | Pure standard library invariant confirmed |

### Development, Test & Build Tooling

| Package / Tool | Version Spec | SPDX Identifier | Scope | Upstream / Repository | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **[pytest](https://pytest.org/)** | `>=8.0.0` | `MIT` | `[test]` | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Automated unit, regression, contract, and metadata test suite execution |
| **[ruff](https://github.com/astral-sh/ruff)** | `>=0.5.0` | `MIT OR Apache-2.0` | `[dev]` | [astral-sh/ruff](https://github.com/astral-sh/ruff) | High-performance Python linter, style enforcer, and AST validation |
| **[setuptools](https://github.com/pypa/setuptools)** | `>=77.0.0` | `MIT` | `[build-system]` | [pypa/setuptools](https://github.com/pypa/setuptools) | Standard PEP 517 / PEP 621 build backend and package distribution |
| **[wheel](https://github.com/pypa/wheel)** | `>=0.40.0` | `MIT` | `[build-system]` | [pypa/wheel](https://github.com/pypa/wheel) | Standard wheel binary distribution format builder |

---

## 4. License Texts

### MIT License

```text
MIT License

Copyright (c) 2026 dev-bricks Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Python Software Foundation License (PSFL-2.0)

```text
PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------

1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
the Individual or Organization ("Licensee") accessing and otherwise using this
software ("Python") in source or binary form and its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works, distribute,
and otherwise use Python alone or in any derivative version, provided, however, that
PSF's License Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001-2026
Python Software Foundation; All Rights Reserved" are included in Python alone or
in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on or incorporates
Python or any part thereof, and wants to make the derivative work available to
others as provided herein, then Licensee hereby agrees to include in any such work
a brief summary of the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS" basis. PSF MAKES NO
REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED. BY WAY OF EXAMPLE, BUT NOT
LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY OF
MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON
WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY
INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF MODIFYING,
DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF
ADVISED OF THE POSSIBILITY THEREOF.
```

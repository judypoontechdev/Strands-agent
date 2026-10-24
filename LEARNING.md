# Serverless AI Agent on AWS Lambda: Architecture & Key Learnings

## 1. End-to-End Pipeline Architecture

### Pipeline Flow Diagram

```text
[ Developer Machine ]
        │  (cdk deploy)
        ▼
   Docker Build ───► Bundles src/ + pip packages (strands-agents) into artifact
        │
        ▼
   AWS Lambda Function (Python 3.11)
        │
   [1. Entry Point: lambda_handler.py]
        │
        ▼
   [2. Orchestrator: agent.py]
        │
        ├──► Amazon Bedrock (Claude 3.5 Haiku) ── Reasoning & Tool Selection
        │                                                     │
        ◄─────────────────────────────────────────────────────┘
        │
        ├──► [3. Tool Execution: tools.py]
        │         │
        │         ├──► get_country_info() ──► REST Countries API (HTTPS + API Key)
        │         │                                  │
        │         ◄──────────────────────────────────┘
        │         │
        │         └──► population_ratio_difference() ── Pure Python computation
        │
        ▼
   [4. Response Serialization: str(AgentResult)]
        │
        ▼
[ Client / Invoker (HTTP 200 JSON Payload) ]
```

---

### Key File Descriptions & Responsibilities

| File                         | Primary Role & Purpose                                                                                                                                                                                                                                               |
| :--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`src/lambda_handler.py`**  | **The Entry Point (`lambda_handler`)**: AWS Lambda's contract target. It receives the incoming event payload (e.g. `event["prompt"]`), invokes the agent instance, casts the response into a JSON-compliant format, and returns the standard HTTP status dictionary. |
| **`src/agent.py`**           | **The Orchestrator**: Instantiates the AI agent (`Agent`) and associates the LLM (AWS Bedrock Claude Haiku) with the registered custom tools (`get_country_info`, `population_ratio_difference`). Handles dialogue history and context windows.                      |
| **`src/tools.py`**           | **The Tool Implementations**: Defines domain-specific tools decorated with `@tool`. Houses the external HTTP request logic (injecting authentication headers) and mathematical calculation functions.                                                                |
| **`cdk/lib/agent-stack.ts`** | **Infrastructure as Code (IaC)**: Configures Docker-based automated packaging (`PythonFunction`), manages environment variable injection, and grants least-privilege IAM permissions for Bedrock invocation.                                                         |

---

## 2. Technical Learnings & CloudWatch Debugging

### 2.1 Python Import Resolution: Flat Packaging in AWS Lambda

- **Issue**: Running `from src.tools import ...` threw `ModuleNotFoundError: No module named 'src'`.
- **Root Cause**: CDK was configured with `entry: "../src"`. When packaging, CDK extracts the _contents_ of `src/` directly to the Lambda deployment root (`/var/task/`). The `src/` folder itself does not exist in Lambda; the files sit at the root level.
- **Fix**: Use direct flat imports instead of package-relative paths:

  ```python
  # Before (Failed)
  from src.tools import get_country_info, population_ratio_difference

  # After (Resolved)
  from tools import get_country_info, population_ratio_difference
  ```

---

### 2.2 Third-Party Library Resolution: Moving to `PythonFunction`

- **Issue**: `from strands import Agent` threw `ImportModuleError`.
- **Root Cause**: Standard CDK `lambda.Function` merely zips existing source files as plain text; it does not resolve or compile external Python dependencies (`requirements.txt`).
- **Fix**:
  1. Migrate to `@aws-cdk/aws-lambda-python-alpha`'s `PythonFunction`.
  2. Place `requirements.txt` inside the `src/` directory where `entry` points.
  3. CDK automatically spins up a local Docker container (`public.ecr.aws/sam/build-python3.11`), runs `pip install -r requirements.txt -t /asset-output`, and produces a deployment zip containing all dependencies.
- _Note: Does this require `npm install`?_ No for Python dependencies, but **yes** for the CDK alpha construct:
  ```bash
  npm install @aws-cdk/aws-lambda-python-alpha
  ```

---

### 2.3 JSON Serialization Failure (`Runtime.MarshalError`)

- **Issue**:
  ```text
  [ERROR] Runtime.MarshalError: Unable to marshal response: Object of type AgentResult is not JSON serializable
  ```
- **Root Cause**: Lambda requires the returned dictionary to be serializable by `json.dumps()`. The variable returned by `agent(user_prompt)` was a custom Python class object (`AgentResult`), not a raw string.
- **Fix**: Wrap the custom object with `str()` to normalize it to standard text before returning:

  ```python
  # src/lambda_handler.py
  response = agent(user_prompt)

  return {
      "statusCode": 200,
      "message": str(response)  # Explicit string conversion
  }
  ```

---

### 2.4 External API Authentication & Environment Variable Injection

- **Issue**: The agent experienced fallback behavior because the tool failed to authenticate against the third-party REST API.
- **Root Cause**: `.env` was not transferred to Lambda, so `os.getenv("REST_COUNTRIES_API_KEY")` returned `None`, sending `"Authorization": "Bearer None"`.
- **Fix**: Safely read the key from the host during CDK synthesis using Node's `dotenv`, and inject it into Lambda's native configuration:

  ```typescript
  // cdk/lib/agent-stack.ts
  import * as dotenv from "dotenv";
  import * as path from "path";

  dotenv.config({ path: path.join(__dirname, "../../.env") });

  const agent = new PythonFunction(this, "AgentHandler", {
    // ...
    environment: {
      REST_COUNTRIES_API_KEY: process.env.REST_COUNTRIES_API_KEY || "",
    },
  });
  ```

  ```python
  # src/tools.py
  api_key = os.getenv("REST_COUNTRIES_API_KEY")
  headers = {"Authorization": f"Bearer {api_key}"}
  ```

---

## 3. Architecture & Dependency Management Insights

### 3.1 CDK Project Metadata Files

- **`cdk.json`**:
  - **Role**: The configuration file that tells the CDK CLI what command to execute when synthesizing CloudFormation (e.g. `"app": "npx ts-node --prefer-ts-exts bin/cdk.ts"`).
  - **Creation**: Created automatically when initializing a CDK project (`cdk init`).
- **`package.json`**:
  - **Role**: Defines project metadata, npm scripts, and dependencies for the **TypeScript / CDK** infrastructure stack.
  - **Creation**: Automatically initialized by `cdk init` and automatically updated whenever you run `npm install <package>`.
- **`package-lock.json`**:
  - **Role**: Locks the exact transitive versions of Node.js dependencies installed in `node_modules` to ensure reproducible builds.
  - **Creation**: Automatically generated and maintained by `npm`. Should never be manually edited.

---

### 3.2 Polyglot Dependency Strategy: NPM vs. Python `pip freeze`

In a polyglot repository (TypeScript CDK + Python Lambda):

```text
Host Environment (Node.js / npm)          Target Environment (Python / pip)
───────────────────────────────          ─────────────────────────────────
cdk/package.json                         src/requirements.txt
Controls CDK compilation & synthesis     Controls Lambda runtime execution
Managed via `npm install <pkg>`          Curated manually (minimal specification)
```

#### Why avoid blind `pip freeze > requirements.txt`?

1. **Container Bloat**: `pip freeze` dumps every package from your local virtual environment, including dev-only tools (`pytest`, `black`, `flake8`, `ipython`).
2. **Slow Deployment**: The Docker bundling process inside CDK has to compile and install dozens of irrelevant wheels, dramatically slowing down `cdk deploy`.
3. **Lambda Storage Limits**: Lambda has a 250 MB unzipped storage cap. Bloated dependencies can exceed this limit.
4. **Best Practice**: Only write runtime imports into `src/requirements.txt`:
   ```text
   strands-agents
   ```
   Pip will resolve and fetch required sub-dependencies automatically during Docker build.

---

### 3.3 What is `__dirname`?

- `__dirname` is an ambient variable in Node.js representing the **absolute directory path of the current source file**.
- In `cdk/lib/agent-stack.ts`, `__dirname` evaluates to:
  ```text
  /path/to/project-root/cdk/lib
  ```
- Navigating via `../../.env`:
  - First `..`: Exits `lib/` into `cdk/`
  - Second `..`: Exits `cdk/` into `project-root/`
  - `path.join(__dirname, "../../.env")` forms an invariant, robust absolute path to `.env` regardless of which sub-directory the CLI command is executed from.

# Serverless Geopolitical Analysis Agent (AWS Bedrock & CDK)

A production-ready, serverless AI agent powered by **Amazon Bedrock (Claude)** and **AWS Lambda**, provisioned with Infrastructure as Code via **AWS CDK (TypeScript)**.

The agent autonomously plans and executes multi-step workflows using custom tool bindings—fetching real-time geopolitical intelligence via REST APIs and computing precise demographic disparities.

---

## Architecture

```text
User / Client Request
        │
        ▼
┌───────────────────────────┐
│        AWS Lambda         │ ◄── [CDK Managed Infrastructure]
│      (Python Runtime)     │
└─────────────┬─────────────┘
              │ (boto3 / Converse API)
              ▼
┌───────────────────────────┐
│       Amazon Bedrock      │ ── (Reasoning & Tool Selection Loop)
│      (Claude Engine)      │
└─────────────┬─────────────┘
              ├──► Tool: get_country_info (REST Countries API)
              └──► Tool: population_ratio_difference (Deterministic Math Engine)
```

- **Runtime & Orchestration**: Python Lambda function driven by AWS Bedrock foundation models using conversational tool invocation loops.
- **Function Calling & Tool Use**: Autonomous selection between external REST endpoints and local computational logic to eliminate hallucinated metrics.
- **Infrastructure as Code (IaC)**: AWS CDK (TypeScript) manages IAM least-privilege role attachments, environment injection, and asset bundling.
- **Security & Secret Isolation**: System-level credential resolution via local AWS profiles, environment isolation through uncommitted `.env` configs, and strict Git exclusion rules.

---

## Tools & Capabilities

1. **`get_country_info`**:
   - Queries real-time geopolitical and demographic data (capital, population, region, currencies, languages) via the REST Countries API.
2. **`population_ratio_difference`**:
   - Executes deterministic arithmetic operations on population data to calculate exact ratios and absolute differences.

---

## Repository Structure

```text
.
├── cdk/                       # AWS CDK Infrastructure (TypeScript)
│   ├── bin/cdk.ts             # CDK entrypoint
│   ├── lib/agent-stack.ts     # Lambda, IAM roles, and Stack definitions
│   └── cdk.json               # CDK CLI configuration
├── src/                       # Application Runtime Logic (Python)
│   ├── agent.py               # Bedrock agent core loop & system prompts
│   ├── lambda_handler.py      # AWS Lambda entrypoint
│   ├── tools.py               # Custom tools definitions & schemas
│   └── requirements.txt       # Production runtime dependencies
├── tests/                     # Unit and integration test suites
│   └── test_agent.py
├── .gitignore                 # Strict secrets and artifact ignore rules
├── LEARNING.md                # Architecture notes & debugging journey
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js (v18+) & npm
- Python (3.10+)
- AWS CLI configured with active credentials (`aws configure`)

### 1. Installation

Clone the repository and set up environment dependencies:

```bash
git clone https://github.com/judypoontechdev/strands-agent.git
cd strands-agent
```

Set up root and CDK dependencies:

```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install CDK dependencies
cd cdk
npm install
cd ..
```

### 2. Configure Environment

Create a `.env` file in the root directory (this file is excluded from Git tracking):

```bash
REST_COUNTRIES_API_KEY=your_api_key_here
```

### 3. Deploy Stack

Deploy the CDK stack directly to your AWS environment:

```bash
cd cdk
npx cdk deploy
```

---

## Verification & Invocation

Invoke the deployed Lambda function directly via the AWS CLI:

```bash
aws lambda invoke \
  --function-name AgentStack-AgentHandler \
  --payload '{"prompt": "Compare the population difference and ratio between Japan and South Korea"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

---

## Teardown

Destroy all provisioned AWS resources to eliminate idle infrastructure overhead:

```bash
cd cdk
npx cdk destroy
```

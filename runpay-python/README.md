# runpay-python

Official Python SDK for [run.pay](https://getrunpay.com) — The API marketplace for AI agents.

[![PyPI version](https://badge.fury.io/py/runpay.svg)](https://pypi.org/project/runpay/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Installation

```bash
pip install runpay
```

## Quick start

```python
import runpay

# Get your free agent ID at getrunpay.com/playground
runpay.configure(agent_id="agt_your_id_here")

# Detect hallucinations
result = runpay.call("halludetect", {
    "response": "According to Harvard, 73.2% of AI models hallucinate daily."
})
print(result["hallucination_score"])  # 87
print(result["risk"])                 # "high"
print(result["_meta"]["cost"])        # 0.01

# Scan for PII
result = runpay.call("piiscan", {"text": "Email me at john@example.com"})
print(result["pii_found"])  # ["email"]

# GDPR check
result = runpay.call("gdprcheck", {"text": "We sell your data to advertisers."})
print(result["compliant"])  # False
```

## Use environment variable

```bash
export RUNPAY_AGENT_ID=agt_your_id_here
```

```python
import runpay
result = runpay.call("halludetect", {"response": "text"})  # no configure() needed
```

## Available functions

| Function | Description |
|---|---|
| `runpay.configure(agent_id)` | Set your agent wallet ID |
| `runpay.call(service_id, payload)` | Call any service and pay |
| `runpay.trial_call(service_id, payload, trial_id)` | Free trial call (3/service) |
| `runpay.services(category=None)` | List all 205 services |
| `runpay.wallet()` | Check balance |

## LangChain & CrewAI tools

Turn all 205 services into ready-to-use agent framework tools — no manual tool definitions needed, generated automatically from the live catalog.

```bash
pip install runpay[langchain]   # or runpay[crewai], or runpay[all]
```

```python
from runpay.langchain import get_tools

tools = get_tools(agent_id="agt_your_id")                     # all 205 services
tools = get_tools(agent_id="agt_your_id", category="Security") # just one category

from langchain.agents import initialize_agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
```

```python
from runpay.crewai import get_tools

tools = get_tools(agent_id="agt_your_id")

from crewai import Agent
researcher = Agent(role="Researcher", goal="...", tools=tools)
```

Each tool's arguments come from the service's published input schema. Services that haven't published one yet still work — they fall back to a single generic `payload` argument.

## Links

- **Get a free agent ID**: [getrunpay.com/playground](https://getrunpay.com/playground)
- **All 205 services**: [getrunpay.com/docs](https://getrunpay.com/docs)
- **OpenAPI spec**: [getrunpay.com/openapi.json](https://getrunpay.com/openapi.json)
- **MCP server**: [smithery.ai/servers/runpay/marketplace](https://smithery.ai/servers/runpay/marketplace)

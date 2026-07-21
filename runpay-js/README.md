# runpay

Official JavaScript/Node.js SDK for [run.pay](https://getrunpay.com) — The API marketplace for AI agents.

[![npm version](https://badge.fury.io/js/runpay.svg)](https://www.npmjs.com/package/runpay)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Installation

```bash
npm install runpay
```

## Quick start

```javascript
const runpay = require('runpay')

// Get your free agent ID at getrunpay.com/playground
runpay.configure('agt_your_id_here')

// Detect hallucinations
const result = await runpay.call('halludetect', {
  response: 'According to Harvard, 73.2% of AI models hallucinate daily.'
})
console.log(result.hallucination_score)  // 87
console.log(result.risk)                 // 'high'
console.log(result._meta.cost)           // 0.01

// Scan for PII
const pii = await runpay.call('piiscan', {
  text: 'Contact john@example.com or call 555-1234'
})
console.log(pii.pii_found)  // ['email', 'phone']
```

## ESM / ES Modules

```javascript
import { configure, call, services, wallet } from 'runpay'

configure('agt_your_id')
const result = await call('halludetect', { response: 'text to check' })
```

## LangChain integration

```javascript
const { Tool } = require('langchain/tools')
const runpay = require('runpay')

runpay.configure(process.env.RUNPAY_AGENT_ID)

const halluTool = new Tool({
  name: 'hallucination_detector',
  description: 'Detects hallucinations in AI responses. Input: text to check.',
  func: async (text) => {
    const r = await runpay.call('halludetect', { response: text })
    return `Score: ${r.hallucination_score}/100. Risk: ${r.risk}. Cost: $${r._meta.cost}`
  }
})
```

## API

| Function | Description |
|---|---|
| `configure(agentId)` | Set your agent wallet ID |
| `call(serviceId, payload, agentId?)` | Call any service and pay |
| `trialCall(serviceId, payload, trialId)` | Free trial call |
| `services(category?)` | List all 205 services |
| `wallet(agentId?)` | Check wallet balance |

## Environment variable

```bash
export RUNPAY_AGENT_ID=agt_your_id_here
```

## Links

- **Get a free agent ID**: [getrunpay.com/playground](https://getrunpay.com/playground)
- **Docs**: [getrunpay.com/docs](https://getrunpay.com/docs)
- **OpenAPI**: [getrunpay.com/openapi.json](https://getrunpay.com/openapi.json)
- **MCP**: [smithery.ai/servers/runpay/marketplace](https://smithery.ai/servers/runpay/marketplace)
- **Python SDK**: [github.com/PalabreX/runpay-python](https://github.com/PalabreX/runpay-python)

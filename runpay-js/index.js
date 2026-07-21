/**
 * run.pay — The API marketplace for AI agents
 * 205 specialized services, pay-per-call via Stripe
 * https://getrunpay.com
 */

const API_BASE = 'https://runpay-backend-visibility-production.up.railway.app'

let _agentId = null

/**
 * Configure your agent wallet ID
 * @param {string} agentId - Your agent ID (agt_xxx). Get one free at getrunpay.com/playground
 */
function configure(agentId) {
  _agentId = agentId
}

function getAgentId(agentId) {
  const aid = agentId || _agentId || process.env.RUNPAY_AGENT_ID
  if (!aid) throw new Error(
    'No agent ID. Set RUNPAY_AGENT_ID env var, call runpay.configure(), or pass agentId. ' +
    'Get a free ID at getrunpay.com/playground'
  )
  return aid
}

/**
 * Call any service on run.pay
 * @param {string} serviceId - Service ID (e.g. 'halludetect', 'piiscan')
 * @param {object} payload - Service-specific input
 * @param {string} [agentId] - Your agent wallet ID
 * @returns {Promise<object>} Service result with _meta cost info
 */
async function call(serviceId, payload, agentId) {
  const aid = getAgentId(agentId)
  const res = await fetch(`${API_BASE}/x402/${serviceId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-agent-id': aid,
      'User-Agent': 'runpay-js/1.0.0'
    },
    body: JSON.stringify(payload)
  })
  const data = await res.json()
  if (res.status === 402) {
    const err = new Error(`Insufficient balance: $${data.balance} available, $${data.required} required. Add funds at getrunpay.com/agent-wallet`)
    err.code = 'INSUFFICIENT_BALANCE'
    err.balance = data.balance
    err.required = data.required
    throw err
  }
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
  return data
}

/**
 * Try a service for free (3 calls per service, no card needed)
 * @param {string} serviceId - Service ID
 * @param {object} payload - Service input
 * @param {string} trialAgentId - Your trial agent ID from getrunpay.com/playground
 */
async function trialCall(serviceId, payload, trialAgentId) {
  const res = await fetch(`${API_BASE}/playground/call/${serviceId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'User-Agent': 'runpay-js/1.0.0' },
    body: JSON.stringify({ ...payload, _trial_agent_id: trialAgentId })
  })
  return res.json()
}

/**
 * List all available services
 * @param {string} [category] - Filter: AI, Security, Compliance, Data, Reasoning
 * @returns {Promise<Array>} Services with IDs, descriptions, pricing
 */
async function services(category) {
  const res = await fetch(`${API_BASE}/api/services/catalog`, {
    headers: { 'User-Agent': 'runpay-js/1.0.0' }
  })
  let svcs = await res.json()
  if (category) svcs = svcs.filter(s => s.category?.toLowerCase() === category.toLowerCase())
  return svcs
}

/**
 * Check agent wallet balance
 * @param {string} [agentId] - Your agent ID
 * @returns {Promise<object>} Wallet with balance, total_spent, mode
 */
async function wallet(agentId) {
  const aid = getAgentId(agentId)
  const res = await fetch(`${API_BASE}/api/agents/wallet/${aid}`, {
    headers: { 'User-Agent': 'runpay-js/1.0.0' }
  })
  return res.json()
}

module.exports = { configure, call, trialCall, services, wallet }

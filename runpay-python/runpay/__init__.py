"""
run.pay — The API marketplace for AI agents.
205 specialized services, pay-per-call via Stripe.

Usage:
    import runpay
    runpay.configure(agent_id="agt_xxx")
    result = runpay.call("halludetect", {"response": "text to check"})
"""

import urllib.request
import json
import os

_API_BASE = "https://runpay-backend-visibility-production.up.railway.app"
_agent_id = None

def configure(agent_id: str, api_base: str = None):
    """Set your agent wallet ID. Get one free at getrunpay.com/playground"""
    global _agent_id, _API_BASE
    _agent_id = agent_id
    if api_base:
        _API_BASE = api_base

def call(service_id: str, payload: dict, agent_id: str = None) -> dict:
    """
    Call any service on run.pay and pay automatically.

    Args:
        service_id: Service ID from the catalog (e.g. 'halludetect', 'piiscan')
        payload: Service-specific input (see getrunpay.com/docs)
        agent_id: Your agent wallet ID. Falls back to configured ID or RUNPAY_AGENT_ID env var.

    Returns:
        dict: Service result + _meta with cost and balance info

    Example:
        result = runpay.call("halludetect", {"response": "text to check"}, agent_id="agt_xxx")
        print(result["hallucination_score"])  # 87
        print(result["_meta"]["cost"])        # 0.01
    """
    aid = agent_id or _agent_id or os.environ.get("RUNPAY_AGENT_ID")
    if not aid:
        raise ValueError(
            "No agent ID provided. Set RUNPAY_AGENT_ID env var, call runpay.configure(), "
            "or pass agent_id=. Get a free ID at getrunpay.com/playground"
        )

    url = f"{_API_BASE}/x402/{service_id}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-agent-id": aid,
            "User-Agent": "runpay-python/1.0.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        if e.code == 402:
            raise InsufficientBalanceError(body.get("balance", 0), body.get("required", 0))
        raise RunpayError(body.get("error", str(e)))

def trial_call(service_id: str, payload: dict, trial_agent_id: str) -> dict:
    """Call a service using a free trial ID (3 calls per service, no card needed)."""
    payload["_trial_agent_id"] = trial_agent_id
    url = f"{_API_BASE}/playground/call/{service_id}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "runpay-python/1.0.0"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())

def services(category: str = None) -> list:
    """
    List all available services.

    Args:
        category: Filter by category (AI, Security, Compliance, Data, Reasoning)

    Returns:
        list: All services with IDs, descriptions, and pricing
    """
    url = f"{_API_BASE}/api/services/catalog"
    req = urllib.request.Request(url, headers={"User-Agent": "runpay-python/1.0.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        svcs = json.loads(response.read())
    if category:
        svcs = [s for s in svcs if s.get("category", "").lower() == category.lower()]
    return svcs

def wallet(agent_id: str = None) -> dict:
    """Check your agent wallet balance."""
    aid = agent_id or _agent_id or os.environ.get("RUNPAY_AGENT_ID")
    if not aid:
        raise ValueError("No agent ID. Set RUNPAY_AGENT_ID or call runpay.configure()")
    url = f"{_API_BASE}/api/agents/wallet/{aid}"
    req = urllib.request.Request(url, headers={"User-Agent": "runpay-python/1.0.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read())

class RunpayError(Exception):
    pass

class InsufficientBalanceError(RunpayError):
    def __init__(self, balance: float, required: float):
        self.balance = balance
        self.required = required
        super().__init__(
            f"Insufficient balance: ${balance:.4f} available, ${required:.4f} required. "
            "Add funds at getrunpay.com/agent-wallet"
        )

__version__ = "1.0.0"
__all__ = ["configure", "call", "trial_call", "services", "wallet", "RunpayError", "InsufficientBalanceError"]

"""
LangChain integration for run.pay.

Turns any of the 205 services in the run.pay catalog into ready-to-use
LangChain tools, generated automatically from the live service catalog —
no manual tool definitions needed.

Usage:
    from runpay.langchain import get_tools

    tools = get_tools(agent_id="agt_your_id")       # all 205 services
    tools = get_tools(agent_id="agt_your_id", category="Security")  # one category

    # Use with any LangChain agent
    from langchain.agents import initialize_agent
    agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

Requires: pip install runpay[langchain]
"""

try:
    from langchain_core.tools import StructuredTool
except ImportError:
    try:
        from langchain.tools import StructuredTool
    except ImportError:
        raise ImportError(
            "LangChain is not installed. Run `pip install langchain` "
            "(or `pip install runpay[langchain]`) to use runpay.langchain."
        )

try:
    from pydantic import create_model, Field
except ImportError:
    raise ImportError("pydantic is required for runpay.langchain. Run `pip install pydantic`.")

import json
import urllib.request
import urllib.parse
import runpay as _runpay


def _fetch_marketplace(category=None):
    """
    /api/marketplace is the catalog endpoint that includes each service's
    published schema_input/schema_output — unlike runpay.services(), which
    hits a lighter endpoint without per-service schemas.
    """
    base = getattr(_runpay, "_API_BASE", "https://runpay-backend-visibility-production.up.railway.app")
    params = {"limit": 250}
    if category:
        params["category"] = category
    url = f"{base}/api/marketplace?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "runpay-python/1.0.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.loads(response.read())
    return data.get("services", [])


def _field_description(field_def):
    """schema_input entries can be a plain string or a {"description": ...} dict."""
    if isinstance(field_def, dict):
        return field_def.get("description", "")
    return str(field_def) if field_def else ""


def _build_args_schema(service_id, schema):
    """
    Build a Pydantic model from a service's schema_input.
    Falls back to a single generic `payload` field when the vendor hasn't
    published a structured schema for their service.
    """
    if schema:
        fields = {
            name: (str, Field(description=_field_description(field_def)))
            for name, field_def in schema.items()
        }
    else:
        fields = {"payload": (dict, Field(description="JSON payload for this service — see getrunpay.com/docs"))}
    return create_model(f"{service_id}_Input", **fields)


def _make_tool(service, agent_id):
    """Build one LangChain StructuredTool from a run.pay catalog entry."""
    service_id = service["id"]
    schema = service.get("schema_input") or {}
    args_schema = _build_args_schema(service_id, schema)
    price = service.get("price_per_call", 0)

    def _run(**kwargs):
        payload = kwargs if schema else (kwargs.get("payload") or {})
        return _runpay.call(service_id, payload, agent_id=agent_id)

    return StructuredTool.from_function(
        func=_run,
        name=service_id,
        description=f"{service.get('description', service_id)} (${price:.3f}/call via run.pay)",
        args_schema=args_schema,
    )


def get_tools(agent_id: str = None, category: str = None):
    """
    Return a list of LangChain StructuredTools, one per run.pay service.

    Args:
        agent_id: Your run.pay agent wallet ID. Falls back to runpay.configure()
                  or the RUNPAY_AGENT_ID env var if not given.
        category: Optional filter, e.g. "Security", "Data", "Reasoning".

    Returns:
        list[StructuredTool]

    Note:
        Tool argument names/descriptions come from each service's published
        schema_input. Services that haven't published one yet fall back to
        a single generic `payload` dict argument — still fully functional,
        just less self-documenting for the LLM.
    """
    services = _fetch_marketplace(category=category)
    return [_make_tool(s, agent_id) for s in services]


__all__ = ["get_tools"]

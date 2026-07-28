"""
CrewAI integration for run.pay.

Turns any of the 205 services in the run.pay catalog into ready-to-use
CrewAI tools, generated automatically from the live service catalog —
no manual tool definitions needed.

Usage:
    from runpay.crewai import get_tools

    tools = get_tools(agent_id="agt_your_id")       # all 205 services
    tools = get_tools(agent_id="agt_your_id", category="Security")  # one category

    # Use with any CrewAI agent
    from crewai import Agent
    researcher = Agent(role="Researcher", goal="...", tools=tools, ...)

Requires: pip install runpay[crewai]
"""

try:
    from crewai.tools import BaseTool
except ImportError:
    raise ImportError(
        "CrewAI is not installed. Run `pip install crewai` "
        "(or `pip install runpay[crewai]`) to use runpay.crewai."
    )

try:
    from pydantic import create_model, Field, PrivateAttr
except ImportError:
    raise ImportError("pydantic is required for runpay.crewai. Run `pip install pydantic`.")

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
    if isinstance(field_def, dict):
        return field_def.get("description", "")
    return str(field_def) if field_def else ""


def _build_args_schema(service_id, schema):
    if schema:
        fields = {
            name: (str, Field(description=_field_description(field_def)))
            for name, field_def in schema.items()
        }
    else:
        fields = {"payload": (dict, Field(description="JSON payload for this service — see getrunpay.com/docs"))}
    return create_model(f"{service_id}_Input", **fields)


def _make_tool(service, agent_id):
    """Build one CrewAI BaseTool instance from a run.pay catalog entry."""
    service_id = service["id"]
    schema = service.get("schema_input") or {}
    args_schema = _build_args_schema(service_id, schema)
    price = service.get("price_per_call", 0)
    description = f"{service.get('description', service_id)} (${price:.3f}/call via run.pay)"

    class _RunPayTool(BaseTool):
        name: str = service_id
        description: str = description
        args_schema: type = args_schema
        _service_id: str = PrivateAttr(default=service_id)
        _agent_id: str = PrivateAttr(default=agent_id)
        _has_schema: bool = PrivateAttr(default=bool(schema))

        def _run(self, **kwargs) -> str:
            payload = kwargs if self._has_schema else (kwargs.get("payload") or {})
            result = _runpay.call(self._service_id, payload, agent_id=self._agent_id)
            return json.dumps(result)

    return _RunPayTool()


def get_tools(agent_id: str = None, category: str = None):
    """
    Return a list of CrewAI BaseTools, one per run.pay service.

    Args:
        agent_id: Your run.pay agent wallet ID. Falls back to runpay.configure()
                  or the RUNPAY_AGENT_ID env var if not given.
        category: Optional filter, e.g. "Security", "Data", "Reasoning".

    Returns:
        list[BaseTool]

    Note:
        Tool argument names/descriptions come from each service's published
        schema_input. Services that haven't published one yet fall back to
        a single generic `payload` dict argument — still fully functional,
        just less self-documenting for the LLM.
    """
    services = _fetch_marketplace(category=category)
    return [_make_tool(s, agent_id) for s in services]


__all__ = ["get_tools"]

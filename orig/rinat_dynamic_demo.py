"""Dynamic tool version of Rinat's original SGR demo."""
from __future__ import annotations

import asyncio
import json
import operator
import os
from functools import reduce
from pathlib import Path
from typing import Annotated, ClassVar, Iterable, List, Literal, Type, TypeVar

import yaml
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig
from jambo import SchemaConverter

from annotated_types import Le, MaxLen, MinLen
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, create_model
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule


# ---------------------------------------------------------------------------
# In-memory data store identical to the original demo
# ---------------------------------------------------------------------------

def new_db():
    return {
        "rules": [],
        "invoices": {},
        "emails": [],
        "products": {
            "SKU-205": {"name": "AGI 101 Course Personal", "price": 258},
            "SKU-210": {"name": "AGI 101 Course Team (5 seats)", "price": 1290},
            "SKU-220": {"name": "Building AGI - online exercises", "price": 315},
        },
    }


DB = new_db()


# ---------------------------------------------------------------------------
# Minimal dynamic tooling framework copied from mini_agent_framework
# ---------------------------------------------------------------------------

T = TypeVar("T", bound="BaseTool")


class ToolRegistry:
    """Registry that keeps track of tool classes."""

    _tools: dict[str, Type[T]] = {}

    @classmethod
    def register(cls, tool_cls: Type[T], *, name: str | None = None) -> None:
        tool_name = name or getattr(tool_cls, "tool_name", tool_cls.__name__)
        cls._tools[tool_name] = tool_cls

    @classmethod
    def all(cls) -> Iterable[Type[T]]:
        return cls._tools.values()


class ToolRegistryMixin:
    """Automatically register subclasses for dynamic discovery."""

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore[override]
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in {"BaseTool", "CRMTool"}:
            ToolRegistry.register(cls, name=getattr(cls, "tool_name", None))


class BaseTool(BaseModel, ToolRegistryMixin):
    """Base class for every tool."""

    model_config = ConfigDict(extra="forbid")

    tool_name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    is_terminal: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs) -> None:  # type: ignore[override]
        cls.tool_name = cls.tool_name or cls.__name__.lower()
        cls.description = cls.description or (cls.__doc__ or "")
        super().__init_subclass__(**kwargs)

    def __call__(self, context: dict) -> str:
        raise NotImplementedError


class CRMTool(BaseTool):
    """Base tool with helpers to operate on CRM DB."""

    tool: ClassVar[str]

    def __call__(self, context: dict) -> str:
        raise NotImplementedError

    @staticmethod
    def _db(context: dict) -> dict:
        return context.setdefault("db", DB)

    @staticmethod
    def _json(result) -> str:
        if isinstance(result, str):
            return result
        return json.dumps(result)


class NextStepDecision(BaseModel):
    """Base structure returned by the planner."""

    current_state: str = Field(..., description="Summary of the current progress")
    plan_remaining_steps_brief: Annotated[List[str], MinLen(1), MaxLen(5)] = Field(
        ..., description="Short plan with up to 5 remaining steps"
    )
    task_completed: bool = Field(..., description="Whether the task is considered done")
    function: BaseTool = Field(..., description="Next tool instance to execute")


class NextStepToolsBuilder:
    """Builder producing a discriminated union for the function field dynamically."""

    @classmethod
    def _create_tool_union(cls, tools: list[Type[T]]):
        if len(tools) == 1:
            return tools[0]
        union_type = reduce(operator.or_, tools)
        return Annotated[union_type, Field(discriminator="tool")]

    @classmethod
    def build_next_step_schema(cls, tools: list[Type[T]]) -> Type[NextStepDecision]:
        return create_model(
            "DynamicNextStepDecision",
            __base__=NextStepDecision,
            function=(cls._create_tool_union(tools), Field(...)),
        )


# ---------------------------------------------------------------------------
# MCP support helpers
# ---------------------------------------------------------------------------


MCP_CONFIG_PATH = Path(__file__).with_suffix(".mcp.yaml")
MCP_CONTEXT_LIMIT = 15_000


def _to_camel_case(name: str) -> str:
    return name.replace("_", " ").title().replace(" ", "")


def _expand_env_vars(value):
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    if isinstance(value, str):
        return os.path.expandvars(os.path.expanduser(value))
    return value


def load_mcp_config(path: Path = MCP_CONFIG_PATH) -> MCPConfig:
    if not path.exists():
        return MCPConfig()
    data = yaml.safe_load(path.read_text()) or {}
    config_dict = data.get("mcp", data)
    config_dict = _expand_env_vars(config_dict)
    try:
        return MCPConfig.model_validate(config_dict)
    except Exception:
        return MCPConfig()


class MCPBaseTool(BaseTool):
    """Base tool that proxies execution to an MCP server."""

    _config_dict: ClassVar[dict | None] = None
    _context_limit: ClassVar[int] = MCP_CONTEXT_LIMIT

    def __call__(self, _context: dict) -> str:
        if not self._config_dict:
            return "MCP is not configured"
        payload = self.model_dump()
        payload.pop("tool", None)
        return asyncio.run(self._execute(payload))

    @classmethod
    async def _execute(cls, payload: dict) -> str:
        client = Client(MCPConfig.model_validate(cls._config_dict))
        async with client:
            result = await client.call_tool(cls.tool_name, payload)
        dumped = (
            result.model_dump()
            if hasattr(result, "model_dump")
            else {"content": getattr(result, "content", str(result))}
        )
        return json.dumps(dumped, ensure_ascii=False)[: cls._context_limit]


def build_mcp_tools(config: MCPConfig) -> list[Type[BaseTool]]:
    if not config.mcpServers:
        return []

    config_dict = config.model_dump(exclude_none=True)

    async def _load() -> list[Type[BaseTool]]:
        tools: list[Type[BaseTool]] = []
        client = Client(config)
        async with client:
            definitions = await client.list_tools()
            for definition in definitions:
                if not getattr(definition, "name", None) or not getattr(definition, "inputSchema", None):
                    continue
                schema = dict(definition.inputSchema)
                schema.setdefault("title", _to_camel_case(definition.name))
                try:
                    pd_model = SchemaConverter.build(schema)
                except Exception:
                    continue
                ToolCls: Type[BaseTool] = create_model(
                    f"MCP{_to_camel_case(definition.name)}",
                    __base__=(pd_model, MCPBaseTool),
                    __doc__=definition.description or "",
                    tool=(Literal[definition.name], definition.name),
                )
                ToolCls.tool_name = definition.name
                ToolCls.description = definition.description or ""
                ToolCls._config_dict = config_dict
                tools.append(ToolCls)
        return tools

    return asyncio.run(_load())


# ---------------------------------------------------------------------------
# Tool implementations (identical behaviour to the original demo)
# ---------------------------------------------------------------------------


class SendEmail(CRMTool):
    """Sends an email to a customer with attachments."""

    tool: Literal["send_email"] = "send_email"
    subject: str
    message: str
    files: List[str]
    recipient_email: str

    def __call__(self, context: dict) -> str:
        email = {
            "to": self.recipient_email,
            "subject": self.subject,
            "message": self.message,
        }
        db = self._db(context)
        db["emails"].append(email)
        return self._json(email)


class GetCustomerData(CRMTool):
    """Loads customer data including rules, invoices, and emails."""

    tool: Literal["get_customer_data"] = "get_customer_data"
    email: str

    def __call__(self, context: dict) -> str:
        db = self._db(context)
        addr = self.email
        data = {
            "rules": [r for r in db["rules"] if r["email"] == addr],
            "invoices": [t for t in db["invoices"].items() if t[1]["email"] == addr],
            "emails": [e for e in db["emails"] if e.get("to") == addr],
        }
        return self._json(data)


class IssueInvoice(CRMTool):
    """Issues an invoice with up to 50% discount."""

    tool: Literal["issue_invoice"] = "issue_invoice"
    email: str
    skus: List[str]
    discount_percent: Annotated[int, Le(50)]

    def __call__(self, context: dict) -> str:
        db = self._db(context)
        total = 0.0
        for sku in self.skus:
            product = db["products"].get(sku)
            if not product:
                return self._json(f"Product {sku} not found")
            total += product["price"]
        discount = round(total * self.discount_percent / 100.0, 2)
        invoice_id = f"INV-{len(db['invoices']) + 1}"
        invoice = {
            "id": invoice_id,
            "email": self.email,
            "file": f"/invoices/{invoice_id}.pdf",
            "skus": self.skus,
            "discount_amount": discount,
            "discount_percent": self.discount_percent,
            "total": total,
            "void": False,
        }
        db["invoices"][invoice_id] = invoice
        return self._json(invoice)


class VoidInvoice(CRMTool):
    """Voids an existing invoice providing a reason."""

    tool: Literal["void_invoice"] = "void_invoice"
    invoice_id: str
    reason: str

    def __call__(self, context: dict) -> str:
        db = self._db(context)
        invoice = db["invoices"].get(self.invoice_id)
        if not invoice:
            return self._json(f"Invoice {self.invoice_id} not found")
        invoice["void"] = True
        invoice["void_reason"] = self.reason
        return self._json(invoice)


class CreateRule(CRMTool):
    """Stores a personalised rule for a customer."""

    tool: Literal["remember"] = "remember"
    email: str
    rule: str

    def __call__(self, context: dict) -> str:
        db = self._db(context)
        rule = {"email": self.email, "rule": self.rule}
        db["rules"].append(rule)
        return self._json(rule)


class ReportTaskCompletion(CRMTool):
    """Signals that the agent finished its task."""

    tool: Literal["report_completion"] = "report_completion"
    completed_steps_laconic: List[str]
    code: Literal["completed", "failed"]

    is_terminal = True

    def __call__(self, context: dict) -> str:
        report = {"code": self.code, "completed_steps": self.completed_steps_laconic}
        return self._json(report)


MCP_CONFIG = load_mcp_config()
build_mcp_tools(MCP_CONFIG)


TOOLKIT: list[Type[BaseTool]] = list(ToolRegistry.all())

NextStep = NextStepToolsBuilder.build_next_step_schema(list(TOOLKIT))


# ---------------------------------------------------------------------------
# Original set of scripted tasks
# ---------------------------------------------------------------------------

TASKS = [
    "Rule: address sama@openai.com as 'The SAMA', always give him 5% discount.",
    "Rule for elon@x.com: Email his invoices to finance@x.com",
    "sama@openai.com wants one of each product. Email him the invoice",
    "elon@x.com wants 2x of what sama@openai.com got. Send invoice",
    "redo last elon@x.com invoice: use 3x discount of sama@openai.com",
    "Add rule for skynet@y.com - politely reject all requests to buy SKU-220",
    "elon@x.com and skynet@y.com wrote emails asking to buy 'Building AGI - online exercises', handle that",
]


system_prompt = f"""
You are a business assistant helping Rinat Abdullin with customer interactions.

- Clearly report when tasks are done.
- Always send customers emails after issuing invoices (with invoice attached).
- Be laconic. Especially in emails
- No need to wait for payment confirmation before proceeding.
- Always check customer data before issuing invoices or making changes.

Products: {DB["products"]}
""".strip()


client = OpenAI()
console = Console()
print = console.print


def reset_db():
    DB.clear()
    DB.update(new_db())


def execute_tasks():
    reset_db()
    context = {"db": DB}

    for task in TASKS:
        print("\n\n")
        print(Panel(task, title="Launch agent with task", title_align="left"))

        log = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]

        for i in range(20):
            step = f"step_{i + 1}"
            print(f"Planning {step}... ", end="")

            completion = client.beta.chat.completions.parse(
                model="gpt-4o",
                response_format=NextStep,
                messages=log,
                max_completion_tokens=10000,
            )
            job = completion.choices[0].message.parsed

            if isinstance(job.function, ReportTaskCompletion):
                print(f"[blue]agent {job.function.code}[/blue].")
                print(Rule("Summary"))
                for s in job.function.completed_steps_laconic:
                    print(f"- {s}")
                print(Rule())
                break

            print(job.plan_remaining_steps_brief[0], f"\n  {job.function}")

            log.append(
                {
                    "role": "assistant",
                    "content": job.plan_remaining_steps_brief[0],
                    "tool_calls": [
                        {
                            "type": "function",
                            "id": step,
                            "function": {
                                "name": job.function.tool,
                                "arguments": job.function.model_dump_json(),
                            },
                        }
                    ],
                }
            )

            result = job.function(context)
            log.append({"role": "tool", "content": result, "tool_call_id": step})


if __name__ == "__main__":
    execute_tasks()

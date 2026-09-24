from __future__ import annotations

import csv
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .provisioning import CapabilityRegistry, ExecutionPlan


REQUIRED_CAPABILITIES = (
    "messaging.whatsapp.receive",
    "messaging.whatsapp.send",
    "durable_state",
)
OPTIONAL_CAPABILITIES = ("ai.interpret",)


@dataclass(frozen=True)
class FlowNode:
    id: str
    order: int
    name: str
    trigger: str
    condition: str
    action: str
    message: str
    success: str
    alternative: str
    references: tuple[str, ...]


@dataclass(frozen=True)
class Decision:
    route: str
    reason: str
    next_id: str | None = None


@dataclass(frozen=True)
class TurnResult:
    conversation_id: str
    state_id: str
    response: str
    status: str
    decision: str
    reason: str


class Interpreter(Protocol):
    def decide(self, node: FlowNode, message: str) -> Decision: ...


class WhatsAppBlueprint:
    def __init__(self, rows: list[dict[str, str]]):
        self.rows = rows
        self.by_id = {row["id"]: row for row in rows}
        self.flow = {
            row["id"]: FlowNode(
                id=row["id"],
                order=int(row["ordem"]),
                name=row["nome"],
                trigger=row["gatilho_ou_pergunta"],
                condition=row["condicao"],
                action=row["acao_ou_conhecimento"],
                message=row["mensagem_cliente"],
                success=row["proximo_sucesso"],
                alternative=row["proximo_alternativo"],
                references=tuple(filter(None, row["referencias"].split("|"))),
            )
            for row in rows
            if row["secao"] == "sequencia"
        }
        self.validate()

    @classmethod
    def load_csv(cls, path: str | Path) -> "WhatsAppBlueprint":
        with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
            return cls(list(csv.DictReader(fh)))

    def validate(self) -> None:
        if len(self.by_id) != len(self.rows):
            raise ValueError("Duplicate IDs in WhatsApp blueprint")
        all_ids = set(self.by_id)
        for node in self.flow.values():
            for target in (node.success, node.alternative):
                if target and target not in self.flow:
                    raise ValueError(f"{node.id} points to unknown flow node {target}")
            for ref in node.references:
                if ref not in all_ids:
                    raise ValueError(f"{node.id} references unknown item {ref}")

    def summary(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in self.rows:
            result[row["secao"]] = result.get(row["secao"], 0) + 1
        return result

    def plan_capabilities(self, resource_graph: dict) -> ExecutionPlan:
        return CapabilityRegistry().resolve(list(REQUIRED_CAPABILITIES), resource_graph)
class SqliteConversationStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS conversations(
                    id TEXT PRIMARY KEY,
                    state_id TEXT NOT NULL,
                    paused INTEGER NOT NULL DEFAULT 0
                )"""
            )
            con.execute(
                """CREATE TABLE IF NOT EXISTS messages(
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL
                )"""
            )
            con.commit()

    def get(self, conversation_id: str) -> tuple[str, bool] | None:
        with closing(sqlite3.connect(self.path)) as con:
            row = con.execute(
                "SELECT state_id, paused FROM conversations WHERE id=?",
                (conversation_id,),
            ).fetchone()
        return (row[0], bool(row[1])) if row else None

    def set(self, conversation_id: str, state_id: str, *, paused: bool = False) -> None:
        with closing(sqlite3.connect(self.path)) as con:
            con.execute(
                """INSERT INTO conversations(id,state_id,paused) VALUES(?,?,?)
                   ON CONFLICT(id) DO UPDATE SET state_id=excluded.state_id, paused=excluded.paused""",
                (conversation_id, state_id, int(paused)),
            )
            con.commit()

    def remember_message(self, conversation_id: str, message_id: str | None) -> bool:
        if not message_id:
            return True
        try:
            with closing(sqlite3.connect(self.path)) as con:
                con.execute(
                    "INSERT INTO messages(message_id, conversation_id) VALUES(?,?)",
                    (message_id, conversation_id),
                )
                con.commit()
            return True
        except sqlite3.IntegrityError:
            return False


class DemoInterpreter:
    """Deterministic fallback for the demonstrator; AI may replace only interpretation."""

    HUMAN_TERMS = ("humano", "pessoa", "dudu", "atendente")
    STOP_TERMS = ("parar", "cancelar", "desistir", "encerrar")
    YES_TERMS = ("sim", "confirmo", "confirmar", "pode seguir")
    CHANGE_TERMS = ("alterar", "mudar", "voltar")

    def decide(self, node: FlowNode, message: str) -> Decision:
        normalized = " ".join(message.casefold().split())
        if any(term in normalized for term in self.HUMAN_TERMS):
            return Decision("explicit", "human requested", "AT-090")
        if any(term in normalized for term in self.STOP_TERMS):
            return Decision("explicit", "stop requested", "AT-092")
        if not normalized:
            return Decision("alternative", "empty or ambiguous message")

        if node.id == "AT-009":
            if any(term in normalized for term in self.YES_TERMS):
                return Decision("success", "explicit proposal acceptance")
            if any(term in normalized for term in self.CHANGE_TERMS):
                return Decision("alternative", "proposal change requested")
            return Decision("explicit", "confirmation not explicit", "AT-091")

        if node.id in {"AT-011", "AT-012"}:
            return Decision("alternative", "demo mode blocks real payment")

        return Decision("success", "non-empty input accepted by deterministic demo")


class WhatsAppFlowRuntime:
    def __init__(
        self,
        blueprint: WhatsAppBlueprint,
        store: SqliteConversationStore,
        interpreter: Interpreter | None = None,
    ):
        self.blueprint = blueprint
        self.store = store
        self.interpreter = interpreter or DemoInterpreter()

    def start(self, conversation_id: str) -> TurnResult:
        node = self.blueprint.flow["AT-001"]
        self.store.set(conversation_id, node.id)
        return TurnResult(
            conversation_id,
            node.id,
            node.message,
            "started",
            "trigger",
            "first message",
        )
    def handle(
        self,
        conversation_id: str,
        message: str,
        *,
        message_id: str | None = None,
    ) -> TurnResult:
        if not self.store.remember_message(conversation_id, message_id):
            current = self.store.get(conversation_id)
            state_id = current[0] if current else "AT-001"
            return TurnResult(
                conversation_id,
                state_id,
                "",
                "duplicate",
                "ignore",
                "REG-010 duplicate event",
            )

        current = self.store.get(conversation_id)
        if current is None:
            return self.start(conversation_id)

        state_id, paused = current
        if paused:
            return TurnResult(
                conversation_id,
                state_id,
                "",
                "human_pending",
                "pause",
                "REG-012 human priority",
            )

        node = self.blueprint.flow[state_id]
        decision = self.interpreter.decide(node, message)

        if decision.next_id:
            next_id = decision.next_id
        elif decision.route == "success":
            next_id = node.success or state_id
        elif decision.route == "alternative":
            next_id = node.alternative or "AT-091"
        else:
            next_id = state_id

        next_node = self.blueprint.flow[next_id]
        pause = next_id == "AT-090"
        self.store.set(conversation_id, next_id, paused=pause)

        return TurnResult(
            conversation_id,
            next_id,
            next_node.message,
            "human_pending" if pause else "ok",
            decision.route,
            decision.reason,
        )


def runtime_status(blueprint: WhatsAppBlueprint, resource_graph: dict) -> dict:
    plan = blueprint.plan_capabilities(resource_graph)
    return {
        "blueprint": blueprint.summary(),
        "required_capabilities": list(REQUIRED_CAPABILITIES),
        "optional_capabilities": list(OPTIONAL_CAPABILITIES),
        "resolutions": [
            {
                "capability": item.capability,
                "action": item.action,
                "provider": item.provider,
                "reason": item.reason,
            }
            for item in plan.resolutions
        ],
        "ready_for_real_whatsapp": all(
            item.action == "reuse"
            for item in plan.resolutions
            if item.capability.startswith("messaging.whatsapp.")
        ),
    }

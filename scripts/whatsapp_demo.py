from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover
from autocompiler.environment import build_resource_graph
from autocompiler.whatsapp_automation import (
    SqliteConversationStore,
    WhatsAppBlueprint,
    WhatsAppFlowRuntime,
    runtime_status,
)

CSV = ROOT / "examples" / "whatsapp" / "atendimento_servicos_digitais.csv"
STATE = ROOT / ".autocompiler" / "whatsapp-demo.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AutoCompiler WhatsApp demonstrator.")
    parser.add_argument("--conversation", default="demo")
    parser.add_argument("--message")
    parser.add_argument("--message-id")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    blueprint = WhatsAppBlueprint.load_csv(CSV)
    graph = build_resource_graph(discover())

    if args.status:
        print(json.dumps(runtime_status(blueprint, graph), indent=2, ensure_ascii=False))
        return

    runtime = WhatsAppFlowRuntime(
        blueprint,
        SqliteConversationStore(STATE),
    )
    if args.message is None:
        result = runtime.start(args.conversation)
    else:
        result = runtime.handle(
            args.conversation,
            args.message,
            message_id=args.message_id,
        )
    print(json.dumps(result.__dict__, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

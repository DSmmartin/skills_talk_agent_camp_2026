"""
agentic_system/tui/app.py

Textual TUI for the Ghost Contributors demo.

Layout:
  ┌─────────────────────┬─────────────────────┐
  │  CHAT               │  AGENT TRACE        │
  │  (accumulated Q&A)  │  (tool-call stream) │
  ├─────────────────────┴─────────────────────┤
  │  > Input (full-width, bottom)             │
  └───────────────────────────────────────────┘

Left  — conversation history: every question + final answer appended.
Right — live trace: sub-agent calls, SQL generated, row counts, per run.
Input — full-width at the bottom; Enter submits.

Memory — ConversationMemory accumulates turn history across questions so the
         orchestrator can answer follow-up questions with full context.
         Ctrl+L clears both the display and the memory.

stdout is suppressed by importing agentic_system.observability.logger before
this module runs (enforced by agentic_system/main.py import order).
"""

import json

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, RichLog

from agentic_system.memory import ConversationMemory


class GhostContributorsApp(App):
    TITLE = "Ghost Contributors — Agentic NL2SQL"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_chat", "Clear"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    /* ── Main area: two side-by-side panes ─────────────────────────── */
    #main-area {
        height: 1fr;
    }

    #chat-pane {
        width: 1fr;
        border-right: solid $surface-darken-2;
        padding: 0 1;
    }

    #trace-pane {
        width: 1fr;
        padding: 0 1;
    }

    .pane-title {
        background: $surface;
        color: $text-muted;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    RichLog {
        height: 1fr;
        scrollbar-gutter: stable;
    }

    /* ── Input bar at the bottom ────────────────────────────────────── */
    #input-bar {
        height: 3;
        border-top: solid $surface-darken-2;
        background: $surface;
        padding: 0 1;
        layout: horizontal;
        align: left middle;
    }

    #prompt-label {
        color: $accent;
        text-style: bold;
        width: auto;
        margin-right: 1;
    }

    #question-input {
        width: 1fr;
        border: none;
        background: $surface;
    }

    #question-input:focus {
        border: none;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-area"):
            with Vertical(id="chat-pane"):
                yield Label("  Chat", classes="pane-title")
                yield RichLog(
                    id="chat-log",
                    wrap=True,
                    markup=True,
                    highlight=False,
                    min_width=1,
                )
            with Vertical(id="trace-pane"):
                yield Label("  Agent Trace", classes="pane-title")
                yield RichLog(
                    id="trace-log",
                    wrap=True,
                    markup=True,
                    highlight=False,
                    min_width=1,
                )
        with Horizontal(id="input-bar"):
            yield Label(">", id="prompt-label")
            yield Input(
                placeholder="Ask about GitHub contributors…",
                id="question-input",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._memory = ConversationMemory()
        self._run_count = 0
        self.query_one("#question-input", Input).focus()
        chat = self.query_one("#chat-log", RichLog)
        chat.write(
            "[dim]Ask a question about GitHub contributor behaviour.\n"
            "Follow-up questions remember the full conversation context.\n"
            "Example: Show me repositories where users opened PRs but never got one merged.[/dim]"
        )

    # ── Input ──────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        question = event.value.strip()
        if not question:
            return
        event.input.clear()
        self.run_worker(self._run_query(question), exclusive=True)

    def action_clear_chat(self) -> None:
        self._memory.clear()
        self._run_count = 0
        self.query_one("#chat-log", RichLog).clear()
        self.query_one("#trace-log", RichLog).clear()
        self.query_one("#chat-log", RichLog).write("[dim]Memory cleared. New session started.[/dim]")

    # ── Agent run ──────────────────────────────────────────────────────

    async def _run_query(self, question: str) -> None:
        from agents import Runner, ToolCallItem, ToolCallOutputItem

        from agentic_system.orchestrator import orchestrator

        chat = self.query_one("#chat-log", RichLog)
        trace = self.query_one("#trace-log", RichLog)

        # ── User message ──
        chat.write("")
        chat.write(f"[bold cyan]You[/bold cyan]")
        chat.write(f"  {question}")

        # ── Trace: run separator with memory status ──
        self._run_count += 1
        run_n = self._run_count
        mem_label = (
            f"  [dim][mem: {self._memory.turn_count} turn{'s' if self._memory.turn_count != 1 else ''}][/dim]"
            if not self._memory.is_empty
            else ""
        )
        if run_n > 1:
            trace.write("")
        trace.write(f"[dim]─── Run {run_n}[/dim]{mem_label}")

        # ── Thinking indicator ──
        chat.write("")
        chat.write("[dim italic]Agent thinking…[/dim italic]")

        try:
            agent_input = self._memory.build_input(question)
            result = Runner.run_streamed(orchestrator, agent_input)

            async for event in result.stream_events():
                if event.type != "run_item_stream_event":
                    continue

                item = event.item

                if isinstance(item, ToolCallItem):
                    raw = item.raw_item
                    tool_name = getattr(raw, "name", "unknown")
                    trace.write(f"[bold cyan]→[/bold cyan] [yellow]{tool_name}[/yellow]")

                    arguments = getattr(raw, "arguments", None)
                    if arguments:
                        try:
                            args = json.loads(arguments)
                            for key, val in args.items():
                                snippet = str(val)[:160].replace("\n", " ")
                                trace.write(f"   [dim]{key}:[/dim] {snippet}")
                        except (json.JSONDecodeError, TypeError):
                            pass

                elif isinstance(item, ToolCallOutputItem):
                    output = item.output
                    if isinstance(output, str):
                        try:
                            out = json.loads(output)
                        except (json.JSONDecodeError, TypeError):
                            out = output
                    else:
                        out = output

                    if isinstance(out, dict):
                        error = out.get("error")
                        sql = out.get("sql", "")
                        row_count = out.get("row_count")
                        if error:
                            trace.write(f"   [red]error:[/red] {error}")
                        if sql:
                            sql_short = sql.replace("\n", " ")[:200]
                            trace.write(f"   [green]sql:[/green] {sql_short}")
                        if row_count is not None:
                            trace.write(f"   [green]rows:[/green] {row_count}")
                    else:
                        snippet = str(out)[:180].replace("\n", " ")
                        trace.write(f"   [dim]{snippet}[/dim]")

            # ── Update memory before rendering answer ──
            self._memory.update(result)

            # ── Answer ──
            answer = result.final_output or "(no response)"
            chat.write("")
            chat.write("[bold green]Agent[/bold green]")
            for line in answer.splitlines():
                chat.write(f"  {line}")

        except Exception as exc:
            chat.write(f"[bold red]Error:[/bold red] {exc}")
            trace.write(f"[red]FAILED:[/red] {exc}")

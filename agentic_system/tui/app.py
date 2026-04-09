"""
agentic_system/tui/app.py

Textual TUI for the Ghost Contributors app.

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
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, Label, RichLog

from agentic_system.config import settings
from agentic_system.memory import ConversationMemory


class GhostContributorsApp(App):
    TITLE = "Ghost Contributors — Agentic NL2SQL"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+l", "clear_chat", "Clear"),
        ("ctrl+y", "copy_run_url", "Copy MLflow URL"),
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

    #mlflow-log {
        height: 4;
        scrollbar-gutter: stable;
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
                yield Label("  MLflow Run", classes="pane-title")
                yield RichLog(
                    id="mlflow-log",
                    wrap=True,
                    markup=True,
                    highlight=False,
                    min_width=1,
                )
        with Horizontal(id="input-bar"):
            yield Label(">", id="prompt-label")
            placeholder = (
            "Ask about org/repo-alpha, org/repo-beta, org/repo-gamma…"
            if settings.local_seed
            else "Ask about GitHub contributors…"
        )
        yield Input(
                placeholder=placeholder,
                id="question-input",
            )
        yield Footer()

    def on_mount(self) -> None:
        self._memory = ConversationMemory()
        self._run_count = 0
        self._mlflow_tracking_uri = settings.mlflow_tracking_uri.rstrip("/")
        self._mlflow_experiment_name = settings.mlflow_experiment_name
        self._mlflow_experiment_id: Optional[str] = None
        self._last_run_url: Optional[str] = None
        self.query_one("#question-input", Input).focus()
        chat = self.query_one("#chat-log", RichLog)
        if settings.local_seed:
            chat.write(
                "[dim]Running with local seed dataset (18 rows, 3 repos).\n"
                "Follow-up questions remember the full conversation context.\n"
                "Example: Show me ghost contributors on org/repo-alpha, org/repo-beta, and org/repo-gamma.[/dim]"
            )
        else:
            chat.write(
                "[dim]Ask a question about GitHub contributor behaviour.\n"
                "Follow-up questions remember the full conversation context.\n"
                "Example: Show me repositories where users opened PRs but never got one merged.[/dim]"
            )
        self._prime_mlflow_panel()

    def _prime_mlflow_panel(self) -> None:
        mlflow_log = self.query_one("#mlflow-log", RichLog)
        mlflow_log.clear()
        mlflow_log.write(f"[dim]Tracking URI:[/dim] {self._mlflow_tracking_uri}")
        try:
            from mlflow import MlflowClient

            client = MlflowClient(tracking_uri=self._mlflow_tracking_uri)
            experiment = client.get_experiment_by_name(self._mlflow_experiment_name)
            if experiment:
                self._mlflow_experiment_id = experiment.experiment_id
                mlflow_log.write(
                    f"[dim]Experiment:[/dim] {experiment.name} ({experiment.experiment_id})"
                )
        except Exception as exc:
            mlflow_log.write(f"[red]MLflow lookup failed:[/red] {exc}")
        mlflow_log.write("[dim]Press Ctrl+Y to copy the latest run URL.[/dim]")
        mlflow_log.write("[dim]Note: clipboard copy may not work in macOS Terminal.[/dim]")

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
        self._last_run_url = None
        self._prime_mlflow_panel()
        self.query_one("#chat-log", RichLog).write("[dim]Memory cleared. New session started.[/dim]")

    def action_copy_run_url(self) -> None:
        mlflow_log = self.query_one("#mlflow-log", RichLog)
        if not self._last_run_url:
            mlflow_log.write("[yellow]No MLflow run URL available yet.[/yellow]")
            return
        self.copy_to_clipboard(self._last_run_url)
        mlflow_log.write("[green]Copied MLflow run URL to clipboard.[/green]")

    # ── Agent run ──────────────────────────────────────────────────────

    async def _run_query(self, question: str) -> None:
        from agents import Runner, ToolCallItem, ToolCallOutputItem

        from agentic_system.orchestrator import orchestrator

        chat = self.query_one("#chat-log", RichLog)
        trace = self.query_one("#trace-log", RichLog)
        mlflow_log = self.query_one("#mlflow-log", RichLog)

        # ── User message ──
        chat.write("")
        chat.write(f"[bold cyan]You[/bold cyan]")
        chat.write(f"  {question}")

        # ── Trace: run separator with memory status ──
        self._run_count += 1
        run_n = self._run_count
        from loguru import logger

        logger.info("TUI query start run={}", run_n)
        logger.debug("TUI question: {}", question)
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

        mlflow_run = None
        try:
            try:
                import mlflow

                mlflow_run = mlflow.start_run(
                    run_name=f"tui-query-{run_n}",
                    tags={
                        "ui": "tui",
                        "query": question[:200],
                        "run_index": str(run_n),
                    },
                )
                self._mlflow_experiment_id = mlflow_run.info.experiment_id
                run_url = self._format_mlflow_run_url(
                    mlflow_run.info.experiment_id,
                    mlflow_run.info.run_id,
                )
                mlflow_log.clear()
                mlflow_log.write(f"[bold]Run {mlflow_run.info.run_id}[/bold]")
                if run_url:
                    mlflow_log.write(run_url)
                    self._last_run_url = run_url
                else:
                    self._last_run_url = None
                mlflow_log.write("[dim]Press Ctrl+Y to copy the latest run URL.[/dim]")
                mlflow_log.write("[dim]Note: clipboard copy may not work in macOS Terminal.[/dim]")
            except Exception as exc:
                mlflow_log.clear()
                mlflow_log.write(f"[red]MLflow start failed:[/red] {exc}")
                self._last_run_url = None

            agent_input = self._memory.build_input(question)
            logger.debug("Agent input type={}", type(agent_input).__name__)
            if isinstance(agent_input, list):
                logger.debug("Agent input items={}", len(agent_input))
            result = Runner.run_streamed(orchestrator, agent_input)

            async for event in result.stream_events():
                if event.type != "run_item_stream_event":
                    continue

                item = event.item

                if isinstance(item, ToolCallItem):
                    raw = item.raw_item
                    tool_name = getattr(raw, "name", "unknown")
                    trace.write(f"[bold cyan]→[/bold cyan] [yellow]{tool_name}[/yellow]")
                    logger.debug("Tool call start: {}", tool_name)

                    arguments = getattr(raw, "arguments", None)
                    if arguments:
                        try:
                            args = json.loads(arguments)
                            for key, val in args.items():
                                snippet = str(val)[:160].replace("\n", " ")
                                trace.write(f"   [dim]{key}:[/dim] {snippet}")
                            logger.debug("Tool call args: {}", args)
                        except (json.JSONDecodeError, TypeError):
                            logger.debug("Tool call args (raw): {}", arguments)
                            pass

                elif isinstance(item, ToolCallOutputItem):
                    output = item.output
                    tool_name = getattr(item, "tool_name", None)
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
                        logger.debug(
                            "Tool output tool={} keys={} error={}",
                            tool_name or "unknown",
                            list(out.keys()),
                            error,
                        )
                    else:
                        snippet = str(out)[:180].replace("\n", " ")
                        trace.write(f"   [dim]{snippet}[/dim]")
                        logger.debug(
                            "Tool output tool={} snippet={}",
                            tool_name or "unknown",
                            snippet,
                        )

            # ── Update memory before rendering answer ──
            self._memory.update(result)
            logger.info("TUI query completed run={}", run_n)
            logger.debug("TUI memory turns={}", self._memory.turn_count)

            # ── Answer ──
            answer = result.final_output or "(no response)"
            chat.write("")
            chat.write("[bold green]Agent[/bold green]")
            for line in answer.splitlines():
                chat.write(f"  {line}")

        except Exception as exc:
            chat.write(f"[bold red]Error:[/bold red] {exc}")
            trace.write(f"[red]FAILED:[/red] {exc}")
            logger.exception("TUI query failed run={}", run_n)
        finally:
            if mlflow_run is not None:
                try:
                    import mlflow

                    mlflow.end_run()
                except Exception as exc:
                    trace.write(f"[red]MLflow end failed:[/red] {exc}")

    def _format_mlflow_run_url(self, experiment_id: Optional[str], run_id: str) -> Optional[str]:
        if not experiment_id:
            return None
        return f"{self._mlflow_tracking_uri}/#/experiments/{experiment_id}/runs/{run_id}"

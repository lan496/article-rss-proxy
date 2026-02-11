from __future__ import annotations

from dataclasses import dataclass
import logging
import threading


FREE_TIER_RPD: dict[str, int] = {
    "gemini-2.5-pro": 100,
    "gemini-2.5-flash": 250,
}


@dataclass(frozen=True)
class ModelUsage:
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0

    def add(self, prompt_tokens: int, candidates_tokens: int, total_tokens: int) -> ModelUsage:
        return ModelUsage(
            prompt_tokens=self.prompt_tokens + prompt_tokens,
            candidates_tokens=self.candidates_tokens + candidates_tokens,
            total_tokens=self.total_tokens + total_tokens,
            call_count=self.call_count + 1,
        )


class UsageTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._usage: dict[str, ModelUsage] = {}

    def record(
        self,
        model: str,
        prompt_tokens: int,
        candidates_tokens: int,
        total_tokens: int,
    ) -> None:
        with self._lock:
            prev = self._usage.get(model, ModelUsage())
            self._usage[model] = prev.add(prompt_tokens, candidates_tokens, total_tokens)

    def log_summary(self) -> None:
        if not self._usage:
            logging.info("No Gemini API calls recorded.")
            return

        lines = [
            "",
            "=" * 60,
            "Gemini API Usage Summary",
            "=" * 60,
        ]
        for model in sorted(self._usage):
            u = self._usage[model]
            rpd = FREE_TIER_RPD.get(model, "?")
            lines.append(f"  Model: {model}")
            lines.append(f"    Calls:              {u.call_count:,} / {rpd} RPD")
            lines.append(f"    Prompt tokens:      {u.prompt_tokens:,}")
            lines.append(f"    Completion tokens:  {u.candidates_tokens:,}")
            lines.append(f"    Total tokens:       {u.total_tokens:,}")
            lines.append("")
        lines.append("=" * 60)

        logging.info("\n".join(lines))


tracker = UsageTracker()

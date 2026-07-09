"""
infra/memory.py — Shiva Sniper v10
Persistent memory file (JSON-based) to track active bot state.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")

class Memory:
    @staticmethod
    def load() -> dict:
        """Load state dictionary from memory.json. Returns empty state if file doesn't exist or is invalid."""
        if not os.path.exists(MEMORY_FILE):
            logger.info("No memory.json file found. Starting with clean state.")
            return {}
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"Successfully loaded state from memory.json: {data}")
                return data
        except Exception as e:
            logger.error(f"Failed to read memory.json: {e}", exc_info=True)
            return {}

    @staticmethod
    def save(in_position: bool, signal_type: str, qty_lots: int, entry_bar_boundary_ms: int,
             risk: dict = None, trail_state: dict = None) -> None:
        """Write current bot state parameters to memory.json."""
        state = {
            "in_position": in_position,
            "signal_type": signal_type,
            "qty_lots": qty_lots,
            "entry_bar_boundary_ms": entry_bar_boundary_ms,
            "risk": risk,
            "trail_state": trail_state
        }
        try:
            # Write to a temporary file first, then rename it to ensure atomicity
            temp_file = MEMORY_FILE + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
            if os.path.exists(MEMORY_FILE):
                os.remove(MEMORY_FILE)
            os.rename(temp_file, MEMORY_FILE)
            logger.info(f"Successfully saved state to memory.json")
        except Exception as e:
            logger.error(f"Failed to write to memory.json: {e}", exc_info=True)

    @staticmethod
    def clear() -> None:
        """Reset memory.json to an empty state."""
        Memory.save(
            in_position=False,
            signal_type="None",
            qty_lots=0,
            entry_bar_boundary_ms=0,
            risk=None,
            trail_state=None
        )

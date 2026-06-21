"""Result display widget with formatting.

Shows calculation results with expression echo, supports exact and
approximate display modes, and provides a copy-to-clipboard button.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class ResultWidget(ttk.Frame):
    """Display area for calculation results.

    Shows the expression and its result, with copy-to-clipboard support.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the result display UI."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Text widget for results (read-only)
        self._text = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 11),
            height=6,
            state=tk.DISABLED,
            bg="#f8f8f8",
            relief=tk.FLAT,
            padx=8,
            pady=4,
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._text.config(yscrollcommand=scrollbar.set)

        # Button frame
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

        self._copy_btn = ttk.Button(
            btn_frame, text="Copy Result", command=self._copy_result
        )
        self._copy_btn.pack(side=tk.RIGHT)

        self._clear_btn = ttk.Button(
            btn_frame, text="Clear", command=self.clear
        )
        self._clear_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # Configure text tags for styling
        self._text.tag_configure("expression", foreground="#2060a0", font=("Consolas", 11, "bold"))
        self._text.tag_configure("result", foreground="#006600", font=("Consolas", 12))
        self._text.tag_configure("error", foreground="#cc0000", font=("Consolas", 11))
        self._text.tag_configure("separator", foreground="#cccccc")

        # Track last result for copy
        self._last_result: str = ""

    def show_result(self, expression: str, result: str) -> None:
        """Display an expression and its result.

        Args:
            expression: The input expression.
            result: The formatted result string.
        """
        self._text.config(state=tk.NORMAL)

        # Add separator if there's existing content
        content = self._text.get("1.0", tk.END).strip()
        if content:
            self._text.insert(tk.END, "\n" + "\u2500" * 50 + "\n", "separator")

        # Expression line
        self._text.insert(tk.END, expression, "expression")
        self._text.insert(tk.END, " =\n")

        # Result line
        self._text.insert(tk.END, result, "result")
        self._text.insert(tk.END, "\n")

        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

        self._last_result = result

    def show_error(self, expression: str, error: str) -> None:
        """Display an expression and its error.

        Args:
            expression: The input expression.
            error: The error message.
        """
        self._text.config(state=tk.NORMAL)

        content = self._text.get("1.0", tk.END).strip()
        if content:
            self._text.insert(tk.END, "\n" + "\u2500" * 50 + "\n", "separator")

        self._text.insert(tk.END, expression, "expression")
        self._text.insert(tk.END, "\n")
        self._text.insert(tk.END, f"Error: {error}", "error")
        self._text.insert(tk.END, "\n")

        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

        self._last_result = ""

    def show_info(self, message: str) -> None:
        """Display an informational message."""
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, message + "\n")
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def clear(self) -> None:
        """Clear all displayed results."""
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.config(state=tk.DISABLED)
        self._last_result = ""

    def _copy_result(self) -> None:
        """Copy the last result to clipboard."""
        if self._last_result:
            self.clipboard_clear()
            self.clipboard_append(self._last_result)

    def get_last_result(self) -> str:
        """Return the last result string."""
        return self._last_result

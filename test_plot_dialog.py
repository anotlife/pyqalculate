"""Automated smoke test for the plot dialog.

Tests:
1. MainWindow launches with PlotDialog
2. PlotDialog opens with an expression
3. Plot renders x^2 from -5 to 5
4. Save-as-PNG succeeds
5. Dialog closes cleanly
"""

from __future__ import annotations

import os
import sys
import tempfile

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk


def main() -> None:
    from pyqalculate_gui.main_window import MainWindow
    from pyqalculate_gui.plot_dialog import PlotDialog

    app = MainWindow()
    root = app.root

    results: dict[str, bool] = {}

    # --- Step 1: MainWindow launched ---
    results["mainwindow_launched"] = True
    print("[PASS] MainWindow launched")

    # --- Step 2: Open plot dialog after 500ms ---
    def open_dialog() -> None:
        try:
            dialog = PlotDialog(root)
            dialog.show(expression="x^2")
            results["dialog_opened"] = True
            print("[PASS] PlotDialog opened with 'x^2'")

            # --- Step 3: Render plot after 500ms ---
            root.after(500, lambda: render_plot(dialog))
        except Exception as exc:
            results["dialog_opened"] = False
            print(f"[FAIL] PlotDialog open: {exc}")
            root.quit()

    def render_plot(dialog: PlotDialog) -> None:
        try:
            # Set range to -5..5
            dialog._x_min_var.set("-5")
            dialog._x_max_var.set("5")
            dialog._render_plot()

            has_fig = dialog._fig is not None
            has_canvas = dialog._canvas is not None
            results["plot_rendered"] = has_fig and has_canvas
            if results["plot_rendered"]:
                print("[PASS] Plot rendered (fig + canvas OK)")
            else:
                print("[FAIL] Plot render: fig or canvas is None")

            # --- Step 4: Save as PNG ---
            root.after(300, lambda: save_png(dialog))
        except Exception as exc:
            results["plot_rendered"] = False
            print(f"[FAIL] Plot render: {exc}")
            root.quit()

    def save_png(dialog: PlotDialog) -> None:
        try:
            tmp = os.path.join(tempfile.gettempdir(), "pyqalc_plot_test.png")
            if dialog._fig is not None:
                dialog._fig.savefig(tmp, dpi=150, bbox_inches="tight")
                exists = os.path.isfile(tmp)
                size = os.path.getsize(tmp) if exists else 0
                results["save_png"] = exists and size > 0
                if results["save_png"]:
                    print(f"[PASS] PNG saved ({size} bytes): {tmp}")
                else:
                    print(f"[FAIL] PNG not created or empty: {tmp}")
                # Cleanup
                if exists:
                    os.remove(tmp)
            else:
                results["save_png"] = False
                print("[FAIL] No figure to save")
        except Exception as exc:
            results["save_png"] = False
            print(f"[FAIL] PNG save: {exc}")

        # --- Step 5: Close dialog and quit ---
        try:
            dialog._on_close()
            results["dialog_closed"] = True
            print("[PASS] Dialog closed cleanly")
        except Exception as exc:
            results["dialog_closed"] = False
            print(f"[FAIL] Dialog close: {exc}")

        # Summary
        print("\n=== Test Summary ===")
        all_pass = all(results.values())
        for k, v in results.items():
            print(f"  {k}: {'PASS' if v else 'FAIL'}")
        print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

        root.after(100, root.quit)

    # Schedule the dialog open
    root.after(500, open_dialog)
    root.mainloop()

    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()

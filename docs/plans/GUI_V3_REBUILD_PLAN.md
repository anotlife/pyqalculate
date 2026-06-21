# PyQalculate GUI v3 Rebuild — Work Plan

## Context

### User Request Summary
Rebuild the PyQalculate GUI from scratch on the `feature/gui-v3-rewrite` branch. The current GUI has architectural issues: a god object (MainWindow), dead code, orphaned widgets, private attribute cross-access, no state management, hardcoded colors, and no dialog base class. The rebuild must match the quality of the original qalculate-gtk using tkinter, with clean architecture.

### Current Codebase Analysis (Verified)

| File | LOC | Status | Issues |
|------|-----|--------|--------|
| `main_window.py` | 501 | **Rewrite** | God object, private attr access (lines 273, 278, 396, 406), hardcoded colors |
| `expression_edit.py` | 229 | **Rewrite** | Callback-based, no undo/redo public API |
| `result_view.py` | 183 | **Rewrite** | 7 hardcoded colors, no theme support |
| `history_view.py` | 336 | **Rewrite** | 5 hardcoded colors, callback-based |
| `keypad.py` | 282 | **Rewrite** | 14 hardcoded colors, callback-based |
| `conversion_view.py` | 610 | **Rewrite** | 4 hardcoded colors, private attr access to calculator |
| `preferences_dialog.py` | 502 | **Rewrite** | Stores `_current_eo`/`_current_po` as private attrs accessed by MainWindow |
| `plot_dialog.py` | 568 | **Rewrite** | 12 hardcoded colors, no base class |
| `import_csv_dialog.py` | 221 | **Rewrite** | No base class, duplicated modal pattern |
| `export_csv_dialog.py` | 236 | **Rewrite** | No base class, duplicated modal pattern |
| `input_widget.py` | 136 | **Delete** | Dead code — zero imports |
| `result_widget.py` | 143 | **Delete** | Dead code — zero imports |
| `sidebar_widget.py` | 307 | **Delete** | Dead code — zero imports |
| `plot_widget.py` | 204 | **Delete** | Dead code — zero imports |

**Total hardcoded colors**: 48 instances across 10 files.
**Private attribute cross-access**: 4 instances in `main_window.py`.

### Design Reference
- `docs/analysis/DESIGN_GUIDE.md` — 294 lines, 8-phase rebuild checklist, widget architecture, threading model, mode_struct
- `docs/analysis/` — 11 analysis files documenting original qalculate-gtk (expression_edit, result_view, history_view, keypad, conversion_view, mainwindow, menu_dialog_system)
- Existing V2.2 plan (`docs/plans/DEVELOPMENT_PLAN_V2.2.md`) — High-level, Chinese, lacks parallel execution strategy

---

## Task Dependency Graph

```
Task  | Depends On          | Reason
------|---------------------|------------------------------------------
T1    | None                | Dead code deletion, independent
T2    | None                | AppState is foundational, no deps
T3    | None                | Theme is foundational, no deps
T4    | None                | CalculatorService is foundational, no deps
T5    | T2, T3              | EventBus needs AppState + Theme patterns
T6    | T3                  | ModalDialog uses Theme for styling
T7    | T2, T3, T5          | ExpressionEdit uses state, theme, events
T8    | T2, T3, T5          | ResultView uses state, theme, events
T9    | T2, T3, T5          | HistoryView uses state, theme, events
T10   | T2, T3, T5          | Keypad uses state, theme, events
T11   | T2, T3, T4, T5      | ConversionView uses all core infra
T12   | T2, T3, T5          | StatusBar uses state, theme, events
T13   | T2, T3, T5          | MenuBar uses state, theme, events
T14   | T3, T6              | PreferencesDialog uses theme + base
T15   | T3, T6              | PlotDialog uses theme + base
T16   | T3, T6              | ImportCsvDialog uses theme + base
T17   | T3, T6              | ExportCsvDialog uses theme + base
T18   | T1..T17             | App integrates everything
T19   | T18                 | Integration tests verify the full app
```

## Parallel Execution Graph

```
Wave 1 (Start Immediately — No Dependencies):
├── T1:  Delete dead code (4 files)
├── T2:  Create state.py (AppState dataclass)
├── T3:  Create theme.py (Theme class)
└── T4:  Create calculator_service.py (Engine wrapper)

Wave 2 (After Wave 1):
├── T5:  Create event_bus.py (depends: T2, T3)
└── T6:  Create dialogs/base.py (depends: T3)

Wave 3 (After Wave 2 — Maximum Parallelism):
├── T7:  Rewrite expression_edit.py (depends: T2, T3, T5)
├── T8:  Rewrite result_view.py (depends: T2, T3, T5)
├── T9:  Rewrite history_view.py (depends: T2, T3, T5)
├── T10: Rewrite keypad.py (depends: T2, T3, T5)
├── T11: Rewrite conversion_view.py (depends: T2, T3, T4, T5)
├── T12: Create status_bar.py (depends: T2, T3, T5)
├── T13: Create menu_bar.py (depends: T2, T3, T5)
├── T14: Rewrite preferences_dialog.py (depends: T3, T6)
├── T15: Rewrite plot_dialog.py (depends: T3, T6)
├── T16: Rewrite import_csv_dialog.py (depends: T3, T6)
└── T17: Rewrite export_csv_dialog.py (depends: T3, T6)

Wave 4 (After Wave 3):
└── T18: Create app.py + update entry points (depends: ALL)

Wave 5 (After Wave 4):
└── T19: Integration testing + cleanup (depends: T18)

Critical Path: T3 → T6 → T14 → T18
Parallel Speedup: ~60% faster than sequential (11 tasks in Wave 3)
```

---

## Tasks

### Task 1: Delete Dead Code

**Description**: Remove 4 files that are never imported: `input_widget.py`, `result_widget.py`, `sidebar_widget.py`, `plot_widget.py`. Update `__init__.py` if it references them.

**Delegation Recommendation**:
- Category: `quick` — Trivial file deletion, no logic
- Skills: [] — No specialized skills needed

**Depends On**: None
**Acceptance Criteria**:
- [ ] 4 files deleted
- [ ] No imports reference deleted files (verified by grep)
- [ ] `__init__.py` updated if needed
- [ ] Existing tests still pass: `python -m pytest tests/test_gui.py -v`

**Commit**: `chore: delete dead code (input_widget, result_widget, sidebar_widget, plot_widget)`

---

### Task 2: Create `state.py` — AppState Dataclass

**Description**: Create a centralized state management module. AppState holds all mutable application state in a single dataclass with observer notification. Replaces scattered state in MainWindow, PreferencesDialog, and widgets.

**Delegation Recommendation**:
- Category: `quick` — Single file, clear spec, ~80-120 LOC
- Skills: [`programming`] — Python type hints, dataclasses

**Depends On**: None
**Acceptance Criteria**:
- [ ] `AppState` dataclass with fields: `expression`, `result`, `exact_mode`, `history_entries`, `show_keypad`, `show_history`, `show_conversion`, `preferences` (dict), `status_text`
- [ ] `StateObserver` protocol with `on_state_changed(field: str, value: Any)` method
- [ ] `add_observer()` / `remove_observer()` / `notify()` methods
- [ ] Type hints on all fields and methods
- [ ] Unit test: `tests/test_state.py` — verify observer notification, field updates
- [ ] File ≤ 150 LOC

**Commit**: `feat(gui): add AppState dataclass with observer pattern`

---

### Task 3: Create `theme.py` — Theme Class

**Description**: Create a centralized theme module with all design tokens (colors, fonts, spacing). Replaces 48 hardcoded color values across 10 files.

**Delegation Recommendation**:
- Category: `quick` — Single file, data-only class, ~100-150 LOC
- Skills: [`programming`] — Python dataclasses, color constants

**Depends On**: None
**Acceptance Criteria**:
- [ ] `Theme` class with color tokens: `expression_fg`, `result_fg`, `result_approx_fg`, `error_fg`, `separator_fg`, `info_fg`, `bg`, `fg`, `entry_bg`, `select_bg`
- [ ] Font tokens: `expression_font`, `result_font`, `info_font`, `keypad_fonts` (dict by button type)
- [ ] Keypad button styles: `digit`, `op`, `func`, `const`, `var`, `action`, `equals` — each with `(bg, fg, hover_bg, font)`
- [ ] `LIGHT` and `DARK` theme presets
- [ ] `get_theme(name: str) -> Theme` factory function
- [ ] Unit test: `tests/test_theme.py` — verify both themes have all required fields
- [ ] File ≤ 150 LOC

**Commit**: `feat(gui): add centralized Theme class with design tokens`

---

### Task 4: Create `calculator_service.py` — Engine Wrapper

**Description**: Create a service layer wrapping the `pyqalculate.Calculator` engine. Provides clean public API for calculation, unit conversion, and CSV operations. Replaces direct calculator access in MainWindow and dialogs.

**Delegation Recommendation**:
- Category: `quick` — Single file, thin wrapper, ~80-120 LOC
- Skills: [`programming`] — Python type hints, error handling

**Depends On**: None
**Acceptance Criteria**:
- [ ] `CalculatorService` class wrapping `pyqalculate.calculator.Calculator`
- [ ] Methods: `calculate(expression, eo, po) -> CalculationResult`, `convert(value, from_unit, to_unit) -> str`, `get_units() -> list`, `get_functions() -> list`, `get_variables() -> list`
- [ ] `CalculationResult` dataclass: `expression: str`, `result: str`, `exact: bool`, `error: str | None`
- [ ] All `EvaluationOptions` and `PrintOptions` handling internal to service
- [ ] Unit test: `tests/test_calculator_service.py` — verify basic calculation, unit conversion, error handling
- [ ] File ≤ 150 LOC

**Commit**: `feat(gui): add CalculatorService engine wrapper`

---

### Task 5: Create `event_bus.py` — Event System

**Description**: Create a publish-subscribe event bus for decoupled widget communication. Replaces direct callback passing and private attribute cross-access.

**Delegation Recommendation**:
- Category: `quick` — Single file, simple pattern, ~60-80 LOC
- Skills: [`programming`] — Python type hints, observer pattern

**Depends On**: T2, T3 (patterns established)
**Acceptance Criteria**:
- [ ] `EventBus` class with `subscribe(event: str, callback: Callable)`, `unsubscribe(event: str, callback: Callable)`, `emit(event: str, *args)`
- [ ] Event constants: `EXPRESSION_SUBMITTED`, `RESULT_DISPLAYED`, `HISTORY_RECALLED`, `MODE_CHANGED`, `PREFERENCE_APPLIED`, `CONVERSION_RESULT`
- [ ] Type hints on all methods
- [ ] Unit test: `tests/test_event_bus.py` — verify subscribe/emit/unsubscribe
- [ ] File ≤ 100 LOC

**Commit**: `feat(gui): add EventBus for decoupled widget communication`

---

### Task 6: Create `dialogs/base.py` — ModalDialog Base Class

**Description**: Create a base class for all modal dialogs. Standardizes transient/grab, OK/Cancel/Apply button pattern, and result return. Replaces 4 independent dialog implementations.

**Delegation Recommendation**:
- Category: `quick` — Single file, base class, ~80-120 LOC
- Skills: [`programming`] — Python ABCs, tkinter patterns

**Depends On**: T3 (Theme for styling)
**Acceptance Criteria**:
- [ ] `ModalDialog` abstract base class
- [ ] Constructor: `__init__(self, parent, title, size, resizable)`
- [ ] Abstract method: `_build_content(self, parent: ttk.Frame)` — subclasses fill this
- [ ] Standard methods: `show() -> None`, `_on_ok()`, `_on_cancel()`, `_on_apply()`, `_close()`
- [ ] Handles: transient, grab_set, protocol WM_DELETE_WINDOW
- [ ] OK/Cancel/Apply button row built automatically
- [ ] Unit test: `tests/test_dialog_base.py` — verify modal behavior (may need display)
- [ ] File ≤ 150 LOC

**Commit**: `feat(gui): add ModalDialog base class for all dialogs`

---

### Task 7: Rewrite `expression_edit.py`

**Description**: Rewrite the expression input widget. Uses AppState for history, Theme for colors, EventBus for submission. Exposes clean public API (no private attribute access needed).

**Delegation Recommendation**:
- Category: `unspecified-low` — Widget rewrite, ~200-250 LOC
- Skills: [`programming`] — Python, tkinter, type hints

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for all colors and fonts (zero hardcoded values)
- [ ] Public API: `get_expression()`, `set_expression()`, `insert_at_cursor()`, `clear()`, `focus_input()`
- [ ] No `_do_submit()` private method exposed — uses EventBus `EXPRESSION_SUBMITTED`
- [ ] History navigation via AppState (not local list)
- [ ] Undo/redo via deque (kept local — UI concern)
- [ ] Unit test: `tests/test_expression_edit.py` — verify get/set/clear (may need display skip)
- [ ] File ≤ 250 LOC

**Commit**: `feat(gui): rewrite ExpressionEdit with state/theme/events`

---

### Task 8: Rewrite `result_view.py`

**Description**: Rewrite the result display widget. Uses Theme for all colors, EventBus for receiving results, AppState for last result.

**Delegation Recommendation**:
- Category: `unspecified-low` — Widget rewrite, ~150-200 LOC
- Skills: [`programming`] — Python, tkinter, type hints

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for all text tag colors (zero hardcoded values)
- [ ] Public API: `show_result()`, `show_error()`, `show_info()`, `clear()`, `get_last_result()`
- [ ] Subscribes to `EXPRESSION_SUBMITTED` via EventBus
- [ ] Emits `RESULT_DISPLAYED` after showing result
- [ ] Unit test: `tests/test_result_view.py` — verify show_result/clear
- [ ] File ≤ 200 LOC

**Commit**: `feat(gui): rewrite ResultView with state/theme/events`

---

### Task 9: Rewrite `history_view.py`

**Description**: Rewrite the history panel. Uses AppState for entries, Theme for colors, EventBus for recall events.

**Delegation Recommendation**:
- Category: `unspecified-low` — Widget rewrite, ~250-300 LOC
- Skills: [`programming`] — Python, tkinter, type hints

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for listbox item colors (zero hardcoded values)
- [ ] Public API: `add_expression()`, `add_result()`, `add_error()`, `get_answer()`, `clear()`
- [ ] Emits `HISTORY_RECALLED` via EventBus (not direct callback)
- [ ] answer(N) support preserved
- [ ] Unit test: `tests/test_history_view.py` — verify add/get_answer/clear
- [ ] File ≤ 300 LOC

**Commit**: `feat(gui): rewrite HistoryView with state/theme/events`

---

### Task 10: Rewrite `keypad.py`

**Description**: Rewrite the virtual keypad. Uses Theme for button styles, EventBus for insert/clear/submit events.

**Delegation Recommendation**:
- Category: `unspecified-low` — Widget rewrite, ~200-250 LOC
- Skills: [`programming`] — Python, tkinter, type hints

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme.keypad_styles` for all button colors (zero hardcoded values)
- [ ] Public API: `set_theme()` for live theme switching
- [ ] Emits events via EventBus (not direct callbacks)
- [ ] Tooltip uses Theme colors
- [ ] Unit test: `tests/test_keypad.py` — verify button creation
- [ ] File ≤ 250 LOC

**Commit**: `feat(gui): rewrite Keypad with state/theme/events`

---

### Task 11: Rewrite `conversion_view.py`

**Description**: Rewrite the unit conversion panel. Uses Theme, EventBus, CalculatorService.

**Delegation Recommendation**:
- Category: `unspecified-low` — Widget rewrite, ~400-500 LOC
- Skills: [`programming`] — Python, tkinter, type hints

**Depends On**: T2, T3, T4, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for all colors (zero hardcoded values)
- [ ] Uses `CalculatorService` instead of direct `Calculator` access
- [ ] Emits `CONVERSION_RESULT` via EventBus
- [ ] Public API: `set_value()`, `set_from_unit()`, `set_target_unit()`, `convert()`
- [ ] No private attribute access to calculator internals (no `self._calc._units`)
- [ ] Unit test: `tests/test_conversion_view.py` — verify category population
- [ ] File ≤ 500 LOC

**Commit**: `feat(gui): rewrite ConversionView with state/theme/events`

---

### Task 12: Create `status_bar.py`

**Description**: New widget. Displays calculator statistics (function/unit/variable counts) and current mode (Exact/Approximate).

**Delegation Recommendation**:
- Category: `quick` — New simple widget, ~60-80 LOC
- Skills: [`programming`] — Python, tkinter

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for colors (zero hardcoded values)
- [ ] Subscribes to `MODE_CHANGED` via EventBus
- [ ] Public API: `update_stats(n_funcs, n_units, n_vars)`, `set_mode(exact: bool)`
- [ ] Two labels: stats (left), mode indicator (right)
- [ ] File ≤ 100 LOC

**Commit**: `feat(gui): add StatusBar widget`

---

### Task 13: Create `menu_bar.py`

**Description**: Extract menu bar from MainWindow into standalone widget. Uses EventBus for actions.

**Delegation Recommendation**:
- Category: `unspecified-low` — New widget, ~120-160 LOC
- Skills: [`programming`] — Python, tkinter

**Depends On**: T2, T3, T5
**Acceptance Criteria**:
- [ ] Uses `Theme` for any menu colors
- [ ] Emits events via EventBus: `CLEAR_ALL`, `OPEN_PREFERENCES`, `OPEN_PLOT`, `TOGGLE_HISTORY`, `TOGGLE_KEYPAD`, `TOGGLE_CONVERSION`, `COPY_RESULT`
- [ ] Menu structure: File (Clear, Import CSV, Export CSV, Exit), Edit (Copy, Clear Expr), Mode (Exact toggle, Preferences), View (History, Keypad, Conversion, Plot), Help (About)
- [ ] Keyboard shortcuts bound: Ctrl+C, Ctrl+P, Ctrl+Shift+P, Escape
- [ ] Public API: `set_exact_mode_var(var: tk.BooleanVar)`
- [ ] File ≤ 160 LOC

**Commit**: `feat(gui): add MenuBar widget with EventBus integration`

---

### Task 14: Rewrite `preferences_dialog.py`

**Description**: Rewrite preferences dialog using ModalDialog base class. Settings persistence to JSON. No private attribute exposure.

**Delegation Recommendation**:
- Category: `unspecified-low` — Dialog rewrite, ~350-400 LOC
- Skills: [`programming`] — Python, tkinter, JSON

**Depends On**: T3, T6
**Acceptance Criteria**:
- [ ] Extends `ModalDialog` base class
- [ ] Uses `Theme` for all colors (zero hardcoded values)
- [ ] Public API: `get_settings() -> dict`, `apply_settings()` (no `_current_eo`/`_current_po` private attrs)
- [ ] Settings persistence to `~/.pyqalculate/preferences.json`
- [ ] Emits `PREFERENCE_APPLIED` via EventBus
- [ ] Tabs: Calculation, Display, Appearance
- [ ] Unit test: `tests/test_preferences_dialog.py` — verify load/save defaults
- [ ] File ≤ 400 LOC

**Commit**: `feat(gui): rewrite PreferencesDialog with ModalDialog base`

---

### Task 15: Rewrite `plot_dialog.py`

**Description**: Rewrite plot dialog using ModalDialog base class. matplotlib integration preserved.

**Delegation Recommendation**:
- Category: `unspecified-low` — Dialog rewrite, ~400-450 LOC
- Skills: [`programming`] — Python, tkinter, matplotlib

**Depends On**: T3, T6
**Acceptance Criteria**:
- [ ] Extends `ModalDialog` base class
- [ ] Uses `Theme` for all colors (zero hardcoded values)
- [ ] Multi-expression support preserved
- [ ] Save as PNG/SVG preserved
- [ ] matplotlib lazy import preserved
- [ ] File ≤ 450 LOC

**Commit**: `feat(gui): rewrite PlotDialog with ModalDialog base`

---

### Task 16: Rewrite `import_csv_dialog.py`

**Description**: Rewrite CSV import dialog using ModalDialog base class.

**Delegation Recommendation**:
- Category: `quick` — Simple dialog rewrite, ~150-180 LOC
- Skills: [`programming`] — Python, tkinter

**Depends On**: T3, T6
**Acceptance Criteria**:
- [ ] Extends `ModalDialog` base class
- [ ] Uses `Theme` for any colors
- [ ] All CSV import functionality preserved
- [ ] File ≤ 180 LOC

**Commit**: `feat(gui): rewrite ImportCsvDialog with ModalDialog base`

---

### Task 17: Rewrite `export_csv_dialog.py`

**Description**: Rewrite CSV export dialog using ModalDialog base class.

**Delegation Recommendation**:
- Category: `quick` — Simple dialog rewrite, ~150-180 LOC
- Skills: [`programming`] — Python, tkinter

**Depends On**: T3, T6
**Acceptance Criteria**:
- [ ] Extends `ModalDialog` base class
- [ ] Uses `Theme` for any colors
- [ ] All CSV export functionality preserved
- [ ] File ≤ 180 LOC

**Commit**: `feat(gui): rewrite ExportCsvDialog with ModalDialog base`

---

### Task 18: Create `app.py` + Update Entry Points

**Description**: Create the App class that owns Tk root, AppState, Theme, CalculatorService, EventBus, and all widgets. Replace MainWindow as the application entry point. Delete `main_window.py`.

**Delegation Recommendation**:
- Category: `unspecified-high` — Integration point, ~200-250 LOC, critical
- Skills: [`programming`] — Python, tkinter, dependency injection

**Depends On**: T1..T17 (all widgets and services)
**Acceptance Criteria**:
- [ ] `App` class owns: `root: tk.Tk`, `state: AppState`, `theme: Theme`, `calculator: CalculatorService`, `event_bus: EventBus`
- [ ] Creates and wires all widgets: ExpressionEdit, ResultView, HistoryView, Keypad, ConversionView, StatusBar, MenuBar
- [ ] Creates all dialogs: PreferencesDialog, PlotDialog, ImportCsvDialog, ExportCsvDialog
- [ ] Wires EventBus subscriptions (EXPRESSION_SUBMITTED → calculator → RESULT_DISPLAYED → HistoryView)
- [ ] `main_window.py` deleted
- [ ] `__main__.py` updated to `from pyqalculate_gui.app import main; main()`
- [ ] `__init__.py` updated with new `__version__`
- [ ] Application launches and displays correctly
- [ ] File ≤ 250 LOC

**Commit**: `feat(gui): create App class replacing MainWindow god object`

---

### Task 19: Integration Testing + Cleanup

**Description**: Run all tests, verify the full application works end-to-end, fix any integration issues.

**Delegation Recommendation**:
- Category: `deep` — Testing, debugging, integration verification
- Skills: [`programming`, `debugging`] — Python testing, tkinter headless

**Depends On**: T18
**Acceptance Criteria**:
- [ ] All existing tests pass: `python -m pytest tests/ -v`
- [ ] GUI launches without errors
- [ ] Expression calculation works end-to-end
- [ ] History with answer(N) works
- [ ] Unit conversion works
- [ ] All dialogs open and close correctly
- [ ] Theme switching works
- [ ] No hardcoded colors remaining (grep `#[0-9a-fA-F]{6}` in gui files — only in Theme)
- [ ] No private attribute cross-access (grep `\._[a-z].*\._` pattern)
- [ ] Integration test: `tests/test_gui_integration.py` — headless calculation flow

**Commit**: `test(gui): add integration tests for v3 GUI rebuild`

---

## Commit Strategy

Each task produces one atomic commit. Commits are ordered by wave:

```
Wave 1 (4 commits, can be parallel):
  chore: delete dead code (input_widget, result_widget, sidebar_widget, plot_widget)
  feat(gui): add AppState dataclass with observer pattern
  feat(gui): add centralized Theme class with design tokens
  feat(gui): add CalculatorService engine wrapper

Wave 2 (2 commits):
  feat(gui): add EventBus for decoupled widget communication
  feat(gui): add ModalDialog base class for all dialogs

Wave 3 (11 commits):
  feat(gui): rewrite ExpressionEdit with state/theme/events
  feat(gui): rewrite ResultView with state/theme/events
  feat(gui): rewrite HistoryView with state/theme/events
  feat(gui): rewrite Keypad with state/theme/events
  feat(gui): rewrite ConversionView with state/theme/events
  feat(gui): add StatusBar widget
  feat(gui): add MenuBar widget with EventBus integration
  feat(gui): rewrite PreferencesDialog with ModalDialog base
  feat(gui): rewrite PlotDialog with ModalDialog base
  feat(gui): rewrite ImportCsvDialog with ModalDialog base
  feat(gui): rewrite ExportCsvDialog with ModalDialog base

Wave 4 (1 commit):
  feat(gui): create App class replacing MainWindow god object

Wave 5 (1 commit):
  test(gui): add integration tests for v3 GUI rebuild
```

**Total: 19 atomic commits** on `feature/gui-v3-rewrite` branch.

---

## Success Criteria

### Architecture Verification
- [ ] No file exceeds 500 LOC (largest: conversion_view.py ~500, preferences_dialog.py ~400)
- [ ] Zero hardcoded colors outside `theme.py` (grep verified)
- [ ] Zero private attribute cross-access (grep verified)
- [ ] All widgets have public APIs only
- [ ] Single AppState holds all mutable state
- [ ] EventBus handles all inter-widget communication
- [ ] All dialogs extend ModalDialog

### Functional Verification
- [ ] Application launches and displays correctly
- [ ] Expression calculation: `2+2` → `4`
- [ ] Unit conversion: `5 ft to m` → `1.524 m`
- [ ] History: `answer(1)` recalls last result
- [ ] Keypad: clicking buttons inserts text
- [ ] Preferences: settings persist to JSON
- [ ] Plot: expression plotted with matplotlib
- [ ] CSV: import/export works

### Test Verification
- [ ] All existing tests pass (978+ unit tests)
- [ ] New GUI tests pass (state, theme, event_bus, calculator_service, dialog_base)
- [ ] Integration test passes (headless calculation flow)

---

## Execution Instructions

1. **Wave 1**: Fire these 4 tasks IN PARALLEL (no dependencies)
   ```
   task(category="quick", load_skills=[], prompt="Task 1: Delete dead code...")
   task(category="quick", load_skills=["programming"], prompt="Task 2: Create state.py...")
   task(category="quick", load_skills=["programming"], prompt="Task 3: Create theme.py...")
   task(category="quick", load_skills=["programming"], prompt="Task 4: Create calculator_service.py...")
   ```

2. **Wave 2**: After Wave 1 completes, fire 2 tasks IN PARALLEL
   ```
   task(category="quick", load_skills=["programming"], prompt="Task 5: Create event_bus.py...")
   task(category="quick", load_skills=["programming"], prompt="Task 6: Create dialogs/base.py...")
   ```

3. **Wave 3**: After Wave 2 completes, fire ALL 11 tasks IN PARALLEL
   ```
   task(category="unspecified-low", load_skills=["programming"], prompt="Task 7: Rewrite expression_edit.py...")
   task(category="unspecified-low", load_skills=["programming"], prompt="Task 8: Rewrite result_view.py...")
   ... (all 11 tasks)
   ```

4. **Wave 4**: After Wave 3 completes, fire 1 task
   ```
   task(category="unspecified-high", load_skills=["programming"], prompt="Task 18: Create app.py...")
   ```

5. **Wave 5**: After Wave 4 completes, fire 1 task
   ```
   task(category="deep", load_skills=["programming", "debugging"], prompt="Task 19: Integration testing...")
   ```

6. **Final QA**: Verify all tasks pass their QA criteria

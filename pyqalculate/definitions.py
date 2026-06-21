"""Definitions loader - loads JSON data files into the Calculator.

Reads the converted JSON definition files (units, functions, variables,
currencies, prefixes, datasets, elements, planets) and registers them
with a Calculator instance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyqalculate.calculator import Calculator
    from pyqalculate.prefix import Prefix

# Path to the data package
_DATA_DIR = Path(__file__).resolve().parent.parent / "pyqalculate_data"


# ---------------------------------------------------------------------------
# Name parsing helpers
# ---------------------------------------------------------------------------


def _extract_text(value: str | dict | None) -> str:
    """Extract text from either a plain string or a {#text, @translatable} dict."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("#text", "")
    return ""


def _extract_bool(value: str | dict | bool | None, default: bool = True) -> bool:
    """Extract a boolean from various JSON representations."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    if isinstance(value, dict):
        text = value.get("#text", "")
        return text.lower() == "true"
    return default


def _extract_int(value: str | dict | None, default: int = 0) -> int:
    """Extract an integer from various JSON representations."""
    if value is None:
        return default
    text = _extract_text(value)
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


def _parse_names(names_str: str) -> dict:
    """Parse a names string and return a dict with parsed name info.

    Returns dict with keys:
        reference: str (primary reference name)
        abbreviation: str (short name)
        singular: str (long form singular)
        plural: str (long form plural)
        all_names: list of (name, is_abbrev, is_plural, is_reference, is_unicode, is_case_sensitive)
    """
    result = {
        "reference": "",
        "abbreviation": "",
        "singular": "",
        "plural": "",
        "unicode": "",
        "all_names": [],
    }
    if not names_str:
        return result

    for entry in names_str.split(","):
        entry = entry.strip()
        if not entry:
            continue

        if ":" in entry:
            prefix, name = entry.split(":", 1)
            name = name.strip()
            if not name:
                continue

            is_abbrev = False
            is_plural = False
            is_reference = False
            is_unicode = False
            is_case_sensitive = False

            i = 0
            while i < len(prefix):
                ch = prefix[i]
                if ch == "a":
                    is_abbrev = True
                elif ch == "r":
                    is_reference = True
                elif ch == "p":
                    is_plural = True
                elif ch == "u":
                    is_unicode = True
                elif ch in ("o", "c"):
                    is_case_sensitive = True
                elif ch == "s":
                    pass  # suffix
                elif ch == "i":
                    pass  # completion-only
                elif ch == "e":
                    is_abbrev = True
                    is_plural = True
                i += 1

            result["all_names"].append({
                "name": name,
                "abbreviation": is_abbrev,
                "plural": is_plural,
                "reference": is_reference,
                "unicode": is_unicode,
                "case_sensitive": is_case_sensitive,
            })

            if is_reference and not result["reference"]:
                result["reference"] = name
            if is_abbrev and not is_unicode and not result["abbreviation"]:
                result["abbreviation"] = name
            if is_unicode and not result["unicode"]:
                result["unicode"] = name
            if is_plural and not result["plural"]:
                result["plural"] = name
            if not is_abbrev and not is_plural and not result["singular"]:
                result["singular"] = name
        else:
            # No prefix - bare name
            result["all_names"].append({
                "name": entry,
                "abbreviation": False,
                "plural": False,
                "reference": False,
                "unicode": False,
                "case_sensitive": False,
            })
            if not result["singular"]:
                result["singular"] = entry

    return result


def _apply_names(unit, names_str: str) -> None:
    """Apply parsed names to a unit object.

    Registers ALL names from the names string so lookups by any name work.
    Previously only the first abbreviation/reference/singular/plural were added,
    causing secondary abbreviations like 'cal' (for cal_th) to be lost.
    """
    from pyqalculate.expression_item import ExpressionName

    parsed = _parse_names(names_str)

    # First name: abbreviation or reference
    if parsed["abbreviation"]:
        unit.add_name(parsed["abbreviation"])
    elif parsed["reference"]:
        unit.add_name(parsed["reference"])
    elif parsed["all_names"]:
        unit.add_name(parsed["all_names"][0]["name"])

    # Second name: singular (non-abbreviation)
    if parsed["singular"]:
        en = ExpressionName(parsed["singular"])
        en.abbreviation = False
        en.plural = False
        unit.add_name(en)

    # Third name: plural
    if parsed["plural"]:
        en = ExpressionName(parsed["plural"])
        en.abbreviation = False
        en.plural = True
        unit.add_name(en)

    # Unicode abbreviation
    if parsed["unicode"]:
        en = ExpressionName(parsed["unicode"])
        en.abbreviation = True
        en.unicode = True
        unit.add_name(en)

    # Reference name (if different from abbreviation)
    if parsed["reference"] and parsed["reference"] != parsed["abbreviation"]:
        en = ExpressionName(parsed["reference"])
        en.reference = True
        if not any(n.name == parsed["reference"] for n in unit._names):
            unit.add_name(en)

    # Register ALL remaining names from the parsed list so lookups work
    # for secondary abbreviations, aliases, case-sensitive names, etc.
    existing_names = {n.name for n in unit._names}
    for entry in parsed["all_names"]:
        name = entry["name"]
        if name and name not in existing_names:
            en = ExpressionName(name)
            en.abbreviation = entry.get("abbreviation", False)
            en.plural = entry.get("plural", False)
            en.reference = entry.get("reference", False)
            en.unicode = entry.get("unicode", False)
            en.case_sensitive = entry.get("case_sensitive", False)
            unit.add_name(en)
            existing_names.add(name)


# ---------------------------------------------------------------------------
# Prefix loading
# ---------------------------------------------------------------------------


def load_prefixes(calc: Calculator, data_dir: Path | None = None) -> int:
    """Load prefix definitions from prefixes.json.

    Returns the number of prefixes loaded.
    """
    data_dir = data_dir or _DATA_DIR
    prefs_file = data_dir / "prefixes.json"
    if not prefs_file.exists():
        return 0

    from pyqalculate.prefix import BinaryPrefix, DecimalPrefix

    with open(prefs_file, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        if not isinstance(item, dict):
            continue

        ptype = item.get("@type", "decimal")
        names_str = _extract_text(item.get("names", ""))
        exp_str = _extract_text(item.get("exponent", ""))

        if not exp_str:
            continue

        try:
            exp_int = int(exp_str)
        except ValueError:
            continue

        parsed = _parse_names(names_str)
        short_name = parsed["abbreviation"] or parsed["reference"]
        long_name = parsed["singular"] or parsed["reference"]

        if ptype == "binary":
            prefix = BinaryPrefix(exp_int, long_name, short_name)
        else:
            prefix = DecimalPrefix(exp_int, long_name, short_name)

        # Add unicode name if present
        if parsed["unicode"]:
            prefix.set_unicode_name(parsed["unicode"])

        calc.add_prefix(prefix)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Unit loading
# ---------------------------------------------------------------------------


def _find_prefix_by_exp(calc: Calculator, exp: int):
    """Find a prefix by its exponent value."""
    for p in calc._prefixes:
        if hasattr(p, '_exponent') and p._exponent == exp:
            return p
    return None


# Dictionaries to track pending unit references during loading
_pending_alias_bases: dict[str, str] = {}  # unit_name -> base_unit_name
_pending_composite_parts: dict[str, list] = {}  # unit_name -> parts list


def _process_unit_entry(
    unit_def: dict,
    category: str,
    calc: Calculator,
) -> bool:
    """Process a single unit definition and register it with the calculator.

    Returns True if a unit was successfully created and registered.
    """
    from pyqalculate.unit import AliasUnit, CompositeUnit, Unit

    unit_type = unit_def.get("@type", "base")
    title_raw = unit_def.get("title", "")
    title = _extract_text(title_raw) if isinstance(title_raw, (dict, str)) else str(title_raw)
    names_str = _extract_text(unit_def.get("names", ""))
    system = _extract_text(unit_def.get("system", ""))
    hidden = _extract_bool(unit_def.get("hidden", ""), default=False)

    if not names_str:
        return False

    parsed = _parse_names(names_str)
    primary_name = parsed["abbreviation"] or parsed["reference"] or parsed["singular"]
    if not primary_name:
        return False

    # Skip if a unit with the same primary name already exists to avoid
    # overriding built-in definitions (e.g., temperature C overridden by Coulomb C).
    if primary_name in calc._units:
        return False

    if unit_type == "base":
        # Base unit
        unit = Unit(
            category=category,
            name=primary_name,
            plural=parsed["plural"],
            singular=parsed["singular"],
            title=title,
            is_local=False,
            is_builtin=True,
        )
        _apply_names(unit, names_str)

        if system:
            unit.set_system(system)

        # use_with_prefixes
        uwp = unit_def.get("use_with_prefixes")
        if uwp is not None:
            use = _extract_bool(uwp, default=True)
            unit.set_use_with_prefixes_by_default(use)
            if isinstance(uwp, dict):
                max_pref = _extract_int(uwp.get("@max", ""))
                if max_pref:
                    unit.set_max_preferred_prefix(max_pref)
                default_pref = _extract_int(uwp.get("@default", ""))
                if default_pref:
                    unit.set_default_prefix(default_pref)

        if hidden:
            unit.set_hidden(True)

        calc.add_unit(unit)
        return True

    elif unit_type == "alias":
        # Alias unit - need to resolve base unit later
        base_def = unit_def.get("base", {})
        if not base_def:
            return False

        base_unit_name = _extract_text(base_def.get("unit", ""))
        relation = _extract_text(base_def.get("relation", "1"))
        exponent = _extract_int(base_def.get("exponent", ""), default=1)
        inverse = _extract_text(base_def.get("inverse", ""))
        mix = base_def.get("mix")

        unit = AliasUnit(
            category=category,
            name=primary_name,
            plural=parsed["plural"],
            singular=parsed["singular"],
            title=title,
            relation=relation,
            exponent=exponent,
            inverse=inverse,
            is_local=False,
            is_builtin=True,
        )
        _apply_names(unit, names_str)

        if system:
            unit.set_system(system)

        # Mix with base
        if mix is not None:
            if isinstance(mix, dict):
                mix_val = _extract_int(mix.get("#text", ""), default=0)
                mix_min = _extract_int(mix.get("@min", ""), default=0)
            else:
                mix_val = _extract_int(mix, default=0)
                mix_min = 0
            if mix_val:
                unit.set_mix_with_base(mix_val)
            if mix_min:
                unit.set_mix_with_base_minimum(mix_min)

        # use_with_prefixes
        uwp = unit_def.get("use_with_prefixes")
        if uwp is not None:
            use = _extract_bool(uwp, default=True)
            unit.set_use_with_prefixes_by_default(use)

        if hidden:
            unit.set_hidden(True)

        # Store base unit name for later resolution
        _pending_alias_bases[primary_name] = base_unit_name
        calc.add_unit(unit)
        return True

    elif unit_type == "composite":
        # Composite unit
        parts = unit_def.get("part", [])
        if not isinstance(parts, list):
            parts = [parts]

        unit = CompositeUnit(
            category=category,
            name=primary_name,
            title=title,
            is_local=False,
            is_builtin=True,
        )
        _apply_names(unit, names_str)

        if system:
            unit.set_system(system)

        if hidden:
            unit.set_hidden(True)

        # Store parts for later resolution
        _pending_composite_parts[primary_name] = parts
        calc.add_unit(unit)
        return True

    return False


def _resolve_unit_references(calc: Calculator) -> None:
    """Resolve pending base unit references for alias and composite units.

    Must be called after all units are initially registered.
    """
    from pyqalculate.unit import AliasUnit, CompositeUnit

    # Resolve alias units
    for unit_name, base_name in _pending_alias_bases.items():
        unit = calc.get_unit(unit_name)
        if unit is not None and isinstance(unit, AliasUnit):
            base_unit = calc.get_unit(base_name)
            if base_unit is not None:
                unit.set_base_unit(base_unit)

    # Resolve composite units
    for unit_name, parts in _pending_composite_parts.items():
        unit = calc.get_unit(unit_name)
        if unit is not None and isinstance(unit, CompositeUnit):
            for part in parts:
                part_unit_name = _extract_text(part.get("unit", ""))
                part_prefix_exp = _extract_text(part.get("prefix", "0"))
                part_exponent = _extract_int(part.get("exponent", ""), default=1)

                part_unit = calc.get_unit(part_unit_name)
                if part_unit is None:
                    continue

                # Resolve prefix
                prefix = None
                try:
                    prefix_exp = int(part_prefix_exp)
                    if prefix_exp != 0:
                        prefix = _find_prefix_by_exp(calc, prefix_exp)
                except (ValueError, TypeError):
                    pass

                unit.add(part_unit, part_exponent, prefix)

    # Clear pending references
    _pending_alias_bases.clear()
    _pending_composite_parts.clear()


def _generate_prefixed_units(calc: Calculator) -> None:
    """Generate prefixed units (km, kg, mm, etc.) from base units and prefixes.

    For each unit that accepts prefixes, create new units with each prefix applied.
    """
    from pyqalculate.unit import AliasUnit, UnitSubtype

    # Get all prefixes
    prefixes = calc._prefixes
    if not prefixes:
        return

    # Snapshot the existing unit list BEFORE generating so newly-created
    # prefixed units are never re-processed (avoids double-prefixing).
    original_units = list(calc._units.values())

    # Get all units to check which ones accept prefixes
    units_to_process = []
    for unit in original_units:
        # Check if unit accepts prefixes (by convention, base units and some alias units do)
        if hasattr(unit, 'subtype') and unit.subtype() == UnitSubtype.BASE_UNIT:
            units_to_process.append(unit)
        # Also check for units with use_with_prefixes flag
        elif hasattr(unit, '_use_with_prefixes') and unit._use_with_prefixes:
            units_to_process.append(unit)

    generated = 0
    for unit in units_to_process:
        unit_name = unit.name()

        for prefix in prefixes:
            if not hasattr(prefix, 'short_name'):
                continue
            prefix_short = prefix.short_name()

            if not prefix_short:
                continue

            prefix_long = prefix.long_name() if hasattr(prefix, 'long_name') else prefix_short

            # Create prefixed unit name
            prefixed_name = f"{prefix_short}{unit_name}"

            # Skip if already exists — use EXACT (case-sensitive) check to avoid
            # "MJ" being skipped because "mJ" (millijoule) already exists.
            if prefixed_name in calc._units:
                continue

            # Create an alias unit with prefix
            # The prefixed unit = prefix_factor * base_unit
            try:
                prefix_factor = 10 ** prefix.exponent() if hasattr(prefix, 'exponent') else 1.0
            except (TypeError, AttributeError):
                continue

            prefixed_unit = AliasUnit(
                unit.category() if hasattr(unit, 'category') else "",
                prefixed_name,
                f"{prefix_long}{unit.plural() if hasattr(unit, 'plural') else unit_name}",
                prefixed_name,
                f"{prefix_long}{unit.title() if hasattr(unit, 'title') else unit_name}",
                base_unit=unit,
                relation=str(prefix_factor),
            )
            # Store prefix reference for later use
            prefixed_unit.__dict__['_prefix'] = prefix
            prefixed_unit.__dict__['_use_with_prefixes'] = False  # Don't double-prefix

            calc.add_unit(prefixed_unit)
            generated += 1


def _add_extra_aliases(calc: Calculator) -> None:
    """Add common unit aliases not present in the JSON definitions.

    These are convenience aliases so users can type common shorthand names
    without needing to know the exact canonical unit name.
    """
    from pyqalculate.expression_item import ExpressionName

    # Map of alias_name -> existing unit key
    extra_aliases = {
        "kcal": "kcal_c",
    }

    for alias, unit_key in extra_aliases.items():
        unit = calc._units.get(unit_key)
        if unit is None:
            continue
        # Skip if alias already exists as a direct unit key
        if alias in calc._units:
            continue
        # Add the alias as a name on the existing unit
        en = ExpressionName(alias)
        en.abbreviation = True
        unit.add_name(en)
        # Index in the name lookup table
        lower = alias.lower()
        if lower not in calc._unit_names:
            calc._unit_names[lower] = []
        if unit_key not in calc._unit_names[lower]:
            calc._unit_names[lower].append(unit_key)


def load_units(calc: Calculator, data_dir: Path | None = None) -> int:
    """Load unit definitions from units.json.

    Returns the number of units loaded.
    """
    data_dir = data_dir or _DATA_DIR
    units_file = data_dir / "units.json"
    if not units_file.exists():
        return 0

    with open(units_file, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for section in data:
        if not isinstance(section, dict):
            continue

        section_title = _extract_text(section.get("title", ""))

        # Units can be directly in "unit" key or nested in "category"
        units_list = section.get("unit", [])
        categories = section.get("category", [])

        # categories can be a list of dicts OR a single dict (e.g. Hz's Frequency category)
        if isinstance(categories, dict):
            categories = [categories]

        if isinstance(units_list, dict):
            units_list = [units_list]

        for unit_def in units_list:
            if isinstance(unit_def, dict):
                if _process_unit_entry(unit_def, section_title, calc):
                    count += 1

        # Process subcategories
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            cat_title = _extract_text(cat.get("title", ""))
            full_category = f"{section_title}/{cat_title}" if section_title else cat_title

            cat_units = cat.get("unit", [])
            if isinstance(cat_units, dict):
                cat_units = [cat_units]

            for unit_def in cat_units:
                if isinstance(unit_def, dict):
                    if _process_unit_entry(unit_def, full_category, calc):
                        count += 1

    # Second pass: resolve base unit references
    _resolve_unit_references(calc)

    # Third pass: generate prefixed units (km, kg, mm, etc.)
    _generate_prefixed_units(calc)

    # Fourth pass: add common aliases that aren't in the JSON definitions
    _add_extra_aliases(calc)

    return count


# ---------------------------------------------------------------------------
# Currency loading
# ---------------------------------------------------------------------------


def load_currencies(calc: Calculator, data_dir: Path | None = None) -> int:
    """Load currency definitions from currencies.json.

    Currencies are loaded as base units in the "Currency" category.
    Exchange rates are not loaded here - they require separate rate data.

    Returns the number of currencies loaded.
    """
    from pyqalculate.unit import Unit

    data_dir = data_dir or _DATA_DIR
    curr_file = data_dir / "currencies.json"
    if not curr_file.exists():
        return 0

    with open(curr_file, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for section in data:
        if not isinstance(section, dict):
            continue

        section_title = _extract_text(section.get("title", ""))

        # Currencies can be in "builtin_unit" key
        currencies = section.get("builtin_unit", [])
        if isinstance(currencies, dict):
            currencies = [currencies]

        for curr_def in currencies:
            if not isinstance(curr_def, dict):
                continue

            curr_name = curr_def.get("@name", "")
            if not curr_name:
                continue

            title = _extract_text(curr_def.get("title", ""))
            names_str = _extract_text(curr_def.get("names", ""))
            countries = _extract_text(curr_def.get("countries", ""))

            unit = Unit(
                category=section_title or "Currency",
                name=curr_name,
                title=title,
                is_local=False,
                is_builtin=True,
            )
            _apply_names(unit, names_str)
            if countries:
                unit.set_countries(countries)
            unit.set_use_with_prefixes_by_default(False)

            calc.add_unit(unit)
            count += 1

    return count


# ---------------------------------------------------------------------------
# Variable loading
# ---------------------------------------------------------------------------


def load_variables(calc: Calculator, data_dir: Path | None = None) -> int:
    """Load variable definitions from variables.json.

    Returns the number of variables loaded.
    """
    data_dir = data_dir or _DATA_DIR
    vars_file = data_dir / "variables.json"
    if not vars_file.exists():
        return 0

    from pyqalculate.variable import KnownVariable

    with open(vars_file, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for category_block in data:
        if not isinstance(category_block, dict):
            continue

        cat_title = _extract_text(category_block.get("title", ""))

        for var_def in category_block.get("variable", []):
            if not isinstance(var_def, dict):
                continue

            title = _extract_text(var_def.get("title", ""))
            names_raw = var_def.get("names", "")
            value = _extract_text(var_def.get("value", ""))
            names_str = _extract_text(names_raw)

            if not names_str or not value:
                continue

            parsed = _parse_names(names_str)
            primary_name = parsed["abbreviation"] or parsed["reference"] or parsed["singular"]
            if not primary_name:
                continue

            var = KnownVariable(cat_title, primary_name, value, title)
            # Register additional names
            for name_entry in names_str.split(","):
                name_entry = name_entry.strip()
                if ":" in name_entry:
                    _, name = name_entry.split(":", 1)
                    name = name.strip()
                    if name and name != primary_name:
                        var.add_name(name)
                elif name_entry and name_entry != primary_name:
                    var.add_name(name_entry)

            calc.add_variable(var)
            count += 1

    return count


# ---------------------------------------------------------------------------
# Master loader
# ---------------------------------------------------------------------------


def load_all(calc: Calculator, data_dir: Path | None = None) -> dict[str, int]:
    """Load all definition files.

    Returns a dict mapping file name to number of items loaded.
    """
    results: dict[str, int] = {}
    results["prefixes"] = load_prefixes(calc, data_dir)
    results["units"] = load_units(calc, data_dir)
    results["currencies"] = load_currencies(calc, data_dir)
    results["variables"] = load_variables(calc, data_dir)
    return results

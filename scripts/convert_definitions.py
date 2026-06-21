"""Convert libqalculate XML definition files to JSON.

Reads XML data files from the libqalculate data directory and produces
JSON equivalents in the pyqalculate_data package directory.

Usage:
    python scripts/convert_definitions.py [--source-dir DIR] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# Default paths (relative to project root)
DEFAULT_SOURCE = Path(r"D:\1\1tmp\libqalculate\data")
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "pyqalculate_data"

# Mapping of XML input files to JSON output files
FILE_MAP: dict[str, str] = {
    "units.xml.in": "units.json",
    "functions.xml.in": "functions.json",
    "variables.xml.in": "variables.json",
    "currencies.xml.in": "currencies.json",
    "prefixes.xml.in": "prefixes.json",
    "datasets.xml.in": "datasets.json",
    "elements.xml.in": "elements.json",
    "planets.xml.in": "planets.json",
}


def element_to_dict(elem: ET.Element) -> dict[str, Any]:
    """Recursively convert an XML element to a dictionary.

    Attributes become dict keys prefixed with '@'.
    Text content becomes '#text'.
    Child elements are nested dicts; repeated tags become lists.
    """
    result: dict[str, Any] = {}

    # Attributes
    for attr_name, attr_val in elem.attrib.items():
        result[f"@{attr_name}"] = attr_val

    # Text content (trimmed)
    if elem.text and elem.text.strip():
        text = elem.text.strip()
        if not result:
            # Leaf node with only text
            return text  # type: ignore[return-value]
        result["#text"] = text

    # Children
    children: dict[str, list[Any]] = {}
    for child in elem:
        child_data = element_to_dict(child)
        tag = child.tag
        children.setdefault(tag, []).append(child_data)

    for tag, items in children.items():
        if len(items) == 1:
            result[tag] = items[0]
        else:
            result[tag] = items

    return result


def convert_xml_to_json(xml_path: Path) -> list[dict[str, Any]]:
    """Parse an XML file and return its root children as a list of dicts."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    items: list[dict[str, Any]] = []
    for child in root:
        items.append(element_to_dict(child))
    return items


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert libqalculate XML definitions to JSON."
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Directory containing XML.in files (default: libqalculate/data)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory to write JSON files (default: pyqalculate_data/)",
    )
    args = parser.parse_args()

    source_dir: Path = args.source_dir.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not source_dir.is_dir():
        print(f"Error: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Also create __init__.py for the data package
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""PyQalculate data files (JSON definitions)."""\n',
            encoding="utf-8",
        )

    converted = 0
    for xml_name, json_name in FILE_MAP.items():
        xml_path = source_dir / xml_name
        json_path = output_dir / json_name

        if not xml_path.exists():
            print(f"  SKIP  {xml_name} (not found)")
            continue

        print(f"  Converting {xml_name} -> {json_name} ... ", end="", flush=True)
        try:
            data = convert_xml_to_json(xml_path)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"OK ({len(data)} entries)")
            converted += 1
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nDone. Converted {converted}/{len(FILE_MAP)} files to {output_dir}")


if __name__ == "__main__":
    main()

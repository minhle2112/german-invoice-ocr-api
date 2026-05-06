from pathlib import Path

from lxml import etree


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
XSD_PATH = SCHEMA_DIR / "CrossIndustryInvoice_100pD22B.xsd"
XSD_NAMESPACE = "{http://www.w3.org/2001/XMLSchema}"


def _missing_imports(xsd_path: Path, seen: set[Path] | None = None) -> list[str]:
    seen = seen or set()
    xsd_path = xsd_path.resolve()

    if xsd_path in seen:
        return []

    seen.add(xsd_path)

    if not xsd_path.exists():
        return [str(xsd_path)]

    xsd_doc = etree.parse(str(xsd_path))
    missing = []

    for import_node in xsd_doc.findall(f"{XSD_NAMESPACE}import"):
        schema_location = import_node.get("schemaLocation")
        if not schema_location:
            continue

        import_path = xsd_path.parent / schema_location
        if import_path.exists():
            missing.extend(_missing_imports(import_path, seen))
        else:
            missing.append(schema_location)

    return missing


def _format_error_log(error_log) -> list[str]:
    return [
        f"line {error.line}, column {error.column}: {error.message}"
        for error in error_log
    ]


def validate_cii_xml(xml_string: str):
    try:
        xml_doc = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return {
            "valid": False,
            "errors": [f"Invalid XML: {exc}"],
        }

    missing_imports = _missing_imports(XSD_PATH)
    if missing_imports:
        return {
            "valid": False,
            "errors": [
                "CII XSD schema set is incomplete. Add the imported XSD files "
                f"next to {XSD_PATH.name}: {', '.join(missing_imports)}"
            ],
        }

    try:
        # Parse from the path string so lxml keeps the schema directory as the
        # base URL for resolving relative xsd:import schemaLocation values.
        xsd_doc = etree.parse(str(XSD_PATH))
        schema = etree.XMLSchema(xsd_doc)
    except (OSError, etree.XMLSchemaParseError, etree.XMLSyntaxError) as exc:
        return {
            "valid": False,
            "errors": [f"Could not load CII XSD schema: {exc}"],
        }

    valid = schema.validate(xml_doc)

    return {
        "valid": valid,
        "errors": _format_error_log(schema.error_log),
    }

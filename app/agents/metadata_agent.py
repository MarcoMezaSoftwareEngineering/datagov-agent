"""Metadata & Catalog Agent: glosario, clasificación, owner/steward (Módulo 5)."""

from __future__ import annotations

from app.agents.prompts import METADATA_SYSTEM
from app.schemas.data_schema import TableProfile
from app.schemas.quality_schema import CatalogEntry, QualityReport
from app.services.llm import get_llm
from app.utils.text_cleaning import extract_json

# Definiciones de negocio base para campos conocidos del dataset sintético.
BUSINESS_DEFINITIONS = {
    "cliente_id": "Identificador único del cliente",
    "producto_id": "Identificador único del producto",
    "proveedor_id": "Identificador único del proveedor",
    "venta_id": "Identificador único de la venta",
    "dni": "Documento Nacional de Identidad del cliente",
    "ruc": "Registro Único de Contribuyentes",
    "sku": "Código único de inventario del producto (Stock Keeping Unit)",
    "correo": "Correo electrónico de contacto",
    "telefono": "Número telefónico de contacto",
    "direccion": "Dirección física",
    "nombre": "Nombre de la persona",
    "apellido": "Apellido de la persona",
    "razon_social": "Razón social del proveedor",
    "precio": "Precio del producto",
    "total": "Importe total de la venta",
    "fecha_registro": "Fecha de registro del cliente",
    "fecha_venta": "Fecha en que se realizó la venta",
}

# Owner/Steward sugerido por tabla
OWNERSHIP = {
    "clientes": ("Gerencia Comercial", "Analista de Clientes"),
    "productos": ("Gerencia de Producto", "Analista de Catálogo"),
    "ventas": ("Gerencia Comercial", "Analista de Ventas"),
    "proveedores": ("Gerencia de Compras", "Analista de Proveedores"),
}

SENSITIVE_HINTS = ("dni", "ruc", "correo", "email", "telefono", "direccion", "nombre", "apellido")


def run_metadata(profile: TableProfile, quality: QualityReport | None = None) -> list[CatalogEntry]:
    """Construye entradas de catálogo para campos sensibles/identificadores/críticos."""
    table = profile.table
    owner, steward = OWNERSHIP.get(table, ("Gobierno de Datos", "Data Steward asignado"))

    # Reglas por campo a partir de los hallazgos de calidad
    rules_by_field: dict[str, list[str]] = {}
    if quality:
        for f in quality.findings:
            rules_by_field.setdefault(f.field, []).append(f.suggested_rule)

    target_fields = _target_fields(profile)
    entries: list[CatalogEntry] = []
    for field in target_fields:
        classification, criticality = _classify(field)
        entries.append(
            CatalogEntry(
                table=table,
                field=field,
                business_definition=BUSINESS_DEFINITIONS.get(
                    field.lower(), f"Campo {field} de la tabla {table}"
                ),
                classification=classification,
                criticality=criticality,
                data_owner=owner,
                data_steward=steward,
                update_frequency="diaria" if table == "ventas" else "según evento",
                quality_rules=sorted(set(rules_by_field.get(field, []))) or _default_rules(field),
            )
        )

    _enrich_with_llm(table, entries)
    return entries


def _target_fields(profile: TableProfile) -> list[str]:
    fields = set(profile.possible_sensitive_fields) | set(profile.possible_identifier_fields)
    # incluir también campos con reglas conocidas
    for cp in profile.column_profiles:
        if cp.name.lower() in BUSINESS_DEFINITIONS:
            fields.add(cp.name)
    return sorted(fields)


def _classify(field: str) -> tuple[str, str]:
    f = field.lower()
    if any(
        h in f
        for h in ("dni", "correo", "email", "telefono", "direccion", "nombre", "apellido", "ruc")
    ):
        return "dato personal", "alta"
    if f.endswith("_id") or f in {"sku"}:
        return "dato maestro", "alta"
    if any(h in f for h in ("precio", "total", "monto")):
        return "dato financiero", "media"
    return "dato operativo", "media"


def _default_rules(field: str) -> list[str]:
    f = field.lower()
    if f == "dni":
        return ["obligatorio", "8 dígitos", "único"]
    if f == "ruc":
        return ["obligatorio", "11 dígitos", "único"]
    if "correo" in f or "email" in f:
        return ["formato de email válido"]
    if f.endswith("_id") or f == "sku":
        return ["obligatorio", "único"]
    return ["obligatorio"]


def _enrich_with_llm(table: str, entries: list[CatalogEntry]) -> None:
    llm = get_llm()
    if not llm.available or not entries:
        return
    fields = ", ".join(e.field for e in entries)
    user = f"Tabla: {table}. Campos a documentar: {fields}."
    raw = llm.complete(METADATA_SYSTEM, user, json_mode=True)
    data = extract_json(raw) if raw else None
    if not isinstance(data, dict):
        return
    by_field = {e.field.lower(): e for e in entries}
    for item in data.get("entries", []):
        entry = by_field.get(str(item.get("field", "")).lower())
        if entry and item.get("business_definition"):
            entry.business_definition = item["business_definition"]

"""Conocimiento del modelo de datos: claves primarias, claves de negocio y relaciones FK.

Centraliza qué columnas son identificadores únicos (PK) frente a claves foráneas (FK),
para que el perfilado y la calidad no marquen falsos duplicados en columnas FK que
legítimamente se repiten (p. ej. ``ventas.cliente_id``).
"""

from __future__ import annotations

# PK por tabla del dominio comercial.
PRIMARY_KEYS: dict[str, str] = {
    "clientes": "cliente_id",
    "productos": "producto_id",
    "proveedores": "proveedor_id",
    "ventas": "venta_id",
    "sucursales": "sucursal_id",
}

# Claves de negocio que también deben ser únicas (además de la PK).
EXPLICIT_KEYS: set[str] = {"dni", "ruc", "sku"}

# Relaciones FK conocidas: columna_hija -> (tabla_padre, columna_padre).
FK_RELATIONS: dict[str, tuple[str, str]] = {
    "cliente_id": ("clientes", "cliente_id"),
    "producto_id": ("productos", "producto_id"),
    "proveedor_id": ("proveedores", "proveedor_id"),
    "sucursal_id": ("sucursales", "sucursal_id"),
}


def primary_key(table: str) -> str | None:
    """Devuelve la PK esperada de la tabla (por nombre conocido o heurística singular+_id)."""
    table = table.lower()
    if table in PRIMARY_KEYS:
        return PRIMARY_KEYS[table]
    # Heurística de respaldo para tablas no catalogadas: singular + _id.
    if table.endswith("es"):
        return table[:-2] + "_id"
    if table.endswith("s"):
        return table[:-1] + "_id"
    return None


def unique_key_fields(table: str, columns) -> list[str]:
    """Columnas que deben ser únicas en la tabla: su PK + claves de negocio presentes.

    Excluye explícitamente las claves foráneas (que se validan por integridad
    referencial, no por unicidad).
    """
    pk = primary_key(table)
    lookup = {c.lower(): c for c in columns}
    out: list[str] = []
    if pk and pk.lower() in lookup:
        out.append(lookup[pk.lower()])
    for key in EXPLICIT_KEYS:
        if key in lookup and lookup[key] not in out:
            out.append(lookup[key])
    return out

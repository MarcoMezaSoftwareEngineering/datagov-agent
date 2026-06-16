"""Genera datasets sintéticos con errores controlados (§16 del plan).

Crea: clientes.csv, productos.csv, ventas.csv, proveedores.csv en data/synthetic/.
Usa Faker con semilla fija para reproducibilidad.

Errores inyectados a propósito (para que el motor de calidad/MDM los detecte):
- clientes: DNI duplicado, DNI corto, correos inválidos, teléfonos vacíos,
  país (Perú/Peru/PE), clientes duplicados, segmento vacío.
- productos: SKU duplicado, precio negativo, moneda vacía, categorías inconsistentes,
  producto sin proveedor, fecha futura.
- ventas: cliente inexistente, producto inexistente, total mal calculado, cantidad cero,
  fecha futura, canal vacío.
- proveedores: RUC duplicado, RUC inválido, proveedor sin correo, país inconsistente.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 42
N_CLIENTES = 120
N_PRODUCTOS = 60
N_PROVEEDORES = 20
N_VENTAS = 300

fake = Faker("es_ES")
Faker.seed(SEED)
random.seed(SEED)

OUT_DIR = Path(__file__).resolve().parent
PAISES = ["Peru", "Perú", "PE", "Chile", "Colombia", "Ecuador"]
SEGMENTOS = ["Retail", "Corporativo", "Pyme", "Premium"]
CATEGORIAS = ["Electronica", "electrónica", "Hogar", "Oficina", "Deportes", "deportes"]
MONEDAS = ["PEN", "USD"]
CANALES = ["Web", "Tienda", "Call Center", "Marketplace"]
SUCURSALES = ["Lima Centro", "Miraflores", "Arequipa", "Trujillo"]


def _maybe(prob: float) -> bool:
    return random.random() < prob


def gen_proveedores() -> pd.DataFrame:
    rows = []
    for i in range(1, N_PROVEEDORES + 1):
        ruc = f"20{random.randint(100000000, 999999999)}"  # 11 dígitos
        if _maybe(0.1):  # RUC inválido (corto)
            ruc = str(random.randint(10000, 99999))
        rows.append(
            {
                "proveedor_id": f"PRV{i:03d}",
                "ruc": ruc,
                "razon_social": fake.company(),
                "correo": "" if _maybe(0.15) else fake.company_email(),  # proveedor sin correo
                "telefono": fake.phone_number(),
                "pais": random.choice(PAISES),  # país inconsistente
                "estado": random.choice(["activo", "inactivo"]),
            }
        )
    df = pd.DataFrame(rows)
    # RUC duplicado
    if len(df) > 3:
        df.loc[2, "ruc"] = df.loc[1, "ruc"]
    return df


def gen_clientes() -> pd.DataFrame:
    rows = []
    for i in range(1, N_CLIENTES + 1):
        dni = f"{random.randint(10000000, 99999999)}"  # 8 dígitos
        if _maybe(0.08):  # DNI corto
            dni = f"{random.randint(100000, 999999)}"
        nombre = fake.first_name()
        apellido = fake.last_name()
        correo = f"{nombre.lower()}.{apellido.lower()}@email.com"
        if _maybe(0.12):  # correo inválido
            correo = f"{nombre.lower()}{apellido.lower()}#email"
        rows.append(
            {
                "cliente_id": f"C{i:03d}",
                "nombre": nombre,
                "apellido": apellido,
                "dni": dni,
                "ruc": f"10{random.randint(100000000, 999999999)}" if _maybe(0.3) else "",
                "correo": correo,
                "telefono": "" if _maybe(0.18) else fake.msisdn()[:9],  # teléfono vacío
                "direccion": fake.street_address(),
                "distrito": fake.city(),
                "pais": random.choice(PAISES),
                "fecha_registro": fake.date_between("-3y", "today").isoformat(),
                "estado_cliente": random.choice(["activo", "Activo", "inactivo"]),
                "segmento": "" if _maybe(0.15) else random.choice(SEGMENTOS),  # segmento vacío
            }
        )
    df = pd.DataFrame(rows)
    # DNI duplicado + cliente duplicado (mismo nombre/dni con variación de tildes)
    if len(df) > 5:
        df.loc[3, "dni"] = df.loc[2, "dni"]
        dup = df.loc[2].copy()
        dup["cliente_id"] = "C201"
        dup["nombre"] = _add_accent(dup["nombre"])
        df = pd.concat([df, dup.to_frame().T], ignore_index=True)
    return df


def _add_accent(name: str) -> str:
    table = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}
    for plain, acc in table.items():
        if plain in name.lower():
            idx = name.lower().index(plain)
            return name[:idx] + acc + name[idx + 1 :]
    return name


def gen_productos(proveedor_ids: list[str]) -> pd.DataFrame:
    rows = []
    today = datetime.now().date()
    for i in range(1, N_PRODUCTOS + 1):
        precio = round(random.uniform(5, 2000), 2)
        if _maybe(0.07):  # precio negativo
            precio = -precio
        fecha_alta = fake.date_between("-2y", "today")
        if _maybe(0.06):  # fecha futura
            fecha_alta = today + timedelta(days=random.randint(10, 120))
        rows.append(
            {
                "producto_id": f"P{i:03d}",
                "sku": f"SKU-{random.randint(1000, 9999)}",
                "nombre_producto": fake.word().capitalize() + " " + fake.word(),
                "categoria": random.choice(CATEGORIAS),  # categorías inconsistentes
                "marca": fake.company(),
                "precio": precio,
                "moneda": "" if _maybe(0.1) else random.choice(MONEDAS),  # moneda vacía
                "estado_producto": random.choice(["activo", "descontinuado"]),
                "fecha_alta": fecha_alta.isoformat(),
                # producto sin proveedor o con proveedor inexistente
                "proveedor_id": "" if _maybe(0.1) else random.choice(proveedor_ids + ["PRV999"]),
            }
        )
    df = pd.DataFrame(rows)
    # SKU duplicado
    if len(df) > 4:
        df.loc[3, "sku"] = df.loc[1, "sku"]
    return df


def gen_ventas(cliente_ids: list[str], producto_ids: list[str]) -> pd.DataFrame:
    rows = []
    today = datetime.now().date()
    for i in range(1, N_VENTAS + 1):
        cliente = random.choice(cliente_ids + ["C999"])  # cliente inexistente
        producto = random.choice(producto_ids + ["P999"])  # producto inexistente
        cantidad = 0 if _maybe(0.05) else random.randint(1, 10)  # cantidad cero
        precio_unitario = round(random.uniform(5, 2000), 2)
        total = round(cantidad * precio_unitario, 2)
        if _maybe(0.08):  # total mal calculado
            total = round(total + random.uniform(1, 100), 2)
        fecha_venta = fake.date_between("-1y", "today")
        if _maybe(0.05):  # fecha futura
            fecha_venta = today + timedelta(days=random.randint(5, 60))
        rows.append(
            {
                "venta_id": f"V{i:04d}",
                "cliente_id": cliente,
                "producto_id": producto,
                "fecha_venta": fecha_venta.isoformat(),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "total": total,
                "canal": "" if _maybe(0.07) else random.choice(CANALES),  # canal vacío
                "sucursal": random.choice(SUCURSALES),
                "vendedor": fake.name(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    proveedores = gen_proveedores()
    clientes = gen_clientes()
    productos = gen_productos(proveedores["proveedor_id"].tolist())
    ventas = gen_ventas(clientes["cliente_id"].tolist(), productos["producto_id"].tolist())

    for name, df in {
        "clientes": clientes,
        "productos": productos,
        "ventas": ventas,
        "proveedores": proveedores,
    }.items():
        path = OUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        print(f"  [OK] {name}.csv -> {len(df)} filas, {df.shape[1]} columnas  ({path})")

    print("\nDatasets sinteticos generados con errores controlados.")


if __name__ == "__main__":
    print("Generando datasets sinteticos de DataGov Agent...\n")
    main()

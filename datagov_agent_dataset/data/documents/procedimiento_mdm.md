# Procedimiento MDM para Datos Maestros

## Objetivo
Definir el proceso para identificar, consolidar y mantener datos maestros confiables.

## Entidades maestras
- Cliente
- Producto
- Proveedor
- Sucursal

## Golden Record
El golden record es la versión consolidada y más confiable de una entidad maestra.

## Criterios de duplicidad
Clientes:
- Coincidencia exacta de DNI.
- Coincidencia de correo.
- Nombre y apellido similares con teléfono igual.

Productos:
- SKU exacto.
- Nombre similar, misma marca y categoría.

Proveedores:
- RUC exacto.
- Razón social similar con teléfono o correo igual.

## Aprobación
La consolidación de registros maestros debe ser revisada por el Data Steward y aprobada por el Data Owner.

# Diccionario de Datos — Datasets Sintéticos

## Tabla `clientes`
| Campo | Tipo | Descripción | Clasificación |
| ----- | ---- | ----------- | ------------- |
| cliente_id | string | Identificador único del cliente | dato maestro |
| nombre | string | Nombre del cliente | dato personal |
| apellido | string | Apellido del cliente | dato personal |
| dni | string | Documento de identidad (8 dígitos) | dato personal |
| ruc | string | RUC del cliente (opcional) | dato personal |
| correo | string | Correo electrónico | dato personal |
| telefono | string | Teléfono de contacto | dato personal |
| direccion | string | Dirección física | dato personal |
| distrito | string | Distrito | dato operativo |
| pais | string | País (a normalizar) | dato operativo |
| fecha_registro | date | Fecha de alta del cliente | dato operativo |
| estado_cliente | string | Estado (activo/inactivo) | dato operativo |
| segmento | string | Segmento comercial | dato operativo |

**Errores inyectados:** DNI duplicado, DNI corto, correos inválidos, teléfonos vacíos,
país inconsistente (Perú/Peru/PE), clientes duplicados, segmento vacío.

## Tabla `productos`
| Campo | Tipo | Descripción | Clasificación |
| ----- | ---- | ----------- | ------------- |
| producto_id | string | Identificador único del producto | dato maestro |
| sku | string | Código único de inventario | dato maestro |
| nombre_producto | string | Nombre del producto | dato operativo |
| categoria | string | Categoría comercial | dato operativo |
| marca | string | Marca | dato operativo |
| precio | float | Precio | dato financiero |
| moneda | string | Moneda (PEN/USD) | dato operativo |
| estado_producto | string | Estado | dato operativo |
| fecha_alta | date | Fecha de alta | dato operativo |
| proveedor_id | string | FK a proveedores | dato maestro |

**Errores inyectados:** SKU duplicado, precio negativo, moneda vacía, categorías inconsistentes,
producto sin proveedor, fecha futura.

## Tabla `ventas`
| Campo | Tipo | Descripción | Clasificación |
| ----- | ---- | ----------- | ------------- |
| venta_id | string | Identificador único de la venta | dato maestro |
| cliente_id | string | FK a clientes | dato maestro |
| producto_id | string | FK a productos | dato maestro |
| fecha_venta | date | Fecha de la venta | dato operativo |
| cantidad | int | Unidades vendidas | dato operativo |
| precio_unitario | float | Precio unitario | dato financiero |
| total | float | Importe total (cantidad × precio_unitario) | dato financiero |
| canal | string | Canal de venta | dato operativo |
| sucursal | string | Sucursal | dato operativo |
| vendedor | string | Vendedor | dato personal |

**Errores inyectados:** cliente/producto inexistente, total mal calculado, cantidad cero,
fecha futura, canal vacío.

## Tabla `proveedores`
| Campo | Tipo | Descripción | Clasificación |
| ----- | ---- | ----------- | ------------- |
| proveedor_id | string | Identificador único del proveedor | dato maestro |
| ruc | string | RUC (11 dígitos) | dato personal |
| razon_social | string | Razón social | dato operativo |
| correo | string | Correo de contacto | dato personal |
| telefono | string | Teléfono | dato personal |
| pais | string | País | dato operativo |
| estado | string | Estado | dato operativo |

**Errores inyectados:** RUC duplicado, RUC inválido, proveedor sin correo, país inconsistente.

## Relaciones (integridad referencial)
- `ventas.cliente_id` → `clientes.cliente_id`
- `ventas.producto_id` → `productos.producto_id`
- `productos.proveedor_id` → `proveedores.proveedor_id`

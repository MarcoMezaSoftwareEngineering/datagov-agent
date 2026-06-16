# Reglas de Negocio del Dominio Comercial

## 1. Clientes
- Todo cliente debe tener un `cliente_id` único y un `dni` válido (8 dígitos).
- El campo `segmento` es obligatorio para clientes activos.
- El `pais` debe registrarse según el catálogo estándar (por ejemplo, "Peru").
- El `correo` debe tener un formato válido para campañas comerciales.

## 2. Productos
- Todo producto debe tener un `sku` único y un `proveedor_id` válido.
- El `precio` debe ser mayor a cero y estar expresado en una `moneda` válida (PEN o USD).
- La `categoria` debe pertenecer al catálogo de categorías estandarizado.
- La `fecha_alta` no puede ser una fecha futura.

## 3. Ventas
- Cada venta referencia un `cliente_id` y un `producto_id` existentes.
- `total = cantidad × precio_unitario`; la `cantidad` debe ser mayor a cero.
- La `fecha_venta` no puede ser una fecha futura.
- El `canal` es obligatorio para el análisis comercial.

## 4. Proveedores
- Cada proveedor debe tener un `ruc` único y válido (11 dígitos).
- El `correo` del proveedor es obligatorio para la gestión de compras.
- El `pais` debe estar normalizado.

## 5. Indicadores comerciales
- Ticket promedio = total de ventas / número de ventas.
- Tasa de duplicados de clientes = duplicados detectados / total de clientes.
- Cobertura de catálogo = productos con proveedor válido / total de productos.

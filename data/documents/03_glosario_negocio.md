# Glosario de Negocio

Este glosario define los términos de negocio y su relación con los campos técnicos de los datos.

| Término de negocio | Definición | Campo técnico | Dominio |
| ------------------ | ---------- | ------------- | ------- |
| Cliente | Persona o empresa que adquiere productos | `cliente_id` | Clientes |
| Documento de identidad | DNI de 8 dígitos del cliente | `dni` | Clientes |
| RUC | Registro Único de Contribuyentes (11 dígitos) | `ruc` | Proveedores/Clientes |
| Correo de contacto | Email del cliente o proveedor | `correo` | Clientes/Proveedores |
| Segmento | Clasificación comercial del cliente | `segmento` | Clientes |
| Producto | Bien ofrecido en el catálogo | `producto_id` | Productos |
| SKU | Código único de inventario | `sku` | Productos |
| Categoría | Agrupación comercial del producto | `categoria` | Productos |
| Proveedor | Empresa que abastece productos | `proveedor_id` | Proveedores |
| Venta | Transacción comercial | `venta_id` | Ventas |
| Importe total | Monto total de una venta | `total` | Ventas |
| Canal | Medio por el cual se realiza la venta | `canal` | Ventas |

## Términos clave
- **Golden Record**: registro consolidado y confiable que representa la versión única de una
  entidad maestra (por ejemplo, un cliente sin duplicados).
- **Data Owner**: responsable de negocio de un dominio de datos.
- **Data Steward**: responsable operativo de la calidad y el catálogo de un dominio.
- **Dato maestro**: entidad de referencia compartida entre procesos (cliente, producto, proveedor).

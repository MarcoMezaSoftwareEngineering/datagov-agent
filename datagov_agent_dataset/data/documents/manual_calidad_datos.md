# Manual de Calidad de Datos

## Dimensiones
1. Completitud: porcentaje de campos obligatorios informados.
2. Validez: cumplimiento de formato, rango o catálogo.
3. Unicidad: ausencia de duplicados no permitidos.
4. Consistencia: coherencia entre campos relacionados.
5. Integridad: relación válida entre tablas.
6. Oportunidad: actualización dentro del plazo definido.

## Score de calidad
El score inicia en 100 puntos y se descuenta según severidad:
- Alta: -20 puntos
- Media: -10 puntos
- Baja: -5 puntos

## Reglas mínimas por dominio
Clientes: DNI válido, correo válido, teléfono informado, país normalizado.
Productos: SKU único, precio positivo, proveedor válido.
Ventas: cliente existente, producto existente, total consistente, fecha no futura.
Proveedores: RUC válido, razón social informada, correo de contacto.

# Política de Gobierno de Datos

## 1. Propósito
Esta política establece el marco de gobierno de datos de la organización con el fin de garantizar
que los datos sean confiables, seguros, consistentes y aptos para la toma de decisiones. Aplica a
todos los dominios de datos: clientes, productos, ventas y proveedores.

## 2. Alcance
La política aplica a todos los datos estructurados y no estructurados gestionados por la
organización, incluyendo datos maestros, transaccionales y de referencia.

## 3. Principios de gobierno
1. **Propiedad clara**: cada dominio de datos tiene un Data Owner responsable.
2. **Calidad por diseño**: las reglas de calidad se aplican desde la ingesta.
3. **Clasificación obligatoria**: todo dato debe clasificarse según su criticidad y sensibilidad.
4. **Mínimo privilegio**: el acceso a los datos se otorga según el rol y la necesidad.
5. **Trazabilidad**: los cambios sobre datos maestros deben quedar registrados.

## 4. Definición de dato crítico
Un dato se considera **crítico** cuando cumple al menos uno de estos criterios:
- Se utiliza en reportes regulatorios o financieros.
- Es un identificador maestro (por ejemplo `cliente_id`, `dni`, `ruc`, `sku`).
- Contiene datos personales o sensibles.
- Su error genera impacto directo en clientes o en ingresos.

Los datos críticos deben tener reglas de calidad obligatorias, un Data Owner asignado y
controles de acceso.

## 5. Clasificación de datos
- **Dato personal**: identifica a una persona (nombre, DNI, correo, teléfono, dirección).
- **Dato sensible**: subconjunto de datos personales con mayor riesgo.
- **Dato maestro**: entidades de referencia compartidas (cliente, producto, proveedor).
- **Dato operativo**: datos transaccionales del día a día.

## 6. Responsabilidades
El Comité de Gobierno de Datos aprueba esta política. Los Data Owners son responsables de la
calidad y clasificación en su dominio. Los Data Stewards ejecutan las reglas y monitorean la
calidad. Toda excepción debe ser aprobada por el Comité de Gobierno de Datos.

## 7. Revisión
Esta política se revisa anualmente o cuando exista un cambio normativo relevante.

# Arquitectura de Datos Demo

## Sistemas origen
- CRM Demo: clientes.
- ERP Demo: productos, proveedores y ventas.
- Maestro Sucursales: sucursales.

## Flujo sugerido
1. Extracción de archivos CSV.
2. Validación inicial.
3. Carga a zona raw.
4. Perfilamiento de calidad.
5. Reglas de limpieza.
6. Carga a zona curada.
7. Publicación para analítica.

## Modernización futura
El flujo puede migrarse a un Data Lake en AWS con almacenamiento tipo S3, procesamiento ETL y consumo analítico en un data warehouse cloud.

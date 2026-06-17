# Dataset para DataGov Agent

Este paquete contiene datos sintéticos y documentos de gobierno de datos para alimentar el proyecto DataGov Agent.

## Contenido

- `data/raw/clientes.csv`: clientes con errores de calidad controlados.
- `data/raw/productos.csv`: productos con SKUs duplicados, precios inválidos y proveedores inconsistentes.
- `data/raw/proveedores.csv`: proveedores con problemas de RUC y completitud.
- `data/raw/sucursales.csv`: catálogo de sucursales.
- `data/raw/ventas.csv`: ventas con integridad referencial rota, totales inconsistentes y fechas futuras.
- `data/raw/diccionario_datos.csv`: catálogo inicial de campos.
- `data/raw/reglas_calidad.csv`: reglas mínimas de calidad.
- `data/documents/`: documentos markdown para alimentar el RAG.
- `data/expected_outputs/known_issues_expected.json`: conteo esperado de problemas para validar el sistema.
- `sql/schema_legacy_demo.sql`: DDL legacy simulado.

## Cómo alimentar el sistema

1. Cargar los CSV desde `data/raw/`.
2. Cargar los documentos `.md` desde `data/documents/` al pipeline RAG.
3. Indexar los documentos en Milvus.
4. Ejecutar agentes de perfilamiento, calidad, MDM y RAG.
5. Comparar resultados con `known_issues_expected.json`.

## Datasets

- Clientes: 1210 registros
- Productos: 350 registros
- Proveedores: 100 registros
- Sucursales: 10 registros
- Ventas: 5000 registros

## Nota ética

Todos los datos son sintéticos. No contienen información personal real.

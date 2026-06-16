# Checklist de Migración a Data Warehouse Moderno

Lista de verificación para migrar de un esquema analítico tradicional a un data warehouse moderno
(simulado sobre una arquitectura tipo S3 + Glue + Redshift + Athena).

## 1. Preparación de datos
- [ ] Perfilamiento completo de las tablas a migrar.
- [ ] Score de calidad ≥ 80 o plan de remediación aprobado.
- [ ] Datos personales clasificados y con controles definidos.
- [ ] Duplicados de entidades maestras consolidados (golden records).

## 2. Modelado
- [ ] Definición de claves primarias y foráneas.
- [ ] Generación del diccionario de datos.
- [ ] DDL SQL del esquema destino revisado.
- [ ] Estrategia de particionamiento y distribución definida.

## 3. Integridad y calidad
- [ ] Reglas de integridad referencial validadas (clientes, productos, proveedores).
- [ ] Reglas de validez (DNI, RUC, correo) automatizadas.
- [ ] Pruebas de reconciliación origen vs destino.

## 4. Seguridad
- [ ] Enmascaramiento de datos personales en ambientes no productivos.
- [ ] Control de acceso por rol configurado.
- [ ] Auditoría de consultas habilitada.

## 5. Gobierno
- [ ] Catálogo de datos actualizado con owners y stewards.
- [ ] Lineage documentado.
- [ ] Tablero de calidad y monitoreo activo.

## 6. Cierre
- [ ] Validación de KPIs post-migración.
- [ ] Documentación técnica entregada.
- [ ] Plan de soporte y monitoreo definido.

# Manual de Calidad de Datos

## 1. Objetivo
Definir las dimensiones, métricas y reglas de calidad que se aplican a los datos de la
organización para asegurar su aptitud de uso.

## 2. Dimensiones de calidad
1. **Completitud**: ausencia de valores nulos o vacíos en campos obligatorios.
2. **Unicidad**: ausencia de duplicados en identificadores.
3. **Validez**: los valores cumplen el formato esperado (por ejemplo, DNI de 8 dígitos).
4. **Consistencia**: los valores son coherentes entre sí y entre tablas.
5. **Integridad referencial**: las claves foráneas existen en la tabla padre.
6. **Conformidad**: los valores se ajustan a catálogos estándar (país, moneda, categoría).
7. **Exactitud**: los valores reflejan la realidad (por ejemplo, total = cantidad × precio).
8. **Oportunidad**: los datos no contienen fechas futuras inválidas.

## 3. Reglas de calidad obligatorias
- **DNI**: debe ser obligatorio, tener exactamente 8 dígitos numéricos y ser único por cliente.
- **RUC**: debe tener 11 dígitos numéricos y ser único por proveedor.
- **Correo**: debe cumplir el formato `usuario@dominio.tld`.
- **Identificadores** (`cliente_id`, `producto_id`, `proveedor_id`, `sku`): obligatorios y únicos.
- **Integridad referencial**: `ventas.cliente_id` debe existir en `clientes`; `ventas.producto_id`
  en `productos`; `productos.proveedor_id` en `proveedores`.
- **Precios y totales**: no pueden ser negativos; `total = cantidad × precio_unitario`.
- **Fechas**: no pueden ser fechas futuras.

## 4. Score de calidad
El score de calidad de una tabla parte de 100 y se penaliza así:
- Campo crítico con nulos: −15
- Duplicados en identificador: −20
- Formato inválido: −10
- Integridad referencial rota: −20
- Campo sensible sin clasificación: −15
- Catálogo incompleto: −10

Un score menor a 65 implica riesgo **alto**; entre 65 y 79, riesgo **medio**; 80 o más, riesgo **bajo**.

## 5. Roles en la calidad
El **Data Steward** monitorea las reglas, reporta hallazgos y propone correcciones. El **Data Owner**
aprueba las reglas y prioriza la remediación. Los hallazgos críticos se escalan al Comité de
Gobierno de Datos.

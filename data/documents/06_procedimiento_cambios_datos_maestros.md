# Procedimiento de Cambios en Datos Maestros

## 1. Objetivo
Definir el flujo de aprobación y control para crear, modificar, fusionar o desactivar registros de
datos maestros (cliente, producto, proveedor).

## 2. Alcance
Aplica a las entidades maestras: **Cliente**, **Producto**, **Proveedor** y **Sucursal**.

## 3. ¿Quién aprueba los cambios sobre datos maestros?
- Los cambios rutinarios los **solicita el Data Steward** y los **aprueba el Data Owner** del dominio.
- Los cambios con impacto transversal (por ejemplo, fusión de clientes o cambio de reglas de
  matching) son **aprobados por el Comité de Gobierno de Datos**.
- Ningún cambio sobre un dato maestro se aplica sin aprobación registrada.

## 4. Flujo de cambio
1. **Solicitud**: el Data Steward registra la solicitud con justificación.
2. **Validación de calidad**: se verifican reglas de unicidad, validez e integridad.
3. **Detección de duplicados (MDM)**: se evalúa si el registro es duplicado.
4. **Propuesta de golden record**: para fusiones, se define el registro consolidado.
5. **Aprobación**: Data Owner (o Comité, según impacto).
6. **Ejecución y trazabilidad**: el cambio se aplica y se registra en la bitácora.

## 5. Reglas de consolidación (MDM)
- Coincidencia exacta por clave (DNI, RUC, SKU) implica duplicado de alta confianza.
- Similaridad alta de nombres más coincidencia de correo implica posible duplicado.
- El golden record se construye eligiendo, por campo, el valor más completo y frecuente.

## 6. Trazabilidad
Cada cambio debe registrar: solicitante, aprobador, fecha, motivo y valores antes/después.

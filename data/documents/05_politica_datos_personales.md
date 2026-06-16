# Política de Datos Personales

## 1. Propósito
Establecer los criterios y controles para el tratamiento de datos personales, minimizando el
riesgo para los titulares y la organización.

## 2. ¿Qué campos se consideran datos personales?
Se consideran datos personales todos aquellos que permiten identificar a una persona, en particular:
- **Nombre** y **apellido**.
- **DNI** (documento de identidad).
- **Correo electrónico**.
- **Teléfono**.
- **Dirección** y **distrito**.

Estos campos deben clasificarse como *dato personal* en el catálogo y tener un Data Owner asignado.

## 3. Criterios para clasificar un dato como sensible
Un dato personal se clasifica como **sensible** cuando su divulgación puede causar un daño mayor al
titular, por ejemplo datos de salud, datos financieros (números de cuenta o tarjeta) o datos
biométricos. En este proyecto, los identificadores como DNI y los datos de contacto se tratan con
controles reforzados por su potencial de identificación.

## 4. Controles aplicables a datos personales
1. **Clasificación obligatoria** en el catálogo de datos.
2. **Acceso restringido** según el principio de mínimo privilegio.
3. **Enmascaramiento** de los campos en ambientes de prueba.
4. **Registro de accesos** y auditoría de consultas.
5. **Reglas de calidad** que garanticen integridad (por ejemplo, DNI válido y único).
6. **Minimización**: no almacenar datos personales que no sean necesarios.

## 5. Responsabilidades
El Data Owner del dominio aprueba la clasificación y los controles. El Data Steward verifica que
los campos personales estén clasificados y que se apliquen los controles. El Custodio Técnico
implementa el enmascaramiento y el control de acceso.

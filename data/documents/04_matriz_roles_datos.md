# Matriz de Roles y Responsabilidades de Datos

## 1. Roles definidos

### Comité de Gobierno de Datos
- Aprueba políticas, estándares y excepciones.
- Prioriza iniciativas de gobierno y calidad.
- **Aprueba los cambios sobre datos maestros** que tengan impacto transversal.

### Data Owner (Propietario de Datos)
- Responsable de negocio de un dominio (clientes, productos, ventas, proveedores).
- Aprueba definiciones de negocio, reglas de calidad y clasificación de datos.
- Autoriza el acceso a los datos de su dominio.

### Data Steward (Administrador de Datos)
- Responsable operativo de la calidad y el catálogo de su dominio.
- Monitorea las reglas de calidad y reporta hallazgos.
- Mantiene el glosario de negocio y la documentación de metadatos.
- Propone y ejecuta la consolidación de duplicados (MDM).

### Custodio Técnico (TI)
- Implementa controles técnicos, respaldos y seguridad.
- Administra las plataformas de datos.

## 2. Matriz RACI (resumen)

| Actividad | Comité | Data Owner | Data Steward | Custodio TI |
| --------- | ------ | ---------- | ------------ | ----------- |
| Aprobar política de gobierno | A | C | C | I |
| Definir reglas de calidad | C | A | R | I |
| Clasificar datos personales | C | A | R | I |
| Aprobar cambios en datos maestros | A | R | C | I |
| Monitorear calidad | I | A | R | C |
| Implementar controles de seguridad | I | C | C | R |

(R = Responsable, A = Aprobador, C = Consultado, I = Informado)

## 3. Responsabilidades del Data Steward (detalle)
1. Ejecutar el perfilamiento periódico de los datos.
2. Documentar definiciones de negocio en el catálogo.
3. Detectar y reportar duplicados y proponer el golden record.
4. Verificar el cumplimiento de las reglas de calidad obligatorias.
5. Escalar al Data Owner los hallazgos de severidad alta.

# Configuración y límites

La configuración de arranque pertenece a variables `AMP_*`; los cambios de identidad y descripción se guardan en `instance_config` mediante la API autenticada. No se aceptan claves desconocidas desde `.env`.

## Roles

`root` completa la instalación y rota la credencial temporal. `sysadmin` administra configuración y backups; `secopsadmin` revisa usuarios y auditoría; `mlopsadmin` importa datasets, revisa su contenido y entrena modelos. Cada endpoint comprueba la capacidad declarada por el rol.

## Datos y modelos

Los CSV deben ser suministrados por el operador. La importación rechaza nombres de persona, empresa, RUC, cuentas, contactos y otros campos sensibles; limita tamaño y filas; valida fechas, duplicados y valores finitos. La revisión local no aprueba publicación. Los artefactos son JSON con checksum, sin `pickle`, y conservan `publication_status=NOT_APPROVED`.

Los scrapers y datos bronce permanecen en una distribución privada. El paquete público sólo puede contener datasets anonimizados revisados y pesos o artefactos expresamente aprobados.

# Geoportal de Emergencias

Geoportal web para registrar, localizar y coordinar alertas durante y después de terremotos. El prototipo está construido con Django, GeoDjango, Django REST Framework, PostgreSQL/PostGIS, Supabase Storage y Leaflet.

## Estado del proyecto

Actualmente están preparadas las **Fases 1 a 9**. Reportes, auditoría ampliada y despliegue quedan pendientes.

La Fase 2 incluye el modelo `usuarios.User`, autenticación por correo electrónico, roles, perfil, recuperación de contraseña, administración Django y un decorador inicial `role_required`. En desarrollo, los correos de recuperación se imprimen en consola mediante `EMAIL_BACKEND`.

La Fase 3 incluye el modelo espacial `alertas.Alert` en EPSG:4326, código público de seguimiento, estados y prioridades iniciales, formulario ciudadano, captura GPS con la API del navegador, confirmación y consulta pública del estado.

La Fase 4 incluye la aplicación `mapas`, el endpoint protegido `/mapa/api/alertas/` en GeoJSON, filtros por estado/prioridad/tipo y un mapa Leaflet con OpenStreetMap, leyenda, actualización sin recarga y agrupación de puntos. La capa no expone identificaciones, teléfonos ni evidencias.

Como adelanto cartográfico se crearon las 10 capas iniciales: OpenStreetMap, alertas, hospitales, refugios, equipos de rescate, vías, tramos bloqueados, edificaciones afectadas, zonas de emergencia y sectores administrativos. Las capas temáticas tienen modelos PostGIS en `infraestructura` y `rescates`, geometrías EPSG:4326, índices espaciales y administración GIS. Se publican por `/mapa/api/capas/?layer=<nombre>` y se activan desde el control de capas de Leaflet. Actualmente están vacías hasta cargar datos autorizados.

La Fase 5 incluye el panel operativo `/alertas/operaciones/`, listado priorizado, búsqueda, filtros por estado/prioridad/tipo/fecha, detalle, verificación, cambio de estado, cambio de prioridad, observaciones internas e historial auditado. El acceso está limitado a operadores, coordinadores y administradores.

La Fase 6 incluye equipos de rescate, asignaciones de equipos a alertas, estados de asignación, historial de seguimiento y registro protegido de víctimas. La información de víctimas no se expone en consultas públicas ni en las capas GeoJSON.

La Fase 7 incluye el catálogo protegido `/infraestructura/` para hospitales, refugios, vías, tramos bloqueados, edificaciones afectadas, zonas de emergencia y sectores administrativos. La carga y edición de geometrías se realiza inicialmente desde el administrador GIS de Django; el mapa consume sus capas mediante GeoJSON.

La Fase 8 incluye servicios PostGIS para hospitales/refugios más cercanos, equipos disponibles dentro de un radio, alertas próximas, vías bloqueadas cercanas y alertas contenidas en zonas de emergencia o sectores administrativos. Los endpoints protegidos son `/mapa/api/espacial/recursos-cercanos/`, `/mapa/api/espacial/alertas-cercanas/` y `/mapa/api/espacial/alertas-zona/`.

La Fase 9 incluye `services/supabase_storage.py`, validación de MIME y tamaño para audios/imágenes, rutas privadas de Storage, URLs firmadas desde backend, rate limiting básico del formulario público y ajustes de cookies/HTTPS para producción. Para activar cargas reales hay que crear el bucket `emergency-evidence` en Supabase Storage y completar las claves correspondientes en `.env`; ningún secreto se envía al navegador.

Las víctimas pueden asociarse de forma protegida a un hospital, refugio o lugar seguro alternativo. La validación impide asignar más de un destino simultáneamente; la migración `rescates.0003` agrega estas relaciones.

El mapa operativo principal `/mapa/` integra ahora el mapa base y todas las capas temáticas en una sola vista. Incluye control individual de capas, filtros globales por estado/prioridad/tipo/fecha/zona, indicadores superiores y un panel lateral con detalle seguro de la alerta, equipo asignado, recursos cercanos y zona de emergencia.

Para cargar datos ficticios de demostración alrededor de la zona urbana de El Empalme, ejecutar:

```powershell
.\.venv\Scripts\python.exe manage.py cargar_datos_demo
```

El comando es idempotente, usa registros identificados con `DEMO-*` y no elimina información existente.

La interfaz visual del mapa fue modernizada con Bootstrap 5, Bootstrap Icons y `static/css/geoportal.css`: barra superior institucional, tarjetas de indicadores, filtros en panel lateral, mapa central responsive, panel de contexto, iconos por recurso, popups organizados y paleta de prioridad crítica/alta/media/baja. No se modificó la lógica principal ni el esquema de datos.

## Arquitectura propuesta

- `config`: configuración Django, URLs, ASGI y WSGI.
- `usuarios`: usuario personalizado, roles, autenticación y permisos.
- `alertas`: alertas ciudadanas, estados, prioridades y seguimiento público.
- `rescates`: equipos, asignaciones, víctimas e historial operativo.
- `infraestructura`: hospitales, refugios, vías, edificaciones y zonas.
- `mapas`: endpoints GeoJSON, capas y consultas espaciales.
- `reportes`: indicadores y panel operativo.
- `services`: integraciones externas, especialmente Supabase Storage.

La base de datos será PostGIS en Supabase. Las geometrías se almacenarán en EPSG:4326 para captura y visualización web; los cálculos métricos se harán con transformaciones temporales a un CRS proyectado apropiado, como EPSG:32717 cuando aplique.

## Requisitos locales en Windows

- Python 3.11+ (el entorno actual usa Python 3.11.9).
- Git.
- Para PostGIS real: un proyecto Supabase con PostGIS habilitado.
- Para ejecutar GeoDjango con operaciones GDAL/GEOS en Windows: instalar una versión moderna de OSGeo4W o usar Docker. La instalación de estas librerías no se ejecuta automáticamente porque modifica el sistema y depende de la arquitectura instalada. La máquina revisada tiene GDAL 2.1.0, que no es compatible con Django 5.2.

## Instalación con PowerShell

Desde la carpeta del proyecto:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py runserver
```

### GDAL/GEOS/PROJ en Windows

Instalar OSGeo4W desde su instalador oficial y seleccionar, como mínimo, GDAL, GEOS y PROJ de la instalación de 64 bits. Después, abrir una nueva PowerShell y comprobar:

```powershell
gdalinfo --version
```

Si las DLL no están en el `PATH`, completar `.env` con rutas a DLL compatibles, por ejemplo `GDAL_LIBRARY_PATH=C:\\OSGeo4W\\bin\\gdalXXX.dll` y `GEOS_LIBRARY_PATH=C:\\OSGeo4W\\bin\\geos_c.dll`. El nombre exacto `gdalXXX.dll` depende de la versión instalada. No usar la instalación GDAL 2.1.0 detectada en esta máquina.

La configuración arranca con SQLite si `DB_HOST` no está definido. Esto permite validar la instalación sin inventar credenciales. Para usar Supabase, completar `.env` con los datos del panel de Supabase y ejecutar:

```powershell
python manage.py check
python manage.py migrate
```

## Datos de Supabase

En Supabase:

1. `Project Settings > Database`: obtener host, puerto, nombre de base y usuario de la sección de conexión. Para Django se recomienda empezar con la conexión directa o el pooler de sesión compatible con SSL.
2. `Project Settings > API`: obtener `Project URL` y `anon public key`.
3. La `service_role key` también se encuentra en `Project Settings > API`, pero se reservará para el backend y nunca se expondrá al navegador.
4. En `Database > Extensions`, habilitar `postgis`.

No guardar valores reales en Git ni incluir contraseñas en documentación.

## Verificación de la Fase 1

Última revisión del entorno:

- Python: 3.11.9.
- Git: 2.55.0; repositorio local inicializado, sin remoto configurado.
- Identidad Git: `user.name` y `user.email` todavía no están configurados.
- GDAL antiguo del sistema: 2.1.0 detectado inicialmente, incompatible con Django 5.2; no se usa.
- GEOS/PROJ del sistema: no se usan para evitar conflictos de DLL.
- Dependencias SIG locales: OSGeo4W instalado en `C:\\OSGeo4W` con GDAL 3.13.1, GEOS 3.14.1 y PROJ 9.8.1.
- Dependencias Python: instaladas y `pip check` no reporta errores.
- Compilación Python: correcta para `manage.py` y `config/`.
- Conexión Supabase: verificada mediante SSL con PostgreSQL 17.6 y PostGIS 3.3.7; el servidor reporta GEOS 3.14.1 y PROJ 9.7.1.
- Pooler Supabase: se usa el puerto `6543` y Psycopg tiene desactivadas las sentencias preparadas para compatibilidad con el pooler transaccional.
- `python manage.py check`: correcto.
- Pruebas `usuarios`: 3 tests correctos mediante `--keepdb`.
- Migraciones: aplicadas correctamente en Supabase.
- Fase 3: 7 pruebas de usuarios y alertas correctas; migración `alertas.0001_initial` aplicada en Supabase.
- Fase 4: 17 pruebas de usuarios, alertas y mapas correctas; migraciones de capas aplicadas en Supabase.
- Fase 5: 15 pruebas de usuarios, alertas y mapas correctas; migración `alertas.0002` aplicada en Supabase.
- Fase 6: 20 pruebas de usuarios, alertas, mapas y rescates correctas; migración `rescates.0002` aplicada en Supabase.
- Fase 7: 22 pruebas de usuarios, alertas, mapas, rescates e infraestructura correctas; sin cambios adicionales de esquema.
- Fase 8: 24 pruebas de usuarios, alertas, mapas, rescates e infraestructura correctas; consultas ejecutadas en PostGIS sin migraciones nuevas.
- Fase 9: 27 pruebas correctas; validación de archivos, rate limiting y adaptador Storage implementados. La carga real queda pendiente de configurar el bucket y las claves de Storage.

Configurar la identidad Git únicamente cuando se vaya a crear el primer commit:

```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@example.com"
```

## Plan por fases

1. Preparación: entorno, configuración, conexión y documentación.
2. Usuarios: usuario personalizado, roles, login, recuperación y permisos.
3. Alertas: modelo espacial, formulario público, GPS y seguimiento.
4. Mapa: Leaflet, GeoJSON, filtros y agrupación.
5. Operaciones: panel, filtros, cambios de estado, prioridad e historial.
6. Rescate: equipos, asignaciones, seguimiento y víctimas.
7. Infraestructura: hospitales, refugios, vías y zonas de emergencia.
8. Consultas espaciales: proximidad, zonas, distancias e índices GiST.
9. Archivos y seguridad: Storage, validaciones, auditoría y rate limiting.
10. Pruebas y despliegue: datos ficticios, documentación y producción.

## Modelo entidad-relación inicial

- `Usuario` 1:N `Alerta` (creador opcional).
- `Alerta` 1:N `Victima`.
- `Alerta` 1:N `AsignacionRescate`; `EquipoRescate` 1:N `AsignacionRescate`.
- `AsignacionRescate` 1:N `HistorialAsignacion`.
- `Alerta` 1:N `HistorialAlerta`.
- `Hospital`, `Refugio`, `EquipoRescate` y `Alerta` tienen geometría puntual.
- `Via`, `EdificacionAfectada` y `ZonaEmergencia` tienen geometrías lineales o poligonales.

Los archivos se registrarán con una ruta de Storage, no con credenciales en los modelos. La información sensible de víctimas solo será visible para roles autorizados.

## Riesgos y decisiones

- **GDAL/GEOS/PROJ en Windows:** son dependencias nativas; se documentará OSGeo4W o Docker antes de activar consultas geográficas avanzadas.
- **Disponibilidad de Supabase:** el MVP debe tener una configuración local reproducible, pero las migraciones finales se validarán contra PostGIS real.
- **Alertas públicas:** aplicar rate limiting, validación de archivos, consentimiento de ubicación y un código no predecible.
- **Información sensible:** separar permisos operativos de la consulta pública; nunca devolver identificación, teléfonos o evidencias en GeoJSON público.
- **Operación en emergencia:** registrar auditoría e historial; el sistema no sustituye los números oficiales de emergencia.

## Primer commit lógico sugerido

`chore: bootstrap Django GeoDjango project configuration`

Debe incluir únicamente la configuración inicial, documentación, dependencias y plantillas ambientales. Los secretos y `.env` quedan excluidos por `.gitignore`.

# EduConnect - Taller API Gateway con Kong

**Asignatura:** Integración de Sistemas (ISWZ3104)  
**Tipo de actividad:** prueba de concepto (PoC) reproducible en Docker Compose.  
**Repositorio de referencia:** https://github.com/RFelipeGR/Taller_EduConnect_Kong

## 1. Objetivo y alcance

La PoC implementa un punto único de entrada con **Kong Gateway OSS 3.9.5**, cuatro servicios REST simulados e independientes (Estudiantes, Matrículas, Pagos y Certificados), autenticación con API Key y límites de tráfico. Se utilizan datos estáticos ficticios, sin base de datos, interfaz de usuario ni reglas de autorización de negocio. No equivale a una instalación de producción.

## 2. Requisitos

- Docker Desktop o Docker Engine, con **Docker Compose v2** habilitado.
- Acceso a Internet **solo para descargar las imágenes Docker** en el primer arranque.
- Postman para importar y ejecutar la colección (opcional si se utiliza `curl`).
- Puerto TCP **8000** disponible en la máquina. El puerto se publica solo en `127.0.0.1`.

El código Python se ejecuta dentro de los contenedores `python:3.12-alpine`; no es necesario instalar Python localmente. No es necesario instalar Kong por separado.

## 3. Estructura

```text
Taller_EduConnect_Kong/
├── docker-compose.yml
├── kong.yml
├── mocks/
│   └── server.py
├── postman/
│   └── EduConnect_Pruebas_URLs_Completas.postman_collection.json
├── scripts/
│   └── probar_trafico.ps1
├── diagramas/
│   └── Arquitectura_EduConnect.png
├── documentos/
│   ├── Matriz_Evidencias_EduConnect.pdf
│   ├── Informe_Tecnico_EduConnect.pdf
│   └── Declaracion_IA_y_Fuentes.pdf
└── README.md
```

## 4. Iniciar el entorno

Desde una terminal ubicada en la carpeta que contiene `docker-compose.yml`, ejecutar:

```powershell
docker compose config
docker compose up -d
docker compose ps
```

Deben aparecer **cinco contenedores**: `kong`, `estudiantes`, `matriculas`, `pagos` y `certificados`. La primera descarga de imágenes puede requerir conexión a Internet. Los cuatro mocks se resuelven entre sí utilizando nombres de servicio de Docker, sin direcciones IP fijas.

Verificar la versión fijada de Kong y la configuración:

```powershell
docker compose exec kong kong version
docker compose exec kong kong config parse /kong/kong.yml
```

Se espera Kong **3.9.5**. Se fijó esa versión porque es la utilizada en las capturas del laboratorio y una etiqueta explícita evita cambios involuntarios entre computadoras. La configuración utiliza modo **DB-less** (`KONG_DATABASE=off`), cargando las rutas, el consumidor y los plugins desde `kong.yml`.

## 5. Direcciones y resultados de ejemplo

Todas las peticiones utilizan **GET** y el mismo puerto público de Kong. Las APIs simuladas no exponen sus propios puertos al equipo anfitrión.

| Recurso | URL local | Respuesta JSON representativa |
|---|---|---|
| Estudiantes | `http://localhost:8000/api/estudiantes` | `{"id":101,"nombre":"Ana Perez"}` |
| Matrículas | `http://localhost:8000/api/matriculas` | `{"id":501,"estudianteId":101,"estado":"ACTIVA"}` |
| Pagos | `http://localhost:8000/api/pagos` | `{"id":701,"matriculaId":501,"valor":150.0,"estado":"PENDIENTE"}` |
| Certificados | `http://localhost:8000/api/certificados` | `{"id":901,"estudianteId":101,"tipo":"Academico","estado":"EMITIDO"}` |

La API Key de **laboratorio ficticio** es:

```text
Encabezado: apikey
Valor: educonnect-demo-clave-2026
```

No reutilizar esta clave fuera del entorno local ni considerarla un secreto de producción.

Ejemplo desde PowerShell o una terminal con `curl`:

```powershell
curl.exe -i -H "apikey: educonnect-demo-clave-2026" "http://localhost:8000/api/estudiantes"
```

## 6. Colección Postman

1. Abrir Postman y seleccionar **Import**.
2. Importar `postman/EduConnect_Pruebas_URLs_Completas.postman_collection.json`.
3. Abrir la colección **EduConnect - Taller Kong Gateway (URLs completas)**.
4. Ejecutar individualmente las solicitudes de las carpetas *Rutas correctas*, *Autenticación*, *Errores* y *Límites de tráfico*.

Las solicitudes utilizan URLs completas `http://localhost:8000`. No dependen de variables de entorno de Postman. **No ejecutar toda la colección de forma indiscriminada**: los límites por consumidor comparten contadores y la prueba de backend caído requiere un cambio de estado deliberado.

## 7. Pruebas positivas y negativas

| Prueba | Preparación | Resultado esperado |
|---|---|---|
| Ruta válida | GET con API Key correcta | `200 OK` y JSON del mock |
| Sin API Key | Quitar el encabezado `apikey` | `401 Unauthorized` |
| API Key incorrecta | Usar `apikey: clave-incorrecta` | `401 Unauthorized` |
| Ruta no registrada | GET `/api/noexiste` | `404 Not Found` |
| Cuota general | Seis solicitudes válidas de Estudiantes en una misma ventana nueva de un minuto | Hasta cinco `200`, después `429 Too Many Requests` |
| Cuota de Certificados | Tres solicitudes válidas de Certificados en una misma ventana nueva de un minuto | Hasta dos `200`, después `429` |
| Backend Pagos detenido | Detener `pagos` y efectuar GET con clave válida | Error de upstream; en la evidencia del equipo se observó `502 Bad Gateway` |

Si una prueba con clave válida recibe `429` antes de lo previsto, probablemente se consumió cuota en la ventana vigente. Registrar la hora de inicio, esperar una **nueva ventana de control** y repetir la secuencia. No modificar los límites para forzar resultados.

### Pruebas de cuota reproducibles en PowerShell

El archivo `scripts/probar_trafico.ps1` realiza secuencias de seis o tres solicitudes y registra los códigos HTTP. Desde Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\probar_trafico.ps1 -Recurso estudiantes
powershell -ExecutionPolicy Bypass -File .\scripts\probar_trafico.ps1 -Recurso certificados
```

No ejecutar ambas inmediatamente si se quiere una secuencia limpia: las solicitudes y los contadores pueden cruzar ventanas temporales. Registrar los códigos realmente obtenidos, no presuponerlos.

### Simular fallo y recuperación de Pagos

Primero verificar que Pagos devuelve `200` con API Key correcta y cuota disponible. Después:

```powershell
docker compose stop pagos
# En Postman: GET http://localhost:8000/api/pagos con apikey válida.
# Registrar el código HTTP obtenido. Captura del equipo: 502.
docker compose start pagos
# Repetir GET /api/pagos y comprobar 200.
```

La disponibilidad del backend y la del gateway son independientes. Esta prueba **no demuestra alta disponibilidad**.

## 8. Registros y diagnóstico

```powershell
docker compose ps -a
docker compose logs --tail 100 kong
docker compose logs --tail 40 pagos
```

Si `kong.yml` cambia, se puede validar y reiniciar la instancia para recargar la configuración:

```powershell
docker compose exec kong kong config parse /kong/kong.yml
docker compose restart kong
```

Si el puerto 8000 está ocupado, liberar el puerto o modificar el mapeo en Compose, y actualizar las URLs de Postman y del README.

## 9. Detener el proyecto

Detener y eliminar los contenedores y su red, **sin borrar los archivos del proyecto**:

```powershell
docker compose down
```

Para volver a iniciarlo en otra sesión:

```powershell
docker compose up -d
```

No es necesario recompilar ni programar nuevamente los servicios. Si se cambia la máquina, debe mantenerse la estructura de carpetas y Docker debe estar operativo.

## 10. Limitaciones y mejoras para producción

- La PoC usa **una sola instancia** de Kong y contadores `policy: local`; no garantiza alta disponibilidad ni cuotas agregadas entre varias réplicas.
- Solo expone **HTTP local**. Para producción serían necesarios HTTPS/TLS, administración de secretos y configuraciones de red apropiadas.
- La API Key **identifica al consumidor**, pero no autoriza el acceso a un registro académico específico; esto requeriría reglas en el backend.
- Los datos son ficticios y estáticos; no existe persistencia, controles de identidad de usuarios finales ni observabilidad distribuida completa.
- Para múltiples gateways se podría evaluar Redis para contadores compartidos, comprobaciones de salud y un balanceador.

## 11. Documentación, evidencias y uso de IA

- `documentos/Matriz_Evidencias_EduConnect.pdf`: capturas originales y explicación de hipótesis, configuración, prueba, resultado y limitación.
- `documentos/Informe_Tecnico_EduConnect.pdf`: decisiones arquitectónicas, AuthN/AuthZ, límites y recomendaciones (máximo 2 páginas).
- `diagramas/Arquitectura_EduConnect.pdf`: diagrama de clientes, gateway, red interna y backends.
- `documentos/Declaracion_IA_y_Fuentes.pdf`: declaración del apoyo de IA y bibliografía.

Las evidencias corresponden a ejecuciones locales realizadas por el equipo y documentadas en capturas. La revisión de documentación y repositorio no sustituye una ejecución nueva en cada equipo.

## 12. Fuentes consultadas

1. Consigna: *Laboratorio de Arquitectura Aplicada: Implementación de un API Gateway para EduConnect*, Integración de Sistemas, ISWZ3104.
2. Kong, *DB-less mode*: https://developer.konghq.com/gateway/db-less-mode/
3. Kong, *Key Auth*: https://developer.konghq.com/plugins/key-auth/
4. Kong, *Rate Limiting*: https://developer.konghq.com/plugins/rate-limiting/
5. Kong, *Plugin scopes / precedence*: https://developer.konghq.com/gateway/entities/plugin/
6. Docker, *Compose*: https://docs.docker.com/compose/
7. Postman, *Collections*: https://learning.postman.com/docs/collections/collections-overview/
8. OWASP, *API Security*: https://owasp.org/API-Security/

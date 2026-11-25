# EduConnect — Taller de API Gateway con Kong

**Asignatura:** Integración de Sistemas (ISWZ3104)  
**Actividad:** Laboratorio de Arquitectura Aplicada — Implementación de un API Gateway para EduConnect  
**Repositorio:** https://github.com/RFelipeGR/Taller_EduConnect_Kong

## 1. Objetivo

Implementar una prueba de concepto (PoC) reproducible con **Kong Gateway OSS 3.9.5** y Docker Compose. Kong expone un único punto de entrada para cuatro servicios REST simulados: Estudiantes, Matrículas, Pagos y Certificados. La PoC incorpora autenticación por API Key, límites de consumo y pruebas de funcionamiento y fallos.

Los servicios responden con datos ficticios y estáticos. La solución está destinada a un entorno local y no incluye autorización de negocio, base de datos ni alta disponibilidad de producción.

## 2. Requisitos

- Docker Desktop o Docker Engine con Docker Compose v2 funcionando.
- Postman para importar la colección de pruebas, o `curl` como alternativa.
- Puerto TCP **8000** disponible en el equipo.
- Acceso a Internet en el primer arranque para descargar las imágenes de Docker, si todavía no están almacenadas localmente.
- PowerShell y `curl.exe` para utilizar el script de tráfico incluido (opcional; pensado para Windows).

No es necesario instalar Python ni Kong por separado: ambos se ejecutan dentro de contenedores. Los cuatro servicios simulados usan la imagen `python:3.12-alpine` y Kong utiliza la imagen `kong:3.9.5`.

## 3. Estructura del repositorio

```text
Taller_EduConnect_Kong/
├── README.md
├── docker-compose.yml
├── kong.yml
├── mocks/
│   └── server.py
├── postman/
│   └── EduConnect_Pruebas_URLs_Completas.postman_collection.json
├── probar_trafico.ps1
├── Diagrama/
│   └── Arquitectura de la PoC EduConnect.png
└── Documentos/
    ├── Informe_Tecnico_EduConnect.pdf
    ├── Matriz_Evidencias_EduConnect.pdf
    └── Declaracion_Uso_IA_y_Fuentes_EduConnect.pdf
```

Los PDF están organizados en `Documentos/` y el diagrama en `Diagrama/`. El script PowerShell `probar_trafico.ps1` está en la raíz; la colección de pruebas permanece en `postman/`.

## 4. Iniciar y comprobar el entorno

1. Descargar el repositorio desde **Code → Download ZIP** en GitHub y descomprimirlo, o clonarlo con Git.
2. Abrir Docker Desktop y comprobar que su motor esté en ejecución.
3. Abrir una terminal en la carpeta que contiene `docker-compose.yml`.
4. Ejecutar:

```powershell
docker compose config
docker compose up -d
docker compose ps
```

Deben aparecer cinco servicios: `kong`, `estudiantes`, `matriculas`, `pagos` y `certificados`. Si se acaban de crear los contenedores, comprobar que Kong haya terminado de iniciar antes de enviar solicitudes.

Verificar la versión de Kong y el archivo de configuración:

```powershell
docker compose exec kong kong version
docker compose exec kong kong config parse /kong/kong.yml
```

La versión fijada es **3.9.5**. Kong utiliza el modo **DB-less** (`KONG_DATABASE=off`) y lee la configuración declarativa desde `kong.yml`. Dentro de la red creada por Docker Compose, Kong alcanza los mocks mediante sus nombres de servicio (`estudiantes`, `matriculas`, `pagos`, `certificados`), sin direcciones IP fijas.

## 5. API y configuración de acceso

El punto de entrada local es `http://localhost:8000`. Los servicios simulados no publican directamente sus puertos al equipo anfitrión. Todas las rutas externas de la PoC utilizan el método **GET**.

| Servicio | URL pública | Respuesta JSON de ejemplo |
|---|---|---|
| Estudiantes | `http://localhost:8000/api/estudiantes` | `{"id":101,"nombre":"Ana Perez"}` |
| Matrículas | `http://localhost:8000/api/matriculas` | `{"id":501,"estudianteId":101,"estado":"ACTIVA"}` |
| Pagos | `http://localhost:8000/api/pagos` | `{"id":701,"matriculaId":501,"valor":150.0,"estado":"PENDIENTE"}` |
| Certificados | `http://localhost:8000/api/certificados` | `{"id":901,"estudianteId":101,"tipo":"Academico","estado":"EMITIDO"}` |

El consumidor ficticio configurado en `kong.yml` se llama `socio-externo`. Para las solicitudes autorizadas, enviar esta credencial de laboratorio en el **encabezado HTTP**:

```text
apikey: educonnect-demo-clave-2026
```

Ejemplo con `curl.exe` en Windows:

```powershell
curl.exe -i -H "apikey: educonnect-demo-clave-2026" "http://localhost:8000/api/estudiantes"
```

La clave es ficticia y se incluye únicamente para permitir pruebas reproducibles en el entorno local. No debe utilizarse como secreto real ni reutilizarse en producción.

## 6. Políticas de Kong

- **Key Authentication (`key-auth`)**: exige una API Key válida para acceder a las rutas registradas.
- **Rate Limiting general**: establece hasta **5 solicitudes por minuto** para el consumidor `socio-externo`, con contador local.
- **Rate Limiting de Certificados**: aplica una política más específica de **2 solicitudes por minuto** al mismo consumidor en la ruta `/api/certificados`.

Al superar el límite aplicable, Kong responde `429 Too Many Requests`. La política `local` contabiliza solicitudes en la instancia actual de Kong; no proporciona una cuota global compartida entre varios gateways.

## 7. Importar la colección Postman

1. Abrir Postman y seleccionar **Import**.
2. Importar `postman/EduConnect_Pruebas_URLs_Completas.postman_collection.json`.
3. Abrir la colección **EduConnect - Taller Kong Gateway (URLs completas)**.
4. Revisar las cuatro carpetas: *Rutas correctas*, *Autenticación*, *Errores* y *Límites de tráfico*.
5. Ejecutar las solicitudes individualmente, según las condiciones descritas en cada prueba.

Las URLs son completas y apuntan a `localhost:8000`; no requieren variables de entorno de Postman. **No ejecutar toda la colección indiscriminadamente:** las cuotas pueden afectar pruebas posteriores y el escenario de backend detenido necesita una preparación específica.

## 8. Pruebas y resultados esperados

| Prueba | Procedimiento | Resultado esperado |
|---|---|---|
| Acceso correcto | GET a una ruta existente con API Key válida | `200 OK` y JSON del servicio |
| Sin API Key | GET a una ruta existente sin encabezado `apikey` | `401 Unauthorized` |
| API Key incorrecta | GET con `apikey: clave-incorrecta` | `401 Unauthorized` |
| Ruta inexistente | GET `http://localhost:8000/api/noexiste` | `404 Not Found` |
| Cuota general | Seis GET válidos a Estudiantes dentro de una misma ventana nueva | Cinco `200` y luego `429`, si la cuota estaba libre |
| Cuota de Certificados | Tres GET válidos a Certificados dentro de una misma ventana nueva | Dos `200` y luego `429`, si la cuota estaba libre |
| Backend no disponible | Detener Pagos y hacer GET válido a `/api/pagos` | Error de comunicación con el backend; en las evidencias se observó `502 Bad Gateway` |
| Recuperación | Volver a iniciar Pagos y repetir GET | `200 OK` con cuota disponible |

Los contadores son temporales. Si una solicitud válida responde `429` antes de lo previsto, verificar las peticiones anteriores y comenzar una nueva ventana de un minuto. Registrar siempre el código realmente obtenido, sin modificar las reglas para forzar el resultado.

### 8.1. Reproducir los límites desde PowerShell

Desde la **raíz del repositorio**, ejecutar una prueba a la vez:

```powershell
powershell -ExecutionPolicy Bypass -File .\probar_trafico.ps1 -Recurso estudiantes
powershell -ExecutionPolicy Bypass -File .\probar_trafico.ps1 -Recurso certificados
```

El script registra fecha/hora de inicio y fin, y los códigos HTTP de seis solicitudes a Estudiantes o tres a Certificados. Para observar una secuencia limpia, esperar una nueva ventana de control antes de ejecutar cada prueba.

### 8.2. Simular un fallo del servicio Pagos

Con el entorno iniciado, comprobar primero que `/api/pagos` responde correctamente con una API Key válida. A continuación:

```powershell
docker compose stop pagos
```

En Postman, ejecutar `GET http://localhost:8000/api/pagos` con la clave válida y registrar el código de respuesta. En las capturas del laboratorio se observó **`502 Bad Gateway`**. Dependiendo de la condición y de la configuración, el código de error del backend podría variar.

Restaurar el servicio y comprobar su recuperación:

```powershell
docker compose start pagos
docker compose ps
```

Repetir el GET de Pagos con cuota disponible; se espera `200 OK`. **Dejar todos los servicios iniciados al finalizar las pruebas.**

## 9. Diagnóstico y registros

Si una solicitud falla inesperadamente, revisar los contenedores y los registros:

```powershell
docker compose ps -a
docker compose logs --tail 100 kong
docker compose logs --tail 40 pagos
```

Después de modificar `kong.yml`, validar la configuración y reiniciar Kong:

```powershell
docker compose exec kong kong config parse /kong/kong.yml
docker compose restart kong
```

Si el puerto 8000 ya está ocupado, liberar el puerto o adaptar el mapeo de Docker Compose y las URLs de las pruebas de forma consistente.

## 10. Detener y volver a iniciar el proyecto

Para detener y eliminar los contenedores y la red del proyecto sin borrar archivos fuente:

```powershell
docker compose down
```

Para iniciarlo posteriormente:

```powershell
docker compose up -d
```

## 11. Alcance y limitaciones

La PoC utiliza datos estáticos, HTTP local, una sola instancia de Kong y contadores locales. No implementa persistencia, autenticación de usuarios finales, autorización sobre matrículas o certificados específicos, monitoreo distribuido ni alta disponibilidad. **Una API Key válida identifica al consumidor, pero no demuestra que tenga permiso sobre cualquier recurso académico.** La autorización de negocio debe implementarse en cada servicio correspondiente.

Para una futura instalación de producción se recomienda habilitar HTTPS/TLS, proteger las credenciales, incorporar observabilidad y comprobaciones de salud, y diseñar redundancia de gateway. Si se necesitan cuotas coherentes entre varias instancias, puede evaluarse un almacenamiento compartido para contadores (por ejemplo, Redis).

## 12. Documentos incluidos

- [`Informe_Tecnico_EduConnect.pdf`](Documentos/Informe_Tecnico_EduConnect.pdf): decisiones arquitectónicas, autenticación frente a autorización, limitaciones y mejoras (máximo dos páginas).
- [`Matriz_Evidencias_EduConnect.pdf`](Documentos/Matriz_Evidencias_EduConnect.pdf): hipótesis, decisiones, procedimientos, resultados, limitaciones y capturas de las pruebas.
- [`Declaracion_Uso_IA_y_Fuentes_EduConnect.pdf`](Documentos/Declaracion_Uso_IA_y_Fuentes_EduConnect.pdf): declaración de uso de IA y fuentes técnicas.
- [`Arquitectura de la PoC EduConnect.png`](Diagrama/Arquitectura%20de%20la%20PoC%20EduConnect.png): diagrama del cliente, Kong, la red Docker y los cuatro backends.

## 13. Fuentes técnicas

1. Consigna de la asignatura: *Laboratorio de Arquitectura Aplicada: Implementación de un API Gateway para EduConnect*.
2. Kong Gateway — [DB-less mode](https://developer.konghq.com/gateway/db-less-mode/).
3. Kong Gateway — [Key Authentication](https://developer.konghq.com/plugins/key-auth/).
4. Kong Gateway — [Rate Limiting](https://developer.konghq.com/plugins/rate-limiting/).
5. Kong Gateway — [Plugins y ámbito de aplicación](https://developer.konghq.com/gateway/entities/plugin/).
6. Docker — [Docker Compose](https://docs.docker.com/compose/).
7. Postman — [Documentación de colecciones](https://learning.postman.com/docs/collections/collections-overview/).
8. OWASP — [API Security](https://owasp.org/API-Security/).

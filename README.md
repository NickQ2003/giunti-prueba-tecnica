# Extractor de cuestionarios

Aplicación para transformar cuestionarios en PDF, DOCX o XLSX en JSON estructurado. React presenta el formulario y FastAPI extrae el texto, consulta Gemini y valida el resultado con Pydantic. El servicio no utiliza base de datos ni guarda los documentos de forma permanente.

**Aplicación pública:** [https://giunti-questionnaires.onrender.com/](https://giunti-questionnaires.onrender.com/).

Render Free suspende el servicio después de un periodo de inactividad; la primera carga puede tardar aproximadamente un minuto mientras vuelve a iniciarse.

## Privacidad y alcance

- Usa exclusivamente cuestionarios inventados o de dominio público. No subas pruebas comerciales ni datos personales.
- El texto extraído se envía a Google Gemini. Consulta las condiciones de uso y privacidad del proveedor antes de utilizarlo; no se garantiza retención cero.
- El JSON requiere revisión humana: el modelo puede equivocarse o no detectar la estructura completa. El prompt indica que no invente contenido ni respuestas correctas, pero no puede garantizarlo.
- Los PDF deben contener texto seleccionable: no hay OCR. Los archivos cifrados, corruptos o sin texto producen un error.
- La vista previa de PDF se dibuja localmente en el navegador; la de DOCX y XLSX muestra texto extraído por el servidor, no una representación fiel del formato. La vista de texto se limita a 40.000 caracteres y lo indica cuando se recorta; el procesamiento posterior utiliza el texto completo dentro de los límites indicados abajo. No se consulta Gemini para la vista previa.
- Límite de archivo: 10 MB; texto extraído: 100.000 caracteres; PDF: 200 páginas; Excel: 50.000 celdas; contenido ZIP descomprimido: 50 MB. XLSX usa valores calculados almacenados: las fórmulas sin valor guardado pueden quedar vacías.
- La carga multipart es procesada por el servidor antes de la validación de tamaño del archivo. La aplicación no incorpora autenticación; para producción configura también límites de tamaño, tiempo y frecuencia en un proxy o plataforma.
- El límite básico es global por proceso, no por usuario: 20 solicitudes compartidas entre vista previa y procesamiento cada 60 segundos por defecto. Se reinicia al reiniciar el servicio y no se comparte entre procesos; no evita abuso distribuido. No se confía en cabeceras de IP proporcionadas por el cliente.
- El esquema original no define una estructura de pares para emparejamiento: las columnas se conservan, cuando es posible, en el enunciado y las alternativas. `respuesta_correcta` solo admite un entero, texto o `null`.

## Requisitos

- Docker y Docker Compose para la opción recomendada; o Python 3.12 y Node.js 22 para desarrollo sin contenedores.
- Clave de Google AI Studio con acceso al modelo configurado. Los modelos y cuotas gratuitas pueden cambiar según disponibilidad, región y cuenta. No subas la clave al repositorio.

## Inicio rápido con Docker

```bash
cp .env.example .env
# Edita .env y establece GEMINI_API_KEY.
docker compose up --build
```

Abre <http://localhost:8000>. La interfaz y la API se sirven desde el mismo contenedor. Para detenerlo, usa `Ctrl+C` y, si corresponde, `docker compose down`. La interfaz y el endpoint de salud arrancan sin clave, pero procesar documentos requiere una clave válida.

| Variable | Uso | Valor predeterminado |
| --- | --- | --- |
| `GEMINI_API_KEY` | Clave de Google AI Studio. | Vacío; necesaria para procesar. |
| `GEMINI_MODEL` | Modelo compatible con la API de Gemini. | `gemini-3.5-flash-lite` |
| `RATE_LIMIT_REQUESTS` | Máximo global de solicitudes por proceso y ventana. | `20` |
| `RATE_LIMIT_WINDOW_SECONDS` | Ventana del límite de solicitudes, en segundos. | `60` |
| `PORT` | Puerto HTTP dentro del contenedor, normalmente asignado por el hosting. | `8000` |

## Desarrollo sin Docker

En una terminal, desde la raíz:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.lock
export GEMINI_API_KEY='tu-clave-local'
cd backend
uvicorn app.main:app --reload --port 8000
```

En otra terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abre la URL mostrada por Vite. El servidor de desarrollo redirige `/api` a FastAPI. No pegues ni publiques claves en comandos compartidos, logs o capturas de pantalla.

## API

- `GET /api/health`: salud del proceso, sin comprobar Gemini.
- `GET /api/version`: SHA de Git informado por Render, o `null` fuera de Render.
- `POST /api/preview`: recibe un archivo en `file` y devuelve una vista de texto limitada y un indicador `truncated`, sin llamar a Gemini.
- `POST /api/process`: formulario `multipart/form-data` con campo `file`. Retorna directamente el cuestionario con `titulo`, `idioma`, `total_items` e `items`.
- `GET /docs`: documentación interactiva de FastAPI.

```bash
curl -F 'file=@examples/cuestionario_inventado.docx' http://localhost:8000/api/process
```

Los tipos admitidos son `escala_likert`, `seleccion_multiple`, `verdadero_falso`, `desarrollo` y `emparejamiento`. El backend calcula `total_items`. Se solicita al modelo detectar el idioma con códigos como `it`, `es` y `en`, o `und` si no puede determinarlo.

Los errores usan `{"error": {"codigo": "...", "mensaje": "...", "request_id": "..."}}`: `415` para formato no soportado, `413` para tamaño excedido, `422` para solicitudes o documentos inválidos, `429` para exceso de solicitudes, `502` para salida inválida del proveedor y `503` cuando no está configurado o disponible. Cada respuesta incluye `X-Request-ID` para correlación con logs sanitizados.

Las respuestas se validan para detectar números y valores de alternativas duplicados, campos vacíos y tipos o idiomas no admitidos. En selección múltiple y verdadero/falso, la respuesta correcta debe coincidir con una alternativa; se normaliza una etiqueta como `C.` a `C` solo si la coincidencia es inequívoca. El emparejamiento conserva respuestas compuestas. Estas reglas no demuestran que el proveedor haya extraído todo ni que la respuesta esté indicada en el documento.

La cabecera `X-Unmatched-Statements` cuenta enunciados que no se pudieron localizar en el texto extraído tras normalizar espacios y puntuación. Es una advertencia conservadora, no una verificación de veracidad: el formato puede causar falsos positivos y una coincidencia tampoco demuestra que la extracción sea correcta. La interfaz muestra el aviso sin modificar el JSON.

Antes de consultar Gemini se calculan pistas de español, inglés e italiano con expresiones regulares sobre palabras y terminaciones frecuentes. Se limita la influencia de repeticiones y, si la evidencia es escasa o ambigua, se usa `und`. Las puntuaciones son heurísticas, **no probabilidades calibradas**; se envían como contexto orientativo, no como una instrucción obligatoria. El modelo conserva la decisión final. Las cabeceras `X-Language-Hint` y `X-Language-Disagreement` permiten advertir discrepancias sin modificar el JSON: coincidir tampoco confirma el idioma, especialmente porque el modelo recibe la pista. Documentos cortos, mixtos o en otros idiomas pueden producir señales incorrectas; se recomienda revisión humana.

## Tests y calidad

```bash
cd backend
ruff check .
ruff format --check .
pytest -q
```

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build
```

Las pruebas automatizadas simulan Gemini y no requieren clave ni consumen cuota. Antes de entregar, realizar además una prueba real con un documento inventado y una clave válida.

`examples/cuestionario_inventado.docx` contiene un cuestionario ficticio. `examples/cuestionario_inventado.expected.json` es una salida de referencia revisada; el modelo puede devolver una representación distinta. `examples/generate_example.py` permite recrear el DOCX usando `python-docx`.

En [`examples/test_docs`](examples/test_docs/README.md) hay cinco cuestionarios inventados más complejos: PDF en inglés, DOCX en italiano, XLSX en español y dos casos bilingües. Su README explica las claves explícitas y los resultados observados sin presentarlos como garantizados.

## CI y despliegue

GitHub Actions ejecuta lint, tests y build de frontend y backend en cada pull request y push a `main`; también audita las dependencias Python de producción y las dependencias npm con severidad alta o superior, construye la imagen y comprueba la interfaz y `/api/health` por HTTP. La auditoría npm puede informar hallazgos moderados que no bloquean el pipeline. No se necesitan secretos para CI.

Para preparar Render:

1. Crear un servicio web desde este repositorio usando el Dockerfile o el Blueprint `render.yaml`; comprobar que la opción y el plan elegidos sigan disponibles.
2. Configurar `GEMINI_API_KEY` en el servicio y, opcionalmente, `GEMINI_MODEL`. No introducir la clave en el repositorio.
3. Desactivar el auto-deploy por push y guardar el deploy hook de Render como secreto de GitHub Actions llamado `RENDER_DEPLOY_HOOK`.
4. Tras un CI exitoso de un push a `main`, el workflow solicita a Render el commit validado y espera hasta 15 minutos a que `/api/version` exponga ese SHA, `/api/health` responda y la página principal cargue. Si falta el hook o no puede confirmar la versión, el workflow falla; un timeout no distingue por sí solo un fallo de Render de un despliegue lento. La variable opcional de GitHub Actions `PUBLIC_BASE_URL` permite cambiar la URL verificada.
5. Comprobar que la URL pública documentada arriba siga funcionando después de cada despliegue.

La disponibilidad, cuotas, arranque y condiciones del plan gratuito dependen de la plataforma. El hook fija el SHA validado, pero Render reconstruye la imagen y no reutiliza la imagen probada en CI. La sincronización automática del Blueprint es independiente del deploy por commit: desactívala si los cambios de `render.yaml` deben aplicarse únicamente de forma deliberada.

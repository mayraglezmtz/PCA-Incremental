# Reporte de Tests — PCA Incremental

## Descripción del Proyecto

Aplicación Django REST que recibe puntos de datos con 10 características numéricas (`f1`–`f10`), los almacena en base de datos y, cuando acumula 20 puntos no procesados, entrena un modelo **Incremental PCA** (scikit-learn) mediante una tarea asíncrona de Celery. Una vez entrenados, los puntos quedan "promovidos" con sus coordenadas PCA (`pca_x`, `pca_y`) y se genera una gráfica de dispersión.

### Modelo principal: `DataPoint` / `DataModel`

| Campo | Tipo | Descripción |
|---|---|---|
| `f1`–`f10` | FloatField | Características del punto de datos |
| `pca_x`, `pca_y` | FloatField (nullable) | Coordenadas tras pasar por el PCA |
| `promoted` | BooleanField | `True` si ya fue procesado por el PCA |
| `created_at` | DateTimeField | Fecha de creación (auto) |

### Endpoints REST

| Método | URL | Nombre |
|---|---|---|
| GET | `/datapoints/` | `datapoint-list` |
| POST | `/datapoints/create/` | `datapoint-create` |
| GET/PATCH/DELETE | `/datapoints/<pk>/` | `datapoint-detail` |
| GET | `/datapoints/<pk>/coords/` | `datapoint-coords` |

---

## Suite de Tests: `DataPointApiTests`

Archivo: `ipca_app/tests.py`  
Clase: `DataPointApiTests` (hereda de `APITestCase`)  
Total de tests: **10**

---

### Test 1 — `test_create_datapoint_returns_201_and_enqueues_training`

**Endpoint probado:** `POST /datapoints/create/`

**Qué hace:**
Envía un payload con los 10 campos numéricos válidos y verifica que la creación sea exitosa.

**Qué prueba:**
- La respuesta tiene código HTTP **201 Created**.
- Se creó exactamente **1 registro** en la base de datos.
- La tarea Celery `entrenar_pca_si_listo.delay()` fue invocada **una sola vez** (se usa `unittest.mock.patch` para no ejecutar Celery realmente).

---

### Test 2 — `test_create_datapoint_ignores_read_only_fields`

**Endpoint probado:** `POST /datapoints/create/`

**Qué hace:**
Envía el payload con campos de solo lectura incluidos: `promoted=True`, `pca_x=99.0`, `pca_y=100.0`.

**Qué prueba:**
- La respuesta sigue siendo **201 Created** (no falla por campos extra).
- El punto guardado en DB tiene `promoted=False` (el valor por defecto), ignorando el `True` enviado.
- `pca_x` y `pca_y` son `None`, ignorando los valores enviados.
- Confirma que `DataPointSerializer` aplica correctamente `read_only_fields`.

---

### Test 3 — `test_list_datapoints_returns_newest_first`

**Endpoint probado:** `GET /datapoints/`

**Qué hace:**
Crea dos puntos directamente en DB y manipula su `created_at` para que uno sea 1 minuto más antiguo que el otro.

**Qué prueba:**
- La respuesta tiene código HTTP **200 OK**.
- El primer elemento de la lista es el punto más **reciente**.
- El segundo elemento es el punto más **antiguo**.
- Confirma el ordenamiento `-created_at` de `DataPointListView`.

---

### Test 4 — `test_update_promoted_datapoint_returns_403`

**Endpoint probado:** `PATCH /datapoints/<pk>/`

**Qué hace:**
Crea un punto con `promoted=True` e intenta modificar el campo `f1`.

**Qué prueba:**
- La respuesta tiene código HTTP **403 Forbidden**.
- El valor de `f1` en DB **no cambió** (sigue siendo `1.0`).
- Confirma que `DataPointDetailView.update()` bloquea la edición de puntos ya promovidos al PCA.

---

### Test 5 — `test_delete_promoted_datapoint_returns_403`

**Endpoint probado:** `DELETE /datapoints/<pk>/`

**Qué hace:**
Crea un punto con `promoted=True` e intenta eliminarlo.

**Qué prueba:**
- La respuesta tiene código HTTP **403 Forbidden**.
- El registro **sigue existiendo** en la base de datos.
- Confirma que `DataPointDetailView.destroy()` bloquea el borrado de puntos ya promovidos.

---

### Test 6 — `test_update_unpromoted_datapoint_succeeds`

**Endpoint probado:** `PATCH /datapoints/<pk>/`

**Qué hace:**
Crea un punto con `promoted=False` (valor por defecto) e intenta modificar `f1` a `123.0`.

**Qué prueba:**
- La respuesta tiene código HTTP **200 OK**.
- El valor de `f1` en DB **se actualizó** a `123.0`.
- Confirma que puntos no promovidos sí pueden editarse libremente.

---

### Test 7 — `test_delete_unpromoted_datapoint_succeeds`

**Endpoint probado:** `DELETE /datapoints/<pk>/`

**Qué hace:**
Crea un punto con `promoted=False` e intenta eliminarlo.

**Qué prueba:**
- La respuesta tiene código HTTP **204 No Content**.
- El registro **ya no existe** en la base de datos.
- Confirma que puntos no promovidos pueden borrarse sin restricción.

---

### Test 8 — `test_coords_returns_400_for_unprocessed_datapoint`

**Endpoint probado:** `GET /datapoints/<pk>/coords/`

**Qué hace:**
Crea un punto con `promoted=False` (sin coordenadas PCA) y consulta sus coordenadas.

**Qué prueba:**
- La respuesta tiene código HTTP **400 Bad Request**.
- Confirma que `DataPointCoordsView` rechaza la consulta cuando el punto todavía no pasó por el PCA.

---

### Test 9 — `test_coords_returns_200_for_processed_datapoint`

**Endpoint probado:** `GET /datapoints/<pk>/coords/`

**Qué hace:**
Crea un punto con `promoted=True`, `pca_x=1.23` y `pca_y=4.56` y consulta sus coordenadas.

**Qué prueba:**
- La respuesta tiene código HTTP **200 OK**.
- El cuerpo de la respuesta contiene el `id` correcto del punto.
- `pca_x` devuelto es `1.23` y `pca_y` es `4.56`.
- Confirma que `DataPointCoordsView` devuelve las coordenadas correctas de puntos ya procesados.

---

### Test 10 — `test_coords_returns_404_for_missing_datapoint`

**Endpoint probado:** `GET /datapoints/99999/coords/`

**Qué hace:**
Consulta las coordenadas de un `pk` que no existe (`99999`).

**Qué prueba:**
- La respuesta tiene código HTTP **404 Not Found**.
- Confirma que `DataPointCoordsView` maneja correctamente la excepción `DataPoint.DoesNotExist`.

---

## Resumen por área funcional

| Área | Tests |
|---|---|
| Creación de DataPoint (`POST /create/`) | Test 1, Test 2 |
| Listado y ordenamiento (`GET /datapoints/`) | Test 3 |
| Protección de puntos promovidos (edición y borrado) | Test 4, Test 5 |
| Operaciones permitidas en puntos no promovidos | Test 6, Test 7 |
| Consulta de coordenadas PCA (`GET /coords/`) | Test 8, Test 9, Test 10 |

## Estrategia de mocking

Los tests que involucran la creación de DataPoints usan `unittest.mock.patch` sobre `ipca_app.views.entrenar_pca_si_listo.delay` para **aislar la lógica HTTP de la tarea Celery**. Esto evita depender de un broker de mensajes (Redis/RabbitMQ) durante los tests y permite verificar únicamente que la tarea fue encolada, no que se ejecutó.

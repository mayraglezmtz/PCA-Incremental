# Proyecto iPCA con Django + DRF + Celery + Redis

## Alumnos
- Mayra Gonzalez Martinez A01769543
- Luis Manuel Delgadillo Guadarrama A01773721

## Descripcion breve
Este proyecto implementa un flujo de iPCA (Incremental PCA) para procesar datos por lotes desde una API REST.

En lugar de recalcular PCA con todo el dataset cada vez, iPCA actualiza el modelo de forma incremental con nuevos datos.

### Que es iPCA y como funciona
- iPCA es una version incremental de PCA (Principal Component Analysis).
- Reduce dimensionalidad proyectando datos de 10 variables a 2 componentes principales.
- En este proyecto, cada vez que se crean registros nuevos, Celery revisa si hay al menos 20 puntos pendientes.
- Si hay 20 o mas:
    1. Carga (o crea) el modelo iPCA.
    2. Entrena el modelo con ese lote.
    3. Guarda coordenadas PCA (`pca_x`, `pca_y`) en la base de datos.
    4. Marca esos puntos como `promoted=True`.
    5. Regenera una grafica en `media/pca_plot.png`.

### Aplicaciones (breve)
- Analisis exploratorio de datos en tiempo casi real.
- Monitoreo de lotes de datos en pipelines ETL.
- Visualizacion 2D de datasets de alta dimensionalidad.
- Deteccion visual de clusters o comportamiento anomalo.

## Stack y componentes
- Python 3.11 (Conda)
- Django + Django REST Framework
- Celery
- Redis (broker/result backend)
- SQLite (desarrollo)
- scikit-learn, numpy, matplotlib

## Estructura del proyecto
- `manage.py`: comandos de Django
- `ipca/settings.py`: configuracion general y Celery
- `ipca_app/views.py`: endpoints API
- `ipca_app/tasks.py`: entrenamiento incremental y grafica
- `seed_data.py`: carga de datos desde `data/pca.csv`
- `environment.yml`: dependencias reproducibles

## Instalacion en cualquier computadora

### 1. Requisitos previos
- Git
- Miniconda o Anaconda (o algun virtual environment)
- Docker Desktop (con engine corriendo)

### 2. Clonar el repositorio
```bash
git clone https://github.com/mayraglezmtz/PCA-Incremental.git
cd django-celery/ipca
```

### 3. Crear y activar entorno (con conda)
```bash
conda env create -f environment.yml
conda activate pca
```

### 3B. Alternativa sin conda (virtualenv / venv)
Si prefieres no usar conda, puedes correr el proyecto con `venv`.

1. Crear entorno virtual:
```bash
python -m venv .venv
```

2. Activar entorno:

Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

3. Instalar dependencias principales del proyecto:
```bash
python -m pip install --upgrade pip
pip install django djangorestframework celery redis numpy matplotlib scikit-learn pandas seaborn requests
```

4. Verificar Django instalado:
```bash
python -m django --version
```

### 4. Preparar base de datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Preparar Redis en Docker
Si el contenedor no existe todavia:
```bash
docker run -d -p 6379:6379 --name redis-pca redis:alpine
```

Si ya existe:
```bash
docker start redis-pca
```

## Como correr el proyecto
Abrir 3 terminales en la carpeta `ipca/` con el entorno activo (`pca` o `.venv`).

### Terminal 1 - Redis
```bash
docker start redis-pca
```

### Terminal 2 - Django
```bash
python manage.py runserver
```

### Terminal 3 - Celery Worker
```bash
celery -A ipca worker --loglevel=info --pool=solo
```

Nota: En Windows, `--pool=solo` es necesario.

## Cargar datos de ejemplo
Con Django y Celery ya corriendo, en otra terminal:
```bash
python seed_data.py
```

La API crea datapoints y Celery entrena iPCA por lotes de 20.

## Endpoints principales
- `GET /api/datapoints/`
- `POST /api/datapoints/create/`
- `GET /api/datapoints/<id>/`
- `PATCH /api/datapoints/<id>/`
- `DELETE /api/datapoints/<id>/`
- `GET /api/datapoints/<id>/coords/`

Vista principal:
- `GET /` (muestra resumen y grafica si existe)

## Ejecutar pruebas
```bash
python manage.py test ipca_app
```

Tambien puedes ejecutar todo el proyecto:
```bash
python manage.py test
```

## Solucion de problemas comunes

### 1. `No module named django`
Estas usando un Python distinto al entorno donde instalaste dependencias.

Solucion:
```bash
conda activate pca
python -m django --version
python manage.py test ipca_app
```

Si usas `venv`:
```powershell
.\.venv\Scripts\Activate.ps1
python -m django --version
python manage.py test ipca_app
```

### 2. `port is already allocated` en Redis (6379)
Ya hay otro contenedor usando ese puerto.

Verifica:
```bash
docker ps -a --filter "publish=6379"
```

### 3. Docker daemon no disponible
Error tipo: `failed to connect to the docker API...`

Solucion: abrir Docker Desktop y esperar a que el engine este activo.

## Notas finales
- Este proyecto esta configurado para desarrollo local.
- Si recreas el entorno, usa siempre `environment.yml` para mantener versiones compatibles.

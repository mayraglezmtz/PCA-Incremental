import os
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # sin pantalla, para que funcione en background pq celery no tiene acceso a la pantalla
import matplotlib.pyplot as plt

from celery import shared_task
from django.conf import settings

MODELO_PATH = os.path.join(settings.MEDIA_ROOT, 'ipca_model.pkl')
GRAFICA_PATH = os.path.join(settings.MEDIA_ROOT, 'pca_plot.png')


@shared_task
def entrenar_pca_si_listo():
    """
    Se llama cada vez que se crea un DataPoint.
    Solo actúa cuando hay 20+ puntos no promovidos.
    """
    # Importación aquí dentro para evitar imports circulares
    from ipca_app.models import DataPoint
    from sklearn.decomposition import IncrementalPCA

    no_promovidos = DataPoint.objects.filter(promoted=False)
    if no_promovidos.count() < 20:
        return "Nada que hacer, menos de 20 puntos"

    # Tomar exactamente 20
    batch = list(no_promovidos[:20])
    X = np.array([p.as_array() for p in batch])

    # Cargar modelo existente o crear uno nuevo
    if os.path.exists(MODELO_PATH):
        with open(MODELO_PATH, 'rb') as f:
            ipca = pickle.load(f)
    else:
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        ipca = IncrementalPCA(n_components=2)

    # Entrenamiento incremental con este batch
    ipca.partial_fit(X)

    # Guardar modelo actualizado
    with open(MODELO_PATH, 'wb') as f:
        pickle.dump(ipca, f)

    # Calcular coordenadas PCA para este batch y guardarlas en DB
    coords = ipca.transform(X)
    ids = [p.pk for p in batch]
    for punto, (px, py) in zip(batch, coords):
        punto.pca_x = float(px)
        punto.pca_y = float(py)
        punto.promoted = True
        punto.save()

    # Regenerar gráfica con TODOS los puntos promovidos
    _generar_grafica(ipca)

    return f"Entrenado con batch de {len(batch)} puntos. IDs: {ids}"


def _generar_grafica(ipca):
    """Genera y guarda la gráfica PCA de todos los puntos promovidos."""
    from ipca_app.models import DataPoint

    todos = DataPoint.objects.filter(promoted=True).exclude(pca_x=None)
    if not todos.exists():
        return

    xs = [p.pca_x for p in todos]
    ys = [p.pca_y for p in todos]
    ids = [p.pk for p in todos]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(xs, ys, alpha=0.7, color='steelblue', s=60)

    for i, txt in enumerate(ids):
        ax.annotate(f'#{txt}', (xs[i], ys[i]), fontsize=7,
                    xytext=(4, 4), textcoords='offset points')

    ax.set_xlabel('Componente Principal 1')
    ax.set_ylabel('Componente Principal 2')
    ax.set_title(f'PCA Incremental — {len(ids)} puntos')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(GRAFICA_PATH, dpi=120)
    plt.close(fig)
"""
seed_data.py — Lee pca.csv y manda los datos a la API de Django
Uso: python seed_data.py
Requiere: pip install requests (ya deberia estar en el entorno conda)
"""
import csv
import time
import requests

# ── Configuración ──────────────────────────────────────────────────
CSV_PATH = "data/pca.csv"       # ruta relativa desde la raiz del proyecto
API_URL  = "http://localhost:8000/api/datapoints/create/"
DELAY    = 0.1                  # segundos entre requests (no saturar)

# Las 10 columnas del CSV que se mapean a f1-f10
COLUMNAS = [
    "compactness",
    "circularity",
    "distance_circularity",
    "radius_ratio",
    "pr.axis_aspect_ratio",
    "max.length_aspect_ratio",
    "scatter_ratio",
    "elongatedness",
    "pr.axis_rectangularity",
    "max.length_rectangularity",
]

# ── Leer y enviar ──────────────────────────────────────────────────
def convertir_payload(fila):
    payload = {}

    for j, col in enumerate(COLUMNAS):
        valor = fila[col].strip()
        if valor == "":
            raise ValueError(f"Falta el valor de {col}")
        payload[f"f{j+1}"] = float(valor)

    return payload


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    total = len(filas)
    print(f"Filas encontradas: {total}")
    print(f"Enviando a {API_URL}\n")

    exitosos = 0
    errores   = 0
    omitidos  = 0

    for i, fila in enumerate(filas, start=1):
        try:
            payload = convertir_payload(fila)
        except ValueError as e:
            omitidos += 1
            print(f"  [{i}/{total}] - Fila omitida: {e}")
            continue

        try:
            resp = requests.post(API_URL, json=payload, timeout=5)

            if resp.status_code == 201:
                exitosos += 1
                # Cada 20 filas Celery deberia dispararse
                if exitosos % 20 == 0:
                    print(f"  [{i}/{total}] ✓ {exitosos} enviados — Celery deberia estar entrenando ahora...")
                else:
                    print(f"  [{i}/{total}] ✓ DataPoint creado (id={resp.json().get('id')})")
            else:
                errores += 1
                print(f"  [{i}/{total}] ✗ Error {resp.status_code}: {resp.text}")

        except requests.exceptions.ConnectionError:
            print("ERROR: No se puede conectar a Django. ¿Está corriendo en localhost:8000?")
            break
        except ValueError as e:
            errores += 1
            print(f"  [{i}/{total}] ✗ Valor inválido en fila {i}: {e}")

        time.sleep(DELAY)

    print(f"\nListo. Exitosos: {exitosos} | Errores: {errores} | Omitidos: {omitidos}")
    print("Abre http://localhost:8000 para ver la gráfica generada.")

if __name__ == "__main__":
    main()
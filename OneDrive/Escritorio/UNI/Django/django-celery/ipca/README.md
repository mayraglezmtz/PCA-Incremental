Cómo levantar el proyecto después

    conda env create -f environment.yml
    conda activate pca


Prender el contenedor de docker con redis
docker start <eebc9687a4e4>

Flujo
Terminal 1: docker start redis-ipca
Terminal 2: python manage.py runserver
Terminal 3: celery -A ipca worker -l INFO -P solo

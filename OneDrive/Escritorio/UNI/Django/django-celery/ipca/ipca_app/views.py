# Create your views here.
# ipca_app/views.py
import os
from django.conf import settings
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DataPoint
from .serializers import DataPointSerializer
from .tasks import entrenar_pca_si_listo


# ── Crear un DataPoint ──────────────────────────────────────────────
class DataPointCreateView(generics.CreateAPIView):
    serializer_class = DataPointSerializer

    def perform_create(self, serializer):
        serializer.save()
        # Disparar tarea de Celery en background (no bloquea)
        entrenar_pca_si_listo.delay()


# ── Listar todos los DataPoints ─────────────────────────────────────
class DataPointListView(generics.ListAPIView):
    queryset = DataPoint.objects.all().order_by('-created_at')
    serializer_class = DataPointSerializer


# ── Ver, editar o borrar un DataPoint ──────────────────────────────
class DataPointDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DataPoint.objects.all()
    serializer_class = DataPointSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.promoted:
            return Response(
                {'error': 'Este punto ya fue promovido al PCA y no se puede modificar.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.promoted:
            return Response(
                {'error': 'Este punto ya fue promovido al PCA y no se puede eliminar.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# ── Endpoint: coordenadas PCA de un punto ──────────────────────────
class DataPointCoordsView(APIView):
    def get(self, request, pk):
        try:
            punto = DataPoint.objects.get(pk=pk)
        except DataPoint.DoesNotExist:
            return Response({'error': 'No encontrado.'}, status=404)

        if not punto.promoted or punto.pca_x is None:
            return Response(
                {'error': 'Este punto aún no ha sido procesado por el PCA.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            'id': punto.pk,
            'pca_x': punto.pca_x,
            'pca_y': punto.pca_y,
        })


# ── Vista raíz: HTML con la gráfica ────────────────────────────────
def index(request):
    grafica_path = os.path.join(settings.MEDIA_ROOT, 'pca_plot.png')
    tiene_grafica = os.path.exists(grafica_path)
    total = DataPoint.objects.count()
    promovidos = DataPoint.objects.filter(promoted=True).count()

    return render(request, 'index.html', {
        'tiene_grafica': tiene_grafica,
        'total': total,
        'promovidos': promovidos,
        'pendientes': total - promovidos,
    })
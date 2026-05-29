# ipca_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('datapoints/',           views.DataPointListView.as_view(),   name='datapoint-list'),
    path('datapoints/create/',    views.DataPointCreateView.as_view(), name='datapoint-create'),
    path('datapoints/<int:pk>/',  views.DataPointDetailView.as_view(), name='datapoint-detail'),
    path('datapoints/<int:pk>/coords/', views.DataPointCoordsView.as_view(), name='datapoint-coords'),
]
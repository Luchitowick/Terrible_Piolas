from django.urls import path
from . import views

app_name = 'tienda'

urlpatterns = [
    path('', views.home, name='home'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('producto/<slug:slug>/', views.producto_detalle, name='producto_detalle'),
    path('categoria/<int:categoria_id>/', views.categoria_detalle, name='categoria_detalle'),
]
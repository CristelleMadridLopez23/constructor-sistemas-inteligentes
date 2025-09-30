from django.urls import path
from .views import ConstructorView

urlpatterns = [
    # Ruta raíz de la aplicación (que ahora es http://127.0.0.1:8000/)
    # Usamos ConstructorView.as_view() porque es una clase View.
    path('', ConstructorView.as_view(), name='constructor'),
]
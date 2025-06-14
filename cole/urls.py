"""
URL configuration for cole project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# aula_inteligente_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gestion_escolar import views
from gestion_escolar.views import CustomAuthToken, MLModelEndpoint

router = DefaultRouter()
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'profesores', views.ProfesorViewSet)
router.register(r'cursos', views.CursoViewSet)
router.register(r'materias', views.MateriaViewSet)
router.register(r'asignaciones', views.AsignacionCursoMateriaViewSet)
router.register(r'inscripciones', views.InscripcionViewSet)
router.register(r'notas', views.NotaViewSet)
router.register(r'asistencias', views.AsistenciaViewSet)
router.register(r'actividades', views.ActividadProyectoViewSet)
router.register(r'entregas', views.EntregaActividadViewSet)
router.register(r'participaciones', views.ParticipacionViewSet)
router.register(r'tutores', views.TutorViewSet)
router.register(r'alumnostutores', views.AlumnoTutorViewSet)
router.register(r'usuarios', views.UsuarioViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)), # Todos nuestros endpoints de la API
    path('api/login/', CustomAuthToken.as_view(), name='api_token_auth'), # Endpoint de login con token y rol
    path('api/mlmodel/', MLModelEndpoint.as_view(), name='ml_model_endpoint'), # Nuevo endpoint ML
]
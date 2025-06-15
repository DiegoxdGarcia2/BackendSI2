# cole/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# --- CORRECCIÓN ---
# Importamos 'views' para el router, y también importamos explícitamente
# cada una de las vistas personalizadas que vamos a usar en las rutas.
from gestion_escolar import views
from gestion_escolar.views import (
    CustomAuthToken, 
    MLModelEndpoint
)

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
    path('api/', include(router.urls)),
    path('api/login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/mlmodel/', MLModelEndpoint.as_view(), name='ml_model_endpoint'),
]
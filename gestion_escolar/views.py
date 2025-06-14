# gestion_escolar/views.py
from rest_framework import viewsets
from .models import (
    Alumno, Profesor, Curso, Materia, AsignacionCursoMateria, Inscripcion,
    Nota, Asistencia, ActividadProyecto, EntregaActividad, Participacion,
    Tutor, AlumnoTutor, Usuario
)
from .serializers import (
    AlumnoSerializer, ProfesorSerializer, CursoSerializer, MateriaSerializer,
    AsignacionCursoMateriaSerializer, InscripcionSerializer, NotaSerializer,
    AsistenciaSerializer, ActividadProyectoSerializer, EntregaActividadSerializer,
    ParticipacionSerializer, TutorSerializer, AlumnoTutorSerializer, UsuarioSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
import secrets
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modelo import LinearRegression, RandomForestClassifier, pd, categorizar_nota
from rest_framework.decorators import action
from django.db import models

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer

class AsignacionCursoMateriaViewSet(viewsets.ModelViewSet):
    queryset = AsignacionCursoMateria.objects.all()
    serializer_class = AsignacionCursoMateriaSerializer

class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.all()
    serializer_class = InscripcionSerializer

class NotaViewSet(viewsets.ModelViewSet):
    queryset = Nota.objects.all()
    serializer_class = NotaSerializer

class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer

class ActividadProyectoViewSet(viewsets.ModelViewSet):
    queryset = ActividadProyecto.objects.all()
    serializer_class = ActividadProyectoSerializer

class EntregaActividadViewSet(viewsets.ModelViewSet):
    queryset = EntregaActividad.objects.all()
    serializer_class = EntregaActividadSerializer

class ParticipacionViewSet(viewsets.ModelViewSet):
    queryset = Participacion.objects.all()
    serializer_class = ParticipacionSerializer

class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer

class AlumnoTutorViewSet(viewsets.ModelViewSet):
    queryset = AlumnoTutor.objects.all()
    serializer_class = AlumnoTutorSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    # Puedes añadir permisos aquí más adelante:
    # permission_classes = [permissions.IsAdminUser] # Ejemplo de solo admins

class CustomAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token = secrets.token_hex(32)
            return Response({'token': token, 'rol': user.rol.lower()})
        return Response({'error': 'Unable to log in with provided credentials.'}, status=400)

class MLModelEndpoint(APIView):
    def post(self, request, *args, **kwargs):
        from gestion_escolar.models import Alumno, Inscripcion, Nota, Asistencia, Participacion, Curso
        import modelo
        import pandas as pd
        
        # Permitir filtrar por curso o alumnos específicos
        curso_id = request.data.get('curso_id')
        alumnos_ids = request.data.get('alumnos_ids')  # lista de IDs
        
        if not curso_id and not alumnos_ids:
            return Response({'error': 'Debes enviar curso_id o alumnos_ids.'}, status=400)
        
        # Obtener alumnos
        if alumnos_ids:
            alumnos = Alumno.objects.filter(id__in=alumnos_ids)
        else:
            inscripciones = Inscripcion.objects.filter(curso_id=curso_id)
            alumnos = Alumno.objects.filter(id__in=inscripciones.values_list('alumno_id', flat=True))
        
        resultados = []
        for alumno in alumnos:
            # Asistencia: contar asistencias presentes sobre total
            inscripciones = Inscripcion.objects.filter(alumno=alumno)
            total_asistencias = Asistencia.objects.filter(inscripcion__in=inscripciones).count()
            presentes = Asistencia.objects.filter(inscripcion__in=inscripciones, estado='Presente').count()
            asistencia_pct = int((presentes / total_asistencias) * 100) if total_asistencias > 0 else 0
            # Participaciones: promedio de puntuacion (0-10) escalado a 100
            participaciones = Participacion.objects.filter(inscripcion__in=inscripciones)
            if participaciones.exists():
                participacion_avg = float(participaciones.aggregate(avg=models.Avg('puntuacion'))['avg'] or 0) * 10
            else:
                participacion_avg = 0
            # Evaluaciones: promedio de calificacion en Notas
            notas = Nota.objects.filter(inscripcion__in=inscripciones)
            if notas.exists():
                evaluaciones_avg = float(notas.aggregate(avg=models.Avg('calificacion'))['avg'] or 0)
            else:
                evaluaciones_avg = 0
            # Preparar dato para el modelo
            nuevo_dato = pd.DataFrame({
                'asistencia': [asistencia_pct],
                'participaciones': [participacion_avg],
                'evaluaciones': [evaluaciones_avg]
            })
            nota_predicha = modelo.modelo.predict(nuevo_dato)[0]
            rendimiento_predicho = modelo.modelo_clasificacion.predict(nuevo_dato)[0]
            recomendaciones = modelo.generar_recomendaciones(nuevo_dato)
            resultados.append({
                'alumno_id': alumno.id,
                'alumno': str(alumno),
                'asistencia': asistencia_pct,
                'participaciones': participacion_avg,
                'evaluaciones': evaluaciones_avg,
                'nota_final_predicha': float(nota_predicha),
                'rendimiento_predicho': rendimiento_predicho,
                'recomendaciones': recomendaciones
            })
        return Response(resultados)
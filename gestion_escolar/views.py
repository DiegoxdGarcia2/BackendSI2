# gestion_escolar/views.py
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.db.models import Avg, Count, Q, F
from django.http import HttpResponse
from django.core.management import call_command
import io

# --- CORRECCIÓN 1: Imports del modelo y librerías ---
# Importa los MODELOS YA CARGADOS y las funciones desde modelo.py
from modelo import modelo_regresion, modelo_clasificacion, generar_recomendaciones
# Importa pandas directamente en este archivo
import pandas as pd
# El resto de tus imports
import secrets
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


# ==============================================================================
# TUS VIEWSETS (No necesitan cambios)
# ==============================================================================

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer

# ... (el resto de tus ViewSets que ya estaban bien) ...

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


# ==============================================================================
# TU VISTA DE AUTENTICACIÓN (No necesita cambios)
# ==============================================================================
class CustomAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token = secrets.token_hex(32)
            # CORRECCIÓN menor: es más seguro usar user.id que el objeto completo
            return Response({'token': token, 'rol': user.rol.lower(), 'user_id': user.id})
        return Response({'error': 'Unable to log in with provided credentials.'}, status=400)


# ==============================================================================
# TU VISTA DEL MODELO DE ML (CORREGIDA Y OPTIMIZADA)
# ==============================================================================
class MLModelEndpoint(APIView):
    def post(self, request, *args, **kwargs):
        curso_id = request.data.get('curso_id')
        alumnos_ids = request.data.get('alumnos_ids')

        if not curso_id and not alumnos_ids:
            return Response({'error': 'Debes enviar curso_id o alumnos_ids.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- OPTIMIZACIÓN DE BASE DE DATOS ---
        # En lugar de hacer queries en un bucle (problema N+1),
        # usamos 'annotate' para calcular todo en una sola consulta grande.
        alumnos_queryset = Alumno.objects.all()
        if alumnos_ids:
            alumnos_queryset = alumnos_queryset.filter(id__in=alumnos_ids)
        else:
            alumnos_queryset = alumnos_queryset.filter(inscripcion__curso_id=curso_id).distinct()

        alumnos_data = alumnos_queryset.annotate(
            # Calcula el promedio de calificaciones de la tabla Nota
            evaluaciones_avg=Avg('inscripcion__nota__calificacion', default=0.0),
            # Calcula el promedio de puntuación de la tabla Participacion
            participacion_avg_raw=Avg('inscripcion__participacion__puntuacion', default=0.0),
            # Cuenta el total de registros de asistencia
            total_asistencias=Count('inscripcion__asistencia', distinct=True),
            # Cuenta solo las asistencias con estado 'Presente'
            presentes=Count('inscripcion__asistencia', filter=Q(inscripcion__asistencia__estado='Presente'), distinct=True)
        ).values(
            'id', 'nombre', 'apellido', 'evaluaciones_avg', 
            'participacion_avg_raw', 'total_asistencias', 'presentes'
        )

        resultados = []
        for alumno in alumnos_data:
            # Ahora los cálculos son en memoria, no en la base de datos
            asistencia_pct = int((alumno['presentes'] / alumno['total_asistencias']) * 100) if alumno['total_asistencias'] > 0 else 0
            participacion_avg = float(alumno['participacion_avg_raw']) * 10 # Escalado de 0-10 a 0-100
            evaluaciones_avg = float(alumno['evaluaciones_avg'])

            nuevo_dato = pd.DataFrame({
                'asistencia': [asistencia_pct],
                'participaciones': [participacion_avg],
                'evaluaciones': [evaluaciones_avg]
            })

            # --- CORRECCIÓN 2: Uso correcto de los modelos importados ---
            # Se usa 'modelo_regresion' en lugar de 'modelo.modelo'
            nota_predicha = modelo_regresion.predict(nuevo_dato)[0]
            rendimiento_predicho = modelo_clasificacion.predict(nuevo_dato)[0]
            recomendaciones = generar_recomendaciones(nuevo_dato)
            
            resultados.append({
                'alumno_id': alumno['id'],
                'alumno': f"{alumno['nombre']} {alumno['apellido']}",
                'asistencia': asistencia_pct,
                'participaciones': round(participacion_avg, 2),
                'evaluaciones': round(evaluaciones_avg, 2),
                'nota_final_predicha': round(float(nota_predicha), 2),
                'rendimiento_predicho': rendimiento_predicho,
                'recomendaciones': recomendaciones
            })
            

            return Response(resultados, status=status.HTTP_200_OK)
    
    # ==============================================================================
    # ENDPOINT PARA POBLAR LA BASE DE DATOS DESDE UN ENDPOINT
    # ==============================================================================
    class PopulateDatabaseView(APIView):
        def get(self, request, *args, **kwargs):
            # Mensaje de advertencia (puedes usar print o logging si no hay self.stdout)
            print('¡ADVERTENCIA! Se ha activado la población de la base de datos desde un endpoint.')
            
            # Usamos un buffer para capturar la salida del comando
            buffer = io.StringIO()
            
            try:
                # Ejecutamos el comando de población de datos internamente
                call_command('populate_db', 
                             '--delete_old_data', 
                             '--start_year', '2022', 
                             '--end_year', '2025', 
                             '--num_alumnos', '500', 
                             '--num_profesores', '50', 
                             '--num_tutores', '200', 
                             '--alumnos_per_course_min', '20', 
                             '--alumnos_per_course_max', '30',
                             stdout=buffer)
                
                # Devolvemos la salida del comando en la respuesta
                log_output = buffer.getvalue()
                return HttpResponse(f"<pre>Población de base de datos iniciada y completada con éxito:\n\n{log_output}</pre>", content_type="text/html")
    
            except Exception as e:
                log_output = buffer.getvalue()
                return HttpResponse(f"<pre>Error durante la población de la base de datos:\n\n{log_output}\n\nError: {e}</pre>", status=500, content_type="text/html")
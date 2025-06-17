# gestion_escolar/management/commands/populate_db.py
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password

from faker import Faker
import pandas as pd
import numpy as np

# Importa tus modelos de Django
from gestion_escolar.models import (
    Alumno, Profesor, Curso, Materia, AsignacionCursoMateria, Inscripcion,
    Nota, Asistencia, ActividadProyecto, EntregaActividad, Participacion,
    Tutor, AlumnoTutor, Usuario
)

class Command(BaseCommand):
    help = 'Popula la base de datos con datos sintéticos para el sistema escolar cubriendo múltiples años académicos y con más coherencia.'

    def add_arguments(self, parser):
        parser.add_argument('--num_alumnos', type=int, default=100, help='Número de alumnos a crear.')
        parser.add_argument('--num_profesores', type=int, default=30, help='Número de profesores a crear.')
        parser.add_argument('--num_tutores', type=int, default=80, help='Número de tutores a crear.')
        parser.add_argument('--start_year', type=int, default=2022, help='Año académico de inicio.')
        parser.add_argument('--end_year', type=int, default=date.today().year, help='Año académico de fin.')
        parser.add_argument('--delete_old_data', action='store_true', help='Elimina los datos existentes antes de poblar.')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if kwargs['delete_old_data']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            self._delete_all_data()
            self.stdout.write(self.style.SUCCESS('Datos existentes eliminados.'))

        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando población de datos...'))
        
        fake = Faker('es_ES')
        
        # --- Creación de Entidades Base (Optimizada) ---
        self._populate_base_entities(fake, kwargs)

        # --- Creación de Datos Académicos Anuales ---
        for anio in range(kwargs['start_year'], kwargs['end_year'] + 1):
            self.stdout.write(self.style.MIGRATE_HEADING(f'Poblando datos para el año académico: {anio}...'))
            self._populate_academic_year_data(fake, anio)

        self.stdout.write(self.style.SUCCESS('¡Población de datos completada exitosamente!'))

    def _delete_all_data(self):
        # El orden de eliminación importa por las dependencias
        for model in [Usuario, AlumnoTutor, Participacion, EntregaActividad, ActividadProyecto, Asistencia, Nota, Inscripcion, AsignacionCursoMateria, Materia, Curso, Profesor, Tutor, Alumno]:
            model.objects.all().delete()
        self.stdout.write(self.style.WARNING('¡Cuidado! Se han eliminado todos los datos de la base de datos.'))

    def _populate_base_entities(self, fake, kwargs):
        num_alumnos = kwargs['num_alumnos']
        num_profesores = kwargs['num_profesores']
        num_tutores = kwargs['num_tutores']

        # Alumnos
        self.stdout.write('Creando Alumnos...')
        alumnos = [Alumno(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(num_alumnos)]
        Alumno.objects.bulk_create(alumnos)
        self.stdout.write(self.style.SUCCESS(f'{num_alumnos} Alumnos creados.'))

        # Profesores
        self.stdout.write('Creando Profesores...')
        profesores = [Profesor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email(), fecha_contratacion=fake.date_between(start_date='-15y')) for _ in range(num_profesores)]
        Profesor.objects.bulk_create(profesores)
        self.stdout.write(self.style.SUCCESS(f'{num_profesores} Profesores creados.'))

        # Tutores
        self.stdout.write('Creando Tutores...')
        tutores = [Tutor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(num_tutores)]
        Tutor.objects.bulk_create(tutores)
        self.stdout.write(self.style.SUCCESS(f'{num_tutores} Tutores creados.'))

        # Cursos
        self.stdout.write('Creando Cursos...')
        cursos_data = {'Preescolar': ['Pre-Kinder', 'Kinder'], 'Primaria': [f'{i}mo de Primaria' for i in range(1, 7)], 'Secundaria': [f'{i}ro de Secundaria' for i in range(1, 7)]}
        cursos_a_crear = [Curso(nombre_curso=nombre, nivel_educativo=nivel) for nivel, nombres in cursos_data.items() for nombre in nombres]
        Curso.objects.bulk_create(cursos_a_crear)
        self.stdout.write(self.style.SUCCESS(f'{len(cursos_a_crear)} Cursos creados.'))
        
        # Materias
        self.stdout.write('Creando Materias...')
        materias_por_nivel = {'Preescolar': ['Lenguaje Pre', 'Matemáticas Pre'], 'Primaria': ['Matemáticas', 'Lenguaje', 'Ciencias Naturales'], 'Secundaria': ['Matemáticas', 'Literatura', 'Historia', 'Física', 'Química']}
        materias_a_crear = [Materia(nombre_materia=nombre, descripcion=f"Materia de {nombre} para {nivel}") for nivel, nombres in materias_por_nivel.items() for nombre in nombres]
        Materia.objects.bulk_create(materias_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(materias_a_crear)} Materias creadas o aseguradas.'))

        # Usuario Admin
        if not Usuario.objects.filter(username='admin').exists():
            Usuario.objects.create(username='admin', password_hash=make_password('admin123'), rol='Admin', activo=True)
            self.stdout.write(self.style.SUCCESS('Usuario Admin creado.'))

    def _populate_academic_year_data(self, fake, anio):
        # Cargar entidades base en memoria para evitar queries repetidas
        alumnos = list(Alumno.objects.all())
        profesores = list(Profesor.objects.all())
        cursos = list(Curso.objects.all())
        materias = list(Materia.objects.all())

        # --- Generación Masiva de Relaciones ---
        asignaciones_a_crear = []
        for curso in cursos:
            materias_del_curso = random.sample(materias, k=random.randint(5, 8))
            for materia in materias_del_curso:
                asignaciones_a_crear.append(AsignacionCursoMateria(
                    curso=curso, materia=materia, profesor=random.choice(profesores),
                    anio_academico=anio, periodo='Año Completo'
                ))
        AsignacionCursoMateria.objects.bulk_create(asignaciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(asignaciones_a_crear)} Asignaciones creadas para {anio}.')

        inscripciones_a_crear = []
        alumnos_restantes = list(alumnos)
        for curso in cursos:
            num_alumnos_en_curso = min(len(alumnos_restantes), random.randint(20, 30))
            alumnos_para_este_curso = random.sample(alumnos_restantes, k=num_alumnos_en_curso)
            for alumno in alumnos_para_este_curso:
                inscripciones_a_crear.append(Inscripcion(
                    alumno=alumno, curso=curso, anio_academico=anio, periodo='Año Completo'
                ))
            alumnos_restantes = [a for a in alumnos_restantes if a not in alumnos_para_este_curso]
        Inscripcion.objects.bulk_create(inscripciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(inscripciones_a_crear)} Inscripciones creadas para {anio}.')

        # --- Generación Masiva de Datos Transaccionales ---
        self.stdout.write(f'  Generando datos transaccionales para {anio}...')
        notas_a_crear, asistencias_a_crear, participaciones_a_crear, entregas_a_crear = [], [], [], []
        
        # Obtenemos las inscripciones recién creadas para este año
        inscripciones_anio = Inscripcion.objects.filter(anio_academico=anio).select_related('alumno', 'curso')

        # --- Generación de Actividades por Materia y Profesor ---
        actividades_a_crear = []
        actividades_por_materia_profesor = {}
        for asignacion in AsignacionCursoMateria.objects.filter(anio_academico=anio):
            num_actividades = random.randint(2, 5)
            actividades = []
            for _ in range(num_actividades):
                fecha_asignacion = fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 10, 31))
                fecha_entrega_limite = fecha_asignacion + timedelta(days=random.randint(7, 30))
                actividad = ActividadProyecto(
                    materia=asignacion.materia,
                    profesor=asignacion.profesor,
                    titulo=f"{fake.word().capitalize()} - {asignacion.materia.nombre_materia}",
                    fecha_asignacion=fecha_asignacion,
                    descripcion=fake.sentence(),
                    fecha_entrega_limite=fecha_entrega_limite,
                    max_puntuacion=random.choice([10, 20, 50, 100]),
                    tipo_actividad=random.choice(['Tarea', 'Proyecto', 'Examen Corto', 'Investigación'])
                )
                actividades.append(actividad)
                actividades_a_crear.append(actividad)
            actividades_por_materia_profesor[(asignacion.materia.id, asignacion.profesor.id)] = actividades
        ActividadProyecto.objects.bulk_create(actividades_a_crear, batch_size=500)

        for inscripcion in inscripciones_anio:
            asignaciones_del_curso = AsignacionCursoMateria.objects.filter(curso=inscripcion.curso, anio_academico=anio)
            perfil = np.random.choice(['bajo', 'promedio', 'alto'], p=[0.2, 0.6, 0.2])
            if perfil == 'bajo':
                asistencia_presente = 0.7
            elif perfil == 'alto':
                asistencia_presente = 0.97
            else:
                asistencia_presente = 0.88
            for asignacion in asignaciones_del_curso:
                # Notas (más variabilidad y solapamiento)
                for _ in range(random.randint(3, 5)):
                    if perfil == 'bajo':
                        calificacion = round(np.clip(np.random.normal(45, 10), 0, 65), 2)
                        comentario_nota = fake.sentence(ext_word_list=['Debe estudiar más', 'Bajo rendimiento en la evaluación', 'No entregó tarea', 'Necesita refuerzo']) if random.random() < 0.6 else None
                    elif perfil == 'alto':
                        calificacion = round(np.clip(np.random.normal(90, 7), 70, 100), 2)
                        comentario_nota = fake.sentence(ext_word_list=['Excelente desempeño', 'Superó expectativas', 'Trabajo impecable', 'Participación destacada']) if random.random() < 0.7 else None
                    else:
                        calificacion = round(np.clip(np.random.normal(70, 10), 40, 90), 2)
                        comentario_nota = fake.sentence(ext_word_list=['Buen trabajo', 'Puede mejorar', 'Cumple con lo requerido']) if random.random() < 0.3 else None
                    notas_a_crear.append(Nota(
                        inscripcion=inscripcion,
                        materia=asignacion.materia,
                        profesor=asignacion.profesor,
                        calificacion=calificacion,
                        fecha_evaluacion=fake.date_between(start_date=date(anio, 1, 1), end_date=date(anio, 12, 31)),
                        tipo_evaluacion=random.choice(['Examen Parcial', 'Examen Final', 'Tarea', 'Proyecto']),
                        comentarios_profesor=comentario_nota
                    ))
                # Asistencia (correlacionada con perfil)
                fechas_asistencia_usadas = set()
                for _ in range(random.randint(20, 35)):
                    fecha_asistencia = fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 11, 30))
                    if fecha_asistencia not in fechas_asistencia_usadas:
                        fechas_asistencia_usadas.add(fecha_asistencia)
                        estado = np.random.choice(['Presente', 'Ausente', 'Tarde'], p=[asistencia_presente, 1-asistencia_presente-0.02, 0.02])
                        if estado == 'Ausente':
                            comentario_asistencia = fake.sentence(ext_word_list=['Falta sin justificar', 'Enfermedad', 'Problemas familiares', 'Ausencia reiterada']) if random.random() < 0.7 else None
                        elif estado == 'Tarde':
                            comentario_asistencia = fake.sentence(ext_word_list=['Llegó tarde', 'Retraso por tráfico', 'Retraso leve']) if random.random() < 0.5 else None
                        else:
                            comentario_asistencia = fake.sentence(ext_word_list=['Asistencia perfecta', 'Siempre puntual', 'Buen comportamiento']) if random.random() < 0.1 else None
                        asistencias_a_crear.append(Asistencia(
                            inscripcion=inscripcion,
                            materia=asignacion.materia,
                            fecha=fecha_asistencia,
                            estado=estado,
                            profesor=asignacion.profesor,
                            observaciones=comentario_asistencia
                        ))
                # Participación (correlacionada con perfil)
                fechas_participacion_usadas = set()
                for _ in range(random.randint(10, 20)):
                    fecha_participacion = fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 11, 30))
                    if fecha_participacion not in fechas_participacion_usadas:
                        fechas_participacion_usadas.add(fecha_participacion)
                        if perfil == 'bajo':
                            puntuacion = round(np.clip(np.random.normal(2, 1.5), 0, 5), 2)
                            comentario = fake.sentence(ext_word_list=['No participa', 'Muy callado', 'Debe mejorar su participación', 'No responde preguntas']) if random.random() < 0.5 else None
                        elif perfil == 'alto':
                            puntuacion = round(np.clip(np.random.normal(9, 1), 7, 9.99), 2)  # Cambiado 10 por 9.99
                            comentario = fake.sentence(ext_word_list=['Participa activamente', 'Excelente en debates', 'Hace preguntas relevantes', 'Lidera discusiones']) if random.random() < 0.7 else None
                        else:
                            puntuacion = round(np.clip(np.random.normal(6, 1.5), 3, 9.5), 2)  # Cambiado 9 por 9.5 para mayor seguridad
                            comentario = fake.sentence(ext_word_list=['Participa ocasionalmente', 'Podría participar más', 'A veces responde']) if random.random() < 0.3 else None
                        participaciones_a_crear.append(Participacion(
                            inscripcion=inscripcion,
                            materia=asignacion.materia,
                            fecha=fecha_participacion,
                            puntuacion=puntuacion,
                            comentarios=comentario,
                            profesor=asignacion.profesor
                        ))
                # Entregas de Actividades
                # --- Antes del bucle de entregas, inicializar el set de pares únicos ---
                entregas_usadas = set()
                num_entregas = random.randint(2, 5)
                for _ in range(num_entregas):
                    actividades_posibles = actividades_por_materia_profesor.get((asignacion.materia.id, asignacion.profesor.id), [])
                    if actividades_posibles:
                        actividad = random.choice(actividades_posibles)
                    else:
                        actividad = None
                    if actividad is None:
                        continue
                    par_entrega = (actividad.id, inscripcion.alumno.id)
                    if par_entrega in entregas_usadas:
                        continue  # Ya existe una entrega para este par
                    entregas_usadas.add(par_entrega)
                    estado_entrega = np.random.choice(['Entregado', 'Retrasado', 'No Entregado'], p=[0.7, 0.2, 0.1])
                    if estado_entrega == 'Entregado':
                        puntuacion_obtenida = round(np.clip(np.random.normal(8, 2), 5, 10), 2) if perfil != 'bajo' else round(np.clip(np.random.normal(5, 2), 0, 7), 2)
                        comentario_entrega = fake.sentence(ext_word_list=['Buen trabajo', 'Entregado a tiempo', 'Cumplió con los requisitos', 'Presentación clara']) if random.random() < 0.5 else None
                    elif estado_entrega == 'Retrasado':
                        puntuacion_obtenida = round(np.clip(np.random.normal(6, 2), 2, 8), 2)
                        comentario_entrega = fake.sentence(ext_word_list=['Entregado fuera de plazo', 'Debe mejorar la gestión del tiempo', 'Retraso justificado']) if random.random() < 0.7 else None
                    else:
                        puntuacion_obtenida = 0.0
                        comentario_entrega = fake.sentence(ext_word_list=['No entregó la actividad', 'Falta de entrega', 'Debe comunicarse con el profesor'])
                    entregas_a_crear.append(EntregaActividad(
                        actividad=actividad,
                        alumno=inscripcion.alumno,
                        fecha_entrega=fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 12, 15)),
                        puntuacion_obtenida=puntuacion_obtenida,
                        comentarios_profesor=comentario_entrega,
                        estado_entrega=estado_entrega
                    ))

        # Inserción masiva final
        self.stdout.write(f'  Insertando {len(notas_a_crear)} notas...')
        Nota.objects.bulk_create(notas_a_crear, batch_size=500)
        self.stdout.write(f'  Insertando {len(asistencias_a_crear)} asistencias...')
        Asistencia.objects.bulk_create(asistencias_a_crear, batch_size=500)
        self.stdout.write(f'  Insertando {len(participaciones_a_crear)} participaciones...')
        Participacion.objects.bulk_create(participaciones_a_crear, batch_size=500)
        self.stdout.write(f'  Insertando {len(entregas_a_crear)} entregas de actividades...')
        EntregaActividad.objects.bulk_create(entregas_a_crear, batch_size=500)
        
        self.stdout.write(self.style.SUCCESS(f'  Datos transaccionales para {anio} creados.'))
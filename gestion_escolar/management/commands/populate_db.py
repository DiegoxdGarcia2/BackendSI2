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
        parser.add_argument('--num_alumnos', type=int, default=100,
                            help='Número de alumnos a crear (base, se distribuirán en cursos).')
        parser.add_argument('--num_profesores', type=int, default=30,
                            help='Número de profesores a crear.')
        parser.add_argument('--num_tutores', type=int, default=80,
                            help='Número de tutores a crear.')
        parser.add_argument('--start_year', type=int, default=2022,
                            help='Año académico de inicio para la población de datos.')
        parser.add_argument('--end_year', type=int, default=date.today().year,
                            help='Año académico de fin para la población de datos.')
        parser.add_argument('--alumnos_per_course_min', type=int, default=20,
                            help='Número mínimo de alumnos por curso por año.')
        parser.add_argument('--alumnos_per_course_max', type=int, default=30,
                            help='Número máximo de alumnos por curso por año.')
        parser.add_argument('--delete_old_data', action='store_true',
                            help='Elimina los datos existentes antes de poblar.')

    def handle(self, *args, **kwargs):
        fake = Faker('es_ES')
        num_alumnos = kwargs['num_alumnos']
        num_profesores = kwargs['num_profesores']
        num_tutores = kwargs['num_tutores']
        start_year = kwargs['start_year']
        end_year = kwargs['end_year']
        alumnos_per_course_min = kwargs['alumnos_per_course_min']
        alumnos_per_course_max = kwargs['alumnos_per_course_max']
        delete_old_data = kwargs['delete_old_data']

        if delete_old_data:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            self._delete_all_data()
            self.stdout.write(self.style.SUCCESS('Datos existentes eliminados.'))

        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando población de datos...'))

        with transaction.atomic():
            self._populate_base_entities(fake, num_alumnos, num_profesores, num_tutores)
            
            for anio in range(start_year, end_year + 1):
                self.stdout.write(self.style.MIGRATE_HEADING(f'Poblando datos para el año académico: {anio}...'))
                self._populate_academic_year_data(fake, anio, alumnos_per_course_min, alumnos_per_course_max)

        self.stdout.write(self.style.SUCCESS('¡Población de datos completada exitosamente!'))

    def _delete_all_data(self):
        Usuario.objects.all().delete()
        AlumnoTutor.objects.all().delete()
        Tutor.objects.all().delete()
        Participacion.objects.all().delete()
        EntregaActividad.objects.all().delete()
        ActividadProyecto.objects.all().delete()
        Asistencia.objects.all().delete()
        Nota.objects.all().delete()
        Inscripcion.objects.all().delete()
        AsignacionCursoMateria.objects.all().delete()
        Materia.objects.all().delete()
        Curso.objects.all().delete()
        Profesor.objects.all().delete()
        Alumno.objects.all().delete()
        self.stdout.write(self.style.WARNING('¡Cuidado! Se han eliminado todos los datos de la base de datos.'))

    def _populate_base_entities(self, fake, num_alumnos, num_profesores, num_tutores):
        self.stdout.write('Creando Alumnos...')
        alumnos = []
        for _ in range(num_alumnos):
            genero = random.choice(['Masculino', 'Femenino'])
            alumnos.append(
                Alumno(
                    nombre=fake.first_name_male() if genero == 'Masculino' else fake.first_name_female(),
                    apellido=fake.last_name(),
                    fecha_nacimiento=fake.date_of_birth(minimum_age=6, maximum_age=18),
                    genero=genero,
                    direccion=fake.address(),
                    telefono=fake.phone_number(),
                    email=fake.unique.email(),
                    nacionalidad=fake.country(),
                    foto_perfil_url=fake.image_url() if random.random() < 0.5 else None
                )
            )
        Alumno.objects.bulk_create(alumnos)
        self.stdout.write(self.style.SUCCESS(f'{num_alumnos} Alumnos creados.'))

        self.stdout.write('Creando Profesores...')
        profesores = []
        especialidades = ['Matemáticas', 'Lenguaje', 'Historia', 'Ciencias', 'Física', 'Química', 'Literatura', 'Educación Física', 'Arte', 'Música', 'Inglés', 'Computación', 'Filosofía', 'Geografía', 'Economía']
        titulos = ['Licenciado', 'Magíster', 'Doctor']
        for _ in range(num_profesores):
            profesores.append(
                Profesor(
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    email=fake.unique.email(),
                    telefono=fake.phone_number(),
                    especialidad=random.choice(especialidades),
                    fecha_contratacion=fake.date_between(start_date='-15y', end_date='today'),
                    titulo_academico=random.choice(titulos)
                )
            )
        Profesor.objects.bulk_create(profesores)
        self.stdout.write(self.style.SUCCESS(f'{num_profesores} Profesores creados.'))

        self.stdout.write('Creando Cursos...')
        cursos = []
        cursos_data = {
            'Preescolar': ['Pre-Kinder', 'Kinder'],
            'Primaria': [f'{i}mo de Primaria' for i in range(1, 7)],
            'Secundaria': [f'{i}ro de Secundaria' for i in range(1, 7)]
        }
        for nivel, nombres in cursos_data.items():
            for nombre in nombres:
                cursos.append(
                    Curso(
                        nombre_curso=nombre,
                        descripcion=f"Curso de {nombre} para el nivel {nivel}.",
                        nivel_educativo=nivel,
                        activo=True
                    )
                )
        Curso.objects.bulk_create(cursos)
        self.stdout.write(self.style.SUCCESS(f'{len(cursos)} Cursos creados.'))

        self.stdout.write('Creando Materias (mapeadas por nivel educativo)...')
        # Materias que queremos crear, incluyendo el nivel educativo para coherencia
        materias_por_nivel = {
            'Preescolar': ['Lenguaje Pre', 'Matemáticas Pre', 'Exploración del Entorno', 'Desarrollo Personal'],
            'Primaria': ['Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Ciencias Sociales', 'Música', 'Arte', 'Educación Física'],
            'Secundaria': ['Matemáticas', 'Literatura', 'Historia', 'Geografía', 'Física', 'Química', 'Biología', 'Inglés', 'Programación', 'Educación Física', 'Filosofía']
        }
        
        # Lista para almacenar las instancias de Materia creadas o recuperadas
        materias_creadas_o_existentes = [] 
        
        for nivel, nombres_materias in materias_por_nivel.items():
            for nombre_materia in nombres_materias:
                # Generar un código único
                codigo = f"{nombre_materia[:3].upper()}{random.randint(100,999)}"
                # En este punto, si 'nombre_materia' es el único campo único, usamos get_or_create
                # Si tu modelo Materia tiene un unique_together = ('nombre_materia', 'nivel_educativo'),
                # la llamada sería: Materia.objects.get_or_create(nombre_materia=nombre_materia, nivel_educativo=nivel, ...)
                
                materia_obj, created = Materia.objects.get_or_create(
                    nombre_materia=nombre_materia,
                    defaults={
                        'descripcion': f"Materia de {nombre_materia} para el nivel {nivel}.",
                        'codigo_materia': codigo,
                        'creditos': random.choice([2.0, 3.0, 4.0, 5.0])
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"  Materia '{nombre_materia}' creada."))
                else:
                    self.stdout.write(self.style.WARNING(f"  Materia '{nombre_materia}' ya existe, saltando creación."))
                materias_creadas_o_existentes.append(materia_obj) # Añadimos la materia (nueva o existente) a la lista

        # Ahora la lista 'materias_creadas_o_existentes' contiene todas las materias únicas.
        # No necesitas bulk_create aquí, ya que get_or_create inserta de uno en uno.
        self.stdout.write(self.style.SUCCESS(f'{len(materias_creadas_o_existentes)} Materias únicas aseguradas (creadas o ya existentes).'))

        self.stdout.write('Creando Tutores...')
        tutores = []
        preferencias = ['Email', 'Telefono', 'WhatsApp']
        for _ in range(num_tutores):
            tutores.append(
                Tutor(
                    nombre=fake.first_name(),
                    apellido=fake.last_name(),
                    telefono=fake.phone_number(),
                    email=fake.unique.email(),
                    direccion=fake.address(),
                    profesion=fake.job(),
                    preferencia_contacto=random.choice(preferencias)
                )
            )
        Tutor.objects.bulk_create(tutores)
        self.stdout.write(self.style.SUCCESS(f'{num_tutores} Tutores creados.'))

        if not Usuario.objects.filter(username='admin').exists():
            Usuario.objects.create(
                username='admin',
                password_hash=make_password('admin123'),
                email='admin@aula.com',
                rol='Admin',
                activo=True
            )
            self.stdout.write(self.style.SUCCESS('Usuario Admin creado.'))

    def _populate_academic_year_data(self, fake, anio_academico, alumnos_per_course_min, alumnos_per_course_max):
        alumnos_disponibles = list(Alumno.objects.all())
        profesores_disponibles = list(Profesor.objects.all())
        cursos_existentes = list(Curso.objects.all())
        materias_existentes = list(Materia.objects.all())
        tutores_existentes = list(Tutor.objects.all())

        periodos = ['Semestre 1', 'Semestre 2']
        start_date_academic_year = date(anio_academico, 1, 1)
        end_date_academic_year = date(anio_academico, 12, 31)

        # --- Materias por curso (cache por curso) ---
        materias_por_curso_cache = {}
        for curso in cursos_existentes:
            materias_curso = Materia.objects.filter(
                descripcion__icontains=curso.nivel_educativo
            ).distinct()
            if not materias_curso.exists():
                materias_curso = random.sample(materias_existentes, random.randint(3, 6))
            else:
                materias_curso = list(materias_curso)
            materias_por_curso_cache[curso.id] = materias_curso

        # --- Asignaciones Curso-Materia ---
        asignaciones_list = []
        for curso in cursos_existentes:
            materias_relevantes = materias_por_curso_cache.get(curso.id, [])
            if not materias_relevantes:
                continue
            num_materias_a_asignar = random.randint(min(3, len(materias_relevantes)), min(8, len(materias_relevantes)))
            profesores_copy = list(profesores_disponibles)
            for materia in random.sample(materias_relevantes, num_materias_a_asignar):
                if not profesores_copy:
                    break
                profesor_asignado = random.choice(profesores_copy)
                for periodo in periodos:
                    asignacion_obj, created = AsignacionCursoMateria.objects.get_or_create(
                        curso=curso,
                        materia=materia,
                        profesor=profesor_asignado,
                        anio_academico=anio_academico,
                        periodo=periodo
                    )
                    if created:
                        asignaciones_list.append(asignacion_obj)

        asignaciones_anio = list(AsignacionCursoMateria.objects.filter(anio_academico=anio_academico).select_related('curso', 'materia', 'profesor'))

        # --- Inscripciones ---
        inscripciones_list = []
        alumnos_sin_inscripcion = list(alumnos_disponibles)
        for curso in cursos_existentes:
            num_alumnos_en_curso = random.randint(alumnos_per_course_min, alumnos_per_course_max)
            alumnos_para_este_curso = []
            if len(alumnos_sin_inscripcion) > 0:
                num_a_seleccionar = min(num_alumnos_en_curso, len(alumnos_sin_inscripcion))
                alumnos_para_este_curso = random.sample(alumnos_sin_inscripcion, num_a_seleccionar)
                alumnos_sin_inscripcion = [a for a in alumnos_sin_inscripcion if a not in alumnos_para_este_curso]
            else:
                break
            for alumno in alumnos_para_este_curso:
                for periodo in periodos:
                    inscripcion_obj, created = Inscripcion.objects.get_or_create(
                        alumno=alumno,
                        curso=curso,
                        anio_academico=anio_academico,
                        periodo=periodo,
                        defaults={
                            'fecha_inscripcion': fake.date_between(
                                start_date=start_date_academic_year,
                                end_date=start_date_academic_year + timedelta(days=74) # hasta marzo 15 aprox
                            )
                        }
                    )
                    if created:
                        inscripciones_list.append(inscripcion_obj)

        inscripciones_anio_actual = list(Inscripcion.objects.filter(anio_academico=anio_academico).select_related('alumno', 'curso'))
        if not inscripciones_anio_actual:
            self.stdout.write(self.style.WARNING(f"  No hay inscripciones para el año {anio_academico}. Saltando generación de datos transaccionales."))
            return

        # --- Alumno-Tutor ---
        alumno_tutores_list_new = []
        relaciones = ['Padre', 'Madre', 'Tío', 'Tía', 'Tutor Legal']
        for alumno in alumnos_disponibles:
            if not AlumnoTutor.objects.filter(alumno=alumno).exists():
                num_tutores_alumno = random.choices([1, 2], weights=[0.7, 0.3], k=1)[0]
                tutores_asignados = random.sample(tutores_existentes, min(num_tutores_alumno, len(tutores_existentes)))
                for i, tutor in enumerate(tutores_asignados):
                    is_principal = (i == 0)
                    alumno_tutor_obj, created = AlumnoTutor.objects.get_or_create(
                        alumno=alumno,
                        tutor=tutor,
                        defaults={
                            'relacion': random.choice(relaciones),
                            'es_contacto_principal': is_principal
                        }
                    )
                    if created:
                        alumno_tutores_list_new.append(alumno_tutor_obj)

        # --- Usuarios ---
        usuarios_list_new = []
        for alumno in alumnos_disponibles:
            if not Usuario.objects.filter(alumno=alumno).exists():
                usuario_obj, created = Usuario.objects.get_or_create(
                    username=f"{alumno.nombre.lower().replace(' ', '')}{alumno.id}",
                    defaults={
                        'password_hash': make_password('password123'),
                        'email': alumno.email or fake.unique.email(),
                        'rol': 'Alumno',
                        'alumno': alumno,
                        'activo': True
                    }
                )
                if created:
                    usuarios_list_new.append(usuario_obj)
        for profesor in profesores_disponibles:
            if not Usuario.objects.filter(profesor=profesor).exists():
                usuario_obj, created = Usuario.objects.get_or_create(
                    username=f"{profesor.nombre.lower().replace(' ', '')}{profesor.id}",
                    defaults={
                        'password_hash': make_password('password123'),
                        'email': profesor.email,
                        'rol': 'Profesor',
                        'profesor': profesor,
                        'activo': True
                    }
                )
                if created:
                    usuarios_list_new.append(usuario_obj)
        for tutor in tutores_existentes:
            if not Usuario.objects.filter(tutor=tutor).exists():
                usuario_obj, created = Usuario.objects.get_or_create(
                    username=f"{tutor.nombre.lower().replace(' ', '')}{tutor.id}",
                    defaults={
                        'password_hash': make_password('password123'),
                        'email': tutor.email or fake.unique.email(),
                        'rol': 'Tutor',
                        'tutor': tutor,
                        'activo': True
                    }
                )
                if created:
                    usuarios_list_new.append(usuario_obj)

        # --- Actividades, Notas, Asistencia, Participación, Entregas ---
        self.stdout.write(f'  Generando datos transaccionales para el año {anio_academico}...')
        notas_a_crear = []
        asistencias_a_crear = []
        participaciones_a_crear = []
        actividades_a_crear = []
        entregas_a_crear = []

        all_actividades_anio = []
        for asignacion in asignaciones_anio:
            alumnos_en_curso_y_periodo = [
                ins.alumno for ins in inscripciones_anio_actual 
                if ins.curso == asignacion.curso and ins.periodo == asignacion.periodo
            ]
            num_actividades_por_materia = random.randint(4, 7)
            for _ in range(num_actividades_por_materia):
                fecha_asignacion = fake.date_between(
                    start_date=start_date_academic_year,
                    end_date=end_date_academic_year - timedelta(days=60)
                )
                fecha_entrega_limite = fecha_asignacion + timedelta(days=random.randint(7, 45))
                if fecha_entrega_limite > end_date_academic_year:
                    fecha_entrega_limite = end_date_academic_year
                max_score = random.choice([10, 20, 50, 100])
                actividad_type = random.choice(['Tarea', 'Proyecto Individual', 'Examen Corto', 'Examen Parcial', 'Investigación'])
                actividad_obj, created = ActividadProyecto.objects.get_or_create(
                    materia=asignacion.materia,
                    profesor=asignacion.profesor,
                    titulo=f"{actividad_type} de {fake.word()} - {asignacion.materia.nombre_materia} ({anio_academico})",
                    fecha_asignacion=fecha_asignacion,
                    defaults={
                        'descripcion': fake.sentence(),
                        'fecha_entrega_limite': fecha_entrega_limite,
                        'max_puntuacion': max_score,
                        'tipo_actividad': actividad_type,
                    }
                )
                if created:
                    actividades_a_crear.append(actividad_obj)
                all_actividades_anio.append(actividad_obj)

        inscripciones_anio_actual = list(Inscripcion.objects.filter(anio_academico=anio_academico).select_related('alumno', 'curso'))
        if not inscripciones_anio_actual:
            self.stdout.write(self.style.WARNING(f"   No hay inscripciones para el año {anio_academico}. Saltando datos transaccionales."))
            return

        for inscripcion in inscripciones_anio_actual:
            materias_del_alumno_qs = AsignacionCursoMateria.objects.filter(
                curso=inscripcion.curso,
                anio_academico=inscripcion.anio_academico,
                periodo=inscripcion.periodo
            ).select_related('materia', 'profesor')

            for asignacion in materias_del_alumno_qs:
                materia = asignacion.materia
                profesor_materia = asignacion.profesor

                # Generar Notas en memoria
                num_notas = random.randint(3, 5)
                for _ in range(num_notas):
                    calificacion = round(random.uniform(40.0, 100.0), 2)
                    fecha_evaluacion = fake.date_between(start_date=start_date_academic_year, end_date=end_date_academic_year)
                    notas_a_crear.append(Nota(
                        inscripcion=inscripcion, materia=materia, profesor=profesor_materia,
                        fecha_evaluacion=fecha_evaluacion, calificacion=calificacion,
                        tipo_evaluacion=random.choice([c[0] for c in Nota.TIPO_EVALUACION_CHOICES])
                    ))

                # Generar Asistencias en memoria
                num_asistencias = random.randint(15, 30)
                for _ in range(num_asistencias):
                    fecha_asistencia = fake.date_between(start_date=start_date_academic_year, end_date=end_date_academic_year)
                    asistencias_a_crear.append(Asistencia(
                        inscripcion=inscripcion, materia=materia, fecha=fecha_asistencia,
                        estado=random.choices([c[0] for c in Asistencia.ESTADO_ASISTENCIA_CHOICES], weights=[0.85, 0.1, 0.03, 0.02], k=1)[0],
                        profesor=profesor_materia
                    ))
                
                # Generar Participaciones en memoria
                num_participaciones = random.randint(5, 15)
                for _ in range(num_participaciones):
                    fecha_participacion = fake.date_between(start_date=start_date_academic_year, end_date=end_date_academic_year)
                    participaciones_a_crear.append(Participacion(
                        inscripcion=inscripcion, materia=materia, fecha=fecha_participacion,
                        puntuacion=round(random.uniform(0.0, 9.99), 2),
                        comentarios=(fake.sentence() if random.random() < 0.2 else None),
                        profesor=profesor_materia
                    ))

        # --- OPTIMIZACIÓN: Escribimos todo en la base de datos en grandes lotes ---
        self.stdout.write(f'  Insertando {len(notas_a_crear)} notas en la base de datos...')
        Nota.objects.bulk_create(notas_a_crear, batch_size=1000)
        
        self.stdout.write(f'  Insertando {len(asistencias_a_crear)} asistencias en la base de datos...')
        Asistencia.objects.bulk_create(asistencias_a_crear, batch_size=1000)

        self.stdout.write(f'  Insertando {len(participaciones_a_crear)} participaciones en la base de datos...')
        Participacion.objects.bulk_create(participaciones_a_crear, batch_size=1000)
        
        self.stdout.write(self.style.SUCCESS(f'  Datos transaccionales para {anio_academico} creados.'))
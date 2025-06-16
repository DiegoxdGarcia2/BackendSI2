# gestion_escolar/management/commands/populate_db.py
import random
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from faker import Faker

from gestion_escolar.models import (
    Alumno, Profesor, Curso, Materia, AsignacionCursoMateria, Inscripcion,
    Nota, Asistencia, ActividadProyecto, EntregaActividad, Participacion,
    Tutor, AlumnoTutor, Usuario
)

class Command(BaseCommand):
    help = 'Popula la base de datos con datos sintéticos de forma masiva y optimizada.'

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

        # Cargar entidades en memoria para usarlas en los bucles
        alumnos = list(Alumno.objects.all())
        profesores = list(Profesor.objects.all())
        cursos = list(Curso.objects.all())
        materias = list(Materia.objects.all())
        tutores = list(Tutor.objects.all())

        # --- Creación de Datos Académicos Anuales ---
        for anio in range(kwargs['start_year'], kwargs['end_year'] + 1):
            self.stdout.write(self.style.MIGRATE_HEADING(f'Poblando datos para el año académico: {anio}...'))
            self._populate_academic_year_data(fake, anio, alumnos, profesores, cursos, materias, tutores)
        
        # --- Creación de Usuarios y Relaciones Finales (Optimizada) ---
        self._populate_users_and_relations(alumnos, profesores, tutores)

        self.stdout.write(self.style.SUCCESS('¡Población de datos completada exitosamente!'))

    def _delete_all_data(self):
        # El orden de eliminación es importante por las dependencias de Foreign Key
        models_to_delete = [
            Usuario, AlumnoTutor, Participacion, EntregaActividad, ActividadProyecto, 
            Asistencia, Nota, Inscripcion, AsignacionCursoMateria, Alumno, 
            Profesor, Tutor, Materia, Curso
        ]
        for model in models_to_delete:
            self.stdout.write(f'Eliminando {model.__name__}...')
            model.objects.all().delete()
        self.stdout.write(self.style.WARNING('¡Cuidado! Se han eliminado todos los datos de la base de datos.'))

    def _populate_base_entities(self, fake, kwargs):
        # Alumnos
        self.stdout.write('Creando Alumnos...')
        alumnos_a_crear = [Alumno(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(kwargs['num_alumnos'])]
        Alumno.objects.bulk_create(alumnos_a_crear)
        self.stdout.write(self.style.SUCCESS(f"{kwargs['num_alumnos']} Alumnos creados."))

        # Profesores
        self.stdout.write('Creando Profesores...')
        profesores_a_crear = [Profesor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email(), fecha_contratacion=fake.date_between(start_date='-20y', end_date='-1y')) for _ in range(kwargs['num_profesores'])]
        Profesor.objects.bulk_create(profesores_a_crear)
        self.stdout.write(self.style.SUCCESS(f"{kwargs['num_profesores']} Profesores creados."))
        
        # Tutores
        self.stdout.write('Creando Tutores...')
        tutores_a_crear = [Tutor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(kwargs['num_tutores'])]
        Tutor.objects.bulk_create(tutores_a_crear)
        self.stdout.write(self.style.SUCCESS(f"{kwargs['num_tutores']} Tutores creados."))
        
        # Cursos
        self.stdout.write('Creando Cursos...')
        cursos_data = {'Preescolar': ['Pre-Kinder', 'Kinder'], 'Primaria': [f'{i}mo de Primaria' for i in range(1, 7)], 'Secundaria': [f'{i}ro de Secundaria' for i in range(1, 7)]}
        cursos_a_crear = [Curso(nombre_curso=nombre, nivel_educativo=nivel) for nivel, nombres in cursos_data.items() for nombre in nombres]
        Curso.objects.bulk_create(cursos_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(cursos_a_crear)} Cursos creados.'))

        # Materias
        self.stdout.write('Creando Materias...')
        materias_data = ['Matemáticas', 'Lenguaje', 'Historia', 'Ciencias', 'Física', 'Química', 'Literatura', 'Arte', 'Música', 'Inglés', 'Programación']
        materias_a_crear = [Materia(nombre_materia=nombre, creditos=random.uniform(2.0, 5.0)) for nombre in materias_data]
        Materia.objects.bulk_create(materias_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(materias_a_crear)} Materias creadas.'))

    def _populate_academic_year_data(self, fake, anio, alumnos, profesores, cursos, materias, tutores):
        # --- Asignaciones y Inscripciones ---
        asignaciones_a_crear = [AsignacionCursoMateria(curso=curso, materia=materia, profesor=random.choice(profesores), anio_academico=anio, periodo='Año Completo') for curso in cursos for materia in random.sample(materias, k=random.randint(5, 8))]
        AsignacionCursoMateria.objects.bulk_create(asignaciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(asignaciones_a_crear)} Asignaciones creadas para {anio}.')

        inscripciones_a_crear = [Inscripcion(alumno=alumno, curso=random.choice(cursos), anio_academico=anio, periodo='Año Completo') for alumno in alumnos]
        Inscripcion.objects.bulk_create(inscripciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(inscripciones_a_crear)} Inscripciones creadas para {anio}.')

        # --- Datos Transaccionales (Notas, Asistencia, etc.) ---
        notas_a_crear, asistencias_a_crear, participaciones_a_crear = [], [], []
        inscripciones_anio = Inscripcion.objects.filter(anio_academico=anio).select_related('alumno', 'curso')

        for inscripcion in inscripciones_anio:
            asignaciones_del_curso = AsignacionCursoMateria.objects.filter(curso=inscripcion.curso, anio_academico=anio)
            for asignacion in asignaciones_del_curso:
                # Notas
                for _ in range(random.randint(3, 5)):
                    notas_a_crear.append(Nota(inscripcion=inscripcion, materia=asignacion.materia, profesor=asignacion.profesor, calificacion=random.uniform(40.0, 100.0), fecha_evaluacion=fake.date_between(start_date=date(anio, 1, 1), end_date=date(anio, 12, 31))))
                
                # Asistencia
                fechas_usadas = set()
                for _ in range(30): # Generar 30 días de asistencia por materia
                    fecha = fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 11, 30))
                    if fecha not in fechas_usadas:
                        fechas_usadas.add(fecha)
                        asistencias_a_crear.append(Asistencia(inscripcion=inscripcion, materia=asignacion.materia, fecha=fecha, estado=random.choices(['Presente', 'Ausente'], weights=[0.9, 0.1])[0], profesor=asignacion.profesor))

        self.stdout.write(f'  Insertando {len(notas_a_crear)} notas...')
        Nota.objects.bulk_create(notas_a_crear, batch_size=500)
        self.stdout.write(f'  Insertando {len(asistencias_a_crear)} asistencias...')
        Asistencia.objects.bulk_create(asistencias_a_crear, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'  Datos transaccionales para {anio} creados.'))

    def _populate_users_and_relations(self, alumnos, profesores, tutores):
        # --- Usuarios ---
        self.stdout.write('Creando Usuarios para Alumnos, Profesores y Tutores...')
        usuarios_a_crear = []
        for alumno in alumnos:
            usuarios_a_crear.append(Usuario(username=f"alumno{alumno.id}", password_hash=make_password('123'), rol='Alumno', alumno=alumno, activo=True))
        for profesor in profesores:
            usuarios_a_crear.append(Usuario(username=f"profesor{profesor.id}", password_hash=make_password('123'), rol='Profesor', profesor=profesor, activo=True))
        for tutor in tutores:
            usuarios_a_crear.append(Usuario(username=f"tutor{tutor.id}", password_hash=make_password('123'), rol='Tutor', tutor=tutor, activo=True))
        
        # Admin
        usuarios_a_crear.append(Usuario(username='admin', password_hash=make_password('admin123'), rol='Admin', activo=True))
        
        Usuario.objects.bulk_create(usuarios_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(usuarios_a_crear)} Usuarios creados.'))
        
        # --- Alumno-Tutor ---
        self.stdout.write('Creando relaciones Alumno-Tutor...')
        relaciones_a_crear = [AlumnoTutor(alumno=alumno, tutor=random.choice(tutores), relacion='Tutor Legal') for alumno in alumnos]
        AlumnoTutor.objects.bulk_create(relaciones_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(relaciones_a_crear)} relaciones Alumno-Tutor creadas.'))
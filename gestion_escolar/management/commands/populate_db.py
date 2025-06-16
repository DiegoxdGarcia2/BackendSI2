# gestion_escolar/management/commands/populate_db.py
import random
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from faker import Faker

from gestion_escolar.models import (
    Alumno, Profesor, Curso, Materia, AsignacionCursoMateria, Inscripcion,
    Nota, Asistencia, Participacion, Tutor, AlumnoTutor, Usuario
)

class Command(BaseCommand):
    help = 'Popula la BD con datos sintéticos de forma masiva y optimizada para producción.'

    def add_arguments(self, parser):
        parser.add_argument('--num_alumnos', type=int, default=100)
        parser.add_argument('--num_profesores', type=int, default=30)
        parser.add_argument('--num_tutores', type=int, default=80)
        parser.add_argument('--start_year', type=int, default=2022)
        parser.add_argument('--end_year', type=int, default=date.today().year)
        parser.add_argument('--alumnos_per_course_min', type=int, default=20)
        parser.add_argument('--alumnos_per_course_max', type=int, default=30)
        parser.add_argument('--delete_old_data', action='store_true')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        if kwargs['delete_old_data']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            self._delete_all_data()
            self.stdout.write(self.style.SUCCESS('Datos existentes eliminados.'))

        self.stdout.write(self.style.MIGRATE_HEADING('Iniciando población de datos...'))
        fake = Faker('es_ES')
        
        # --- 1. Creación de Entidades Base ---
        profesores = self._populate_profesores(fake, kwargs['num_profesores'])
        cursos = self._populate_cursos()
        materias = self._populate_materias()
        alumnos = self._populate_alumnos(fake, kwargs['num_alumnos'])
        tutores = self._populate_tutores(fake, kwargs['num_tutores'])

        # --- 2. Creación de Datos Académicos Anuales ---
        for anio in range(kwargs['start_year'], kwargs['end_year'] + 1):
            self.stdout.write(self.style.MIGRATE_HEADING(f'Poblando datos para el año académico: {anio}...'))
            self._populate_academic_year_data(fake, anio, alumnos, profesores, cursos, materias, kwargs)
        
        # --- 3. Creación de Usuarios y Relaciones Finales ---
        self._populate_users_and_relations(alumnos, profesores, tutores)

        self.stdout.write(self.style.SUCCESS('¡Población de datos completada exitosamente!'))

    def _delete_all_data(self):
        models_to_delete = [Usuario, AlumnoTutor, Participacion, EntregaActividad, ActividadProyecto, Asistencia, Nota, Inscripcion, AsignacionCursoMateria, Alumno, Profesor, Tutor, Materia, Curso]
        for model in models_to_delete:
            model.objects.all().delete()

    def _populate_profesores(self, fake, num_profesores):
        self.stdout.write('Creando Profesores...')
        profesores = [Profesor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email(), fecha_contratacion=fake.date_between(start_date='-20y', end_date='-1y')) for _ in range(num_profesores)]
        Profesor.objects.bulk_create(profesores)
        self.stdout.write(self.style.SUCCESS(f"{len(profesores)} Profesores creados."))
        return list(Profesor.objects.all())

    def _populate_cursos(self):
        self.stdout.write('Creando Cursos...')
        cursos_data = {'Preescolar': ['Pre-Kinder', 'Kinder'], 'Primaria': [f'{i}mo de Primaria' for i in range(1, 7)], 'Secundaria': [f'{i}ro de Secundaria' for i in range(1, 7)]}
        cursos_a_crear = [Curso(nombre_curso=nombre, nivel_educativo=nivel) for nivel, nombres in cursos_data.items() for nombre in nombres]
        Curso.objects.bulk_create(cursos_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(cursos_a_crear)} Cursos creados.'))
        return list(Curso.objects.all())

    def _populate_materias(self):
        self.stdout.write('Creando Materias...')
        materias_data = ['Matemáticas', 'Lenguaje', 'Historia', 'Ciencias', 'Física', 'Química', 'Literatura', 'Arte', 'Música', 'Inglés', 'Programación']
        materias_a_crear = [Materia(nombre_materia=nombre, creditos=random.uniform(2.0, 5.0)) for nombre in materias_data]
        Materia.objects.bulk_create(materias_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(materias_a_crear)} Materias creadas.'))
        return list(Materia.objects.all())
    
    def _populate_alumnos(self, fake, num_alumnos):
        self.stdout.write('Creando Alumnos...')
        alumnos_a_crear = [Alumno(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(num_alumnos)]
        Alumno.objects.bulk_create(alumnos_a_crear)
        self.stdout.write(self.style.SUCCESS(f"{len(alumnos_a_crear)} Alumnos creados."))
        return list(Alumno.objects.all())

    def _populate_tutores(self, fake, num_tutores):
        self.stdout.write('Creando Tutores...')
        tutores_a_crear = [Tutor(nombre=fake.first_name(), apellido=fake.last_name(), email=fake.unique.email()) for _ in range(num_tutores)]
        Tutor.objects.bulk_create(tutores_a_crear)
        self.stdout.write(self.style.SUCCESS(f"{len(tutores_a_crear)} Tutores creados."))
        return list(Tutor.objects.all())

    def _populate_academic_year_data(self, fake, anio, alumnos, profesores, cursos, materias, kwargs):
        asignaciones_a_crear = [AsignacionCursoMateria(curso=curso, materia=materia, profesor=random.choice(profesores), anio_academico=anio, periodo='Año Completo') for curso in cursos for materia in random.sample(materias, k=random.randint(5, 8))]
        AsignacionCursoMateria.objects.bulk_create(asignaciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(asignaciones_a_crear)} Asignaciones creadas para {anio}.')

        alumnos_restantes = list(alumnos)
        inscripciones_a_crear = []
        for curso in cursos:
            num_alumnos_a_inscribir = min(len(alumnos_restantes), random.randint(kwargs['alumnos_per_course_min'], kwargs['alumnos_per_course_max']))
            if num_alumnos_a_inscribir == 0: continue
            alumnos_para_este_curso = random.sample(alumnos_restantes, k=num_alumnos_a_inscribir)
            for alumno in alumnos_para_este_curso:
                inscripciones_a_crear.append(Inscripcion(alumno=alumno, curso=curso, anio_academico=anio, periodo='Año Completo'))
            alumnos_restantes = [a for a in alumnos_restantes if a not in alumnos_para_este_curso]
        Inscripcion.objects.bulk_create(inscripciones_a_crear, ignore_conflicts=True)
        self.stdout.write(f'  {len(inscripciones_a_crear)} Inscripciones creadas para {anio}.')

        notas_a_crear, asistencias_a_crear, participaciones_a_crear = [], [], []
        inscripciones_anio = Inscripcion.objects.filter(anio_academico=anio).select_related('alumno', 'curso')
        
        for inscripcion in inscripciones_anio:
            asignaciones_del_curso = AsignacionCursoMateria.objects.filter(curso=inscripcion.curso, anio_academico=anio)
            for asignacion in asignaciones_del_curso:
                for _ in range(5):
                    notas_a_crear.append(Nota(inscripcion=inscripcion, materia=asignacion.materia, profesor=asignacion.profesor, calificacion=random.uniform(40.0, 100.0), fecha_evaluacion=fake.date(pattern=f'{anio}-%m-%d')))
                
                fechas_usadas = set()
                while len(fechas_usadas) < 25:
                    fechas_usadas.add(fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 11, 30)))
                for fecha in fechas_usadas:
                    asistencias_a_crear.append(Asistencia(inscripcion=inscripcion, materia=asignacion.materia, fecha=fecha, estado='Presente', profesor=asignacion.profesor))
                
                fechas_usadas.clear()
                while len(fechas_usadas) < 10:
                    fechas_usadas.add(fake.date_between(start_date=date(anio, 3, 1), end_date=date(anio, 11, 30)))
                for fecha in fechas_usadas:
                    participaciones_a_crear.append(Participacion(inscripcion=inscripcion, materia=asignacion.materia, profesor=asignacion.profesor, fecha=fecha, puntuacion=random.uniform(0.0, 9.99)))

        Nota.objects.bulk_create(notas_a_crear, batch_size=500)
        Asistencia.objects.bulk_create(asistencias_a_crear, batch_size=500)
        Participacion.objects.bulk_create(participaciones_a_crear, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f'  Datos transaccionales para {anio} creados.'))

    def _populate_users_and_relations(self, alumnos, profesores, tutores):
        self.stdout.write('Creando Usuarios y relaciones Alumno-Tutor...')
        usuarios_a_crear, relaciones_a_crear = [], []
        for alumno in alumnos:
            usuarios_a_crear.append(Usuario(username=f"alumno{alumno.id}", password_hash=make_password('123'), rol='Alumno', alumno=alumno))
            relaciones_a_crear.append(AlumnoTutor(alumno=alumno, tutor=random.choice(tutores), relacion='Tutor Legal'))
        for profesor in profesores:
            usuarios_a_crear.append(Usuario(username=f"profesor{profesor.id}", password_hash=make_password('123'), rol='Profesor', profesor=profesor))
        for tutor in tutores:
            usuarios_a_crear.append(Usuario(username=f"tutor{tutor.id}", password_hash=make_password('123'), rol='Tutor', tutor=tutor))
        
        Usuario.objects.bulk_create(usuarios_a_crear, ignore_conflicts=True)
        AlumnoTutor.objects.bulk_create(relaciones_a_crear, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'{len(usuarios_a_crear)} Usuarios y {len(relaciones_a_crear)} relaciones creadas.'))
# gestion_escolar/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# --- Entidades Base ---

class Alumno(models.Model):
    # alumno_id es automático con Django (AutoField por defecto)
    nombre = models.CharField(max_length=100, null=False)
    apellido = models.CharField(max_length=100, null=False)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
    ]
    genero = models.CharField(max_length=10, choices=GENERO_CHOICES, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, null=False)
    # Propuestas adicionales
    nacionalidad = models.CharField(max_length=50, null=True, blank=True)
    foto_perfil_url = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Profesor(models.Model):
    nombre = models.CharField(max_length=100, null=False)
    apellido = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=100, unique=True, null=False)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    especialidad = models.CharField(max_length=100, null=True, blank=True)
    fecha_contratacion = models.DateField(null=False)
    # Propuesta adicional
    titulo_academico = models.CharField(max_length=100, null=True, blank=True)
    # departamento_id necesitaría una tabla Departamentos primero, lo omitimos por ahora

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Curso(models.Model):
    nombre_curso = models.CharField(max_length=100, unique=True, null=False)
    descripcion = models.TextField(null=True, blank=True)
    NIVEL_EDUCATIVO_CHOICES = [
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
        ('Universidad', 'Universidad'),
        ('Otro', 'Otro'),
    ]
    nivel_educativo = models.CharField(max_length=50, choices=NIVEL_EDUCATIVO_CHOICES, null=True, blank=True)
    activo = models.BooleanField(default=True, null=False)

    def __str__(self):
        return self.nombre_curso

class Materia(models.Model):
    nombre_materia = models.CharField(max_length=100, unique=True, null=False)
    descripcion = models.TextField(null=True, blank=True)
    codigo_materia = models.CharField(max_length=20, unique=True, null=True, blank=True)
    creditos = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    def __str__(self):
        return self.nombre_materia

# --- Tablas de Relación y Eventos Académicos ---

class AsignacionCursoMateria(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=False)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=False)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=False)
    anio_academico = models.IntegerField(null=False)
    PERIODO_CHOICES = [
        ('Semestre 1', 'Semestre 1'),
        ('Semestre 2', 'Semestre 2'),
        ('Año Completo', 'Año Completo'),
        ('Trimestre 1', 'Trimestre 1'),
        ('Trimestre 2', 'Trimestre 2'),
        ('Trimestre 3', 'Trimestre 3'),
    ]
    periodo = models.CharField(max_length=50, choices=PERIODO_CHOICES, null=False)
    # Propuestas adicionales
    # aula_id, horario_clase (pueden ser ForeignKeys a otras tablas si se implementan)
    # aula = models.ForeignKey(Aula, on_delete=models.SET_NULL, null=True, blank=True)
    # horario = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = (('curso', 'materia', 'profesor', 'anio_academico', 'periodo'),)
        verbose_name = "Asignación de Curso y Materia"
        verbose_name_plural = "Asignaciones de Cursos y Materias"

    def __str__(self):
        return f"{self.curso.nombre_curso} - {self.materia.nombre_materia} ({self.anio_academico} {self.periodo})"

class Inscripcion(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=False)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=False)
    anio_academico = models.IntegerField(null=False)
    periodo = models.CharField(max_length=50, null=False) # Coincide con PERIODO_CHOICES de Asignacion
    fecha_inscripcion = models.DateField(auto_now_add=True, null=False)
    ESTADO_INSCRIPCION_CHOICES = [
        ('Activa', 'Activa'),
        ('Inactiva', 'Inactiva'),
        ('Suspendida', 'Suspendida'),
        ('Completada', 'Completada'),
        ('Retirada', 'Retirada'),
    ]
    estado_inscripcion = models.CharField(max_length=20, choices=ESTADO_INSCRIPCION_CHOICES, default='Activa', null=False)
    # Propuesta adicional
    fecha_baja = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (('alumno', 'curso', 'anio_academico', 'periodo'),)
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"

    def __str__(self):
        return f"{self.alumno.nombre} en {self.curso.nombre_curso} ({self.anio_academico} {self.periodo})"

class   Nota(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, null=False)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=False)
    TIPO_EVALUACION_CHOICES = [
        ('Examen Parcial 1', 'Examen Parcial 1'),
        ('Examen Parcial 2', 'Examen Parcial 2'),
        ('Examen Final', 'Examen Final'),
        ('Proyecto', 'Proyecto'),
        ('Tarea', 'Tarea'),
        ('Participación', 'Participación'), # Si la participación se califica como nota
        ('Cuestionario', 'Cuestionario'),
    ]
    tipo_evaluacion = models.CharField(max_length=50, choices=TIPO_EVALUACION_CHOICES, null=False)
    # Calificación sobre 100. Ajusta MinValueValidator y MaxValueValidator si es diferente.
    calificacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        db_index=True
    )
    fecha_evaluacion = models.DateField(null=False)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=False)
    comentarios_profesor = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Nota de {self.inscripcion.alumno.nombre} en {self.materia.nombre_materia}: {self.calificacion}"

class Asistencia(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, null=False)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=False)
    fecha = models.DateField(null=False)
    ESTADO_ASISTENCIA_CHOICES = [
        ('Presente', 'Presente'),
        ('Ausente', 'Ausente'),
        ('Tarde', 'Tarde'),
        ('Justificado', 'Justificado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_ASISTENCIA_CHOICES, null=False, db_index=True)
    observaciones = models.TextField(null=True, blank=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True) # Profesor que tomó la asistencia

    class Meta:
        unique_together = (('inscripcion', 'materia', 'fecha'),)
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"

    def __str__(self):
        return f"Asistencia de {self.inscripcion.alumno.nombre} en {self.materia.nombre_materia} el {self.fecha}: {self.estado}"

class ActividadProyecto(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=False)
    titulo = models.CharField(max_length=255, null=False)
    descripcion = models.TextField(null=True, blank=True)
    fecha_asignacion = models.DateField(auto_now_add=True, null=False)
    fecha_entrega_limite = models.DateField(null=False)
    max_puntuacion = models.DecimalField(max_digits=5, decimal_places=2, null=False)
    TIPO_ACTIVIDAD_CHOICES = [
        ('Tarea', 'Tarea'),
        ('Proyecto Individual', 'Proyecto Individual'),
        ('Proyecto Grupal', 'Proyecto Grupal'),
        ('Examen Corto', 'Examen Corto'),
        ('Práctica', 'Práctica'),
    ]
    tipo_actividad = models.CharField(max_length=50, choices=TIPO_ACTIVIDAD_CHOICES, null=False)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return f"{self.titulo} para {self.materia.nombre_materia} (Max: {self.max_puntuacion})"

class EntregaActividad(models.Model):
    actividad = models.ForeignKey(ActividadProyecto, on_delete=models.CASCADE, null=False)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=False)
    fecha_entrega = models.DateTimeField(auto_now_add=True, null=False)
    puntuacion_obtenida = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Puede ser null si aún no se ha calificado
    comentarios_profesor = models.TextField(null=True, blank=True)
    ESTADO_ENTREGA_CHOICES = [
        ('Entregado', 'Entregado'),
        ('Pendiente', 'Pendiente'),
        ('Retrasado', 'Retrasado'),
        ('Revisado', 'Revisado'),
        ('No Entregado', 'No Entregado'),
    ]
    estado_entrega = models.CharField(max_length=50, choices=ESTADO_ENTREGA_CHOICES, default='Entregado', null=False)

    class Meta:
        unique_together = (('actividad', 'alumno'),)
        verbose_name = "Entrega de Actividad"
        verbose_name_plural = "Entregas de Actividades"

    def __str__(self):
        return f"Entrega de {self.actividad.titulo} por {self.alumno.nombre}"

class Participacion(models.Model):
    inscripcion = models.ForeignKey(Inscripcion, on_delete=models.CASCADE, null=False)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, null=False)
    fecha = models.DateField(null=False)
    # Puntuación de 0 a 10 (ej. 0=Nula, 10=Excelente)
    puntuacion = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        db_index=True,
        null=False,
        validators=[MinValueValidator(0.00), MaxValueValidator(10.00)] # Ajusta este rango si es necesario
    )
    comentarios = models.TextField(null=True, blank=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = (('inscripcion', 'materia', 'fecha', 'profesor'),)
        verbose_name = "Participación"
        verbose_name_plural = "Participaciones"

    def __str__(self):
        return f"Participación de {self.inscripcion.alumno.nombre} en {self.materia.nombre_materia} el {self.fecha}: {self.puntuacion}"

# --- Gestión de Usuarios y Tutores ---

class Tutor(models.Model):
    nombre = models.CharField(max_length=100, null=False)
    apellido = models.CharField(max_length=100, null=False)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True, null=False)
    # Propuestas adicionales
    profesion = models.CharField(max_length=100, null=True, blank=True)
    PREFERENCIA_CONTACTO_CHOICES = [
        ('Email', 'Email'),
        ('Telefono', 'Teléfono'),
        ('WhatsApp', 'WhatsApp'),
        ('Cualquiera', 'Cualquiera'),
    ]
    preferencia_contacto = models.CharField(max_length=50, choices=PREFERENCIA_CONTACTO_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} (Tutor)"

class AlumnoTutor(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, null=False)
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, null=False)
    RELACION_CHOICES = [
        ('Padre', 'Padre'),
        ('Madre', 'Madre'),
        ('Tio', 'Tío'),
        ('Tia', 'Tía'),
        ('Abuelo', 'Abuelo'),
        ('Abuela', 'Abuela'),
        ('Tutor Legal', 'Tutor Legal'),
        ('Otro', 'Otro'),
    ]
    relacion = models.CharField(max_length=50, choices=RELACION_CHOICES, null=False)
    es_contacto_principal = models.BooleanField(default=False, null=False)

    class Meta:
        unique_together = (('alumno', 'tutor', 'relacion'),)
        # Esto es más complejo en Django sin raw SQL. Para asegurar un solo contacto principal por alumno
        # tendríamos que hacer una validación a nivel de modelo o en el serializer/view.
        # unique_together = (('alumno', 'es_contacto_principal'),) # No funciona con WHERE TRUE
        verbose_name = "Relación Alumno-Tutor"
        verbose_name_plural = "Relaciones Alumno-Tutor"

    def __str__(self):
        return f"{self.alumno.nombre} - {self.tutor.nombre} ({self.relacion})"

class Usuario(models.Model):
    username = models.CharField(max_length=50, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False) # Almacenar hashes de contraseñas
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    ROL_CHOICES = [
        ('Admin', 'Admin'),
        ('Profesor', 'Profesor'),
        ('Alumno', 'Alumno'),
        ('Tutor', 'Tutor'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, null=False)
    activo = models.BooleanField(default=True, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=False)
    ultima_sesion = models.DateTimeField(null=True, blank=True)

    # Foreign Keys condicionales (pueden ser NULL si el rol no aplica)
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE, null=True, blank=True)
    profesor = models.OneToOneField(Profesor, on_delete=models.CASCADE, null=True, blank=True)
    tutor = models.OneToOneField(Tutor, on_delete=models.CASCADE, null=True, blank=True)

    # Validación a nivel de modelo para asegurar que solo una FK esté seteada según el rol
    def clean(self):
        related_fields = [self.alumno, self.profesor, self.tutor]
        num_related = sum(1 for field in related_fields if field is not None)

        if self.rol == 'Admin':
            if num_related > 0:
                raise models.ValidationError("Un usuario Admin no debe estar asociado a un Alumno, Profesor o Tutor.")
        elif self.rol == 'Alumno':
            if not self.alumno or num_related != 1:
                raise models.ValidationError("Un usuario Alumno debe estar asociado solo a un Alumno.")
        elif self.rol == 'Profesor':
            if not self.profesor or num_related != 1:
                raise models.ValidationError("Un usuario Profesor debe estar asociado solo a un Profesor.")
        elif self.rol == 'Tutor':
            if not self.tutor or num_related != 1:
                raise models.ValidationError("Un usuario Tutor debe estar asociado solo a un Tutor.")
        # Podemos añadir más checks si es necesario, como que el email del usuario
        # coincida con el email de la entidad asociada.

    def save(self, *args, **kwargs):
        self.full_clean() # Ejecuta la validación clean() antes de guardar
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.rol})"
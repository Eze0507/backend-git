"""
Comando de Django para asociar un Empleado a un usuario.

Uso:
    python manage.py asociar_empleado --username pastor --empleado-id 1
    python manage.py asociar_empleado --username pastor --empleado-nombre "Pastor" --empleado-apellido "Apellido"
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from personal_admin.models import Empleado, Cargo


class Command(BaseCommand):
    help = 'Asocia un Empleado a un usuario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username del usuario al que se asociará el empleado'
        )
        parser.add_argument(
            '--empleado-id',
            type=int,
            help='ID del empleado existente a asociar'
        )
        parser.add_argument(
            '--empleado-nombre',
            type=str,
            help='Nombre del empleado (si se crea uno nuevo)'
        )
        parser.add_argument(
            '--empleado-apellido',
            type=str,
            help='Apellido del empleado (si se crea uno nuevo)'
        )
        parser.add_argument(
            '--empleado-ci',
            type=str,
            help='CI del empleado (si se crea uno nuevo)'
        )
        parser.add_argument(
            '--cargo-id',
            type=int,
            help='ID del cargo (requerido si se crea un empleado nuevo)'
        )

    def handle(self, *args, **options):
        username = options['username']
        empleado_id = options.get('empleado_id')
        empleado_nombre = options.get('empleado_nombre')
        empleado_apellido = options.get('empleado_apellido')
        empleado_ci = options.get('empleado_ci')
        cargo_id = options.get('cargo_id')

        # Verificar que el usuario existe
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario encontrado: {user.username} (ID: {user.id})'))
        except User.DoesNotExist:
            raise CommandError(f'❌ Usuario "{username}" no existe')

        # Verificar si ya tiene empleado asociado
        try:
            empleado_existente = Empleado.objects.get(usuario=user)
            self.stdout.write(self.style.WARNING(
                f'⚠️ El usuario {username} ya tiene un empleado asociado: '
                f'{empleado_existente.nombre} {empleado_existente.apellido} (ID: {empleado_existente.id})'
            ))
            self.stdout.write(self.style.WARNING(
                f'   Usuario del empleado: {empleado_existente.usuario.username if empleado_existente.usuario else "Sin usuario"}'
            ))
            # Verificar si el empleado realmente pertenece a este usuario
            if empleado_existente.usuario and empleado_existente.usuario.id == user.id:
                self.stdout.write(self.style.SUCCESS('✅ La asociación es correcta'))
            else:
                self.stdout.write(self.style.ERROR('❌ ERROR: El empleado NO pertenece a este usuario!'))
                self.stdout.write(self.style.ERROR('   Esto es un error de datos. ¿Deseas corregirlo?'))
            return

        except Empleado.DoesNotExist:
            pass

        # Si se especificó un empleado_id, asociarlo
        if empleado_id:
            try:
                empleado = Empleado.objects.get(id=empleado_id)
                if empleado.usuario:
                    raise CommandError(
                        f'❌ El empleado {empleado.nombre} {empleado.apellido} ya está asociado al usuario {empleado.usuario.username}'
                    )
                empleado.usuario = user
                empleado.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Empleado "{empleado.nombre} {empleado.apellido}" asociado al usuario "{username}"'
                ))
                return
            except Empleado.DoesNotExist:
                raise CommandError(f'❌ Empleado con ID {empleado_id} no existe')

        # Si no se especificó empleado_id, buscar empleados sin usuario asociado
        empleados_sin_usuario = Empleado.objects.filter(usuario__isnull=True, estado=True)
        
        if empleados_sin_usuario.exists():
            self.stdout.write(self.style.WARNING('📋 Empleados disponibles sin usuario asociado:'))
            for emp in empleados_sin_usuario:
                self.stdout.write(f'   - ID: {emp.id}, Nombre: {emp.nombre} {emp.apellido}, CI: {emp.ci}')
            
            # Si se especificó nombre y apellido, buscar por coincidencia
            if empleado_nombre and empleado_apellido:
                empleado_coincidente = empleados_sin_usuario.filter(
                    nombre__iexact=empleado_nombre,
                    apellido__iexact=empleado_apellido
                ).first()
                
                if empleado_coincidente:
                    empleado_coincidente.usuario = user
                    empleado_coincidente.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Empleado "{empleado_coincidente.nombre} {empleado_coincidente.apellido}" asociado al usuario "{username}"'
                    ))
                    return

        # Si no hay empleados sin usuario y se especificaron datos para crear uno nuevo
        if empleado_nombre and empleado_apellido and empleado_ci and cargo_id:
            try:
                cargo = Cargo.objects.get(id=cargo_id)
            except Cargo.DoesNotExist:
                raise CommandError(f'❌ Cargo con ID {cargo_id} no existe')

            empleado = Empleado.objects.create(
                usuario=user,
                nombre=empleado_nombre,
                apellido=empleado_apellido,
                ci=empleado_ci,
                cargo=cargo,
                sueldo=5000.00,  # Valor por defecto
                estado=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'✅ Empleado "{empleado.nombre} {empleado.apellido}" creado y asociado al usuario "{username}"'
            ))
            return

        # Si llegamos aquí, no se pudo hacer la asociación
        self.stdout.write(self.style.ERROR('❌ No se pudo asociar empleado. Opciones:'))
        self.stdout.write('   1. Usar --empleado-id para asociar un empleado existente')
        self.stdout.write('   2. Usar --empleado-nombre, --empleado-apellido, --empleado-ci y --cargo-id para crear uno nuevo')
        self.stdout.write('   3. Primero crear un empleado en el sistema y luego asociarlo')


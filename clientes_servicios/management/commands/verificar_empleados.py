"""
Comando de Django para verificar y corregir asociaciones incorrectas entre usuarios y empleados.

Uso:
    python manage.py verificar_empleados
    python manage.py verificar_empleados --corregir
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from personal_admin.models import Empleado


class Command(BaseCommand):
    help = 'Verifica y corrige asociaciones incorrectas entre usuarios y empleados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corregir',
            action='store_true',
            help='Corregir automáticamente las asociaciones incorrectas'
        )

    def handle(self, *args, **options):
        corregir = options['corregir']
        
        self.stdout.write(self.style.SUCCESS('🔍 Verificando asociaciones usuario-empleado...\n'))
        
        # Verificar todos los usuarios
        usuarios_con_problemas = []
        usuarios_ok = []
        
        for user in User.objects.all():
            try:
                empleado = Empleado.objects.get(usuario=user)
                # Verificar que realmente pertenece a este usuario
                if empleado.usuario.id == user.id:
                    usuarios_ok.append((user.username, empleado.nombre, empleado.apellido))
                else:
                    usuarios_con_problemas.append({
                        'usuario': user,
                        'empleado': empleado,
                        'problema': f'El empleado {empleado.nombre} {empleado.apellido} está asociado al usuario {user.username}, pero pertenece a {empleado.usuario.username}'
                    })
            except Empleado.DoesNotExist:
                # Usuario sin empleado - esto está bien, solo informar
                pass
            except Empleado.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(
                    f'❌ Usuario {user.username} tiene MÚLTIPLES empleados asociados (esto no debería pasar)'
                ))
        
        # Mostrar resultados
        if usuarios_ok:
            self.stdout.write(self.style.SUCCESS(f'✅ Usuarios con empleado correctamente asociado ({len(usuarios_ok)}):'))
            for username, nombre, apellido in usuarios_ok:
                self.stdout.write(f'   - {username} → {nombre} {apellido}')
            self.stdout.write('')
        
        if usuarios_con_problemas:
            self.stdout.write(self.style.ERROR(f'❌ Usuarios con problemas ({len(usuarios_con_problemas)}):'))
            for item in usuarios_con_problemas:
                self.stdout.write(self.style.ERROR(f'   - {item["problema"]}'))
                if corregir:
                    # Desasociar el empleado incorrecto
                    item['empleado'].usuario = None
                    item['empleado'].save()
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✅ Empleado desasociado del usuario {item["usuario"].username}'
                    ))
            self.stdout.write('')
        
        # Mostrar empleados sin usuario
        empleados_sin_usuario = Empleado.objects.filter(usuario__isnull=True, estado=True)
        if empleados_sin_usuario.exists():
            self.stdout.write(self.style.WARNING(f'📋 Empleados sin usuario asociado ({empleados_sin_usuario.count()}):'))
            for emp in empleados_sin_usuario:
                self.stdout.write(f'   - ID: {emp.id}, {emp.nombre} {emp.apellido}, CI: {emp.ci}')
            self.stdout.write('')
        
        # Mostrar usuarios sin empleado
        usuarios_sin_empleado = []
        for user in User.objects.all():
            try:
                Empleado.objects.get(usuario=user)
            except Empleado.DoesNotExist:
                usuarios_sin_empleado.append(user)
        
        if usuarios_sin_empleado:
            self.stdout.write(self.style.WARNING(f'📋 Usuarios sin empleado asociado ({len(usuarios_sin_empleado)}):'))
            for user in usuarios_sin_empleado:
                self.stdout.write(f'   - {user.username} (ID: {user.id})')
            self.stdout.write('')
        
        if not usuarios_con_problemas:
            self.stdout.write(self.style.SUCCESS('✅ No se encontraron problemas en las asociaciones'))
        elif not corregir:
            self.stdout.write(self.style.WARNING('💡 Para corregir automáticamente, ejecuta:'))
            self.stdout.write(self.style.WARNING('   python manage.py verificar_empleados --corregir'))


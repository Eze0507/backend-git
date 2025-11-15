import google.generativeai as genai
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from operaciones_inventario.modelsArea import Area

class GeminiChatView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        if not settings.GEMINI_API_KEY:
            return Response(
                {"error": "GEMINI_API_KEY no está configurada en el servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        user_message = request.data.get('message')
        if not user_message:
            return Response(
                {"error": "El campo 'message' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = request.user
            genai.configure(api_key=settings.GEMINI_API_KEY)
            generation_config = {
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 1024,
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            if user.is_authenticated and hasattr(user, 'profile'):
                user_tenant = user.profile.tenant
                
                nombre_taller = user_tenant.nombre_taller or "nuestro taller"
                horarios = user_tenant.horarios or "Horarios no especificados"
                ubicacion = user_tenant.ubicacion or "Ubicación no especificada"
                telefono = user_tenant.telefono or "Teléfono no especificado"
                info_areas = ""
                try:
                    areas_del_taller = Area.objects.filter(tenant=user_tenant)
                    
                    if areas_del_taller.exists():
                        lista_areas = ", ".join([area.nombre for area in areas_del_taller])
                        info_areas = f"Nuestras áreas de servicio registradas son: {lista_areas}."
                    else:
                        info_areas = "Actualmente, el administrador del taller no ha registrado ninguna área de servicio específica en el sistema."
                
                except Exception as e:
                    print(f"Error cargando áreas para chatbot: {e}")
                    info_areas = "Tuve un problema al consultar nuestras áreas de servicio."
                INSTRUCCIONES = f"""
                Eres 'AutoBot', el asistente virtual de {nombre_taller}.
                Tu trabajo es ayudar a los clientes y empleados de ESTE TALLER.
                
                INFORMACIÓN DE NUESTRO TALLER ({nombre_taller}):
                - Horarios: {horarios}
                - Ubicación: {ubicacion}
                - Teléfono: {telefono}
                {info_areas}
                
                REGLAS:
                - Sé breve, amable y profesional.
                - NUNCA menciones a otros talleres. Solo eres el bot de {nombre_taller}.
                - Si te preguntan por un servicio, básate en la lista de áreas registradas.
                """
            else:
                INSTRUCCIONES = """
                Eres 'AutoBot', el asistente virtual de AutoFix SaaS.
                Tu trabajo es ayudar a usuarios NUEVOS a entender cómo funciona la plataforma.
                
                QUÉ ES AUTOFIX:
                - Somos una plataforma de software (SaaS) para talleres mecánicos.
                
                CÓMO REGISTRARSE:
                - TALLERES: Si eres dueño de un taller, puedes registrarlo en '.../register/taller'.
                - CLIENTES: Si eres cliente de un taller, NO puedes registrarte aquí. Debes pedirle a tu taller su 'Código de Invitación' secreto y usarlo en '.../register/cliente'.
                
                CODIGO DE INVITACIÓN:
                - Es un código único que los talleres usan para invitar a sus clientes a unirse a su taller en AutoFix.
                
                REGLAS:
                - NUNCA des información de talleres específicos (horarios, teléfonos, etc.).
                """
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", 
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=INSTRUCCIONES
            )
            response = model.generate_content(user_message)
            return Response(
                {
                    "response": response.text,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Error Gemini: {str(e)}")
            return Response(
                {"error": "Error al comunicarse con el servicio de IA."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
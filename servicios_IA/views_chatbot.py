import google.generativeai as genai
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class GeminiChatView(APIView):
    """
    Vista para interactuar con Google Gemini.
    Recibe {"message": "tu pregunta"} y devuelve la respuesta de la IA.
    """    # Permite acceso a cualquier usuario (público)
    
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        # 1. Validar que existe la API Key en settings
        if not settings.GEMINI_API_KEY:
            return Response(
                {"error": "GEMINI_API_KEY no está configurada en el servidor."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. Obtener el mensaje del usuario
        user_message = request.data.get('message')
        if not user_message:
            return Response(
                {"error": "El campo 'message' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 3. Configurar Gemini (se hace aquí para asegurar que use la key actual)
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Configuración opcional del modelo (puedes ajustar temperatura)
            generation_config = {
                "temperature": 0.7,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 1024,
            }

            # Inicializar el modelo (usa 'gemini-pro' o 'gemini-1.5-flash' si quieres más velocidad)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",  # <--- Usa este nombre, es el más compatible.
                generation_config=generation_config,
            )

            # 4. Generar respuesta
            # Si quieres mantener una conversación real, necesitarás manejar el historial.
            # Para una pregunta/respuesta simple, generate_content está bien.
            response = model.generate_content(user_message)

            return Response(
                {
                    "response": response.text,
                    # "raw": response.candidates[0] # Útil para depurar si necesitas más datos
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Manejo de errores (ej. cuota excedida, error de red)
            print(f"Error Gemini: {str(e)}")
            return Response(
                {"error": "Error al comunicarse con el servicio de IA."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
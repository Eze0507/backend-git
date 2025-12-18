import google.generativeai as genai
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from operaciones_inventario.modelsItem import Item
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class GenerarPresupuestoIAView(APIView):
    """
    Recibe síntomas en lenguaje natural, consulta a Gemini para obtener palabras clave,
    y busca coincidencias reales en el inventario del Tenant.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sintomas = request.data.get('sintomas', '')
        # Obtenemos el tenant del usuario (según tu estructura UserProfile -> Tenant)
        try:
            tenant = request.user.profile.tenant
        except AttributeError:
            return Response({'error': 'Usuario no tiene un taller asignado.'}, status=400)

        if not sintomas:
            return Response({'error': 'Debes describir los síntomas del vehículo.'}, status=400)

        # 1. EL PROMPT: Ingeniería de prompts para obtener datos estructurados
        prompt = f"""
        Actúa como un jefe de taller mecánico experto. 
        El cliente reporta el siguiente problema: "{sintomas}".

        Tu tarea es:
        1. Identificar de 3 a 5 nombres genéricos y cortos de repuestos o insumos necesarios para esta reparación.
        2. Estimar las horas de mano de obra promedio para este trabajo.

        Responde ESTRICTAMENTE con este formato de una sola línea, separando los repuestos por comas y usando una barra vertical (|) para las horas:
        REPUESTO_1, REPUESTO_2, REPUESTO_3 | HORAS_MANO_OBRA

        Ejemplo de respuesta válida:
        Pastillas de freno, Disco de freno, Líquido de freno | 2.5
        """

        try:
            # Configurar Gemini igual que en el chatbot
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
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            response = model.generate_content(prompt)
            texto_respuesta = response.text.strip()
            
            # 2. PROCESAR LA RESPUESTA DE LA IA
            # Separamos repuestos de las horas
            if '|' in texto_respuesta:
                partes = texto_respuesta.split('|')
                keywords_str = partes[0].strip()
                horas_mano_obra = partes[1].strip()
            else:
                # Fallback si la IA no respeta el formato
                keywords_str = texto_respuesta
                horas_mano_obra = "1.0"
            
            # Limpiamos la lista de palabras clave
            lista_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            items_sugeridos = []

            # 3. BUSCAR EN TU BASE DE DATOS REAL (El "Match")
            # Esto es lo que hace que la funcionalidad sea útil y no alucinada
            for palabra in lista_keywords:
                # Buscamos en tu modelo Item, filtrando por el Tenant del usuario
                # Usamos __icontains para búsqueda insensible a mayúsculas
                items_reales = Item.objects.filter(
                    nombre__icontains=palabra, 
                    tenant=tenant,
                    estado='Disponible' # Estado correcto según el modelo
                )[:3] # Traemos máximo 3 opciones por cada palabra clave para no saturar
                
                if items_reales.exists():
                    for item in items_reales:
                        # Adaptamos los campos a tu modelo Item real
                        items_sugeridos.append({
                            "id": item.id,
                            "nombre": item.nombre,
                            "codigo": item.codigo,
                            "stock": item.stock or 0,
                            "precio": float(item.precio) if item.precio else 0,
                            "tipo": item.tipo,
                            "origen_ia": palabra # Para mostrar "Sugerido por: Pastillas"
                        })
                else:
                    # Opcional: Agregar un item "fantasma" para indicar que falta stock
                    items_sugeridos.append({
                        "id": None,
                        "nombre": f"{palabra} (No encontrado en inventario)",
                        "stock": 0,
                        "precio": 0,
                        "origen_ia": palabra
                    })

            # 4. Respuesta Final JSON
            return Response({
                "sintomas_analizados": sintomas,
                "palabras_clave_detectadas": lista_keywords,
                "mano_obra_estimada": horas_mano_obra,
                "items_encontrados": items_sugeridos
            })

        except Exception as e:
            print(f"Error en GenerarPresupuestoIAView: {e}")
            return Response({'error': 'Hubo un error consultando a la IA. Intenta de nuevo.'}, status=500)
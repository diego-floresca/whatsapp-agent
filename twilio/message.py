
from google import genai

# El secreto está en cómo inicializas el cliente.
# Si solo pasas la api_key, la librería asume por defecto el endpoint de Google AI Studio.
client = genai.Client(api_key="AIzaSyDhpUWn6HxeTY6V7zTFZ-wqJXK27BCadYs")

# IMPORTANTE: Asegúrate de NO estar pasando el parámetro 'vertexai=True' 
# ni configuraciones de 'project' o 'location', ya que eso fuerza el uso de OAuth.

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=""
    )
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
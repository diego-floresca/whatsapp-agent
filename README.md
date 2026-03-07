# whatsapp-agent
> 👋 Bienvenido a la documentación oficial del :wa-logo: w**hatsapp-agent**. Este proyecto es un asistente conversacional inteligente, desplegado 100% en la nube bajo una arquitectura *Serverless* de :google-cloud-icon: Google Cloud Platform (GCP) .
> 

> El bot es capaz de recibir mensajes de texto (y audio 🎙️) a través de la API oficial de WhatsApp de Meta, mantener el contexto de la conversación gracias a una memoria persistente, y generar respuestas naturales usando los modelos de inteligencia artificial de Google Vertex AI (Gemini).
> 

---

## 🏗️ Capítulo 1: Arquitectura y Tecnologías

El sistema está diseñado para ser altamente escalable, seguro y con costos optimizados (escala a cero cuando no hay tráfico).

### Flujo de la Información

1. **Entrada:** El usuario envía un mensaje a nuestro número de WhatsApp Business.
2. **Transporte:** Los servidores de Meta disparan un evento `POST` (Webhook) hacia nuestro endpoint de Google Cloud Run.
3. **Procesamiento:**  
    - FastAPI recibe y valida el mensaje de Meta.
    - `firestore_service` recupera el historial de conversación previo del usuario.
    - `ai_service` envía el historial y el nuevo mensaje a Vertex AI (Gemini) usando LangChain.
    - La IA genera la respuesta ideal basándose en el contexto y en la configuración del negocio (`business_info.py`).
4. **Salida:** `messenger_service` toma la respuesta generada y hace una petición HTTP a la Graph API de Meta para entregar el mensaje al usuario de WhatsApp.

### Stack Tecnológico

- **Backend:** Python 3.13.3-slim, FastAPI, Uvicorn (Framework ultrarrápido para APIs).
- **Inteligencia Artificial:** LangChain y Google Vertex AI.
- **Base de Datos (Memoria):** Google Cloud Firestore (NoSQL).
- **Infraestructura (GCP):** Cloud Run (Ejecución), Artifact Registry (Contenedores), Cloud Build (CI/CD).
- **Integración Externa:** Meta Graph API (WhatsApp Cloud API).

---

## 📱 Capítulo 2: El Ecosistema de Meta (Paso a Paso)

Para que tu código en GCP pueda hablar con WhatsApp, necesitas configurar el "puente" del lado de Meta. Aquí están los pasos críticos:

### 1. Creación de la App en Meta for Developers

1. Ingresa a [Meta for Developers](https://developers.facebook.com/) y crea una cuenta si no la tienes.
2. Haz clic en **“Mis Apps”** > ****Selecciona **"Crear app"** > Ponle **"Nombre a tu App"** > En casos de uso selecciona: **"Conectarte con los clientes a través de WhatsApp"** > Selecciona un **“Portfolio Comercial o Crea uno”** > Finaliza el **“Formulario”**.
3. Sigue las instrucciones del Panel.

### 2. Configurar WhatsApp y el Número de Pruebas

1. Una vez dentro del panel busca el apartado **“Personalizar caso de uso”,**  luego ahí ve a “**Configuración de la API“.**
2. Meta te proporcionará un **Número de teléfono de prueba** y un **Token de acceso temporal** (válido por 24 horas) [***opcional***]
3. Registra tu número de teléfono personal en la sección **“Enviar y recibir mensajes” >** **"De"** , despliega el menú y dale al ícono **“Agregar número de Teléfono”** > Llena el formulario que te pida y espera hasta la validación del número.
4. *Nota importante sobre métodos de pago:* Meta cobra por "Conversaciones" (ventanas de 24 horas). Las primeras 1,000 conversaciones de servicio al mes suelen ser gratuitas, pero **debes agregar una tarjeta de crédito** en tu Business Manager para que la API siga funcionando sin interrupciones una vez superes el límite.

### 3. Configuración del Webhook (La conexión con GCP)

El Webhook es la URL de tu servicio en Google Cloud Run a donde Meta enviará los mensajes entrantes 

1. En el menú izquierdo de nuevo en el apartado **“Personalizar caso de uso”**, ve a **Configuración** y busca la sección de **Webhooks**.
2. Haz clic en **Editar**. Necesitarás dos cosas:
    - **URL de devolución de llamada (Callback URL):** La URL pública de tu Cloud Run terminada en la ruta de tu endpoint (ej. `https://tu-proyecto.a.run.app/webhook`) 🧐 algo cómo … `https://whatsapp-bot-1111.southamerica.run.app/webhook`) ojo que debes añadir `/webhook`a tu URL.
    - **Identificador de verificación (Verify Token):** Una contraseña secreta 🤐 que tú **inventas** (ej. `mi_token_super_secreto_123`). Esta misma contraseña debe existir en tu archivo `.env` en GCP para que FastAPI autorice la conexión (`META_ACCESS_TOKEN`).
3. Al guardar, Meta hará una petición `GET` a tu URL para verificar que tu servidor responde correctamente.

---

## 🛠️ Capítulo 3: Pre-requisitos y Entorno Local

Antes de escribir una sola línea de código o hacer un despliegue, necesitamos preparar el terreno. Este proyecto requiere herramientas específicas tanto en tu computadora local como en la nube.

### 1. Herramientas Necesarias

Asegúrate de tener instalado lo siguiente en tu sistema (Mac, Linux o Windows):

- **Python 3.13+**: El lenguaje base del proyecto.
- **Google Cloud CLI (`gcloud`)**: La herramienta de línea de comandos para interactuar con GCP.
- **Git**: Para el control de versiones.
- **Docker** (Opcional pero recomendado): Para probar el contenedor localmente antes de subirlo.

### 2. Configuración en Google Cloud Platform (GCP)

1. Crea un nuevo proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. **Habilita la Facturación:** GCP requiere una tarjeta de crédito activa, aunque usaremos servicios que entran en la capa gratuita.
3. **Habilita las APIs clave:** Busca y habilita las siguientes APIs en la consola:
    - *Cloud Run API*
    - *Cloud Build API*
    - *Artifact Registry API*
    - *Vertex AI API*
    - *Cloud Firestore API*
4. Autentícate en tu terminal local ejecutando:

```sql
gcloud auth login
gcloud config set project TU_PROJECT_ID
```

### 3. Clonar el Repositorio y Entorno Virtual

Para mantener las librerías aisladas y evitar conflictos en tu computadora, usaremos un entorno virtual (`venv`).

```bash
# 1. Clona el repositorio
git clone https://github.com/diego-floresca/whatsapp-agent.git
cd tu-repo

# 2. Crea el entorno virtual (lo llamaremos venv_wa)
python3 -m venv venv_wa

# 3. Activa el entorno virtual
# En Mac/Linux:
source venv_wa/bin/activate
# En Windows:
venv_wa\Scripts\activate

# 4. Instala las dependencias limpias
pip install -r requirements.txt
```

### 4. Variables de Entorno (`.env`)

El proyecto necesita credenciales para funcionar, pero **NUNCA** debemos subirlas a GitHub. Crea un archivo llamado `.env` en la raíz de tu proyecto con esta estructura:

```bash
# GCP basic
PROJECT_ID="PROJECT-ID"
REGION="REGION-SERVICE"
# GCP Image
REPO="REPO-ARTIFACT-NAME"
SERVICE_NAME="CLOUD-RUN-SERVICE-NAME"
IMAGE_TAG="VERSION"
# GCP storage
BUCKET_NAME="BUCKET-NAME-AUDIO-FILES" # Storage
DATABASE_NAME="DATABASE-NAME-FIRESTORE-WA-MESSAGES" # Firestore
# Facebook Meta
META_ACCESS_TOKEN="TOKEN SECRETO QUE NOS DA META" \
WEBHOOK_VERIFY_TOKEN="CLAVE SECRETA QUE NOSOTROS DECIDIMOS"
PHONE_NUMBER_ID="ID DEL NUMERO CONFIGURADO DADO POR META AL CONFIGURAR NUESTRO NUMERO"
```

---

## 📂 Capítulo 4: Estructura del Código

El proyecto sigue una arquitectura modular y limpia. Cada archivo tiene una responsabilidad única, lo que facilita encontrar errores y agregar nuevas funcionalidades.

Aquí tienes la radiografía del proyecto (`tree`):

```bash
├── Dockerfile                  # Receta para construir el contenedor Linux
├── README.md                   # Esta documentación
├── deploy.sh                   # Script mágico para automatizar despliegues a GCP
├── requirements.txt            # Dependencias estrictamente necesarias (FastAPI, LangChain, etc.)
└── gcp_whatsapp/               # 🧠 EL CORAZÓN DE LA APLICACIÓN
    ├── __init__.py
    ├── main.py                 # Punto de entrada (FastAPI). Recibe y responde los Webhooks.
    │
    ├── config/                 # Configuraciones Estáticas
    │   └── business_info.py    # La "personalidad" de la IA, reglas del negocio y prompts.
    │
    ├── services/               # Módulos de Lógica de Negocio
    │   ├── __init__.py
    │   ├── ai_service.py       # Conexión con Vertex AI (Gemini) y LangChain.
    │   ├── audio_service.py    # Procesamiento y manejo de notas de voz enviadas por usuarios.
    │   ├── firestore_service.py# Operaciones de lectura/escritura en la base de datos (Historial).
    │   └── messenger_service.py# Cliente HTTP para enviar mensajes de vuelta usando Meta Graph API.
    │
    └── tests/                  # Pruebas Unitarias y de Integración
        ├── __init__.py
        └── test_firestore_service.py # Validaciones para asegurar que la BD guarde correctamente.
```

La separación en "Servicios" es clave. Si mañana Meta cambia su API, solo modificas `messenger_service.py`. Si decides cambiar a otra base de datos, solo tocas `firestore_service.py`. `main.py` actúa únicamente como un "director de tráfico" que recibe la petición HTTP y llama a estos servicios en el orden correcto.

## 🧠 Capítulo 5: El Cerebro del Bot (IA y Memoria)

Un chatbot tradicional solo responde comandos preprogramados. Nuestro bot es un **Agente Conversacional** que entiende contexto, recuerda detalles de la plática y responde con lenguaje natural. Esto se logra combinando tres tecnologías clave:

### 1. Vertex AI (El Motor de Inteligencia)

Usamos los modelos **Gemini** de Google a través de Vertex AI. Este es el "cerebro" puro que procesa el texto (y el audio, si se requiere) para generar una respuesta coherente.

- Le inyectamos la personalidad del negocio a través del archivo `config/business_info.py` usando un *System Prompt* (ej. "Eres un asistente amable de ventas para la empresa X...").

### 2. LangChain (El Director de Orquesta)

LangChain es el framework que conecta todas las piezas. En lugar de mandar peticiones simples a Gemini, LangChain nos permite crear "Cadenas" (Chains) que:

- Toman la instrucción base (Prompt).
- Toman el historial de la conversación.
- Toman el mensaje nuevo del usuario.
- Envían todo esto estructurado a Vertex AI y formatean la respuesta para que WhatsApp la entienda.

### 3. Firestore (La Memoria a Corto y Largo Plazo)

**El problema:** Google Cloud Run es *stateless* (sin estado). Cada vez que recibe un mensaje, "nace" sin recordar nada del pasado.
**La solución:** Usamos Google Cloud Firestore (una base de datos NoSQL ultrarrápida) como libreta de apuntes.

- **El Flujo de Memoria:**
    1. El usuario envía un mensaje (ej. "Sí, envíamelo a esa dirección").
    2. `firestore_service.py` busca el número de teléfono del usuario en la base de datos y recupera los últimos mensajes.
    3. El bot se da cuenta de que hace 2 minutos hablaron de "Calle Falsa 123".
    4. LangChain junta el historial con el mensaje nuevo, Gemini responde afirmativamente, y el nuevo intercambio se guarda de vuelta en Firestore para la próxima interacción.

---

## **☁️ Capítulo 6: Infraestructura en Google Cloud (GCP)**

Para que nuestro bot viva en la nube, necesitamos habilitar y configurar cinco servicios clave dentro de nuestro proyecto de GCP. Piensa en esto como construir las diferentes áreas de un restaurante inteligente.

### **1. Cloud Storage (La Bodega de Archivos) 🪣**

WhatsApp permite a los usuarios enviar notas de voz, imágenes y documentos. 

- **El Rol:** Cloud Storage actúa como un disco duro infinito. Cuando el servicio `audio_service.py` detecta que el usuario envió una nota de voz, descarga el archivo de los servidores de Meta y lo guarda aquí de forma segura.
- **Configuración:** Debes ir a la consola de GCP, buscar "Cloud Storage", crear un nuevo **Bucket** (ej. `nombre-de-tu-bucket`) y elegir la región más cercana a ti.

### **2. Firestore (La Libreta de Notas) 🗂️**

Aquí es donde vive el historial de las conversaciones para darle "memoria" a nuestra Inteligencia Artificial.

- **El Rol:** Es una base de datos NoSQL ultrarrápida. En lugar de tablas, usa "Documentos" y "Colecciones". Aquí guardamos qué dijo el usuario, qué respondió el bot y en qué fecha, para que LangChain tenga contexto.
- **Configuración:** 1. Ve a "Firestore" en la consola de GCP.
2. Haz clic en **Crear base de datos**.
3. **¡Muy importante!** Selecciona el modo **Native mode** (Modo nativo), ya que es el recomendado para aplicaciones web y móviles modernas. Selecciona tu región y finaliza.

### **3. Artifact Registry (El Refrigerador de Contenedores) 📦**

Cloud Run no ejecuta código fuente directamente; necesita una "Imagen de Docker" pre-empacada con todo lo necesario (Linux, Python, librerías).

- **El Rol:** Artifact Registry es el almacén privado de Google donde guardaremos estas imágenes (las diferentes versiones de nuestro bot).
- **Configuración:**
    1. Ve a "Artifact Registry".
    2. Haz clic en **Crear Repositorio**.
    3. Ponle un nombre (ej. `name-artifact-repository`).
    4. Formato: **Docker**.
    5. Tipo de ubicación: Región (ej. `northamerica-1`).

### **4. Cloud Build (La Cocina / Ensambladora) 🏗️**

No necesitas construir la imagen de Docker en tu propia computadora, lo que ahorra tiempo y dolores de cabeza con incompatibilidades (Windows/Mac vs Linux).

- **El Rol:** Cloud Build toma tu código fuente (comprimido en un `.tar`), lee las instrucciones de tu `Dockerfile`, descarga Python, instala el `requirements.txt` y genera la imagen final, guardándola automáticamente en Artifact Registry. Todo esto ocurre en la nube.

### **5. Cloud Run (El Motor / El Mesero) 🚀**

Este es el corazón de nuestro backend Serverless.

- **El Rol:** Toma la imagen almacenada en Artifact Registry y la expone al internet público a través de una URL segura (`https://...`). Es el servicio que recibe directamente el Webhook de Meta.
- **La Magia:** Escala a cero. Si nadie te escribe por WhatsApp a las 3:00 AM, Cloud Run se "apaga" y Google no te cobra un solo centavo. Si a las 9:00 AM te escriben 100 personas al mismo tiempo, Cloud Run enciende 100 copias de tu bot instantáneamente para responderles a todos sin retrasos.

---

## 🔐 Capítulo 7: Seguridad y Buenas Prácticas

Manejar integraciones con Meta y Google Cloud implica tener **Tokens, API Keys y Contraseñas**. Si estos datos se filtran, cualquier persona podría controlar tu bot o generar costos en tu factura de la nube.

Aquí explico las capas de seguridad implementadas en este proyecto:

### 1. La Regla de Oro: El archivo `.env`

Todas las contraseñas viven en un archivo local llamado `.env`. **Este archivo jamás debe subirse a internet.** Si clonas este repositorio por primera vez, tendrás que crear tu propio archivo `.env` basándote en un archivo de ejemplo (`.env.example`).

### 2. Los Guardianes: `.gitignore` y `.gcloudignore`

Tenemos dos archivos de configuración que actúan como "cadeneros" de discoteca, decidiendo qué archivos entran y cuáles se quedan fuera:

- **`.gitignore`**: Evita que archivos pesados o secretos se suban a GitHub (ej. `.env`, la carpeta del entorno virtual `venv_wa/`, y archivos basura de caché como `__pycache__` o `.DS_Store`).
- **`.gcloudignore`**: Hace exactamente lo mismo, pero para los servidores de Google Cloud Build.
    - *Beneficio extra:* Al ignorar la carpeta `venv_wa/` (que puede pesar cientos de megabytes), hacemos que el comando de despliegue suba solo el código fuente. Esto reduce el tiempo de despliegue de minutos a **solo unos segundos**.

### 3. El "Lavado de Cerebro" de Git (Troubleshooting)

Si por error subiste un archivo secreto a Git antes de ponerlo en el `.gitignore`, el archivo se quedará en la memoria (caché) de Git. Para limpiar el historial de rastreo de forma segura sin borrar tus archivos locales, ejecuta:

```bash
git rm -r --cached .
git add .
git commit -m "Limpieza profunda de caché y aplicación de gitignore"
```

### 4. Inyección de Secretos en Cloud Run

Si nuestro `.env` no se sube a Google Cloud, ¿cómo sabe el servidor las contraseñas?
La respuesta está en el despliegue. Usamos la bandera `--set-env-vars` en nuestro script de `gcloud run deploy`. Esto lee las contraseñas de tu computadora local de forma temporal y se las inyecta de forma segura a los servidores internos de Google Cloud, sin dejarlas escritas en el código.

---

## 🪄 Capítulo 8: La Magia del Despliegue Automático

Desplegar código manualmente en la nube suele ser un proceso tedioso de múltiples pasos. Para solucionar esto y adoptar prácticas de **DevOps / CI-CD**, el proyecto incluye un script mágico llamado `deploy.sh`.

Con un solo comando (`./deploy.sh`), tu computadora empaca el código, lo manda a la nube, construye la imagen, y enciende el servidor.

### ¿Cómo funciona el `deploy.sh` por dentro?

El script hace 3 tareas fundamentales de forma secuencial:

1. **Carga los Secretos Locales:**
El script lee tu archivo local `.env` y extrae variables temporales (como el `PROJECT_ID`, la región y las contraseñas de Meta).
2. **Construye la Imagen en Cloud Build:**
Genera una URL única (URI) para Artifact Registry (ej. `america-south3-docker.pkg.dev/.../whatsapp-bot:v1`). Luego, ejecuta `gcloud builds submit` respetando el `.gcloudignore` (para no subir el pesado `venv_wa`) y crea tu contenedor en los servidores de Google.
3. **Despliega en Cloud Run e Inyecta Contraseñas:**
Usa el comando `gcloud run deploy` para lanzar el contenedor recién creado. La parte más importante de este paso es la bandera `-set-env-vars`. Esta instrucción toma los secretos leídos en el paso 1 y se los "inyecta" de forma segura a la memoria de Cloud Run para que FastAPI pueda autenticarse con Meta y Google.

**Para usarlo:**
Asegúrate de darle permisos de ejecución a tu script la primera vez:

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🧪 Capítulo 9: Pruebas y Calidad de Código (Testing)

Probar un bot de WhatsApp enviando mensajes manualmente desde tu celular cada vez que cambias una línea de código es lento, costoso y propenso a errores. Para esto implementamos **Pruebas Unitarias (aún faltan más pruebas)**.

En la carpeta `gcp_whatsapp/tests/` encontrarás archivos como `test_firestore_service.py`.

### ¿Por qué probar Firestore de forma aislada?

Antes de conectar todo a WhatsApp, necesitamos estar 100% seguros de que nuestra base de datos es capaz de leer y escribir el historial de conversaciones correctamente.

- El archivo `test_firestore_service.py` simula un usuario "falso", escribe un mensaje en la nube, verifica que se guardó bien, y luego lo lee.
- Al usar un framework como **Pytest**, podemos automatizar esto.

**¿Cómo ejecutar las pruebas?**
Abre tu terminal (asegúrate de que tu entorno virtual `venv_wa` esté activado) y ejecuta:

```bash
pytest gcp_whatsapp/tests/
```

Verás un reporte en verde diciéndote que la lógica del negocio está intacta y lista para producción. A medida que el proyecto crezca, agregaremos más pruebas para simular los Webhooks locales sin depender de los servidores de Meta.

---

## 💰 Capítulo 10: Costos y Facturación

Una de las mayores ventajas de la arquitectura *Serverless* es que **pagas solo por lo que usas**. Si tu bot no tiene tráfico, tu factura será de $0.00.

Aquí tienes un desglose de los dos frentes de facturación:

### 1. Costos de Google Cloud Platform (GCP)

GCP tiene una capa "Always Free" (Siempre Gratuita) sumamente generosa que este proyecto aprovecha al máximo:

- **Cloud Run:** Te regala 2 millones de peticiones HTTP al mes. Es muy poco probable que pagues algo por este servicio en etapas iniciales.
- **Firestore:** Te regala 50,000 lecturas y 20,000 escrituras al día.
- **Cloud Build:** Ofrece 120 minutos de compilación gratuitos al día. Nuestros despliegues toman apenas segundos.
- **Vertex AI (Gemini):** Este es el único servicio que puede generar un costo desde el principio, ya que se cobra por cantidad de caracteres (Tokens) enviados y generados. Sin embargo, para texto, el costo es de fracciones de centavo por conversación. Es muy económico.

### 2. Costos de Meta (WhatsApp Cloud API)

Meta no cobra por enviar cada mensaje individualmente, sino por **"Conversaciones"** (ventanas de 24 horas).

- Una vez que el bot le responde a un usuario, se abre una ventana de 24 horas donde pueden intercambiar mensajes ilimitados.
- **Capa Gratuita:** Meta otorga **1,000 conversaciones de servicio gratuitas al mes**. (Una conversación "de servicio" es aquella que inicia el usuario).
- **Superado el límite:** Después de las primeras 1,000, Meta cobra una tarifa fija por conversación iniciada que varía según el país del usuario (para números en México, suele rondar entre los $0.01 y $0.03 USD por ventana de 24h).
- *Aviso:* Debes tener una tarjeta de crédito válida configurada en tu Administrador Comercial de Meta; de lo contrario, cuando llegues a las 1,000 conversaciones gratuitas, la API dejará de enviar mensajes.

# Dudas

- Escríbe al correo **floresca.diego@gmail.com**
import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
from PIL import Image
import base64
import io
import json
import streamlit.components.v1 as components


# Inicializar la sesión de estado para almacenar la estructura del mapa mental
if 'mapa_mental' not in st.session_state:
    st.session_state['mapa_mental'] = {
        'nombre': '',
        'imagen': '',
        'ramas': []
    }

# Definir colores para las categorías
categoria_colores = ['#1f77b4', '#2ca02c', '#9467bd', '#bcbd22', '#ff7f0e', '#d62728']

# Función para convertir imagen a base64
def get_image_base64(image_data):
    """
    Convierte una imagen en base64.
    Puede manejar imágenes en formato base64, objetos PIL o bytes.
    """
    if isinstance(image_data, str) and image_data.startswith("data:image"):  # Si ya es base64
        return image_data
    elif isinstance(image_data, Image.Image):  # Si la imagen es un objeto PIL
        buffered = io.BytesIO()
        image_data = image_data.resize((150, 150))  # Ajustar tamaño de la imagen a 150x150 píxeles
        image_data.save(buffered, format="PNG")  # Convertir imagen a bytes
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")
    elif isinstance(image_data, bytes):  # Si es un archivo cargado
        buffered = io.BytesIO(image_data)
        image = Image.open(buffered).resize((150, 150))
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")
    return None

# Función para agregar una nueva rama a un nodo específico
def agregar_rama(nodo):
    """
    Añade una nueva rama a un nodo dado.
    """
    nueva_rama = {
        'nombre': '',
        'imagen': '',
        'ramas': []
    }
    nodo['ramas'].append(nueva_rama)

# Función recursiva para renderizar el formulario de cada rama
def renderizar_ramas(nodo, ruta):
    """
    Renderiza un formulario en el sidebar para una rama específica.
    Permite ingresar el nombre y la imagen, y agregar sub-ramas.
    """
    for idx, rama in enumerate(nodo['ramas']):
        nueva_ruta = f"{ruta} -> Rama {idx + 1}"
        st.sidebar.markdown(f"### Nodo: {nueva_ruta}")
        
        # Entrada de texto para el nombre
        nombre = st.sidebar.text_input(f"Nombre de la idea en {nueva_ruta}", value=rama['nombre'], key=f"nombre_{nueva_ruta}")
        rama['nombre'] = nombre

        # Entrada para la imagen
        imagen = st.sidebar.file_uploader(f"Cargar imagen para {nueva_ruta}", type=["png", "jpg", "jpeg"], key=f"imagen_{nueva_ruta}")
        if imagen:
            imagen_base64 = get_image_base64(imagen.read())
            rama['imagen'] = imagen_base64
        elif not rama['imagen']:
            rama['imagen'] = ''

        # Botón para agregar una sub-rama
        if st.sidebar.button(f"Agregar rama a {nueva_ruta}", key=f"boton_agregar_{nueva_ruta}"):
            agregar_rama(rama)

        # Llamar recursivamente para renderizar sub-ramas
        renderizar_ramas(rama, nueva_ruta)

# Función recursiva para agregar nodos al grafo
def agregar_nodos_recursivamente(G, nodo, datos, color, edge_width_dict):
    """
    Añade nodos y edges al grafo de manera recursiva.
    """
    nombre = datos["nombre"]
    imagen = datos.get("imagen", None)
    G.add_node(nombre, type='central' if nodo == "root" else 'ramificado', image=imagen if imagen else None, color=color)
    
    if nodo != "root":
        G.add_edge(nodo, nombre, color=color, width=edge_width_dict.get(nodo, 1))
    
    ramas = datos.get("ramas", [])
    num_ramas = len(ramas)
    edge_width = max(1, 5 - num_ramas)  # Ajusta el grosor según el número de ramas
    edge_width_dict[nombre] = edge_width
    
    # Asignar color
    if color in categoria_colores:
        color_index = (categoria_colores.index(color) + 1) % len(categoria_colores)
        nuevo_color = categoria_colores[color_index]
    else:
        nuevo_color = 'gray'
    
    for rama in ramas:
        agregar_nodos_recursivamente(G, nombre, rama, nuevo_color, edge_width_dict)

# Función para crear el grafo
def crear_grafico_mind_map(datos_entrada):
    """
    Crea y visualiza el grafo del mapa mental usando Pyvis.
    """
    G = nx.Graph()
    edge_width_dict = {}
    
    if not datos_entrada['nombre']:
        st.warning("Por favor, ingresa la idea principal.")
        return
    
    # Iniciar con el nodo raíz
    raiz = datos_entrada["nombre"]
    raiz_imagen = datos_entrada.get("imagen", None)
    G.add_node(raiz, type='central', image=raiz_imagen if raiz_imagen else None, color=categoria_colores[0])
    
    ramas = datos_entrada.get("ramas", [])
    for rama in ramas:
        agregar_nodos_recursivamente(G, raiz, rama, categoria_colores[0], edge_width_dict)
    
    # Crear visualización con pyvis
    person_net = Network(
        height='600px',
        width='100%',
        bgcolor='#222222',
        font_color='white',
        notebook=False
    )
    
    # Configurar los nodos con imágenes, colores y tamaños
    for node, data in G.nodes(data=True):
        node_categoria = data.get('type', 'central')
        color = data.get('color', 'gray')  # Color por defecto si no se encuentra la categoría
        
        node_options = {
            "label": node,
            "shape": "circularImage" if data.get('image') else "circle",
            "image": data.get('image', ''),
            "color": color,
            "size": 80 if node_categoria == 'central' else 20,  # Tamaño más grande para el nodo central
            "fixed": {"x": False, "y": False}  # No fijar posición
        }
        person_net.add_node(node, **node_options)
    
    # Agregar edges con color y grosor
    for source, target, edge_data in G.edges(data=True):
        person_net.add_edge(source, target, color=edge_data.get('color', 'gray'), width=edge_data.get('width', 1))
    
    # Configurar layout del grafo con centrado
    person_net.repulsion(
        node_distance=200,
        central_gravity=0.33,
        spring_length=100,
        spring_strength=0.10,
        damping=0.95
    )
    
    # Agregar opciones para mantener el gráfico centrado
    person_net.set_options("""
        var options = {
            "physics": {
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000
                },
                "minVelocity": 0.75
            },
            "interaction": {
                "dragNodes": true,
                "zoomView": true
            }
        }
    """)
    
    # Guardar y mostrar grafo en HTML
    path = '/tmp'
    person_net.save_graph(f'{path}/pyvis_graph.html')
    
    with open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8') as HtmlFile:
        graph_html = HtmlFile.read()
    
    # Mostrar grafo en la app con Streamlit Components con ancho responsivo
    components.html(graph_html, height=600, width=800)

# Pestaña principal
def main():
    st.set_page_config(layout="wide")
    # Display the image above the title
    st.image('Mind Mapp.jpg', use_column_width=True)
    st.title("Generador de Mapas Mentales")
    # Agregar pestañas
    tabs = st.tabs(["Reseña del Libro", "Mapa Mental", "Acerca de mí"])

    # Pestaña: Reseña del libro
    with tabs[0]:
        resumen = """
        ## Resumen del libro: "Mapas Mentales" de Tony Buzan

        "Mapas Mentales" de Tony Buzan es una guía completa sobre la creación y uso de mapas mentales como herramienta para el pensamiento creativo, la organización de ideas y la mejora de la memoria. Tony Buzan, reconocido como el padre de los mapas mentales, introduce en este libro técnicas probadas para maximizar la eficiencia mental y potenciar el aprendizaje.

        ### **Conceptos Clave del Libro**

        1. **Estructura de los Mapas Mentales:**
           - **Idea Central:** Comienza con una idea o concepto principal en el centro de la página.
           - **Ramas Principales:** Se extienden desde la idea central, representando las ideas principales relacionadas.
           - **Palabras Clave:** Cada rama está etiquetada con palabras clave que representan conceptos importantes.
           - **Imágenes y Colores:** El uso de imágenes y colores ayuda a estimular el cerebro y facilita la memorización y comprensión.

        2. **Beneficios de los Mapas Mentales:**
           - **Mejora la Memoria:** La estructura visual facilita la retención de información.
           - **Fomenta la Creatividad:** Permite explorar múltiples conexiones y asociaciones de ideas.
           - **Organización Eficiente:** Ayuda a estructurar pensamientos de manera lógica y coherente.
           - **Resolución de Problemas:** Facilita la identificación de soluciones mediante el análisis visual de situaciones complejas.

        3. **Aplicaciones Prácticas:**
           - **Educación:** Para tomar apuntes, planificar estudios y resumir información.
           - **Negocios:** En la planificación de proyectos, brainstorming y presentaciones.
           - **Desarrollo Personal:** En la definición de metas, planificación de carrera y organización de ideas personales.

        4. **Técnicas Avanzadas:**
           - **Asociaciones Liberadas:** Estimula la generación de ideas sin restricciones.
           - **Uso de Símbolos y Dibujo:** Potencia la creatividad y hace que los mapas sean más atractivos visualmente.
           - **Integración de Información:** Combina diferentes fuentes de información en un solo mapa mental para una visión holística.

        ### **Métodos de Creación de Mapas Mentales**

        - **Inicio Central:** Colocar la idea principal en el centro y dibujar ramas radiales hacia las ideas secundarias.
        - **Palabras Clave:** Utilizar palabras breves que capturen la esencia de cada idea.
        - **Colores y Símbolos:** Aplicar diferentes colores para categorizar información y símbolos para representar conceptos.
        - **Jerarquía Visual:** Utilizar tamaños de fuente y grosor de líneas para indicar la importancia relativa de las ideas.

        ### **Conclusión**

        "Mapas Mentales" de Tony Buzan es una herramienta poderosa para cualquier persona que busque mejorar su capacidad de pensar, organizar ideas y aprender de manera más efectiva. El libro no solo explica la teoría detrás de los mapas mentales, sino que también proporciona instrucciones prácticas para su implementación en diversas áreas de la vida personal y profesional.
        """
        st.markdown(resumen)

    # Pestaña: Mapa Mental
    with tabs[1]:
        st.header("Mapa Mental")
        st.sidebar.subheader("Ingresar Datos del Mapa Mental:")

        # Formulario para la idea principal
        st.sidebar.markdown("## Idea Principal")
        nombre_principal = st.sidebar.text_input(
            "Ingrese el nombre de la idea principal:", 
            st.session_state['mapa_mental']['nombre'], 
            key="nombre_principal"
        )
        
        imagen_principal = st.sidebar.file_uploader(
            "Cargue una imagen para la idea principal", 
            type=["png", "jpg", "jpeg"], 
            key="imagen_principal"
        )
        if imagen_principal:
            imagen_base64 = get_image_base64(imagen_principal.read())
            st.session_state['mapa_mental']['imagen'] = imagen_base64
        elif not st.session_state['mapa_mental']['imagen']:
            st.session_state['mapa_mental']['imagen'] = ''
        
        st.session_state['mapa_mental']['nombre'] = nombre_principal
        
        st.sidebar.markdown("---")
        
        # Botón para agregar rama a la idea principal
        if st.sidebar.button("Agregar rama a la idea principal"):
            agregar_rama(st.session_state['mapa_mental'])
        
        # Renderizar las ramas de la idea principal
        if st.session_state['mapa_mental']['nombre']:
            renderizar_ramas(st.session_state['mapa_mental'], "Idea Principal")
        
        st.sidebar.markdown("---")
        
        # Botón para resetear el mapa mental
        if st.sidebar.button("Resetear Mapa Mental"):
            st.session_state['mapa_mental'] = {
                'nombre': '',
                'imagen': '',
                'ramas': []
            }
            st.experimental_rerun()
        
        # Botón para generar el grafo
        if st.sidebar.button("Generar Mapa Mental"):
            crear_grafico_mind_map(st.session_state['mapa_mental'])

    # Pestaña: Acerca de mí
    with tabs[2]:
        st.header("Acerca de mí")
        acerca_de_mi = """
        ¡Hola! Soy Migue, desarrollo herramientas para facilitar la visualización y organización de ideas mediante mapas mentales interactivos. Esta aplicación está diseñada para ayudarte a estructurar tus pensamientos de manera eficiente y creativa, utilizando tecnologías como Streamlit, Pyvis y NetworkX.

        **Características de la Aplicación:**
        - **Interfaz Intuitiva:** Agrega ideas principales y sus ramas de forma sencilla.
        - **Visualización Interactiva:** Explora tus mapas mentales de manera dinámica y visualmente atractiva.
        - **Personalización:** Asigna imágenes y colores a tus nodos para una mejor organización y estética.

        **Contacto:**
        - **Correo Electrónico:** [mail](mailto:josemiguelaguilart.com)
        - **LinkedIn:** [LinkedIn](https://www.linkedin.com/in/josemaguilar/)

        """
        st.markdown(acerca_de_mi)

if __name__ == "__main__":
    main()

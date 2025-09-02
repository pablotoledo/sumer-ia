from mcp_agent.core.fastagent import FastAgent
# Importa las definiciones de los agentes para que el orquestador los conozca
from agents import transcription_agents 

# Inicializa la aplicación fast-agent
fast = FastAgent("TranscriptionWorkflow")

# Define el flujo Evaluador-Optimizador para el formateo verificado
@fast.evaluator_optimizer(
    name="verified_formatter",
    generator="formatter",
    evaluator="quality_evaluator",
    max_refinements=3 # Intentará corregir hasta 3 veces
)

# Define el Orquestador principal que gestiona todo el proceso
@fast.orchestrator(
    name="master_orchestrator",
    agents=["segmenter", "titler", "verified_formatter"],
    instruction="""
    Tu objetivo es estructurar una transcripción de texto en bruto.
    1. Primero, usa el agente 'segmenter' para dividir el texto en fragmentos temáticos.
    2. Para cada fragmento, usa el agente 'titler' para generar un título.
    3. Para cada fragmento con título, usa el flujo 'verified_formatter' para aplicar formato y asegurar que no haya pérdida de información ni alucinaciones.
    4. Finalmente, ensambla todos los fragmentos procesados en un único documento Markdown.
    """
)
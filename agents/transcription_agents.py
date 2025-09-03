from pathlib import Path

# Nota: Este archivo requiere fast-agent-mcp para funcionar en producción
# from workflows.main_workflow import fast

class PlaceholderAgent:
    """Placeholder para definiciones de agentes cuando fast-agent no está disponible"""
    def __init__(self, name, instruction, servers=None):
        self.name = name
        self.instruction = instruction
        self.servers = servers or []

# Definiciones de agentes - reemplazar con decoradores @fast.agent cuando fast-agent esté disponible

# Agente para segmentar el texto en temas
segmenter = PlaceholderAgent(
    name="segmenter",
    instruction="Analiza el texto proporcionado y divídelo en una lista de fragmentos de texto, donde cada fragmento es temáticamente coherente. Responde solo con la lista de fragmentos."
)

# Agente para titular cada fragmento
titler = PlaceholderAgent(
    name="titler",
    instruction="Dado un fragmento de texto, genera un título conciso y descriptivo. NO resumas el contenido. Responde únicamente con el título."
)

# Agente Generador: aplica el formato
formatter = PlaceholderAgent(
    name="formatter",
    instruction=Path("./prompts/formatter_prompt.md")
)

# Agente Evaluador: verifica la calidad
quality_evaluator = PlaceholderAgent(
    name="quality_evaluator",
    instruction="""
    Evalúa la salida del formateador comparando el texto original con el formateado.
    Usa la herramienta 'fidelity_check' para asegurar que el significado no ha cambiado.
    Usa la herramienta 'hallucination_check' para asegurar que no se ha añadido información.
    Si ambas comprobaciones pasan, responde con 'PASS'.
    Si alguna falla, responde con 'FAIL' y proporciona feedback específico y accionable para que el generador pueda corregir el error.
    """,
    servers=["verification_tools"] 
)

# Cuando fast-agent esté disponible, reemplazar las definiciones anteriores con:
"""
from workflows.main_workflow import fast

@fast.agent(
    name="segmenter",
    instruction="Analiza el texto proporcionado y divídelo en una lista de fragmentos de texto, donde cada fragmento es temáticamente coherente. Responde solo con la lista de fragmentos."
)

@fast.agent(
    name="titler",
    instruction="Dado un fragmento de texto, genera un título conciso y descriptivo. NO resumas el contenido. Responde únicamente con el título."
)

@fast.agent(
    name="formatter",
    instruction=Path("./prompts/formatter_prompt.md")
)

@fast.agent(
    name="quality_evaluator",
    instruction=\"\"\"
    Evalúa la salida del formateador comparando el texto original con el formateado.
    Usa la herramienta 'fidelity_check' para asegurar que el significado no ha cambiado.
    Usa la herramienta 'hallucination_check' para asegurar que no se ha añadido información.
    Si ambas comprobaciones pasan, responde con 'PASS'.
    Si alguna falla, responde con 'FAIL' y proporciona feedback específico y accionable para que el generador pueda corregir el error.
    \"\"\",
    servers=["verification_tools"] 
)
"""
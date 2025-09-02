from pathlib import Path
from workflows.main_workflow import fast

# Agente para segmentar el texto en temas
@fast.agent(
    name="segmenter",
    instruction="Analiza el texto proporcionado y divídelo en una lista de fragmentos de texto, donde cada fragmento es temáticamente coherente. Responde solo con la lista de fragmentos."
)

# Agente para titular cada fragmento
@fast.agent(
    name="titler",
    instruction="Dado un fragmento de texto, genera un título conciso y descriptivo. NO resumas el contenido. Responde únicamente con el título."
)

# Agente Generador: aplica el formato
@fast.agent(
    name="formatter",
    # Carga el prompt desde un archivo externo para mayor claridad
    instruction=Path("./prompts/formatter_prompt.md")
)

# Agente Evaluador: verifica la calidad
@fast.agent(
    name="quality_evaluator",
    instruction="""
    Evalúa la salida del formateador comparando el texto original con el formateado.
    Usa la herramienta 'fidelity_check' para asegurar que el significado no ha cambiado.
    Usa la herramienta 'hallucination_check' para asegurar que no se ha añadido información.
    Si ambas comprobaciones pasan, responde con 'PASS'.
    Si alguna falla, responde con 'FAIL' y proporciona feedback específico y accionable para que el generador pueda corregir el error.
    """,
    # Habilita el uso del servidor MCP definido en el config
    servers=["verification_tools"] 
)
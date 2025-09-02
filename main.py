import asyncio
from workflows.main_workflow import fast

async def main():
    # Carga aquí tu transcripción en bruto
    raw_transcript = "en 2018 investigadores de cornell construyeron un detector de alta potencia que en combinación con un proceso algorítmico llamado ticografía estableció un récord mundial al triplicar la resolución de un microscopio electrónico de última generación..."

    print("Iniciando el flujo de trabajo de estructuración de transcripción...")
    
    # fast.run() inicializa todos los agentes y flujos de trabajo definidos
    async with fast.run() as agent_app:
        # Llama al orquestador principal para procesar el texto
        structured_document = await agent_app.master_orchestrator.send(raw_transcript)
        
        print("\n--- Documento Estructurado Final ---\n")
        print(structured_document)

if __name__ == "__main__":
    asyncio.run(main())
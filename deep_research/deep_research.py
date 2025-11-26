import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str, clarifications: str):

    full_query = query

    if clarifications and clarifications.strip():
        full_query += (
            "\n\nAclaraciones adicionales del usuario para dar más contexto:\n"
            + clarifications.strip()
        )

    should_show_clarifications_box = not (clarifications and clarifications.strip())

    first_chunk = True
    async for chunk in ResearchManager().run(full_query):
        if first_chunk and should_show_clarifications_box:
            first_chunk = False
            yield chunk, gr.update(visible=True)
        else:
            first_chunk = False
            yield chunk, gr.update()


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Búsqueda Profunda")

    query_textbox = gr.Textbox(
        label="¿Sobre qué tema te gustaría investigar?",
        placeholder="Ejemplo: Impacto de la IA en la educación superior",
    )

    clarifications_textbox = gr.Textbox(
        label="Aclaraciones / contexto adicional (opcional)",
        placeholder=(
            "Después de que el sistema te muestre preguntas aclaratorias, "
            "escribe aquí tus respuestas para refinar la investigación."
        ),
        lines=6,
        visible=False,
    )

    run_button = gr.Button("Ejecutar", variant="primary")
    report = gr.Markdown(label="Informe")

    run_button.click(
        fn=run,
        inputs=[query_textbox, clarifications_textbox],
        outputs=[report, clarifications_textbox],
    )
    query_textbox.submit(
        fn=run,
        inputs=[query_textbox, clarifications_textbox],
        outputs=[report, clarifications_textbox],
    )

ui.launch(inbrowser=True)


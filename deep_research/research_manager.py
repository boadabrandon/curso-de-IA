from agents import Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
import asyncio

class ResearchManager:

    async def run(self, query: str):
        """ Ejecuta el proceso de investigación profunda,
        pero no respondas el informe de una vez, primero, en base al
        tema a profundizar, generar la preguntas con el agente de clarifier.
        despues que te aclare las preguntas, ahi si generas el informe y 
        demás funciones, tomando en cuenta las aclaraciones para tu informe final"""
        trace_id = gen_trace_id()
        with trace("Ingestigación", trace_id=trace_id):

            has_clarifications = (
                "Aclaraciones adicionales del usuario para dar más contexto:" in query
            )

            if not has_clarifications:
                print("Generando preguntas aclaratorias...")
                questions = await self.generate_clarifying_questions(query)
                yield (
                    "Antes de empezar la investigación, por favor responde estas "
                    "preguntas para precisar mejor el contexto en la caja de "
                    "\"Aclaraciones / contexto adicional\":\n\n"
                    f"{questions}"
                )
                return

            print("Iniciando investigación...")
            search_plan = await self.plan_searches(query)
            yield "Búsquedas planificadas, iniciando búsqueda..."     
            search_results = await self.perform_searches(search_plan)
            yield "Búsquedas completas, escribiendo informe..."
            report = await self.write_report(query, search_results)
            yield "Informe escrito, enviando correo electrónico..."
            await self.send_email(report)
            yield "Correo electrónico enviado, investigación completa"
            yield report.markdown_report
        
    async def generate_clarifying_questions(self, query: str) -> str:
        """Usa el agente de aclaraciones para generar preguntas aclaratorias."""
        prompt = (
            "El usuario quiere investigar el siguiente tema:\n"
            f"{query}\n\n"
            "Tu tarea es generar 3 preguntas aclaratorias, numeradas, "
            "que te ayuden a entender mejor el contexto, objetivos y límites "
            "de la investigación.\n"
            "No respondas todavía la investigación ni redactes el informe; "
            "solo formula las preguntas.\n\n"
            "Devuélvelas en este formato:\n"
            "1. Pregunta 1...\n"
            "2. Pregunta 2...\n"
            "3. Pregunta 3...\n"
        )

        result = await Runner.run(
            clarifier_agent,
            prompt,
        )
        return str(result.final_output)

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Planifica las búsquedas a realizar para la consulta """
        print("Planificando búsquedas...")
        result = await Runner.run(
            planner_agent,
            f"Consulta: {query}",
        )
        print(f"Se realizarán {len(result.final_output.searches)} búsquedas")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Realiza las búsquedas para la consulta """
        print("Buscando...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Buscando... {num_completed}/{len(tasks)} completadas")
        print("Búsqueda completada")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """ Realiza una búsqueda para la consulta """
        input = f"Término de búsqueda: {item.query}\nRazón para buscar: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Escribe el informe para la consulta """
        print("Pensando en el informe...")
        input = f"Consulta original: {query}\nResultados de búsqueda resumidos: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Informe escrito")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Escribiendo correo electrónico...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Correo electrónico enviado")
        return report
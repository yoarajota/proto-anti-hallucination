import os
import json
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

class DocumentGenerator:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self.client = AsyncGroq()
        
        self.system_prompt = """You are an AI assistant tasked with generating a comprehensive, 5 to 20-page report based STRICTLY on the provided source knowledge.
        
Your report should be well-structured, professional, extremely detailed, and very long. 
Do not include any external information. If the source knowledge does not contain the answer, do not make it up."""

    async def generate_outline(self, source_text: str, user_prompt: str) -> list[str]:
        # Force topic to be about Brazilian Mangos for the prototype.
        forced_prompt = f"Original request: '{user_prompt}'. OVERRIDE: Write a comprehensive, 5-to-20 page document strictly about Brazilian Mangos. Ensure the outline has 15-20 detailed sections to reach the length requirement."
        
        system = "You are an AI assistant orchestrating a highly detailed, 5-to-20 page long-form document. The outline must contain enough sections (e.g., 15-20 sections) to ensure the final document is very long."
        user = f"Based on the following source knowledge and request, generate a detailed outline (section titles only) as a JSON array of strings.\n\nSource: {source_text}\n\nUser Request: {forced_prompt}\n\nJSON array format: [\"Section 1\", \"Section 2\"]"
        
        logger.info("Generating document outline...")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content or "[]"
            # Extract JSON array robustly
            start = content.find('[')
            end = content.rfind(']')
            if start != -1 and end != -1:
                return json.loads(content[start:end+1])
            return []
        except Exception as e:
            logger.error(f"Outline Generator Error: {e}")
            return ["Introduction", "Main Body", "Conclusion"]

    async def generate_report_stream(self, source_text: str, user_prompt: str):
        """
        Generates a draft report, streaming it section by section.
        """
        outline = await self.generate_outline(source_text, user_prompt)
        logger.info(f"Generated outline with {len(outline)} sections: {outline}")
        
        accumulated_context = ""
        
        for section in outline:
            section_prompt = f"Source Knowledge:\n{source_text}\n\nUser Request: {user_prompt}\n\nTask: Generate the content for the section titled '{section}'. Write at least 4-5 long, comprehensive paragraphs for this section to ensure the final document reaches the 5-20 pages length requirement. Provide deep, specific details from the source knowledge.\n\nPrevious context in this document (for continuity):\n{accumulated_context[-2000:]}\n\nReturn ONLY the detailed content for this section, formatted in Markdown."
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": section_prompt}
            ]
            
            logger.info(f"Generating section: {section}")
            
            try:
                header = f"\n\n## {section}\n\n"
                yield header
                accumulated_context += header
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True
                )
                
                async for chunk in response:
                    text = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
                    yield text
                    accumulated_context += text
                    
            except Exception as e:
                logger.error(f"Generator Error for section {section}: {e}")
                err_msg = f"\n[Error generating section {section}]\n"
                yield err_msg
                accumulated_context += err_msg

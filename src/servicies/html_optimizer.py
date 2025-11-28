from lxml import html
import requests

import openai

from src.core.constants import GPT_API_KEY


class HTMLOptimizer:

    def __init__(self, query):
        self.scripts = []
        self.styles = []
        page = requests.get(query).content
        tree = html.fromstring(page)

        self.head = tree.find('head')
        self.body = tree.find('body')
        self._extract_scripts()
        self._extract_styles()

        self.head_str = html.tostring(self.head, encoding='unicode', method='html')
        self.body_str = html.tostring(self.body, encoding='unicode', method='html')

    def _extract_scripts(self):
        if self.head is not None:
            self.scripts = self.head.findall('.//script')
            for script in self.scripts:
                script.getparent().remove(script)

    def _extract_styles(self):
        if self.head is not None:
            self.styles = self.head.findall('.//style')
            for style in self.styles:
                style.getparent().remove(style)

    async def optimize(self):
        client = openai.OpenAI(
            api_key=GPT_API_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project="b1gs54f9vbkh4nmvr8ef"

        )

        response2 = client.responses.create(
            prompt={
                "id": "fvtnisbnrsuolsccso07",
                "variables": {
                    "body": self.body_str,
                }
            },
            input="Верни ТОЛЬКО HTML",
        )

        response1 = client.responses.create(
            prompt={
                "id": "fvt3h8l7vkkv9aab12ua",
                "variables": {
                    "head": self.head_str,
                }
            },
            input="Верни ТОЛЬКО HTML",
        )


        return response1.output_text, response2.output_text

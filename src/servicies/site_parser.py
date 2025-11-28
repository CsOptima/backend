import requests
from lxml import html


class SiteParser:
    @staticmethod
    def extract_text(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()

        tree = html.fromstring(response.content)

        text_content = tree.xpath(
            '//text()[not(ancestor::script)][not(ancestor::style)][not(ancestor::meta)]'
            '[not(ancestor::noscript)][not(ancestor::iframe)]'
        )

        cleaned_text = ' '.join([
            ' '.join(text.strip().split())
            for text in text_content
            if text.strip() and not text.isspace()
               and not any(char in text for char in ['{', '}', '<', '>', '[', ']'])
        ])

        return cleaned_text

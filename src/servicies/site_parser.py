import requests
from bs4 import BeautifulSoup
from lxml import html
from markdownify import markdownify as md


class SiteParser:

    @staticmethod
    def load_page(url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content.decode('utf-8'), "html.parser")

        for img in soup.find_all("img"):
            img.decompose()

        for a in soup.find_all("a"):
            #a.unwrap()
            a.decompose()

        markdown = md(str(soup), strip=['a', 'img'])

        lines = [line for line in markdown.splitlines() if line.strip()]
        return "\n".join(lines)

    @staticmethod
    def extract_text(url) -> str:
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

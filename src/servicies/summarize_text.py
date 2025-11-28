import requests

from src.core.constants import SUMMARIZER_IP


class SummarizerText:
    @staticmethod
    def summarize_text(text):

        url = f"http://{SUMMARIZER_IP}:8001/summarize"
        payload = {
            "text": text,
            "min_length": 100,
            "max_length": 300,
            "num_beams": 4
        }
        headers = {"Content-Type": "application/json"}

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()

        return resp.json()['summary_text']


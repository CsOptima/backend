import requests

from src.core.constants import LLM_IP


class LLMAsker:
    @staticmethod
    def ask_llm(subject):

        url = f"http://{LLM_IP}:8000/queries"
        payload = {
            "message": subject,
        }
        headers = {"Content-Type": "application/json"}

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()

        return resp.json()['queries']


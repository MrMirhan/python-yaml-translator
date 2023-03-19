import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

class OAITranslated:
    def __init__(self, result, source, to):
        self.result = result
        self.source = source
        self.to = to

    def __str__(self):
        return self.result

    def __repr__(self):
        return self.__str__()

class OAITranslator:
    def __init__(self, api_key):
        openai.api_key = api_key
        self.spentTokens = 0

    def translate(self, text, to):
        prompt = "The given text is from the YAML file, respect of the special characters, symbols and names in the following text. Translate this into {{to_lang}} (short code of the language): `{{text}}`\n\nTranslated Text: "
        prompt = prompt.replace("{{text}}", text)
        prompt = prompt.replace("{{to_lang}}", to)

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20))
        def completion_with_backoff(**kwargs):
            return openai.Completion.create(**kwargs)

        response = completion_with_backoff(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.9,
            max_tokens=4000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=["\n"]
        )
        result = response["choices"][0]["text"]
        self.spentTokens += response["usage"]["total_tokens"]
        return OAITranslated(result, text, to)
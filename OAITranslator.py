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
    def __init__(self, api_key, engine):
        try:
            openai.api_key = api_key
        except openai.APIError as e:
            print("OpenAI API key is invalid")
            exit()
        self.spentTokens = 0
        self.engine = engine
        self.prompt = "The given text is from the YAML file, respect of the special characters, symbols and names in the following text. Any value between {} or () is special value. Any char after '&' like '&c' is special value. Any value like 'ezcolors.color.water' is special value. Translate this into {{to_lang}} (short code of the language): `{{text}}`\n\nTranslated Text: "
        self.messages = [
            {"role": "system", "content": "The given text is from the YAML file, respect of the special characters, symbols and names in the following text. Any value between {} or () is special value. Any char after '&' like '&c' is special value. Any value like 'ezcolors.color.water' is special value."}
        ]

    def translate(self, text, to):
        if self.engine == "gpt-4":
            self.messages.append(
                {"role": "user", "content": f"Translate this into {to} (short code of the language): `{text}`"}
            )
        else:
            prompt = self.prompt.replace("{{text}}", text)
            prompt = prompt.replace("{{to_lang}}", to)

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20))
        def chat_completion_with_backoff(**kwargs):
            return openai.ChatCompletion.create(**kwargs)
        
        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(20))
        def completion_with_backoff(**kwargs):
            return openai.Completion.create(**kwargs)

        if self.engine == "gpt-4":
            response = chat_completion_with_backoff(
                model=self.engine,
                messages=self.messages,
                temperature=1.2,
                max_tokens=500
            )
            result = response["choices"][0]["message"]["content"]
            self.messages.append(
                {"role": "translator", "content": f"{result}"}
            )
        else:
            response = completion_with_backoff(
            model=self.engine,
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
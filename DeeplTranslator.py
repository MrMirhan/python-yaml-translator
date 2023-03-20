from deepl import deepl
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import asyncio

class DeeplTranslated:
    def __init__(self, result, source, to):
        self.result = result
        self.source = source
        self.to = to

    def __str__(self):
        return self.result

    def __repr__(self):
        return self.__str__()

class DeeplTranslator:
    def __init__(self):
        pass

    @retry(wait=wait_random_exponential(min=30, max=120), stop=stop_after_attempt(60))
    async def _translate(self, text: str, to: str) -> str:
        t = deepl.DeepLCLI("auto", to)
        return await t.translate(text, asynchronous=True)
    
    def translate(self, text, to):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        translation_task = loop.create_task(self._translate(text, to))
        while not translation_task.done():
            loop.run_until_complete(asyncio.sleep(1))
        result = translation_task.result()
        return DeeplTranslated(result, text, to)
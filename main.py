import concurrent.futures
import ruamel.yaml as yaml
import config
import os, io, calendar, time, sys
from threading import Thread

from translatepy.translators import GoogleTranslate, YandexTranslate, TranslateComTranslate, BingTranslate, MicrosoftTranslate, ReversoTranslate, MyMemoryTranslate
from DeeplTranslator import DeeplTranslator
from OAITranslator import OAITranslator

translator = None;

if config.TRANSLATOR == "google":
    translator = GoogleTranslate()
elif config.TRANSLATOR == "yandex":
    translator = YandexTranslate()
elif config.TRANSLATOR == "translatecom":
    translator = TranslateComTranslate()
elif config.TRANSLATOR == "microsoft":
    translator = MicrosoftTranslate()
elif config.TRANSLATOR == "bing":
    translator = BingTranslate()
elif config.TRANSLATOR == "reverso":
    translator = ReversoTranslate()
elif config.TRANSLATOR == "mymemory":
    translator = MyMemoryTranslate()
elif config.TRANSLATOR == "ai":
    translator = OAITranslator(config.OPENAI_KEY, config.OPENAI_ENGINE)
elif config.TRANSLATOR == "deepl":
    translator = DeeplTranslator()
else:
    print("Translator not found")
    exit()

total_translated = 0
passed_times = []
attempted = []

total_translated_files = 0

first_timestamp = calendar.timegm(time.gmtime())

def translate_value(value):
    global total_translated
    global passed_times
    global attempted
    global first_timestamp
    if isinstance(value, str):
        # translate string values
        if value == "" or value == " " or value == None:
            return value
        start_timestamp = calendar.timegm(time.gmtime())
        attempts = 0
        response = value
        while attempts < 10:
            attempts += 1
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=config.NUM_WORKERS) as executor:
                    result = executor.submit(translator.translate, value, config.TO)
                    if result.result().result != response:
                        response = result.result().result
                        break
            except Exception as e:
                continue
        attempted.append(attempts)
        end_timestamp = calendar.timegm(time.gmtime())
        passed_time = end_timestamp - start_timestamp
        passed_times.append(passed_time)
        total_translated += 1
        return response
    elif isinstance(value, list):
        # translate list values recursively
        return [translate_value(item) for item in value]
    elif isinstance(value, dict):
        # translate dictionary values recursively
        return {key: translate_value(val) for key, val in value.items()}
    else:
        # pass non-translatable values unchanged
        return value
    
def print_progress():
    global total_translated_files
    global total_translated
    global passed_times
    global attempted
    global first_timestamp
    
    while total_translated_files < len(os.listdir(config.INPUT_FOLDER)):
        try:
            end_timestamp = calendar.timegm(time.gmtime())
            status = f"Total translated files: {total_translated_files} Total translated: {total_translated} Avg passed time: {round(sum(passed_times) / len(passed_times), 2)} Avg attemps: {round(sum(attempted) / len(attempted), 2)} Total passed time: {end_timestamp - first_timestamp}"
            if config.TRANSLATOR == "ai":
                status += f" Total spent Tokens: {translator.spentTokens}"
            print(status)
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
        except:
            pass
        time.sleep(0.5)

def main():
    global total_translated_files
    thread = Thread(target=print_progress, args=( ), daemon=True)
    thread.start()
    # loop over files in input directory
    for filename in os.listdir(config.INPUT_FOLDER):
        # read YAML file
        with open(os.path.join(config.INPUT_FOLDER, filename), 'r+b') as f:
            print("reading to file: ", config.INPUT_FOLDER + filename)
            data = yaml.safe_load(f)

        # translate YAML data
        translated_data = translate_value(data)

        # save translated YAML data to output file
        with io.open(os.path.join(config.OUTPUT_FOLDER, filename), 'w', encoding='utf-8') as f:
            print("writing to file: ", config.OUTPUT_FOLDER + filename)
            yaml.dump(translated_data, f, default_flow_style=False, allow_unicode=True)
            total_translated_files = total_translated_files + 1
    thread.join()

if __name__ == "__main__":
    main()
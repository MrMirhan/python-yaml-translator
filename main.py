import concurrent.futures
import ruamel.yaml as yaml
import config
import os
from translatepy.translators import google, yandex, translatecom, microsoft, reverso, mymemory

translator = None;

if config.TRANSLATOR == "google":
    translator = google.GoogleTranslate()
elif config.TRANSLATOR == "yandex":
    translator = yandex.YandexTranslate()
elif config.TRANSLATOR == "translatecom":
    translator = translatecom.TranslateComTranslate()
elif config.TRANSLATOR == "microsoft":
    translator = microsoft.MicrosoftTranslate()
elif config.TRANSLATOR == "reverso":
    translator = reverso.ReversoTranslate()
elif config.TRANSLATOR == "mymemory":
    translator = mymemory.MyMemoryTranslate()

def translate_list(base_dict, key):
    value_list = base_dict[key]
    base_dict[key] = []
    for string in value_list:
        attempts = 0
        while attempts < 10:
            attempts = attempts + 1
            translated = translator.translate(string, config.TO)
            if translated.result != translated.source:
                base_dict[key].append(translated.result)
                break
            else:
                if attempts == 10:
                    base_dict[key].append(translated.result)


def translate_key(base_dict, key):
    if type(base_dict[key]) is dict:
        for inner_key in base_dict[key]:
            translate_key(base_dict[key], inner_key)
    elif type(base_dict[key]) is list:
        translate_list(base_dict, key)
    else:
        attempts = 0
        while attempts < 10:
            attempts = attempts + 1
            translated = translator.translate(base_dict[key], config.TO)
            if translated.result != translated.source:
                base_dict[key] = translated.result
                break
            else:
                base_dict[key] = translated.result

for filename in os.listdir(config.INPUT_FOLDER):
    f = os.path.join(config.INPUT_FOLDER, filename)
    if os.path.isfile(f):
        with open(f, "r+b") as toLoad:
            print("reading to file: ", config.INPUT_FOLDER + filename)
            to_translate = yaml.safe_load(toLoad)
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.NUM_WORKERS) as executor:
            futures = {executor.submit(translate_key, to_translate, key) for key in to_translate}
            concurrent.futures.wait(futures)
        with open(config.OUTPUT_FOLDER + filename, 'w') as out:
            print("writing to file: ", config.OUTPUT_FOLDER + filename)
            yaml.dump(to_translate, out, default_flow_style=False, allow_unicode=True)
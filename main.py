import concurrent.futures
import ruamel.yaml as yaml
import config
import os

import calendar
import time

from translatepy.translators import google, yandex, translatecom, microsoft, reverso, mymemory
from OAITranslator import OAITranslator

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
elif config.TRANSLATOR == "ai":
    translator = OAITranslator(config.OPENAI_KEY)

total_translated = 0
passed_times = []
attempted = []

first_timestamp = calendar.timegm(time.gmtime())

def translate_list(base_dict, key):
    global total_translated
    global passed_times
    global attempted
    global first_timestamp
    value_list = base_dict[key]
    base_dict[key] = []
    start_timestamp = calendar.timegm(time.gmtime())
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
                    break
        try:
            attempted.append(attempts)
            end_timestamp = calendar.timegm(time.gmtime())
            passed_time = end_timestamp - start_timestamp
            passed_times.append(passed_time)
            total_translated = total_translated + 1
            print("Total translated: ", total_translated, "Avg passed time: ", sum(passed_times) / len(passed_times), "Avg attemps: ", sum(attempted) / len(attempted), "Total passed time: ", end_timestamp - first_timestamp, end="\r")
        except Exception as e:
            print("Error", e)
        
def translate_key(base_dict, key):
    global total_translated
    global passed_times
    global attempted
    global first_timestamp
    start_timestamp = calendar.timegm(time.gmtime())
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
                if attempts == 10:
                    base_dict[key] = translated.result
                    break
        try:
            attempted.append(attempts)
            end_timestamp = calendar.timegm(time.gmtime())
            passed_time = end_timestamp - start_timestamp
            passed_times.append(passed_time)
            total_translated = total_translated + 1
            print("Total translated: ", total_translated, "Avg passed time: ", sum(passed_times) / len(passed_times), "Avg attemps: ", sum(attempted) / len(attempted), "Total passed time: ", end_timestamp - first_timestamp, end="\r")
        except Exception as e:
            print("Error", e)

print("Translator mode:", config.TRANSLATOR)
print("Translating to:", config.TO)
print("Translator threads:", config.NUM_WORKERS)
print("Input Folder:", config.INPUT_FOLDER)
print("Output Folder:", config.OUTPUT_FOLDER)
print("Files will be translate:", len(os.listdir(config.INPUT_FOLDER)))

for filename in os.listdir(config.INPUT_FOLDER):
    f = os.path.join(config.INPUT_FOLDER, filename)
    if os.path.isfile(f):
        with open(f, "r+b") as toLoad:
            print("reading to file: ", config.INPUT_FOLDER + filename)
            print()
            to_translate = yaml.safe_load(toLoad)
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.NUM_WORKERS) as executor:
            futures = {executor.submit(translate_key, to_translate, key) for key in to_translate}
            concurrent.futures.wait(futures)
            # wait for the threads to finish
        with open(config.OUTPUT_FOLDER + filename, 'w') as out:
            print()
            if config.TRANSLATOR == "ai":
                print("Total translated: ", total_translated, "Avg passed time: ", sum(passed_times) / len(passed_times), "Avg attemps: ", sum(attempted) / len(attempted), "Total passed time: ", calendar.timegm(time.gmtime()) - first_timestamp, "Total spent Tokens: ", translator.spentTokens)
            else:
                print("Total translated: ", total_translated, "Avg passed time: ", sum(passed_times) / len(passed_times), "Avg attemps: ", sum(attempted) / len(attempted), "Total passed time: ", calendar.timegm(time.gmtime()) - first_timestamp)
            print("writing to file: ", config.OUTPUT_FOLDER + filename)
            yaml.dump(to_translate, out, default_flow_style=False, allow_unicode=True)
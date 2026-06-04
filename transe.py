import json
import urllib.request
import urllib.parse
import random
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_FILE = "ja_jp.json"
OUTPUT_FILE = "reverse_lang.json"
CACHE_FILE = "translate_cache.json"

TRANSLATE_COUNT = 20
FINAL_LANG = "ja"
THREADS = 30

LANGS = [
"af","sq","am","ar","hy","az","eu","be","bn","bs","bg","ca","ceb","ny","zh-cn","zh-tw",
"co","hr","cs","da","nl","en","eo","et","tl","fi","fr","fy","gl","ka","de","el","gu",
"ht","ha","haw","he","hi","hmn","hu","is","ig","id","ga","it","ja","jw","kn","kk","km",
"ko","ku","ky","lo","la","lv","lt","lb","mk","mg","ms","ml","mt","mi","mr","mn","my",
"ne","no","ps","fa","pl","pt","pa","ro","ru","sm","gd","sr","st","sn","sd","si","sk",
"sl","so","es","su","sw","sv","tg","ta","te","th","tr","uk","ur","uz","vi","cy","xh",
"yi","yo","zu"
]

def log_error(msg):
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def translate(text, target):

    url = "https://translate.googleapis.com/translate_a/single"

    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "q": text
    }

    url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())

    return data[0][0][0]


# キャッシュ読み込み
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    print("キャッシュ読み込み:", len(cache))
else:
    cache = {}


def chaos_translate(text):

    if text in cache:
        return cache[text]

    current = text

    for i in range(TRANSLATE_COUNT):

        lang = random.choice(LANGS)

        try:
            current = translate(current, lang)
        except Exception as e:
            log_error(f"{lang} : {e}")

    try:
        current = translate(current, FINAL_LANG)
    except Exception as e:
        log_error(f"final : {e}")

    cache[text] = current
    return current


def progress_bar(done, total):

    bar_length = 40
    percent = done / total
    filled = int(bar_length * percent)

    bar = "█" * filled + "-" * (bar_length - filled)

    sys.stdout.write(f"\r[{bar}] {done}/{total} ({percent*100:.1f}%)")
    sys.stdout.flush()


# 入力 lang
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lang = json.load(f)


# 途中結果読み込み
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        output = json.load(f)
    print("途中翻訳読み込み:", len(output))
else:
    output = {}


# 未翻訳だけ抽出
remaining = [(k, v) for k, v in lang.items() if k not in output]

total = len(lang)
done = len(output)


def worker(item):
    key, value = item
    return key, chaos_translate(value)


with ThreadPoolExecutor(max_workers=THREADS) as executor:

    futures = [executor.submit(worker, item) for item in remaining]

    for future in as_completed(futures):

        key, value = future.result()

        output[key] = value
        done += 1

        progress_bar(done, total)

        # 途中保存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)


print("\n翻訳完了")
print("生成:", OUTPUT_FILE)
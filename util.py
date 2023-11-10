import json, os, sys, urllib, requests, time

# TODO as submodule we need this to be chrome2anki_repo.models due to difference in starting path
# but this is awkward when make_anki_cards is used standalone, called from its root path
# this path fiddling allows make_anki_cards to still be run standalone, from its root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # TODO There is surely a better way to do this, but I don't know it
from chrome2anki_repo.models import english_to_kanji, kanji_to_english_card, kanji_to_reading, kanji_to_kanaMeaning, sound_card

import genanki
import numpy as np

from collections import defaultdict

def find_anki_txt_duplicates(inputf):
    lines = open(inputf, 'r', encoding='utf-8').readlines()
    lines = [l.strip().split('\t') for l in lines]
    kanji2meanings = defaultdict(set)
    for i, l in enumerate(lines):
        kanji_key = l[0].replace('   ', '  ')
        kanji2meanings[kanji_key].add( (i, l[1]) )

    num_dups = 0
    dups = {}
    for i, (k, v) in enumerate(kanji2meanings.items()):
        if len(v) > 1:
            num_dups += 1
            print(f"Duplicates # {num_dups}: {k} -> {v}")
            dups[k] = v
        #first_elem = list(v)[0][1]
        #print(f"first_elem for {k}: {first_elem}")
        #if "ill-treat" in first_elem:
        #    print(f"ill-treat: {k} -> {v}")

    return dups

def parse_wani_file(filename):
    lines = open(filename, 'r', encoding='utf-8').readlines()
    words_by_lvl = {}
    cur_words = []
    cur_lvl = ""
    index = 1
    for i, l in enumerate(lines):
        if "Level " not in l and "/" not in l:
            if index % 3 == 1:
                cur_words.append(l.strip())
            index += 1
        if "Level " in l:
            if cur_lvl != "":
                words_by_lvl[cur_lvl.strip()] = cur_words
            cur_words = []
            cur_lvl = l
    words_by_lvl[cur_lvl.strip()] = cur_words # For final level (60)

    kanji_to_waniLev = defaultdict(lambda: 61)
    for k, v in words_by_lvl.items():
        for vv in v:
            kanji_to_waniLev[vv] = int(k[6:])

    return words_by_lvl, kanji_to_waniLev

def loadAnkiJP10KWords():
    if os.path.isfile("apkgs/Japanese Core 10K Lexico-Wani Ordered.preprocessed"):
        sorted_lines = open("apkgs/Japanese Core 10K Lexico-Wani Ordered.preprocessed", 'r', encoding='utf-8').readlines()
        sorted_lines = [l.strip().split('\t') for l in sorted_lines]
        return sorted_lines
    else:
        lines = open("apkgs/Japanese Core 10K +Pics +Aud +Pitch.txt", 'r', encoding='utf-8').readlines()
        word_pronunc_defn = defaultdict(dict)
        lines = [l.strip().split('\t') for l in lines]
        sorted_lines = sorted([l[2:4+1] for l in lines], key=lambda l: lexicographicValue(l[0]))
        return sorted_lines

def findWordsWithKanji(kanji, words, limit=3, retry_limit=3, verbose=False, mode="jisho"):
    """Finds words in <words> where <kanji> appears at least once, up to limit, in order given by words.
        <words> is a list with structure [word, pronuncination, defn]
    """
    # TODO apparently 10K isnt enough. Will have to use Jisho -- just search on kanji, grab first 100 results, & lexico order them?
    if mode == "jisho":
        success, attempts = False, 0
        words_obj = {}
        while not success and attempts <= retry_limit:
            attempts += 1
            try:
                words_obj = get_word_object(kanji)
            except:
                time.sleep(1)
        if words_obj:
            kanjis_readings_meanings = []
            for word_data in words_obj['data']:
                try:
                    wrs = [wr['word'] for wr in word_data['japanese']]
                    wrs_mask = [1 if kanji in wr_w else 0 for wr_w in wrs]
                    print(f"For kanji {kanji}, wrs: {wrs} {wrs_mask}")
                    ind = wrs_mask.index(1)
                    print(f"Index: {ind}")
                    word = word_data['japanese'][ind]['word']
                    reading = word_data['japanese'][ind]['reading']
                    meaning = word_data['senses'][0]['english_definitions']
                    kanji_reading_meaning = [word, reading, meaning]
                    kanjis_readings_meanings.append(kanji_reading_meaning)
                except:
                    print(f"Failed to parse word_data: {word_data}")
            kanjis_readings_meanings = sorted(kanjis_readings_meanings, key=lambda krm: lexicographicValue(krm[0]))
            return kanjis_readings_meanings[:limit]
    else:
        index, matching_words = 0, []
        while len(matching_words) < limit and index<len(words):
            if kanji in words[index][0]:
                if verbose:
                    print(f"Found kanji {kanji} in word # {index}: {words[index]}")
                matching_words.append(words[index])
            index += 1
    return matching_words

def lexicographicValue(word):
    words_by_lvl, kanji_to_waniLev = parse_wani_file("search_inputs/wanikani_kanji_by_level.wani") # TODO cache this so we don't re-read wani file for each word
    wani = int(waniSum(word, kanji_to_waniLev))
    kanji = int(numKanji(word))
    ssc = int(sumStrokeComplexity(word))
    readingsBnd = int(numKunOnReadingsBound(word))
    readingsLen = int(kunOnReadingsLen(word))
    lexicoValue = str(wani).zfill(4) + str(kanji).zfill(3) + str(ssc).zfill(4) + str(readingsBnd).zfill(3) + str(readingsLen).zfill(3)
    return lexicoValue

def getKana():
    hiragana = [h.strip() for h in open("search_inputs/hiragana.txt", 'r', encoding='utf-8').readlines()]
    katakana = [k.strip() for k in open("search_inputs/katakana.txt", 'r', encoding='utf-8').readlines()]
    kana = hiragana + katakana
    return kana

def waniSum(word, kanji_to_waniLev):
    total = 0.0
    hiragana = [h.strip() for h in open("search_inputs/hiragana.txt", 'r', encoding='utf-8').readlines()]
    katakana = [k.strip() for k in open("search_inputs/katakana.txt", 'r', encoding='utf-8').readlines()]
    kana = hiragana + katakana
    for c in word:
        waniLev = 0.0
        if c not in kana:
            print(f"{c} not in kana. Checking waniLev...")
            waniLev = kanji_to_waniLev[c]
        print(f"Adding {c} Wani Level {waniLev} to total for word {word}")
        total += waniLev 
    print(f"\t{word} waniSum: {total}")
    return total

def numKanji(word):
    total = 0.0
    hiragana = [h.strip() for h in open("search_inputs/hiragana.txt", 'r', encoding='utf-8').readlines()]
    katakana = [k.strip() for k in open("search_inputs/katakana.txt", 'r', encoding='utf-8').readlines()]
    kana = hiragana + katakana
    for c in word:
        if c not in kana:
            print(f"Adding 1.0 for non-kana {c} in word {word}")
            total += 1.0
    print(f"\t{word} numKanji: {total}")
    return total

def numKunOnReadingsBound(word):
    total = 1.0
    for c in word:
        kanji_obj = get_kanji_object(c)
        num_readings = 1.0
        if kanji_obj:
            if 'kun_readings' in kanji_obj.keys() and 'on_readings' in kanji_obj.keys():
                num_readings = float(len(kanji_obj['kun_readings']) + len(kanji_obj['on_readings']))
        else:
            print(f"WARNING: received None kanji_obj for kanji {c}")
            num_readings = 50
        print(f"Multiplying by {c} num readings {num_readings} for {word}")
        total *= num_readings
    print(f"\t{word} numKunOnReadingsBound: {total}")
    return total

def kunOnReadingsLen(word):
    total = 0.0
    for c in word:
        kanji_obj = get_kanji_object(c)
        len_readings = 0.0
        if kanji_obj:
            if 'kun_readings' in kanji_obj.keys() and 'on_readings' in kanji_obj.keys():
                kun_len = sum([len(reading) for reading in kanji_obj['kun_readings']])
                on_len = sum([len(reading) for reading in kanji_obj['on_readings']])
                len_readings = kun_len + on_len
        else:
            print(f"WARNING: received None kanji_obj for kanji {c}")
            len_readings = 50
        print(f"Adding {c} len readings {len_readings} for {word}")
        total += float(len_readings)
    print(f"\t{word} kunOnReadingsLen: {total}")
    return total

def sumStrokeComplexity(word):
    total = 0.0
    for c in word:
        kanji_obj = get_kanji_object(c)
        stroke_count = 50
        if kanji_obj:
            stroke_count = kanji_obj['stroke_count'] if 'stroke_count' in kanji_obj.keys() else 50
        else:
            print(f"WARNING: received None kanji_obj for kanji {c}")
        print(f"Adding {c} stroke count {stroke_count} to total for word {word}")
        total += stroke_count
    print(f"\t{word} sumStrokeComplexity: {total}")
    return total

def get_kanji_object(kanji):
    request_session = return_request_session()
    url = f"https://kanjiapi.dev/v1/kanji/{kanji}"
    print(f"Requesting access to URL: {url}")
    success, num_tries, kanjiapi_response = False, 0, None
    while not success and num_tries <= 1:
        try:
            kanjiapi_response = request_session.get(url)
            success = True
        except:
            print(f"Failed to access kanjiapi.dev for kanji: {kanji}")
            time.sleep(1)
            kanjiapi_response = None
            success = False
        num_tries += 1
    if kanjiapi_response:
        result = json.loads(kanjiapi_response.text)
        return result
    else:
        return None

def return_request_session():
    request_session = requests.Session()
    request_adapter = requests.adapters.HTTPAdapter(max_retries=3)
    request_session.mount("http://", request_adapter)
    return request_session

def generate_cards_extended(english_meaning, kanji, reading):
    try:

        front = genanki.Note(
            model=english_to_kanji,
            fields=[english_meaning, kanji, ""])

        reverse = genanki.Note(
            model=kanji_to_english_card,
            fields=[kanji, english_meaning, reading])

        kanji_reading = genanki.Note(
            model=kanji_to_reading,
            fields=[kanji, reading, reading[0]])

        kanji2meaningKana = genanki.Note(
            model=kanji_to_kanaMeaning,
            fields=[kanji, english_meaning, reading])

        result = {"front":front, "reverse":reverse, "kanji2kana": kanji_reading, "kanji2meaningKana":kanji2meaningKana}
        return result

    except Exception as e:
        print(e)

def generate_kanji_cards(obj):
    desired_keys = ['kanji', 'meanings', 'kun_readings', 'on_readings']
    kanji = obj['kanji']
    english_meaning = '\n'.join([str(i) + '. ' + m for i, m in enumerate(obj['meanings'])])
    on_readings = '\n'.join(['[' + str(i) + '] ' + r for i, r in enumerate(obj['on_readings'])])
    kun_readings = '\n'.join(['(' + str(i) + ') ' + r for i, r in enumerate(obj['kun_readings'])])
    reading = '[on] (kun) ' + '\n' + on_readings + '\n' + kun_readings
    try:
        kanji2meaningKana = genanki.Note(
            model = kanji_to_kanaMeaning,
            fields = [kanji, english_meaning, reading])
        result = {"kanji2meaningKana":kanji2meaningKana}
        return result
    except Exception as e:
        print(e)

def generate_cards_basic(english_meaning, kanji, reading):
    try:
        is_audio = proces_forvo(kanji, english_meaning)
        audio_name = 'sound{0}.mp3'.format(english_meaning)

        front = genanki.Note(
            model=english_to_kanji,
            fields=[english_meaning, kanji, reading])

        reverse = genanki.Note(
            model=kanji_to_english_card,
            fields=[kanji + '[sound:{0}]'.format(audio_name), english_meaning, reading])

        result = []


        if is_audio:
            print(audio_name)
            pronaunciation = genanki.Note(
                model=sound_card,
                fields=['[sound:{0}]'.format(audio_name), english_meaning, reading])
            result.append(pronaunciation)
        result.append(front)
        result.append(reverse)
        return result

    except Exception as e:
        print(e)

def insert_cards_to_deck(cards, deckname="unnamed_anki_deck", apkgname="unnamed_apkg"):
    print(f"Inserting cards into deck {deckname}, and then generating apkg {apkgname}.apkg")
    my_deck = genanki.Deck(
        int(np.pi * 1e15),
        deckname)
    my_package = genanki.Package(my_deck)
    my_package.media_files = ()
    for card in cards:
        my_deck.add_note(card)
    my_package.write_to_file(f"{apkgname}.apkg") 
    print(f"Package {apkgname}.apkg generated")

def print_first_n_options(jisho_json, num_to_print):
    for i, v in enumerate(jisho_json['data'][0:num_to_print]):
        japanese_reading = v['japanese'][0]
        english_definition = get_english_definition(v)
        print(i, english_definition, japanese_reading)

def get_english_definition(element):
    arr = element['senses'][0]['english_definitions']
    if len(arr) > 3:
        return ', '.join(arr[:3])
    else:
        return ', '.join(arr)

def clean_up():
    dir_name = os.getcwd()
    test = os.listdir(dir_name)
    for item in test:
        if item.endswith(".mp3"):
            os.remove(os.path.join(dir_name, item))

def append_obj_to_json(obj, outfilename="words.json"):
    try:
        with open(outfilename, 'r') as f:
            try:
                data = json.load(f)
            except Exception as e:
                data = {'data':[]}
    except FileNotFoundError as e:
        data = {'data':[]}

    obj = [obj] if isinstance(obj, dict) else obj
    data['data'] = data['data'] + obj
    with open(outfilename, 'w+') as f:
        json.dump(data, f)
        print(f"{obj} added to {outfilename}")

def get_word_object(word):
    request_session = return_request_session()
    url = f"http://beta.jisho.org/api/v1/search/words?keyword={word}"
    print(f"Requesting access to URL: {url}")
    jisho_definition = request_session.get(url)
    result = json.loads(jisho_definition.text)
    return result

def get_kanji_object(kanji):
    request_session = return_request_session()
    url = f"https://kanjiapi.dev/v1/kanji/{kanji}"
    print(f"Requesting access to URL: {url}")
    kanjiapi_response = request_session.get(url)
    result = json.loads(kanjiapi_response.text)
    return result

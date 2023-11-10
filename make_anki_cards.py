"""
Attribution: the original skeleton for this file and models.py was based on
    https://github.com/adamkozuch/jisho-anki/
This has been rewritten extensively since, but still bears structural similarities
inherited from the setup of Adam's repository.
"""

import json, glob, time, pathlib
import fire
from util import return_request_session, print_first_n_options, get_english_definition, clean_up
from util import generate_cards_extended, generate_kanji_cards, insert_cards_to_deck, append_obj_to_json
from util import lexicographicValue, get_word_object, get_kanji_object

class Jisho:
    """
        Run-time examples:

            1. For building words.json from an exported Chrome HTML file

                    python make_anki_cards.py search --inputf="bookmarks_example.html" --output_format="txt" --mode="NON-INTERACTIVE"

            2. For building a tab-delimited txt (or apkg, but txt is more flexible) importable by Anki from words.json, w/ cards in
                an ordering based on a custom measure of word complexity (see various fxns in util.py)

                    python make_anki_cards.py generate --deckname="bookmarks_examples_deck"

            3. ... (TODO)
    """
    def __init__(self, inputf="test", deckname="unnamed_deck", apkgname="unnamed_apkg",
                    wordsf="words.json", ignore_wordsf=None, char_type="word", only_unupdated_cards=False,
                    card_types=["kanji2meaningKana"], # ["front", "reverse", "kanji2kana", "kanji2meaningKana"],
                    delay=0.1, mode="INTERACTIVE", num_jisho_entries_to_examine=3, ordering="unordered",
                    output_format="txt", test_mode=False):
        self.inputf = inputf # input file of words to search Jisho for [Chrome exported bookmarks .html, Duolingo Words txt .duo]
        self.deckname = deckname
        self.apkgname = apkgname
        self.mode = mode # INTERACTIVE, NON-INTERACTIVE
        self.delay = delay
        self.num_jisho_entries_to_examine = num_jisho_entries_to_examine # in interactive mode, number of Jisho defns to display
        self.wordsf = wordsf # json file to which searched words are written
        self.ignore_wordsf = ignore_wordsf # when searching Jisho for words, words in this file are ignored
        self.card_types = card_types # type/style of Anki Notes (see templates in util) to generate
        self.char_type = char_type # 'word' [uses Jisho] or 'kanji' [uses kanjiapi.dev]
        self.ordering = ordering # 'unordered' or 'lexicographic'
        self.output_format = output_format # 'apkg' or 'txt' (txt has richer import options in Anki)
        self.test_mode = bool(test_mode) # set to True to only print first 20 entries in output type
        self.only_unupdated_cards = only_unupdated_cards # If True, will not generate cards corresponding to entries in ignore_wordsf any updated fields

    def list(self):
        with open(self.wordsf) as f:
            words = json.load(f)['data']
            for i, w in enumerate(words):
                print(f"Word # {i} in {self.wordsf} currently is: {w}")

    def prune(self):
        with open (self.wordsf, 'w') as f:
            json.dump({'data':[]}, f)
            clean_up()

    def generate(self):
        print(f"From data in {self.wordsf}, generating card types: {self.card_types}")
        # TODO allow generation from source txt (generated e.g. from another apkg, like the Anki 10K one), rather than self.wordsf

        elements_dict = {}
        if pathlib.PurePath(self.wordsf).suffix == ".preprocessed":
            lines = open(self.wordsf, 'r', encoding='utf-8').readlines()
            lines = [l.strip().split('\t') for l in lines]
            elements_dict['data'] = {}
            for l in lines:
                kanji, reading, english_definition = l 
                obj = {'english': english_definition, 'kanji': kanji, 'reading':reading}
                elements_dict['data'].append(obj)
        else:
            with open(self.wordsf) as f:
                elements_dict = json.load(f)
        assert elements_dict, f"elements_dict cannot be {elements_dict}"

        elements = elements_dict['data']
        unduplicated_elements = []
        for obj in elements:
            if obj not in unduplicated_elements:
                unduplicated_elements.append(obj)
        cards = []
        if self.ordering == "lexicographic":
            print(f"Typical undup'd elements element: {unduplicated_elements[0]}")
            unduplicated_elements = sorted(unduplicated_elements, key=lambda k: k['lexicoValue'])

        if self.output_format == "apkg": # APKG output
            for i, obj in enumerate(unduplicated_elements):
                print(f"Making Anki note/card # {i} for: {obj}")
                if self.char_type != "kanji":
                    new_cards = generate_cards_extended(obj['english'], obj['kanji'], obj['reading'])
                else:
                    new_cards = generate_kanji_cards(obj)
                cards = cards + [new_cards[ct] for ct in self.card_types]
            insert_cards_to_deck(cards, deckname=self.deckname, apkgname=self.apkgname)
        elif self.output_format == "txt": # TXT output
            assert self.card_types == ["kanji2meaningKana"], "Only kanji2meaningKana supported for txt, but requested: {self.card_types}"

            if self.only_unupdated_cards:
                old_len = len(unduplicated_elements)
                print(f"Before restricting to unupdated cards, unduplicated elements len, first 5: {old_len}, {unduplicated_elements[:5]}")
                old_cards = [l.strip().split('\t') for l in open(self.ignore_wordsf, 'r', encoding='utf-8').readlines()]
                old_cards_d = dict([(l[0].replace('   ', '  '), l[1]) for l in old_cards]) # TODO: brittle :(
                unduplicated_elements2 = []
                for ue in unduplicated_elements:
                    kanji_key = ue['kanji']
                    if kanji_key in old_cards_d.keys():
                        # TODO Is the above not catching verbs usually written in kana? e.g., kakaru (to take (a resource)), ijimeru (to ill-treat, to bully)
                        if '1.' not in old_cards_d[kanji_key]:# and 'Transitive' not in old_cards_d[kanji_key]: # TODO brittle :(
                            unduplicated_elements2.append(ue)
                    else:# kanji_key not in old_cards_d.keys():
                        print(f"ue Kanji did not match: {ue}")
                    #elif ue['english'].replace(' (Transitive Verb)', '').replace(' ', '')==old_cards_d[kanji_key]:
                    #    print(f"ue English did not match: {ue}")
                    if "to do, to carry out, to perform" in ue['english']:
                        print("DEBUGGING")
                        print(f"\tundup'd element: {ue}")
                        ocd_key1, ocd_english1 = list(old_cards_d.items())[0]
                        #print(f"Typical ocd_key: {ocd_key1}")
                        #print(f"Typical ocd_english: {ocd_english1}")
                        for ocd, ocd_english in old_cards_d.items():
                            if "to do, to carry out, to perform" in ocd_english:
                                print(f"\tocd: {ocd}")
                                print(f"\tocd_english: {ocd_english}")
                                print(f"kanji equal? {ue['kanji'] == ocd}")
                        #raise ValueError("hora! kiite")
                unduplicated_elements = unduplicated_elements2
                print(f"After restricting to unupdated cards: {len(unduplicated_elements)}, {unduplicated_elements[:5]}")
                print(f"Excluded as updated {old_len - len(unduplicated_elements)} cards")
                #raise ValueError("stop. drop. debug")

            unduplicated_elements = unduplicated_elements[:20] if self.test_mode else unduplicated_elements
            with open(self.deckname + ".txt", 'w', encoding='utf-8') as outf:
                for i, obj in enumerate(unduplicated_elements):
                    print(f"Writing to {self.deckname}.txt: obj # {i}, {obj}")
                    out_line = obj['kanji'].replace('\n', ' ').replace('   ', '  ') + '\t'
                    out_line += obj['english'].replace('\n', ' ') + '\t' + obj['reading'].replace('\n', ' ') + '\n'
                    outf.write(out_line)
        else:
            raise ValueError(f"output_format {self.output_format} not recognized")

    def search(self):
        ignore_wordsl = []
        print(f"Ignore words file: {self.ignore_wordsf}")
        if self.ignore_wordsf is not None:
            assert self.ignore_wordsf.endswith('.duo'), f"Unrecognized ignore_wordsf suffix: {self.ignore_wordsf}"
            ignore_wordsl = open(self.ignore_wordsf, 'r', encoding='utf-8').readlines()
            ignore_wordsl = [entry.strip() for entry in ignore_wordsl]
        print(f"List of words to ignore (not search for): {ignore_wordsl}")

        inputf = open(f"search_inputs/{self.inputf}", encoding='utf-8').readlines()
        if self.inputf.endswith('.html'):
            inputf = [l for l in inputf if "A HREF" in l and "jisho.org/search" in l]
        total_words_added = 0
        for bn, ib in enumerate(inputf):
            stripped_ib = ib.strip()
            print("\n <----------------------> \n")
            if self.char_type == "word" or self.char_type == "kanji":
                print(f"Considering stripped_ib: {stripped_ib}")
                if ( (self.char_type == "word" and ("jisho.org/search/" in stripped_ib or self.inputf.endswith('.duo')
                    or ("jisho.org/search" in stripped_ib and "ADD_DATE" in stripped_ib) ) ) or
                    (self.char_type == "kanji" and self.inputf.endswith('.kanji')) ):

                    search_terms = stripped_ib
                    if "jisho.org/search/" in stripped_ib:
                        search_terms = stripped_ib[stripped_ib.find("jisho.org/search/")+len("jisho.org/search/"):]
                    elif "jisho.org/search" in stripped_ib and "ADD_DATE" in stripped_ib:
                        sub_ib = stripped_ib[stripped_ib.find("ADD_DATE"):]
                        sub_ib = sub_ib[sub_ib.find(">")+len(">"):sub_ib.find("<")]
                        sub_ib = sub_ib[:sub_ib.find(" - Jisho.org")]
                        goog_ime_space = "　"
                        search_terms = sub_ib#.split(goog_ime_space)
                        #raise ValueError(f"From {stripped_ib}, found search terms: {search_terms}")
                    if self.char_type != "kanji":
                        search_terms = search_terms.replace("%E3%80%80", "%20").split("%20") # Google IME space; English space
                    else:
                        search_terms = search_terms.split(" ")
                    search_terms = [st for st in search_terms if st != ""]
                    print(f"Search terms # {bn}: {search_terms}")
                    #raise Exception('stop')
                    for sn, st in enumerate(search_terms):
                        if st not in ignore_wordsl:
                            print(f"\nTrying to retrieve bookmark # {bn}, search term # {sn} result. Search term was: {st}")
                            try:
                                if self.char_type == "word":
                                    word_object = get_word_object(st)
                                    if word_object:
                                        print_first_n_options(word_object, self.num_jisho_entries_to_examine)

                                        if len(word_object['data']) == 0:
                                            raise Exception(f"No Jisho results found for {st}")

                                        word_index = 0 # If in NON-INTERACTIVE mode
                                        if self.mode == "INTERACTIVE":
                                            word_index = input("\tWhich word should we add? (default 0)") or 0
                                            try:
                                                val = int(word_index)
                                            except ValueError:
                                                raise Exception("Chosen value is not a number")

                                            if len(word_object['data']) < int(word_index):
                                                print("Specified index {word_index} does not exist. Defaulting to 0")
                                                word_index = 0

                                        chosen_object = word_object['data'][int(word_index)]
                                        japanese_info = chosen_object['japanese'][0]

                                        english_definition = get_english_definition(chosen_object)
                                        tags = word_object['data'][int(word_index)]['senses'][0]['tags']                                           

                                        print(f"\t Japanese Info: {japanese_info}")
                                        print(f"\t English Defn: {english_definition}")
                                        kanji = japanese_info['word']
                                        if 'Usually written using kana alone' in tags:
                                            kanji = japanese_info['reading'] + f" ({kanji}) "
                                            kanji += " (Usually written in kana)"
                                        obj = {'english': english_definition, 'kanji': kanji, 'reading': japanese_info['reading']}
                                        #obj['Transitive'] = None # Checking if first definition has a part-of-speech indicating Transitive verb
                                        if 'Transitive verb' in word_object['data'][0]['senses'][0]['parts_of_speech']:
                                            obj['english'] += ' (Transitive Verb)'
                                        elif 'Intransitive verb' in word_object['data'][0]['senses'][0]['parts_of_speech']:
                                            obj['english'] += ' (Intransitive Verb)'
                                        if self.ordering == "lexicographic":
                                            obj['lexicoValue'] = lexicographicValue(st)
                                    else:
                                        print('Word {0} not found'.format(word))
                                elif self.char_type == "kanji":
                                    assert self.mode == "NON-INTERACTIVE", "Only non-interactive mode supported for Kanji search currently"
                                    assert self.ordering == "unordered", "Lexicographic ordering not yet supported for Kanji search"
                                    kanji_object = get_kanji_object(st)
                                    if list(kanji_object.keys()) == ['error']:
                                        raise Exception(f"No kanjiapi.dev result found for {st}")
                                    required_keys = ['kanji', 'meanings', 'kun_readings', 'on_readings']
                                    if not set(required_keys).issubset(set(kanji_object.keys())):
                                        raise Exception(f"kanjiapi.dev result result: {kanji_object} lacks some required keys (required: {required_keys})")
                                    obj = kanji_object

                                append_obj_to_json(obj, outfilename=self.wordsf)
                                total_words_added += 1
                            except Exception as e:
                                print(e)
                            time.sleep(self.delay)
                        else:
                            print(f"Skipping {st}. Already present in ignore words file {self.ignore_wordsf}")
                else:
                    print(f"\nSkipping this; not recognized as valid search target: {stripped_ib}")
                print(f"Search complete. Total objects added to {self.wordsf}: {total_words_added}")
            else:
                raise ValueError(f"char_type {self.char_type} not recognized")

if __name__ == '__main__':
    fire.Fire(Jisho)

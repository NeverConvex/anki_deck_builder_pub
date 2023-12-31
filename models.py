import genanki
fields = [
    {'name': 'Question'},
    {'name': 'Answer'},
    {'name': 'Hint'},
]

fields_1 = [
    {'name': 'Question'},
    {'name': 'Kanji'},
    {'name': 'Diagram'},
]

# For cards that present the Kanji as a prompt, and expect both English meaning & kana spelling in answer
fields_2 = [
    {'name': 'Kanji'},
    {'name': 'Meaning'},
    {'name': 'Kana'},
]

templates_1 = [
    {
        'name': 'Card 1',
        'qfmt': 'English meaning <br> {{Question}} <br> <br> <br> {{hint:Hint}}',
        'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    }]

templates_2 = [
    {
        'name': 'Card 1',
        'qfmt': 'English meaning <br> {{Question}} <br> <br> <br> {{hint:Hint}}',
        'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    }]

templates_3 = [
    {
        'name': 'Card 1',
        'qfmt': 'Kanji <br> {{Question}} <br> <br> <br>',# {{hint:Hint}}', # TODO 1/1/22: fix this? Not sure what it was meant to do
        'afmt': '{{FrontSide}}<hr id="answer">{{Kanji}} <br> {{Diagram}}',
    }]

templates_4 = [
    {
        'name': 'Card 1',
        'qfmt': 'Kanji reading <br> {{Question}} <br> <br> <br> {{hint:Hint}}',
        'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    }]

templates_5 = [
    {
        'name': 'Card {{Kanji}}',
        'qfmt': '{{Kanji}}',
        'afmt': '{{FrontSide}}<hr id="answer">{{Kana}} <br> {{Meaning}}',
    }]

sound_card = genanki.Model(
    160739111519,
    'sound model',
    fields=fields,
    templates=templates_1,
    css='''.card {
        font-family: honyaji-re;
        font-size: 40px;
        text-align: center;
        color: black;
        background-color: white;
        }
        .jp { font-size: 35px }
            .win .jp { font-family: "arial", "arial"; }
        .mac .jp { font-family: "honyaji-re", "ヒラギノ明朝 Pro"; }
        .linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
        .mobile .jp { font-family: "Hiragino Mincho ProN"; }'''
)

kanji_to_english_card = genanki.Model(
    160739118319,
    'kanji model',
    fields=fields,
    templates=templates_2,
    css='''.card {
        font-family: honyaji-re;
        font-size: 40px;
        text-align: center;
        color: black;
        background-color: yellow;
        }
        .jp { font-size: 35px }
            .win .jp { font-family: "arial", "arial"; }
        .mac .jp { font-family: "honyaji-re", "ヒラギノ明朝 Pro"; }
        .linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
        .mobile .jp { font-family: "Hiragino Mincho ProN"; }'''
)

english_to_kanji = genanki.Model(
    160739191319,
    'Japanese_model',
    fields=fields_1,
    templates=templates_3,
    css='''.card {
        font-family: honyaji-re;
        font-size: 40px;
        text-align: center;
        color: black;
        background-color: Aqua;
        }
        .jp { font-size: 35px }
            .win .jp { font-family: "arial", "arial"; }
        .mac .jp { font-family: "honyaji-re", "ヒラギノ明朝 Pro"; }
        .linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
        .mobile .jp { font-family: "Hiragino Mincho ProN"; }'''
)

kanji_to_reading = genanki.Model(
    1607391018319,
    'kanji reading model',
    fields=fields,
    templates=templates_4,
    css='''.card {
        font-family: honyaji-re;
        font-size: 40px;
        text-align: center;
        color: black;
        background-color: LightCyan;
        }
        .jp { font-size: 35px }
            .win .jp { font-family: "arial", "arial"; }
        .mac .jp { font-family: "honyaji-re", "ヒラギノ明朝 Pro"; }
        .linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
        .mobile .jp { font-family: "Hiragino Mincho ProN"; }'''
)

kanji_to_kanaMeaning = genanki.Model(
    1607391018320,
    'kanji -> meaning, kana model',
    fields=fields_2,
    templates=templates_5,
    css='''.card {
        font-family: honyaji-re;
        font-size: 40px;
        text-align: center;
        color: black;
        background-color: LightCyan;
        }
        .jp { font-size: 35px }
            .win .jp { font-family: "arial", "arial"; }
        .mac .jp { font-family: "honyaji-re", "ヒラギノ明朝 Pro"; }
        .linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
        .mobile .jp { font-family: "Hiragino Mincho ProN"; }'''
)

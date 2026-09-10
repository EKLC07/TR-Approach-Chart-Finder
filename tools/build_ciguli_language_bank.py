from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAINING_DIR = ROOT / "app" / "ai" / "training_data"
TARGET = 16000


TR_BASE = """
abi aga hacı kral kaptan hocam dostum selam merhaba günaydın iyi akşamlar iyi geceler naber nasılsın iyiyim
kötüyüm fena değil yorgunum mutluyum heyecanlıyım sıkıldım konuşalım muhabbet sohbet yardım anlat öğret açıkla
hatırla unutma seviyorum sevmiyorum ilgileniyorum öğreniyorum çalışıyorum deniyorum başlıyorum bitiriyorum devam
tamam olur olmaz belki şimdi sonra bugün yarın dün biraz fazla az çok güzel kötü iyi harika mükemmel sakin hızlı
yavaş dikkatli ciddi basit doğal günlük ingilizce türkçe cevap soru konu fikir hedef proje plan adım aşama sistem
panel tasarım premium modern temiz karanlık açık kullanıcı uygulama masaüstü kurulum kaldırma güncelleme dosya klasör
hafıza kişilik karakter veri eğitim kelime cümle bağlam mantık düşünce tercih seviye başlangıç orta ileri uzman
simülasyon uçuş uçak pilot kokpit meydan havalimanı pist yaklaşma ayrılma iniş kalkış rota irtifa hız baş manyetik
minimum brifing chart harita prosedür fix frekans radyo trafik hava rüzgar görüş bulut yağmur kar buzlanma tehdit
risk kontrol notam aip ils rnav vor dme ndb ifr vfr airbus boeing thy pegasus msfs xplane prepar3d xplane12 vatsim
ivao kule yaklaşma merkez yer kontrol apron taksi clearance transponder squawk flap gear trim spoiler autothrottle
autopilot fms mcdu fmc sid star arrival departure glide slope localizer decision altitude decision height missed
holding waypoint waypointler briefing taxi taxiway apron gate stand pushback clearance checklist landing takeoff
crosswind tailwind headwind visibility ceiling metar taf atis qnh qfe temperature dewpoint pressure turbulence
"""


EN_BASE = """
bro captain friend hello hi hey good morning good evening good night thanks thank you anytime welcome okay sure maybe
now later today tomorrow yesterday little much more less good bad great perfect calm fast slow careful serious simple
natural daily english turkish answer question topic idea target project plan step stage system panel design premium
modern clean dark light user app desktop setup uninstall update file folder memory personality character data training
word sentence context logic thought preference level beginner intermediate advanced expert simulation flight aircraft
airplane pilot cockpit airport runway approach departure landing takeoff route altitude speed heading magnetic minimums
briefing chart map procedure fix frequency radio traffic weather wind visibility cloud rain snow icing threat risk
control notam aip ils rnav vor dme ndb ifr vfr airbus boeing airliner msfs xplane prepar3d vatsim ivao tower approach
center ground apron taxi clearance transponder squawk flap gear trim spoiler autothrottle autopilot fms mcdu fmc sid
star arrival departure glide slope localizer decision altitude decision height missed holding waypoint briefing taxiway
gate stand pushback checklist crosswind tailwind headwind ceiling metar taf atis qnh qfe temperature dewpoint pressure
turbulence vector intercept final base downwind climb descend maintain cleared contact monitor report advise request
confirm verify expect unable ready standby continue cancel proceed hold short line up vacate runway frequency change
"""


TR_CATEGORIES = {
    "daily": "selam merhaba naber nasılsın iyiyim kötüyüm yorgun keyifli sıkılmış mutlu heyecanlı sakin dertli rahat sohbet muhabbet konuşma cevap soru teşekkür sağol eyvallah görüşürüz".split(),
    "aviation": "uçuş uçak pilot kokpit pist meydan havalimanı yaklaşma iniş kalkış rota irtifa hız baş manyetik rüzgar görüş minimum brifing chart prosedür fix frekans trafik emniyet tehdit risk".split(),
    "sim": "simülasyon msfs xplane prepar3d vatsim ivao airbus boeing airliner joystick throttle rudder kamera kokpit görev senaryo uçuşplanı online offline eğitim pratik".split(),
    "learning": "öğrenme çalışma deneme tekrar pratik gelişim seviye başlangıç orta ileri uzman anlatım örnek açıklama basitleştirme detay soru cevap".split(),
    "tone": "samimi doğal kısa net detaylı sakin eğlenceli ciddi premium modern temiz akıcı canlı özgün sıcak meraklı yardımcı öğretici".split(),
}


EN_CATEGORIES = {
    "daily": "hello hi hey how are you good bad tired happy excited calm bored chat talk answer question thanks welcome bye see you".split(),
    "aviation": "flight aircraft pilot cockpit runway airport approach landing takeoff route altitude speed heading magnetic wind visibility minimums briefing chart procedure fix frequency traffic safety threat risk".split(),
    "sim": "simulation msfs xplane prepar3d vatsim ivao airbus boeing airliner joystick throttle rudder camera cockpit mission scenario flightplan online offline training practice".split(),
    "learning": "learning study practice repeat progress level beginner intermediate advanced expert explanation example simplify detail question answer".split(),
    "tone": "friendly natural short clear detailed calm playful serious premium modern clean fluent alive original warm curious helpful educational".split(),
}

EN_PHRASAL_VERBS = [
    "ask around", "back off", "back up", "break down", "bring up", "call back", "calm down",
    "carry on", "check in", "check out", "come across", "come back", "come up with",
    "count on", "cut down", "deal with", "drop by", "end up", "figure out", "fill in",
    "find out", "follow up", "get across", "get along", "get around", "get back",
    "get into", "get over", "get through", "give up", "go ahead", "go back", "go over",
    "grow up", "hang out", "hold on", "keep going", "keep up", "kick off", "lay out",
    "look after", "look around", "look at", "look for", "look into", "look up", "make up",
    "move on", "pick up", "point out", "pull up", "put together", "read back", "run into",
    "set up", "show up", "slow down", "sort out", "speak up", "stand by", "start over",
    "take off", "talk through", "think over", "try out", "turn around", "turn down",
    "turn on", "turn off", "warm up", "work on", "work out", "write down",
]

EN_DAILY_EXPRESSIONS = [
    "no worries", "sounds good", "fair enough", "that makes sense", "give me a second",
    "let me think", "let's go over it", "let's figure it out", "I get it", "I see",
    "my bad", "all good", "not a big deal", "take your time", "what do you mean",
    "tell me more", "walk me through it", "keep it simple", "from scratch",
    "step by step", "for now", "so far", "in a bit", "right away", "by the way",
    "to be honest", "kind of", "sort of", "a little bit", "pretty much", "at least",
    "as soon as possible", "on the other hand", "in that case", "good call",
    "nice catch", "we are getting there", "let's keep going", "we can build on that",
]

TR_DAILY_EXPRESSIONS = [
    "sıkıntı yok", "olur abi", "tamam kaptan", "bir saniye", "şimdi anladım",
    "adım adım gidelim", "kafam karıştı", "birlikte çözelim", "bence mantıklı",
    "çok iyi olur", "şimdilik böyle", "sonra bakarız", "devam edelim",
    "bunu not al", "bunu hatırla", "basit anlat", "detaylı anlat", "örnek ver",
    "kısaca söyle", "neyi kaçırıyorum", "ben yeni başladım", "bana göre anlat",
    "havadan sudan konuşalım", "muhabbet edelim", "biraz takılalım", "gaz ver",
    "işi büyütelim", "premium dursun", "kokpit gibi olsun", "uçuş havası versin",
    "selamın aleyküm", "aleyküm selam", "aleykümselam", "eyvallah hacı",
    "sağ olasın hocam", "naber reis", "ne diyorsun kral", "hayırlısı olsun",
    "Allah razı olsun", "kolay gelsin", "eline sağlık", "adamsın abi",
    "kral hareket", "hacı bir bak", "hocam şuna bakalım", "reis devam",
]


TR_PHRASAL_EXPRESSIONS = [
    "göz at", "üstünden geç", "üzerinden geç", "ele al", "el at", "not al",
    "hafızaya yaz", "aklına yatmak", "aklıma yattı", "aklım karıştı",
    "kafama takıldı", "kafaya takma", "yoluna koy", "çözmeye çalış",
    "devam et", "geri dön", "ileri sar", "takip et", "kontrol et",
    "hesaba kat", "bağlantı kur", "farkına var", "anlamaya çalış",
    "kısa kes", "detaya in", "derine in", "sadeleştir", "parçalara ayır",
    "üstüne konuş", "birlikte çözelim", "rahat bırak", "takılalım",
    "muhabbet edelim", "gaz ver", "heveslen", "yol göster", "yardım et",
    "akış çıkar", "senaryo kur", "brifing çıkar", "minimum ayır",
    "chart çek", "chart oku", "piste in", "tura çık", "pas geç",
    "tekrar dene", "devreye al", "devreden çıkar", "açıklığa kavuştur",
    "aklımda tut", "gözden kaçırma", "yanına yaz", "örnekle anlat",
    "konuyu aç", "konuyu kapat", "uçuşa bağla", "sim'e bağla",
    "rotaya oturt", "yaklaşmayı çöz", "pisti seç", "meydanı seç",
    "frekansı bul", "haritaya bak", "profil çıkar", "riskleri ayır",
]


TR_SUFFIXES = [
    "", "lar", "ler", "ım", "im", "um", "üm", "ın", "in", "un", "ün", "da", "de", "dan", "den",
    "daki", "deki", "lık", "lik", "luk", "lük", "lı", "li", "lu", "lü", "sız", "siz", "sal", "sel",
]

EN_SUFFIXES = [
    "", "s", "ing", "ed", "er", "ers", "able", "less", "ful", "ly", "ness", "al", "ive", "ion",
]

TR_CONNECTORS = [
    "için", "ile", "gibi", "hakkında", "önce", "sonra", "sırasında", "tarafında",
    "üstünden", "üzerinden", "beraber", "kısa", "detaylı", "sakin", "net",
]

EN_CONNECTORS = [
    "for", "with", "like", "about", "before", "after", "during", "around",
    "through", "over", "together", "short", "detailed", "calm", "clear",
]


TR_PHRASES = {
    "greeting": [
        "Selam kaptan, Ciguli hatta.",
        "Merhaba kaptan, frekans açık.",
        "Hoş geldin, kokpit hazır.",
        "Selam, bugün ne uçuyoruz?",
        "Buradayım, chart mı muhabbet mi?",
        "Kaptan geldi, Ciguli uyandı.",
        "Selam hocam, hava güzel görünüyor.",
        "Merhaba, bugün rotamız ne?",
        "Aleyküm selam kaptan, Ciguli sağ koltukta.",
        "Selamın aleyküm hocam, frekans temiz.",
        "Hoş geldin reis, kule bizi duyuyor.",
    ],
    "how_are_you": [
        "İyiyim kaptan, radar sakin.",
        "Keyfim yerinde, frekans temiz.",
        "İyiyim, kokpit modu açık.",
        "Fena değil, yaklaşma için hazırım.",
        "Gayet iyiyim, senin uçuş nasıl gidiyor?",
        "İyiyim hacı, bugün biraz IFR kokusu var.",
        "Modum iyi, chartlar da hazır.",
        "Ciguli iyi, kaptanı bekliyor.",
    ],
    "thanks": [
        "Her zaman kaptan.",
        "Ne demek, kokpitte ekip işi.",
        "Eyvallah, beraber çözeriz.",
        "Rica ederim, sağ koltuk burası.",
        "Her zaman buradayım.",
        "İşimiz bu kaptan.",
    ],
    "bye": [
        "Görüşürüz kaptan.",
        "Bir sonraki yaklaşmada yine buradayım.",
        "Kendine iyi bak, frekans kapanıyor.",
        "İyi uçuşlar kaptan.",
        "Sonraki rotada görüşürüz.",
    ],
    "bored": [
        "O zaman küçük bir IFR görevi atalım.",
        "Can sıkıntısına en iyi ilaç kısa bir yaklaşma brifingi.",
        "Bir meydan seç, üç dakikalık mini uçuş planı çıkaralım.",
        "İstersen muhabbet ederiz, istersen chart sökeriz.",
        "Gel bugün bir pist seçip senaryo yazalım.",
    ],
    "motivation": [
        "Bu proje yürür kaptan, küçük küçük ama sağlam.",
        "Pist uzun, yakıt yeter; devam.",
        "Bugün bir modül, yarın bir panel; ürün böyle doğar.",
        "Sen yeter ki çizgiyi bozma, Ciguli sağ koltukta.",
        "Bu işte premium hava var, acele etmeden işleyelim.",
    ],
    "casual_chat": [
        "Olur kaptan, biraz muhabbet döndürelim.",
        "Havadan sudan da konuşuruz, chart da sökeriz.",
        "Hacı buradayım, gündelik de konuşuruz uçuşu da bağlarız.",
        "Reis ne taraftan girelim, sohbet mi pist mi?",
        "Kral anlat, Ciguli dinliyor.",
    ],
    "confused": [
        "Sıkıntı yok, konunun üstünden beraber geçelim.",
        "Kafanı kurcalayan yeri bulalım, sonra sadeleştirelim.",
        "Burada takıldıysan normal, adım adım açalım.",
        "Anlamadığın kısmı söyle, Ciguli parçalarına ayırsın.",
        "Hacı kafaya takma, birlikte çözeriz.",
    ],
}


EN_PHRASES = {
    "greeting": [
        "Hello captain, Ciguli is on frequency.",
        "Hi captain, cockpit is ready.",
        "Welcome back, what are we flying today?",
        "Hey, charts or casual aviation talk?",
        "Captain is here, Ciguli is awake.",
        "Good to see you, route or briefing first?",
        "Hi, frequency is clean.",
        "Hello, runway lights are on.",
    ],
    "how_are_you": [
        "I am good, captain. Radar is calm.",
        "Doing well, frequency is clean.",
        "I am solid, cockpit mode is on.",
        "Not bad, ready for the next approach.",
        "Good here. How is your flight going?",
        "Ciguli is good, waiting in the right seat.",
        "Mood is good, charts are ready.",
        "All good, captain.",
    ],
    "thanks": [
        "Anytime, captain.",
        "You are welcome; cockpit work is teamwork.",
        "No problem, we solve it together.",
        "Always here in the right seat.",
        "Glad to help.",
        "That is what I am here for.",
    ],
    "bye": [
        "See you, captain.",
        "I will be here for the next approach.",
        "Take care, frequency closing.",
        "Good flights, captain.",
        "See you on the next route.",
    ],
    "bored": [
        "Then let's turn it into a small IFR mission.",
        "Best cure for boredom: a short approach briefing.",
        "Pick an airport and we can build a three-minute mini flight.",
        "We can chat, or we can break down a chart.",
        "Let's pick a runway and write a scenario.",
    ],
    "motivation": [
        "This project can grow, captain. Small steps, strong build.",
        "Runway is long, fuel is enough; keep going.",
        "One module today, one premium panel tomorrow.",
        "Keep the heading, Ciguli is in the right seat.",
        "There is a premium product hiding here; we shape it patiently.",
    ],
    "casual_chat": [
        "Sure, we can just talk for a bit.",
        "We can keep it casual or drift into aviation whenever you want.",
        "Tell me what is on your mind, captain.",
        "Charts can wait for a second; let's talk.",
        "I am here for flying talk and normal life talk too.",
    ],
    "confused": [
        "No worries, let's sort it out step by step.",
        "Tell me which part feels messy and I will break it down.",
        "We can go over it from scratch.",
        "Give me the confusing bit and I will simplify it.",
        "Good catch, let's clear that up.",
    ],
}


def unique_words(
    seed: str,
    categories: dict[str, list[str]],
    suffixes: list[str],
    expressions: list[str] | None = None,
    connectors: list[str] | None = None,
) -> list[str]:
    words = {item.strip().lower() for item in seed.split() if item.strip()}
    for expression in expressions or []:
        clean = expression.strip().lower()
        if clean:
            words.add(clean)
    base = sorted({word for group in categories.values() for word in group})

    for word in base:
        for suffix in suffixes:
            words.add((word + suffix).lower())

    labels = list(categories)
    for left_label in labels:
        for right_label in labels:
            for left in categories[left_label]:
                for right in categories[right_label]:
                    words.add(f"{left}-{right}".lower())
                    if len(words) >= TARGET + 250:
                        return sorted(words)

    connectors = connectors or []
    for left_label in labels:
        for right_label in labels:
            for connector in connectors:
                for left in categories[left_label]:
                    for right in categories[right_label]:
                        words.add(f"{left} {connector} {right}".lower())
                        if len(words) >= TARGET + 250:
                            return sorted(words)

    for first_label in labels:
        for second_label in labels:
            for third_label in labels:
                for first in categories[first_label][:12]:
                    for second in categories[second_label][:12]:
                        for third in categories[third_label][:12]:
                            words.add(f"{first} {second} {third}".lower())
                            if len(words) >= TARGET + 250:
                                return sorted(words)
    return sorted(words)


def phrase_bank(base_phrases: dict[str, list[str]], lang: str) -> dict[str, list[str]]:
    if lang == "tr":
        openers = ["Kaptan", "Abi", "Hacı", "Dostum", "Hocam", "Ciguli burada"]
        tails = [
            "istersen devamını beraber açarız.",
            "bunu hafızaya da alırım.",
            "konuyu fazla kasmadan çözeriz.",
            "sim tarafına göre örneklerim.",
            "chart seçersen daha net bağlarım.",
        ]
    else:
        openers = ["Captain", "Friend", "Ciguli here", "Right seat ready", "Good call"]
        tails = [
            "we can expand it together.",
            "I can remember that for later.",
            "we can keep it simple.",
            "I will tune it for simulation.",
            "select a chart and I can connect it better.",
        ]

    bank = {}
    for intent, phrases in base_phrases.items():
        variants = set(phrases)
        for opener in openers:
            for phrase in phrases:
                variants.add(f"{opener}, {phrase[0].lower()}{phrase[1:]}")
        for phrase in phrases:
            for tail in tails:
                variants.add(f"{phrase} {tail}")
        bank[intent] = sorted(variants)
    return bank


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    tr_words = unique_words(TR_BASE, TR_CATEGORIES, TR_SUFFIXES, TR_DAILY_EXPRESSIONS + TR_PHRASAL_EXPRESSIONS, TR_CONNECTORS)
    en_words = unique_words(EN_BASE, EN_CATEGORIES, EN_SUFFIXES, EN_PHRASAL_VERBS + EN_DAILY_EXPRESSIONS, EN_CONNECTORS)

    write_lines(TRAINING_DIR / "vocabulary_tr.txt", ["# Ciguli Turkish vocabulary bank", *tr_words])
    write_lines(TRAINING_DIR / "vocabulary_en.txt", ["# Ciguli English vocabulary bank", *en_words])

    (TRAINING_DIR / "phrase_bank_tr.json").write_text(
        json.dumps(phrase_bank(TR_PHRASES, "tr"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (TRAINING_DIR / "phrase_bank_en.json").write_text(
        json.dumps(phrase_bank(EN_PHRASES, "en"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"TR vocabulary entries: {len(tr_words)}")
    print(f"EN vocabulary entries: {len(en_words)}")
    print("Phrase banks generated.")


if __name__ == "__main__":
    main()

# apps/content/structure.py — постоянная структура разделов (из старого сайта)
"""
Разделы сайта и их СТАРЫЕ адреса (docs/data/redirects.csv, строки keep).

Используется командами ``seed_site`` (создание пустого сайта) и ``import_joomla`` (привязка
материалов к разделам). ⚠️ Адреса менять нельзя — на них ведут поисковики.
"""

from __future__ import annotations

from typing import TypedDict


class CategoryDef(TypedDict, total=False):
    """Описание раздела."""

    slug: str
    title: str
    menu_title: str
    path: str | None
    kind: str
    template: str
    legacy_id: str
    folder: str  # папка в выгрузке (content/<folder>/)
    show_in_useful: bool
    ordering: int


# Разделы «Полезное» (вкладки на странице раздела)
USEFUL: list[CategoryDef] = [
    {
        "slug": "nuzhnye-dokumenty",
        "title": "Нужные документы",
        "path": "/nuzhnye-dokumenty/",
        "kind": "documents",
        "folder": "nuzhnye-dokumenty",
        "show_in_useful": True,
        "ordering": 10,
    },
    {
        "slug": "instrukcii-po-ohrane-truda",
        "title": "Инструкции по охране труда",
        "menu_title": "Инструкции по ОТ",
        "path": "/instrukcii-po-ohrane-truda/",
        "kind": "instructions",
        "folder": "instrukcii",
        "show_in_useful": True,
        "ordering": 20,
    },
    {
        "slug": "prikazy-po-ohrane-truda",
        "title": "Приказы по охране труда",
        "menu_title": "Приказы по ОТ",
        "path": "/prikazy-po-ohrane-truda/",
        "kind": "orders",
        "folder": "prikazy",
        "show_in_useful": True,
        "ordering": 30,
    },
    {
        "slug": "karty-identifikacii-opasnostej-ocenki-riskov",
        "title": "Карты идентификации опасностей, оценки рисков",
        "menu_title": "Карты рисков",
        "path": "/karty-identifikacii-opasnostej-ocenki-riskov/",
        "kind": "risk_cards",
        "folder": "karty-riskov",
        "show_in_useful": True,
        "ordering": 40,
    },
    {
        "slug": "stati",
        "title": "Статьи",
        "path": "/stati/",
        "kind": "articles",
        "folder": "stati",
        "show_in_useful": True,
        "ordering": 50,
    },
]

FAQ_ROOT: CategoryDef = {
    "slug": "chasto-zadavaemye-voprosy-po-ohrane-truda",
    "title": "Часто задаваемые вопросы по охране труда",
    "menu_title": "Вопрос-ответ",
    "path": "/chasto-zadavaemye-voprosy-po-ohrane-truda/",
    "kind": "faq",
    "template": "faq_hub",
    "legacy_id": "cat-24",
    "ordering": 60,
}

# 13 подразделов «Вопрос-ответ»: legacy_id = номер категории Joomla (папка vopros-otvet/<N>-…)
FAQ_SECTIONS: list[CategoryDef] = [
    {
        "legacy_id": "cat-31",
        "slug": "osnovnye-polozheniya-zakonodatelstva-respubliki-belarus-o-trude",
        "title": "Основные положения законодательства Республики Беларусь о труде",
    },
    {"legacy_id": "cat-32", "slug": "raznoe", "title": "Разное"},
    {
        "legacy_id": "cat-33",
        "slug": "gosudarstvennoe-upravlenie-ohranoj-truda.-nadzor-i-kontrol-za-soblyudeniem-trebovanij-ohrany-truda",
        "title": "Государственное управление охраной труда. Надзор и контроль за соблюдением требований охраны труда",
    },
    {
        "legacy_id": "cat-34",
        "slug": "organizaciya-raboty-po-ohrane-truda",
        "title": "Организация работы по охране труда",
    },
    {
        "legacy_id": "cat-35",
        "slug": "ohrana-truda-pri-proizvodstvennyh-processah-i-ekspluatacii-oborudovaniya",
        "title": "Охрана труда при производственных процессах и эксплуатации оборудования",
    },
    {
        "legacy_id": "cat-36",
        "slug": "ohrana-truda-pri-ekspluatacii-zdanij-i-sooruzhenij",
        "title": "Охрана труда при эксплуатации зданий и сооружений",
    },
    {"legacy_id": "cat-37", "slug": "elektrobezopasnost", "title": "Электробезопасность"},
    {"legacy_id": "cat-38", "slug": "pozharnaya-bezopasnost", "title": "Пожарная безопасность"},
    {
        "legacy_id": "cat-39",
        "slug": "proizvodstvennaya-sanitariya",
        "title": "Производственная санитария",
    },
    {
        "legacy_id": "cat-40",
        "slug": "sredstva-individualnoj-i-kollektivnoj-zashchity-smyvayushchie-i-obezvrezhivayushchie-sredstva",
        "title": "Средства индивидуальной и коллективной защиты, смывающие и обезвреживающие средства",
    },
    {
        "legacy_id": "cat-41",
        "slug": "sanitarno-bytovoe-i-lechebno-profilakticheskoe-obespechenie",
        "title": "Санитарно-бытовое и лечебно-профилактическое обеспечение",
    },
    {
        "legacy_id": "cat-42",
        "slug": "rassledovanie-i-uchet-neschastnyh-sluchaev-na-proizvodstve-i-professionalnyh-zabolevanij",
        "title": "Расследование и учёт несчастных случаев на производстве и профессиональных заболеваний",
    },
    {
        "legacy_id": "cat-43",
        "slug": "strahovanie-ot-neschastnyh-sluchaev-na-proizvodstve-i-professionalnyh-zabolevanij",
        "title": "Страхование от несчастных случаев на производстве и профессиональных заболеваний",
    },
]

# Группы услуг: своей страницы у них нет (path=None), они нужны хабу «Все услуги»
SERVICE_GROUPS: list[CategoryDef] = [
    {
        "slug": "uslugi-po-ohrane-truda",
        "title": "Услуги по охране труда",
        "path": None,
        "kind": "services_ot",
        "ordering": 1,
    },
    {
        "slug": "uslugi-po-suot",
        "title": "Услуги по СУОТ",
        "path": None,
        "kind": "services_suot",
        "ordering": 2,
    },
]

# Служебные страницы, которые должны существовать даже на пустом сайте (адрес → заголовок)
SPECIAL_PAGES: dict[str, str] = {
    "/uslugi-po-ohrane-truda-v-minske-i-po-belarusi.html": "Услуги по охране труда в Минске и по Беларуси",
    "/pages/more-pages/vse-uslugi-po-suot.html": "Услуги по системе управления охраной труда",
    "/ceny-na-razrabotku-suot-v-minske.html": "Цены на разработку СУОТ в Минске и по Беларуси",
    "/kontakty.html": "Контакты",
    "/o-nas.html": "О нас",
    "/nashi-klienty.html": "Наши клиенты",
    "/usloviya-okazaniya-uslug.html": "Условия оказания услуг",
    "/karta-sajta.html": "Карта сайта",
}

# Клиенты со старой страницы /nashi-klienty.html (материал id 39); первые 7 — в блок «Нам доверяют»
CLIENTS_FEATURED: list[str] = [
    "ККСУП «АкваМинск» (Аквапарк «Лебяжий»)",
    "ОАО «Строммаш»",
    "СЗАО «Фидмаш»",
    "ОАО «Союзпищепром»",
    "ОАО «Институт «БЕЛОРГСТАНКИНПРОМ»",
    "Белорусский государственный музей народной архитектуры и быта",
    "РУП «Издательский центр БГУ»",
]
CLIENTS: list[str] = [
    "ООО «БрэндФэшнГрупп»",
    "ОАО «Автопромторгагросервис»",
    "ИЧТПУП «Книжный клуб «Клуб любителей книги»",
    "СООО «М&М Милитцер & Мюнх»",
    "ООО «Детави»",
    "ТЧУП «Альфамед»",
    "ООО «Антес Мед»",
    "ООО «БиПластСервис»",
    "ИООО «БелМаркетКомпани»",
    "ККСУП «АкваМинск» (Аквапарк «Лебяжий»)",
    "ООО «Эскорт»",
    "СООО «Эволайн»",
    "СЗАО «Фидмаш»",
    "РУП «Издательский центр БГУ»",
    "ООО «Камена-Шабаны»",
    "ЗАО «Универсам «Щетовка»",
    "ООО «Дженерейшн-Пи Консалтинг»",
    "ООО «Витрум»",
    "УП «Клецкий автотехсервис» (г. Клецк)",
    "ОДО «БелСАР» (г. Орша)",
    "ОДО «Ольга-1» (г. Брест)",
    "ООО «Аполло Транс» (г. Брест)",
    "ОАО «Строммаш»",
    "ОАО «Союзпищепром»",
    "ООО «Реалкомсервис»",
    "ООО «А-Вент»",
    "ООО «ЭверестЭнерго»",
    "ООО «РИФТЭК ТЕХНО»",
    "ООО «Лузан»",
    "ООО «Камфи-Юнайтед»",
    "ООО «ЮМИКС»",
    "ЧУП «СКОП»",
    "ООО «АйКью Энерго»",
    "ООО «МАКАРДИС»",
    "ООО «Логрин»",
    "ООО «Холокс»",
    "ООО «СтройОлтэкс»",
    "ООО «ЛЕГУСГрупп»",
    "ЧТУП «Мапан»",
    "ООО «АрсеналМеталл»",
    "НПООО «Бикад-С»",
    "ООО «МелиусСтрой»",
    "ООО «Истэко»",
    "ООО «Надежный формат»",
    "ООО «ЮНИОНГАЗ»",
    "ПЧУП «Аксистрой»",
    "ООО «Строительная компания «Реновация»",
    "ООО «Рэйнбоу Инжиниринг»",
    "ТУП «Рэйнбоу Электроникс»",
    "ООО «МодульТехноСтрой»",
    "ООО «ЭнержетикБОКС»",
    "ЧУП «БилдингХоум»",
    "ООО «ВЕДИЗ электрострой»",
    "ООО «Ладинвест»",
    "ООО «Ваша Рамка»",
    "ПКООО «Интехмонтаж»",
    "ЧП «НАТУРГРАН»",
    "ООО «ДжиАйТекс»",
    "ЗАО «БелТетрисСтрой»",
    "ООО «ПолимерТорг»",
    "ОДО «Сантехремсервис-РСП»",
    "ООО «ДорСиСтрой»",
    "ОДО «КМСТРОЙ»",
    "ПЧУП «Полиринг»",
    "ООО «БелГазАгроМонтаж-Плюс»",
    "ИООО «Белбизнесальянс»",
    "ООО «КвантИнвест»",
    "ООО «Йорк кампании»",
    "ЧРСУП «Бизнесархсервис»",
    "ООО «Жибуль»",
    "ОДО «Кензо»",
    "ООО «Глорис»",
    "СООО «Бергамо»",
    "ОДО «Композан»",
    "ООО «Креатив-Запад»",
    "ИЧТУП «КоимпексПлюс»",
    "ИООО «Мегавита»",
    "ТРУП «Беллесбумпромэкспорт»",
    "ПЧТУП «Славалекс»",
    "ЧПУП «ГолденМебель»",
    "ЧУП «АктивКлининг Плюс»",
    "ЧУП «Мечтание»",
    "ОДО «Петрокар»",
    "ООО «Белхимсеть»",
    "ЧПСУП «Проект-Строймастер»",
    "ООО «Проект-Строймастер Плюс»",
    "ООО «ТеплоГазПроект»",
    "РИУ «Культура и искусство»",
    "Белорусский государственный музей народной архитектуры и быта",
    "ОАО «Институт «БЕЛОРГСТАНКИНПРОМ»",
    "РУП «Институт НИИСМ»",
    "Представительство АО «SKF EUROTRADE AB» (Швеция) в РБ",
    "Представительство ООО «РИГЛИ» (РФ) в РБ",
]

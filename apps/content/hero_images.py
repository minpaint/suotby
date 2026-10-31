# apps/content/hero_images.py — тематические фотоподложки страниц и разделов.
"""Изображение и точка кадрирования для каждого сюжета."""

CATEGORY_IMAGES: dict[str, tuple[str, str]] = {
    "osnovnye-polozheniya-zakonodatelstva-respubliki-belarus-o-trude": (
        "faq-law.webp",
        "center 55%",
    ),
    "raznoe": ("faq-misc.webp", "center 45%"),
    "gosudarstvennoe-upravlenie-ohranoj-truda.-nadzor-i-kontrol-za-soblyudeniem-trebovanij-ohrany-truda": (
        "faq-oversight.webp",
        "center 10%",
    ),
    "organizaciya-raboty-po-ohrane-truda": ("faq-organization.webp", "center 40%"),
    "ohrana-truda-pri-proizvodstvennyh-processah-i-ekspluatacii-oborudovaniya": (
        "faq-equipment.webp",
        "center 10%",
    ),
    "ohrana-truda-pri-ekspluatacii-zdanij-i-sooruzhenij": ("faq-buildings.webp", "center 25%"),
    "elektrobezopasnost": ("faq-electrical.webp", "center 15%"),
    "pozharnaya-bezopasnost": ("faq-fire.webp", "center 35%"),
    "proizvodstvennaya-sanitariya": ("faq-hygiene.webp", "center 15%"),
    "sredstva-individualnoj-i-kollektivnoj-zashchity-smyvayushchie-i-obezvrezhivayushchie-sredstva": (
        "faq-ppe.webp",
        "center 55%",
    ),
    "sanitarno-bytovoe-i-lechebno-profilakticheskoe-obespechenie": (
        "faq-health.webp",
        "center 20%",
    ),
    "rassledovanie-i-uchet-neschastnyh-sluchaev-na-proizvodstve-i-professionalnyh-zabolevanij": (
        "faq-investigation.webp",
        "center 40%",
    ),
    "strahovanie-ot-neschastnyh-sluchaev-na-proizvodstve-i-professionalnyh-zabolevanij": (
        "faq-insurance.webp",
        "center 35%",
    ),
    # ✏️ ИЗМЕНЕНО: у каждого раздела «Полезное» свой сюжет.
    "instrukcii-po-ohrane-truda": ("category-instructions.webp", "center 40%"),
    "karty-identifikacii-opasnostej-ocenki-riskov": ("category-risks.webp", "center 40%"),
    "nuzhnye-dokumenty": ("category-documents.webp", "center 40%"),
    "prikazy-po-ohrane-truda": ("category-orders.webp", "center 40%"),
    "stati": ("category-articles.webp", "center 40%"),
}


def category_hero(slug: str, *, is_faq: bool) -> dict[str, str]:
    image, position = CATEGORY_IMAGES.get(slug, ("knowledge-documents.webp", "center 55%"))
    return {
        "hero_image": f"img/{image}",
        "hero_position": position,
        "hero_eyebrow": "Вопрос-ответ" if is_faq else "Полезное по охране труда",
        "hero_subtitle": (
            "Ответы на практические вопросы нанимателей и специалистов"
            if is_faq
            else "Материалы для ежедневной работы вашей организации"
        ),
    }


MATERIAL_IMAGES: dict[str, str] = {
    # ✏️ ИЗМЕНЕНО: услуги и два каталога больше не используют общую фотоподложку.
    "34": "service-34.webp",
    "68": "service-68.webp",
    "69": "service-69.webp",
    "70": "service-70.webp",
    "71": "service-71.webp",
    "72": "service-72.webp",
    "73": "suot-development.webp",
    "74": "service-74.webp",
    "75": "service-75.webp",
    "76": "service-76.webp",
    "77": "service-77.webp",
    "78": "service-78.webp",
    "79": "service-79.webp",
    "80": "service-80.webp",
    "81": "service-81.webp",
    "179": "service-179.webp",
    "50": "services-inspection.webp",
    "pb-125": "hub-suot.webp",
    "100": "article-100.webp",
    "101": "article-101.webp",
    "308": "article-308.webp",
    "309": "article-309.webp",
    "311": "article-311.webp",
    "312": "article-312.webp",
    "318": "article-318.webp",
    "90": "article-90.webp",
    "95": "article-95.webp",
    "96": "article-96.webp",
    "97": "article-97.webp",
    "98": "article-98.webp",
    "99": "article-99.webp",
    "102": "order-102.webp",
    "103": "order-103.webp",
    "104": "order-104.webp",
    "105": "order-105.webp",
    "106": "order-106.webp",
    "235": "order-235.webp",
}


def material_hero(legacy_id: str, material_type: str) -> dict[str, str]:
    """Возвращает фотоподложку по ID Joomla; оба адреса одной услуги используют один сюжет."""
    if material_type == "service" or legacy_id in {"50", "pb-125"}:
        image = MATERIAL_IMAGES.get(legacy_id, "services-inspection.webp")
        return {"hero_image": f"img/{image}", "hero_position": "center 40%"}
    if material_type not in {"article", "order_sample"}:
        return {}
    image = MATERIAL_IMAGES.get(legacy_id, "knowledge-documents.webp")
    return {
        "hero_image": f"img/{image}",
        "hero_position": "center 35%",
        "hero_eyebrow": "Статья" if material_type == "article" else "Образец приказа",
    }

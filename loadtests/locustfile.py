# loadtests/locustfile.py — нагрузочный сценарий: locust -f loadtests/locustfile.py --host https://staging.suot.by
"""Типичный посетитель: главная, раздел, материал, вопрос-ответ, поиск."""

import random

from locust import HttpUser, between, task

MATERIALS = [
    "/prikaz-o-naznachenii-otvetstvennyh-po-ohrane-truda-primernyj-obrazec.html",
    "/instrukciya-po-ohrane-truda-dlya-operatorov-stankov-s-chislovym-programmnym-upravleniem.html",
    "/v-kakih-sluchayah-i-v-kakom-poryadke-provoditsya-proverka-znanij-po-voprosam-ohrany-truda-rabotayushchih.html",
    "/strasti-vokrug-kanavy-trebovaniya-po-ohrane-truda-k-osmotrovym-kanavam.html",
    "/razrabotka-i-vnedrenie-suot-pod-klyuch.html",
]
SECTIONS = ["/prikazy-po-ohrane-truda/", "/karty-identifikacii-opasnostej-ocenki-riskov/", "/stati/"]
QUERIES = ["инструктаж", "стажировка", "проверка знаний", "СИЗ", "медосмотр"]


class Visitor(HttpUser):
    wait_time = between(1, 4)

    @task(5)
    def material(self) -> None:
        self.client.get(random.choice(MATERIALS), name="/[материал].html")

    @task(3)
    def home(self) -> None:
        self.client.get("/")

    @task(2)
    def section(self) -> None:
        self.client.get(random.choice(SECTIONS), name="/[раздел]/")

    @task(1)
    def faq_hub(self) -> None:
        self.client.get("/chasto-zadavaemye-voprosy-po-ohrane-truda/")

    @task(1)
    def search(self) -> None:
        self.client.get("/poisk/", params={"q": random.choice(QUERIES)}, name="/poisk/")

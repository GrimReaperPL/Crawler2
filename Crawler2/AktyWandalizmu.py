# -- coding: utf-8 --
import requests
import re
from bs4 import BeautifulSoup

def przetworzStrone(url):
    "Funckja przetwarzająca strone na obiekt klasy BeautfulSoup"
    req = requests.get(url)
    req.encoding = "utf-8"

class Zmiany(object):
    "Przechowuje zmienione paragrafy wraz z informacją o ilości zmian"
    def __init__(self):
        self.paragrafPrzed = ""       #paragraf przed edycją
        self.paragrafPo = ""          #paragraf po edycji
        self.iloscZnakow = 0          #liczba zmienionych znaków
        self.iloscZmian = 0           #ilosc nastepujących po sobie + i - (lub odwrotnie)
        self.usuwany = False          #czy akapit został usunięty i jest przywracany czy odwrotnie
        self.komentarz = ""           #komentarz do wykonanej zmiany (dodadny przez autora wpisu)

class AktyWandalizmu(object):
    "Klasa główna crawlera"
    def __init__(self):
        self.strona = "https://en.wikipedia.org/w/index.php?title=God&offset=&limit=500&action=history"
        self.rewizje = []       #kontener na linki do rewizji powyżej 200 zmian
        self.liczbaZmian = 200  #liczba zmian do wyszukania
    def wyszukajZmiany(self):
        "Pobiera linki do wszystkich rewizji które mają więcej niż 200 zmian"

    def crawl(self):
        return "<h1>Crawler ended</h1>"


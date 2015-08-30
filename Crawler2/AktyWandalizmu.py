# -- coding: utf-8 --
import requests
import re
from bs4 import BeautifulSoup

def przetworzStrone(url):
    "Funckja przetwarzająca strone na obiekt klasy BeautfulSoup"
    req = requests.get(url)
    req.encoding = "utf-8"
    return BeautifulSoup(req.text, 'html.parser')

class Zmiany(object):
    "Przechowuje zmienione paragrafy wraz z informacją o ilości zmian"
    def __init__(self):
        self.paragrafPrzed = ""       #paragraf przed edycją
        self.paragrafPo = ""          #paragraf po edycji
        self.iloscZnakow = 0          #liczba zmienionych znaków
        self.iloscZmian = 0           #ilosc nastepujących po sobie + i - (lub odwrotnie)
        self.usuwany = False          #czy akapit został usunięty i jest przywracany czy odwrotnie
        self.komentarz = ""           #komentarz do wykonanej zmiany (dodadny przez autora wpisu)
        self.urlCur = ""              #link do cur
        self.urlPrev = ""             #link do prev
        self.odnosnik = ""            #link do wpisu w historii

class AktyWandalizmu(object):
    "Klasa główna crawlera"
    def __init__(self):
        self.strona = "https://en.wikipedia.org/w/index.php?title=God&offset=&limit=500&action=history"
        self.rewizje = []       #kontener na linki do rewizji powyżej 200 zmian
        self.liczbaZmian = 200  #liczba zmian do wyszukania
        self.wojny = {}         #słownik zawierający pary id: powiązane zmiany
    def wyszukajZmiany(self):
        "Pobiera linki do wszystkich rewizji które mają więcej niż 200 zmian"
        historia = przetworzStrone(self.strona).find(id="pagehistory").find_all("li")    #w stronie historii wyciągnij wszystkie wpisy zmian
        next = 0;       #zmienna pilnująca aby wpisy były obok siebie
        id = -1          #id potrzebne do klasyfikowania wpisów odnoszących się do tej samej zmiany
        for odnosnik in historia:
            for span in odnosnik.find_all('span', class_=re.compile("mw-plusminus-")):   #wyszukaj wszystkie wystapienia klas mw-plusminus-pos oraz mw-plusminus-neg czyli ilość zmian
                if abs(int(span.string[1:-1])) > self.liczbaZmian:      #jeżeli liczba zmian jest większa niż zakładana              
                    zmiana = Zmiany()
                    zmiana.iloscZnakow = abs(int(span.string[1:-1]))
                    zmiana.odnosnik = odnosnik
                    if int(span.string[1:-1]) > 0:
                        zmiana.usuwany = False
                    else:
                        zmiana.usuwany = True
                    if id in self.wojny and next > 0:       #jeżeli zmiany są obok siebie oraz jest już wcześniej dodane to dopisuje do tego id w słowniku
                        self.wojny[id].append(zmiana)
                        print("Weszlo" + str(span.string) + "z id: " + str(id))
                        next += 1                           #kontynuujemy numerowanie - jeżeli zmiany są następujące po sobie to ta zmienna rośnie
                    elif id not in self.wojny or next == 0:
                        id += 1                 #zwiększ id o 1, za pierwszym razem ustawia na 0 (w sumie to nie ma znaczenia - to nie C)
                        self.wojny[id] = []     #dodaje do słownika o kluczu id nową liste na której będą obiekty reprezentujące zmiany tych samych paragrafów
                        self.wojny[id].append(zmiana)
                        print("Weszlo" + str(span.string) + "z id: " + str(id))
                        next += 1               #dodajemy aby było powyżej zera
                    else:
                        pass        #coś nie pykło (powinien być tutaj jakiś exception)
                else:
                    next = 0
                    #id += 1
        for item in self.wojny:
            print item
        return self.wojny

    def crawl(self):
        "Glówna funkcja, zwraca rezultat do przeglądarki"
        return self.wyszukajZmiany()


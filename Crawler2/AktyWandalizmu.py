# -- coding: utf-8 --
import requests
import re
from bs4 import BeautifulSoup
from bs4 import NavigableString

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
        self.usunietoCaly = False     #czy złośliwie usunięto cały wpis
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
        self.calyAkapit = 20000 #liczba powyżej której uznajemy że cały akapit został usunięty
        self.wojny = {}         #słownik zawierający pary id: powiązane zmiany
        self.rezultat = ""      #wyniki do zwrócenia

    def wyszukajZmiany(self):
        "Pobiera linki do wszystkich rewizji które mają więcej niż 200 zmian"
        historia = przetworzStrone(self.strona).find(id="pagehistory").find_all("li")    #w stronie historii wyciągnij wszystkie wpisy zmian
        next = 0;       #zmienna pilnująca aby wpisy były obok siebie
        id = -1          #id potrzebne do klasyfikowania wpisów odnoszących się do tej samej zmiany
        for odnosnik in historia:
            for span in odnosnik.find_all(re.compile('span|strong'), class_=re.compile("mw-plusminus-")):   #wyszukaj wszystkie wystapienia klas mw-plusminus-pos oraz mw-plusminus-neg czyli ilość zmian
                liczba = int(span.string[1:-1].replace(',', ''))         #zamiana przecinka na nic czyli z 23,444 zrobi 23444 (inaczej będą błędy)       
                if abs(liczba) > self.liczbaZmian:      #jeżeli liczba zmian jest większa niż zakładana      
                    self.rezultat += "\n"               #żeby to jakoś wyglądało w przeglądarce        
                    zmiana = Zmiany()
                    zmiana.iloscZnakow = abs(liczba)
                    zmiana.odnosnik = odnosnik
                    if liczba > 0:          #jeśli dodatnia to znaczy że dodano jakiś tekst
                        zmiana.usuwany = False
                    else:
                        zmiana.usuwany = True
                        if abs(liczba) > self.calyAkapit:   #prawdopodobnie usunięto cały akapit
                            zmiana.usunietoCaly = True
                            print("Usunieto caly akapit");
                            self.rezultat += "Usunieto caly akapit \n "
                    komentarz = odnosnik.find('span', class_="comment")     #poszukaj komentarza
                    try:
                        print("Komentarz: " + unicode(komentarz.text).encode('ascii', 'ignore'))
                        self.rezultat += str("Komentarz: " + unicode(komentarz.text).encode('ascii', 'ignore')) + " \n "
                        zmiana.komentarz = unicode(komentarz.text).encode('ascii', 'ignore')
                    except AttributeError:
                        pass        #nie było opisu przy zmianie (zdarza się to jednak dość rzadko
                    cur = odnosnik.find('span', class_="mw-history-histlinks").find_all("a")    #wyszukanie linków do prev i cur
                    first = True    #pierwszy to zawsze cur a drugi prev
                    for link in cur:
                        if first:
                            print("Cur: " + "https://en.wikipedia.org/" + str(link.get('href')))
                            self.rezultat += str("Cur: " + "https://en.wikipedia.org/" + str(link.get('href'))) + " \n "
                            first = False
                        else:
                            print("Prev: " + "https://en.wikipedia.org/" + str(link.get('href')))
                            self.rezultat += str("Prev: " + "https://en.wikipedia.org/" + str(link.get('href'))) + " \n "
                    if id in self.wojny and next > 0:       #jeżeli zmiany są obok siebie oraz jest już wcześniej dodane to dopisuje do tego id w słowniku
                        self.wojny[id].append(zmiana)
                        print("Dodano" + str(span.string) + "z id: " + str(id))
                        self.rezultat += str("Dodano" + str(span.string) + "z id: " + str(id)) + " \n "
                        next += 1                           #kontynuujemy numerowanie - jeżeli zmiany są następujące po sobie to ta zmienna rośnie
                    elif id not in self.wojny or next == 0:
                        id += 1                 #zwiększ id o 1, za pierwszym razem ustawia na 0 (w sumie to nie ma znaczenia - to nie C)
                        self.wojny[id] = []     #dodaje do słownika o kluczu id nową liste na której będą obiekty reprezentujące zmiany tych samych paragrafów
                        self.wojny[id].append(zmiana)
                        print("Dodano" + str(span.string) + "z id: " + str(id))
                        self.rezultat += str("Dodano" + str(span.string) + "z id: " + str(id)) + " \n "
                        next += 1               #dodajemy aby było powyżej zera
                    else:
                        pass        #coś nie pykło (powinien być tutaj jakiś exception)
                else:
                    if liczba != 0:        #zauważyłem że czasem pomiędzy dwoma zmianami jest jedna z numerem zmian równym 0, nie wiem dlaczego tak jest
                        next = 0

    def odfiltrujPojedyncze(self):
        "Jeżeli nastąpiło dodanie tesktu lub jego usunięcie ale jest to jedynie uzupełnienie jakiejś informacji a nie ciągła zmiana akapitu to usuń takie wyniki"
        tylkoWojny = {}     #nowy słownik bez pojedynczych wystąpień
        for key in self.wojny:
            if len(self.wojny[key]) > 1:        #jeżeli wystąpiło + - (lub - +), czyli więcej niż pojedynczy niepowiązany wpis
                tylkoWojny[key] = self.wojny[key]
                #print tylkoWojny[key]
        self.wojny = tylkoWojny

    def crawl(self):
        "Glówna funkcja, zwraca rezultat do przeglądarki"
        self.wyszukajZmiany()
        self.odfiltrujPojedyncze()
        return self.rezultat


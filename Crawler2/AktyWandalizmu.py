# -- coding: utf-8 --
import requests
import re
from bs4 import BeautifulSoup
import datetime as dt   #do pomiaru czasu (to działa tak wooooolno)

def przetworzStrone(url):
    "Funckja przetwarzająca strone na obiekt klasy BeautfulSoup"
    requests.packages.urllib3.disable_warnings()        #wyłącza informacje o obsłudze SSL
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
        self.strona = "https://en.wikipedia.org/w/index.php?title=God&offset=&limit=500&action=history"     #chwilowa zmiana na 100 (bo za wolno)
        self.rewizje = []       #kontener na linki do rewizji powyżej 200 zmian
        self.liczbaZmian = 200  #liczba zmian do wyszukania
        self.calyAkapit = 20000 #liczba powyżej której uznajemy że cały akapit został usunięty
        self.wojny = {}         #słownik zawierający pary id: powiązane zmiany
        self.rezultat = ""      #wyniki do zwrócenia
        self.najwyzej = []       #zawiera posortowane id od największej ilości zmian do najmniejszej

    def wyszukajZmiany(self):
        "Pobiera linki do wszystkich rewizji które mają więcej niż 200 zmian"
        historia = przetworzStrone(self.strona).find(id="pagehistory").find_all("li")    #w stronie historii wyciągnij wszystkie wpisy zmian
        next = 0;       #zmienna pilnująca aby wpisy były obok siebie
        id = -1          #id potrzebne do klasyfikowania wpisów odnoszących się do tej samej zmiany
        for odnosnik in historia:
            for span in odnosnik.find_all(re.compile('span|strong'), class_=re.compile("mw-plusminus-")):   #wyszukaj wszystkie wystapienia klas mw-plusminus-pos oraz mw-plusminus-neg czyli ilość zmian
                liczba = int(span.string[1:-1].replace(',', ''))         #zamiana przecinka na nic czyli z 23,444 zrobi 23444 (inaczej będą błędy)       
                if abs(liczba) > self.liczbaZmian:      #jeżeli liczba zmian jest większa niż zakładana      
                    #self.rezultat += "\n"               #żeby to jakoś wyglądało w przeglądarce        
                    zmiana = Zmiany()
                    zmiana.iloscZnakow = abs(liczba)
                    zmiana.odnosnik = odnosnik
                    if liczba > 0:          #jeśli dodatnia to znaczy że dodano jakiś tekst
                        zmiana.usuwany = False
                        if abs(liczba) > self.calyAkapit:   #prawdopodobnie usunięto cały akapit
                            zmiana.usunietoCaly = True
                            print("Przywrocono caly akapit");
                    else:
                        zmiana.usuwany = True
                        if abs(liczba) > self.calyAkapit:   #prawdopodobnie usunięto cały akapit
                            zmiana.usunietoCaly = True
                            print("Usunieto caly akapit");
                            #self.rezultat += "Usunieto caly akapit \n "
                    komentarz = odnosnik.find('span', class_="comment")     #poszukaj komentarza
                    try:
                        print("Komentarz: " + unicode(komentarz.text).encode('ascii', 'ignore'))
                        #self.rezultat += str("Komentarz: " + unicode(komentarz.text).encode('ascii', 'ignore')) + " \n "
                        zmiana.komentarz = unicode(komentarz.text).encode('ascii', 'ignore')
                    except AttributeError:
                        pass        #nie było opisu przy zmianie (zdarza się to jednak dość rzadko
                    cur = odnosnik.find('span', class_="mw-history-histlinks").find_all("a")    #wyszukanie linków do prev i cur
                    first = True    #pierwszy to zawsze cur a drugi prev
                    for link in cur:
                        if first:
                            print("Cur: " + "https://en.wikipedia.org/" + str(link.get('href')))
                            #self.rezultat += str("Cur: " + "https://en.wikipedia.org/" + str(link.get('href'))) + " \n "
                            zmiana.urlCur = "https://en.wikipedia.org/" + str(link.get('href'))
                            first = False
                        else:
                            print("Prev: " + "https://en.wikipedia.org/" + str(link.get('href')))
                            #self.rezultat += str("Prev: " + "https://en.wikipedia.org/" + str(link.get('href'))) + " \n "
                            zmiana.urlPrev = "https://en.wikipedia.org/" + str(link.get('href'))
                    if id in self.wojny and next > 0:       #jeżeli zmiany są obok siebie oraz jest już wcześniej dodane to dopisuje do tego id w słowniku
                        self.wojny[id].append(zmiana)
                        print("Dodano" + str(span.string) + "z id: " + str(id))
                        #self.rezultat += str("Dodano" + str(span.string) + "z id: " + str(id)) + " \n "
                        next += 1                           #kontynuujemy numerowanie - jeżeli zmiany są następujące po sobie to ta zmienna rośnie
                    elif id not in self.wojny or next == 0:
                        id += 1                 #zwiększ id o 1, za pierwszym razem ustawia na 0 (w sumie to nie ma znaczenia - to nie C)
                        self.wojny[id] = []     #dodaje do słownika o kluczu id nową liste na której będą obiekty reprezentujące zmiany tych samych paragrafów
                        self.wojny[id].append(zmiana)
                        print("Dodano" + str(span.string) + "z id: " + str(id))
                        #self.rezultat += str("Dodano" + str(span.string) + "z id: " + str(id)) + " \n "
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
        self.wojny = tylkoWojny

    def poszukajAkapitu(self, zmiana):
        "Funkcja znajdująca zmienione akapity i zwraca zmieniony tekst przed i po"
        if zmiana.usunietoCaly:
            zmiana.paragrafPo = "Usunieto caly"
            zmiana.paragrafPrzed = "Usunieto caly"
            return
        edycja = przetworzStrone(zmiana.urlPrev)                #przeglądamy tylko obecną wersje z poprzednią (czyli prev)
        znaleziono = False                      #czasem zmiany nie są pogrubione (takie coś też należy wykryć)
        if zmiana.usuwany:
            usuniety = edycja.find_all('del', class_="diffchange diffchange-inline")
            for wpis in usuniety:
                print unicode("Usuniety wpis: ") + unicode(wpis.text).encode('ascii', 'ignore')
                zmiana.paragrafPrzed += unicode(wpis.text).encode('ascii', 'ignore')
                znaleziono = True
            if not znaleziono:      #jeśli nie znaleziono pogrubionego tekstu
                usuniety = edycja.find_all('td', class_="diff-deletedline")
                for wpis in usuniety:
                    try:
                        print unicode("Usuniety wpis: ") + unicode(wpis.div.text).encode('ascii', 'ignore')
                        zmiana.paragrafPrzed += unicode(wpis.div.text).encode('ascii', 'ignore')
                    except AttributeError:
                        pass        #usunięto pustą linie
        else:
            dodany = edycja.find_all('ins', class_="diffchange diffchange-inline")
            for wpis in dodany:
                print unicode("Dodany wpis: ") + unicode(wpis.text).encode('ascii', 'ignore')
                zmiana.paragrafPo += unicode(wpis.text).encode('ascii', 'ignore')
                znaleziono = True
            if not znaleziono:
                dodany = edycja.find_all('td', class_="diff-addedline")
                for wpis in dodany:
                    try:
                        print unicode("Dodany wpis: ") + unicode(wpis.div.text).encode('ascii', 'ignore')
                        zmiana.paragrafPo += unicode(wpis.div.text).encode('ascii', 'ignore')
                    except AttributeError:
                        pass        #dodano pustą linie

    def poszukajZmian(self):
        "Wykonuje typowego diffa na podanych stronach"
        for key in self.wojny:
            for zmiana in self.wojny[key]:
                zmiana.iloscZmian = len(self.wojny[key])        #uzupełnienie każdego obiektu o ilość zmian (będzie potrzebne do sortowania wg najbardziej zmienianego akapitu)
                print zmiana.iloscZmian
                self.poszukajAkapitu(zmiana)

    def sortuj(self):
        "Sortuje od największej ilości zmian do najmniejszej"
        for item in self.wojny:
            max = 0
            maxId = 0
            for id in self.wojny:
                if len(self.wojny[id]) > max and id not in self.najwyzej:
                    max = len(self.wojny[id])
                    maxId = id
            self.najwyzej.append(maxId)
        print self.najwyzej

    def formatujWyniki(self):
        "Funcja zwraca wyniki wyszukiwania w postaci 'czytelnej' dla użytkownika"
        for key in self.najwyzej:
            pierwszeWystapienie = 0         #zmienna pilnuje żeby Liczba zmian wyświetliła się tylko raz
            self.rezultat += "\n --------------- Zmiana ----------------- \n"
            for zmiana in self.wojny[key]:
                if pierwszeWystapienie == 0:
                   self.rezultat += "\nLiczba zmian: " + str(zmiana.iloscZmian) + "\n"
                   pierwszeWystapienie += 1
                self.rezultat += "Komentarz: " + zmiana.komentarz + "\n"
                if zmiana.usunietoCaly and zmiana.usuwany:
                    self.rezultat += "Zlosliwie usunieto cala tresc\n"
                elif zmiana.usunietoCaly and not zmiana.usuwany:
                    self.rezultat += "Przywrocono usunieta tresc\n"
                elif zmiana.usuwany:
                    self.rezultat += "Usunieto: " + zmiana.paragrafPrzed + " \n\n"
                elif not zmiana.usuwany:
                    self.rezultat += "Dodano: " + zmiana.paragrafPo + " \n\n"
                else:
                    pass        #coś zdecydowanie nie pykło

    def crawl(self):
        "Glówna funkcja, zwraca rezultat do przeglądarki"
        n1 = dt.datetime.now()
        self.wyszukajZmiany()
        self.odfiltrujPojedyncze()
        self.poszukajZmian()
        self.sortuj()
        self.formatujWyniki()
        n2 = dt.datetime.now()
        print "Uplyneło: " + str((n2-n1).seconds) + " sekund\n"
        return self.rezultat


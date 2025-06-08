# Projekt_Informacijski_Sustavi_v2

Ovaj projekt predstavlja cjelovit Point-of-Sale (POS) sustav dizajniran specifično za potrebe kafića. Aplikacija omogućava učinkovito upravljanje narudžbama, stolovima, proizvodima i korisnicima, uz preglednu analizu zarade.

Ključne Značajke
Upravljanje Stolovima: Interaktivni prikaz stolova s informacijama o statusu (slobodan/zauzet) i mogućnošću brzog otvaranja novih narudžbi.
Blagajna (POS Sučelje): Intuitivno sučelje za unos narudžbi. Omogućuje dodavanje proizvoda na račun, modifikaciju količina, te opcije za djelomično ili potpuno plaćanje (gotovina/kartica).
Administracija Proizvoda: Potpuna kontrola nad asortimanom proizvoda. Administratori mogu dodavati, uređivati i brisati proizvode, te ih organizirati po kategorijama.
Kategorije Proizvoda: Organizacija proizvoda po kategorijama za brži i jednostavniji pregled i odabir.
Autentifikacija Korisnika: Siguran sustav prijave za različite uloge (npr. konobar, administrator) s odgovarajućim razinama pristupa.
Dashboard za Analizu Zarade: Pregledna nadzorna ploča s grafičkim prikazima ukupne zarade i prodaje po kategorijama, omogućujući bolje razumijevanje poslovnih performansi.
Praćenje Narudžbi: Sustav bilježi sve narudžbe s detaljima o stavkama, količinama i cijenama.
Tehnologije Korištene u Projektu
Ovaj projekt je razvijen korištenjem sljedećih tehnologija:

Backend:
Flask: Mikro-web framework za Python.
Flask-SQLAlchemy: Proširenje za Flask koje olakšava rad s bazama podataka.
SQLite: Lagana datotečna baza podataka, idealna za razvoj i manje aplikacije.
Flask-Login: Upravljanje korisničkim sesijama.
Flask-WTF: Integracija WTForms za jednostavnije kreiranje web formi.
Werkzeug: WSGI alatna biblioteka za Python.
Frontend:
HTML5 & CSS3: Za strukturu i stil korisničkog sučelja.
JavaScript (Vanilla JS): Za interaktivnost i dinamičko ponašanje na strani klijenta.
Chart.js: JavaScript biblioteka za kreiranje interaktivnih grafičkih prikaza podataka na dashboardu.


# POKRETANJE APLIKACIJU

cd ~/Desktop

git clone https://github.com/SseBaaa/Projekt_Informacijski_Sustavi_v2

cd Projekt_Informacijski_Sustavi_v2

docker-compose up --build

Pokrećemo ga sa http://127.0.0.1:8080/

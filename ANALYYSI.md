**1. Mitä tekoäly teki hyvin?**
   
Models.py ja schemas.py tiedostot olivat mielestäni tekoälyltä hyvin tehty, jonka takia niihin en muutoksia tehnytkään.
Simppelit loogiset operaatiot toimivat pääosin semmoisinaan.
Annoin aluksi laajoja konteksteja kehotteina tekoälylle, jolloin tekoäly ei tuottanut niin hyviä vastauksia. Mutta aina tarkentaessani kehotteita sekä ohjaamalla keskustelua haluamaani suuntaan tekoälyn tuottamat vastaukset paranivat huomattavasti.








**2. Mitä tekoäly teki huonosti?**
    
Mielestäni reittien nimeämisessä ja etenkin GET-metodin, jolla haettiin tietyn huoneen varaukset alkuperäinen muoto oli epälooginen ja nurinkurinen.
Myös tietokantaan ja sen alustamiseen liittyviä toiminnallisuuksia oli ripoteltuna siellä täällä.
Liittyen edelliseen tekoäly sekoitti hieman eri kokonaisuuksia keskenään kuten data-kerroksen operaatioita ja business-logiikkaa. Myös HTTP-virheitä käsiteltiin CRUD operaatioiden kanssa samassa logiikassa.
Jotain käyttämättömiä riippuvuuksia myös tuli tekoälyn tuottamaan koodiin.







**3. Mitkä olivat tärkeimmät parannukset, jotka teit tekoälyn tuottamaan koodiin ja miksi?**

Refaktoroin ja erittelin ohjelman kokonaisrakennetta loogisiin osiin, jotta alkuperäisen version yhden tiedoston tyylistä päästiin pois. Helpottaa koodin ylläpitoa ja luettavuutta merkittävästi. 
    
Tietokantayhteyteen ja sen alustamiseen liittyvää logiikkaa siirsin database.py alle, ettei tulevaisuudessa muut tiedostot sotkeennu vaan logiikka on omassa selkeästi määritetyssä paikassa.
    
Määritetyt URL-reitit muutin loogisemmiksi. Itselle tietyn huoneen varauksien haku on loogisempi muodossa /varaukset/huoneet/huone_id kuin /huoneet/huone_id/varaukset kun kyse on huoneiden *varaus*rajapinnasta.
    
Tekoälyn tuottamassa koodissa sekoittui CRUD operaatiot ja business-logiikka. Refaktoroin tekoälyn tuottaman crud.py tiedoston kahteen eri loogiseen kokonaisuuteen, omiin luokkiinsa. Tein tiedostot repositories.py, joka vastaa
data-kerroksesta ja services.py, joka vastaa business-logiikasta. Testauksen, uudelleenkäytettävyyden ja ylläpidon kannalta olennainen muutos. Muutoksen myötä pystyy testaamaan tietokanta operaatioita, tulematta testanneeksi            validointi logiikkaa samalla. Muutoksen myötä esimerkiksi "overlap" logiikkaa voi käyttää myös muualla saamatta samaan pakettiin HTTP-poikkeus logiikkaa. Ylläpidettävyyden kannalta, jos täytyy muokata validointi logiikkaa ei           tarvitse koskea data-kerroksen logiikkaan, ja päinvastoin.

Tekoälyn tuottamaa repositories.py tiedostoa muokkasin sopivammaksi omaan luokkapainotteisempaan tyyliin, jossa tietokanta säilyy instanssina muuttujassa eikä sitä syötetä jokaiselle funktiolle erikseen. Tekoäly nimesi funktioita todella nimenomaisesti ja muutin ne kontekstin huomioiden simppelimmiksi. Varauksen poisto-logiikassa oli sotkettuna myös haku ja validointi, jotka siirsin services.py hoidettavaksi. Myös id-generoinnin siirsin data-kerroksesta services.py huolehdittavaksi.

Tekoälyn tuottama services.py koodia muokkasin niin että validointi logiikka on omissa metodeissa eikä useassa eri if lohkossa saman funktion sisällä. Helpottaa luettavuuta, testattavuutta ja uudelleenkäytettävyyttä. Myös logiikka jossa validoidaan annetun päivämäärän aikavyöhyke, palauttivat geneerisen virheilmoituksen. Parannetussa toteutuksessa erillisillä funktiokutsuilla saadaan tarkempi tieto virheestä.
 

    

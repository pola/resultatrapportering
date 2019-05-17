# betygsrapportering
Katalogen innehåller olika skript för att rapportera in resultat på uppgifter i kurser i Canvas på KTH.

## Kom igång
Skripten behöver en hemlig nyckel för att kunna användas. För att skapa en sådan hemlig nyckel, kör nyckelskaparen:  
``$ nyckelskapare.py``  
Nyckeln sparas i filen `hemlig-nyckel.txt` och används sedan av skripten.

Alla skript tar åtminstone ett `<kursnamn>` som argument. Det är en hel eller en del av ett kursnamn som man har en annan roll än student på. Det går att ge smeknamn på kurser, om man exempelvis tycker att ett kursnamn är för långt, genom att köra:__
``$ smeknamn.py``

Skripten kan endast rapportera in resultat för studenter som är inlagda på kurser i Canvas och uppgifterna måste vara i publicerat läge.

## enstaka.py
Det här skriptet kan användas för att rapportera in enstaka uppgifter för enstaka studenter. Det är interaktivt i bemärkelsen att man tillåts söka upp studenter, uppgifter och sätta resultat genom inmatningsfält i terminalen.

Starta skriptet för en kurs:  
``$ enstaka.py <kursnamn>``

### Användargränssnitt
Skriptet är interaktivt och flödet är enligt följande.
1. Sök upp en student genom att ange en del av namnet. Om det finns flera studenter får du välja vilken du vill rapportera resultat för.
2. Välj uppgift att rapportera för. Här går det antingen att ange uppgiftens namn eller löpnumret på uppgiften från listan med sökresultat (`1`, `2`, ...)
3. Skriv in ett resultat. Om uppgiften tar emot poäng ska det vara ett heltal och om uppgiften står som godkänd/icke godkänd ska det vara `P` eller `F`. Det går även att ange ett minustecken (`-`) för att rensa ett tidigare inlagt resultat.
4. Efter att resultatet har sparats går skriptet tillbaka till steg 2, så att man kan rapportera ytterligare resultat samma student.

Det går alltid att gå tillbaka till föregående steg genom att lämna inmatningsfältet tomt (tryck bara ENTER).

### Begränsningar
Just nu finns det endast stöd för uppgifter som har poäng, godkänt/icke godkänt eller graderade resultat (typiskt sett A-F) som betygsskala. Skriptet varnar om man är på väg att sätta ett resultat på en gruppuppgift där alla i gruppen får samma resultat, men man får inte reda på vilka andra studenter som är på väg att få det resultatet.

## klump.py
Det här skriptet kan användas för att rapportera in resultat för många studenter och på en gång, från en resultatfil.

Skriptet körs så här:  
``$ klump.py <kursnamn> <sökväg till resultatfil>``

### Format för resultatfil
Resultatfilen ska innehålla en rad med kolumnhuvuden följt av en rad per student. I den första raden ska det alltid framgå vilken kolumn som innehåller studenternas ID-nummer. Den raden ska även innehålla kolumnhuvuden för de uppgifter som skriptet ska rapportera in resultat för. Kolumenhuvudet med studenternas ID-nummer ska heta `ID` och kolumnhuvudena med uppgifterna ska sluta med `(<ID-nummer>)`, där `<ID-nummer>` är respektive uppgifts ID-nummer i Canvas. För att hitta ID-numret för en uppgift, gå in på uppgiften i Canvas och titta i webbläsarens adressfält.

Kolumnerna separeras med TAB (`\t`). Det måste vara lika många kolumner i varje rad, men det kan finnas kolumner som varken avser studenter eller uppgifter. Här är ett exempel på en resultatfil:
```
namn	ID	uppg1 (1234)	uppg2 (5678)	uppg3	slutbetyg (9123)
Per Silja	456	E	E	C	D
Tom At	789	E	D	-	E
Per On	876			C	C
```
I exemplet ovan finns det tre studenter. Resultat kommer rapporteras in för `uppg1`, `uppg2` och `slutbetyg`. Den tredje uppgiften, `uppg3`, saknar ID-nummer och kommer ignoreras. Även den första kolumnen, `namn`, kommer ignoreras. Varje resultat kan vara något från respektive uppgifts betygsskala, eller `-` för att rensa ett tidigare inlagt resultat. Om en cell är tom, som hos den sista studenten i resultatfilen ovan, kommer skriptet inte ändra det resultatet alls.

### Hämta resultatfil från Canvas
Gå in på omdömesmatrisen i Canvas och exportera den som en CSV-fil för att få ett underlag som kan fungera som resultatfil till skriptet. Öppna filen i ett kalkylprogram. För att skapa en resultatfil som skriptet kan läsa in, spara filen som en CSV-fil med TAB som kolumnseparator. Se till att _inte_ ha med några andra tecken runt kolumner, så som `"` eller `'`.

Canvas har en möjlighet att importera en CSV-fil som tidigara har exporterats, och på så sätt uppdatera de ändrade betygen. Det kan tyckas göra det här skriptet onödigt, men erfarnheten har visat att Canvas funktion för att importera CSV-filer inte fungerar tillfredsställande. Webbläsaren skickar ett HTTP-anrop per resultat att ändra, sekventiellt. Det sker i bakgrunden, när man har importerat en fil, och som användare får man ingen återkoppling på hur det går om man inte öppnar webbläsarkonsolen och tittar på nätverkstrafiken. Dessutom hoppar den över studenter långt ned i omdömesmatrisen om för stora kurser, vilket gör att vissa resultat inte rapporteras in alls. Ytterligare ett problem är avsaknaden av felhantering; importeringsfunktionen i Canvas ger inget meddelande om ett resultat är felaktigt angivet eller om en student inte är inlagd i kursen. Det här skriptet löser de problemen genom att inte avslutas förrän alla resultat är inrapporterade och genom att vara generös med att skriva ut eventuella felmeddelanden.

### Kontroller
När skriptet körs kommer det ske extensiva kontroller av resultatfil. Bland annat följande kontrolleras.
* De angivna uppgifterna existerar för den valda kursen.
* De angivna studenterna är inlagda i den valda kursen.
* Ingen uppgift förekommer flera gånger, i flera kolumnhuvuden.
* Ingen student förekommer flera gånger, i flera rader.
* De angivna resultaten är giltiga för uppgiften; bokstavsbetyg från uppgiftens betygsskala, poäng, `-` eller ingenting.

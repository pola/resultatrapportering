# betygsrapportering
Skriptet kan användas för att rapportera betyg på uppgifter i kurser i Canvas på KTH.

## Kom igång
Kopiera filen `config.example.py` till konfigurationsfilen `config.py` och lägg in en API-nyckel. Om du inte har en API-nyckel kan det fås genom att besöka https://kth.instructure.com/profile/settings och klicka på knappen _Ny tillgångstoken_.

Lägg även in en kurs i konfigurationsfilen genom att mappa ett namn till kursens ID-nummer i Canvas. Du kan få reda på en kurs ID-nummer genom att gå in på kursen i webbläsaren och titta i adressfältet.

Kör sedan skriptet för en kurs:  
``betygsrapportering.py <kursnamn>``

Kursnamnet hämtas från konfigurationsfilen. I `config.example.py` är `tilpro18` kursnamnet och det skulle kunna användas så här:  
``betygsrapportering.py tilpro18``

## Användargränssnitt
Skriptet är interaktivt och flödet är enligt följande.
1. Sök upp en student genom att ange en del av namnet. Om det finns flera studenter får du välja vilken du vill rapportera betyg för.
2. Välj uppgift att rapportera för. Här går det antingen att ange uppgiftens namn eller löpnumret på uppgiften från listan med sökresultat (`1`, `2`, ...)
3. Skriv in ett betyg. Om uppgiften tar emot poäng ska det vara ett heltal och om uppgiften står som godkänd/icke godkänd ska det vara `P` eller `F`. Det går även att ange ett minustecken (`-`) för att rensa ett tidigare inlagt betyg.
4. Efter att betyget har sparats går skriptet tillbaka till steg 2, så att man kan rapportera ytterligare betyg samma student.

Det går alltid att gå tillbaka till föregående steg genom att lämna inmatningsfältet tomt (tryck bara ENTER).

## Begränsningar
Just nu finns det endast stöd för uppgifter som har poäng, godkänt/icke godkänt eller graderade betyg (typiskt sett A-F) som betygsskala. Skriptet varnar om man är på väg att sätta ett betyg på en gruppuppgift där alla i gruppen får samma betyg, men man får inte reda på vilka andra studenter som är på väg att få det betyget.

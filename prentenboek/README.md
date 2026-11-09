# Agent Daan & Joep — De koekjesboeven

Een prentenboek voor een peuter van drie, in de stijl van een **papieren kijkdoos**: elke plaat is een gelaagd diorama van uitgeknipt papier, gefotografeerd zoals een maquette op tafel. Daan is politieagent, zijn aapje Joep is zijn hulpagent. Samen vangen ze twee boeven die alle koekjes van de bakker hebben gepakt.

Alle platen zijn gemaakt in **Blender 5.1 (Cycles)**, volledig procedureel vanuit Python. Geen AI-beeldgenerator en geen externe modellen.

## De papierstijl

- **Knipsels** (`blender/lib/papier.py`): elke vorm wordt in centimeters ontworpen en als dun karton uitgesneden, met een iets onregelmatige schaarrand, een lichtere snijkant en een klein beetje kromming. Laagjes liggen 1,2 mm uit elkaar, zodat er echte schaduwen tussen vallen. Veel kleine stukjes (klinkers, tegels, kruimels) worden als één mesh gemaakt (`tiles`).
- **Papiersoorten**: karton, mat papier, linnenreliëf, kraftpapier (vezels en spikkels), aquarelpapier (gewassen kleur), crêpepapier (plooitjes), zijdepapier (doorschijnend), golfkarton, glanspapier, goud- en zilverfolie, glas, en bedrukt papier: strepen, stippen, boerenbont en breisel.
- **Figuren** (`blender/lib/papierpop.py`): Daan (politiepakje van linnen, ster en schildje van goudfolie, haar van crêpepapier; ook in gewone kleren en pyjama), Joep (kraftpapieren knuffelaapje), de bakker (boerenbont schort) en de twee boeven (gestreept shirt, gebreide muts).
- **Decors en voorwerpen** (`blender/lib/papierset.py`): luchtdoek van aquarelpapier met wolken en zon aan draadjes, heuvels, bomen en struiken van crêpepapier, een Hollandse straat met rode klinkers in visgraat en grijze stoeptegels, huisjes met golfkartonnen daken, de bakkerij (binnen en buiten), een polderweggetje met molen, het tuinhekje en de schommel, de slaapkamer met lappendeken. De koekjes zijn **koekmannetjes** met wit glazuur en snoepknoopjes; de politieauto heeft de Nederlandse striping en echte raamopeningen, zodat Daan achter het stuur zit.
- **Beeld**: licht zoals bij een kijkdoos op tafel (zacht hoofdlicht van linksvoor, een lamp op het luchtdoek), per plaat een eigen standpunt: laag bij de omslag, van bovenaf bij het kruimelspoor, vanuit de boomkruin naar de struik.

## Het boek

Formaat zoals *De Stip*: dicht 21 × 21 cm, open 42 × 21 cm. 32 pagina's: voorkant, p. 1-30, achterkant.

| Bestand | Wat het is |
|---|---|
| `agent-daan-en-joep.pdf` | Het boek als bladen van 42 × 21 cm: de omslag (achter- en voorkant) en 15 dubbele pagina's. |
| `agent-daan-en-joep-druk.pdf` | Drukbestand: 32 losse pagina's van 21 × 21 cm met 3 mm afloop rondom (300 dpi). |
| `web/` | Het bladerboek als website (statisch, zoals *De Stip*): `index.html`, `pages/` (1600 px) en `pages-hd/` (2400 px). |
| `artifact/` | Dezelfde bladerboekpagina als Claude-artifact. |
| `renders/` | De ruwe Cycles-renders (5040 × 2520 per dubbele pagina, 2520 × 2520 per losse pagina; incl. afloop). |
| `storyboard.jpg` | Alle bladen op een rij met beeld, uitsnede en plaats van de tekst. |
| `ontwerp/` | Ontwerpbeelden en proefplaten. |
| `v1-threejs/` | De eerste, interactieve three.js-versie met losse platen. |

## Bladzijden

| Pagina | Tekst | Beeld |
|---|---|---|
| Omslag | *Agent Daan & Joep — De koekjesboeven* | Daan groot vooraan, salueert; Joep op de motorkap van de politieauto. Achterop sluipen de boeven bij de bakkerij weg; een kruimelspoor loopt schuin naar Daan. |
| 1-2 | Titelpagina | Schutblad met koekmannetjes, petjes, sterren, vergrootglazen en bananen; Daan houdt Joep vast. |
| 3-4 | Dit is Daan. En dit is Joep, het aapje van Daan. | In de tuin achter het witte hekje: Daan zwaait, Joep schommelt. |
| 5 | Daan zet zijn politiepet op. | In zijn kamer, met twee handen, naast de verkleedkist. |
| 6 | Joep krijgt ook een pet. Nu zijn ze agent! | Samen salueren; Joep staat op de kist. |
| 7-8 | *Nie-nu, nie-nu!* Daar gaat de politieauto. | Door de polder langs de molen, Daan achter het stuur, Joep achterin, stofwolkjes erachter. |
| 9-10 | Oh nee! Bij de bakker zijn alle koekjes weg. | In de bakkerij: lege bakplaten, lege koekjespot, de bakker steekt zijn handen omhoog. |
| 11-12 | Kijk eens, kruimels! Wie heeft dat gedaan? | Van bovenaf op de stoep: Daan met vergrootglas, Joep wijst het kruimelspoor na. |
| 13-14 | Joep klimt in de boom. *Hup, hup, hup!* | Joep tegen de dikke stam, Daan wijst omhoog. |
| 15-16 | Joep ziet iets. Daar, achter de struik! | Joep in de boomkruin; ver weg schoenen, een mouw en de zak onder een struik. |
| 17-18 | Twee boeven met een zak vol koekjes. *Smik, smak, smul!* | De boeven smullen in het gras; Daan en Joep gluren over een struik. |
| 19-20 | *Stop! Politie!* roept Daan. *Oe-oe-aa-aa!* roept Joep. | Daan links, Joep springt rechts uit de struik; de boeven ertussen, koekjes vliegen rond. |
| 21 | De boeven schrikken. | Armen omhoog, de koekmannetjes vliegen door de lucht. |
| 22 | ‘Sorry,’ zeggen ze. ‘We hadden zo’n honger.’ | Masker omhoog, beteuterd; ze geven de zak terug aan Daan. |
| 23-24 | Samen brengen ze de koekjes terug. Iedereen krijgt er één. Joep krijgt er twee! | Lange tafel met boerenbont kleed voor de bakkerij. |
| 25-26 | Goed gedaan, agent Daan! Goed gedaan, agent Joep! | Feest op het plein: medailles, vlaggetjes, confetti; de boeven met een koksmuts. |
| 27-28 | Nu is het bedtijd. Welterusten, agent Daan. Welterusten, Joep. | Nacht: Daan slaapt onder de lappendeken met Joep, de pet aan het bed. |
| 29-30 | Einde | Joep slaapt tegen een groot koekmannetje; schutblad. |

## Zelf opnieuw maken

```bash
# één plaat (preview of eindkwaliteit) — vanuit de map prentenboek
"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P blender/run.py -- sp07_auto uit.png --q final
# alle platen
SAMPLES=256 blender/batch.sh final renders omslag sp03_dit_is_daan p05_pet_op ...
# boek, PDF's, website en artifact uit de renders
python boek/build.py --bron renders
```

- `blender/lib/papier.py`, `papierpop.py`, `papierset.py`, `papierscene.py`: de papierbibliotheek (knipsels en papiersoorten, figuren, decors en voorwerpen, opzet per plaat).
- `blender/scenes/`: één script per plaat; `papier_ontwerp.py` en `papier_props.py` zijn ontwerpvellen.
- `boek/build.py`: nabewerking, tekstopmaak, PDF's, website en artifact. Lettertype: Museo Sans Rounded.
- Oudere bibliotheekdelen (`wol*`, `vilt*`, `felt`, `sdf`, `head*`, `hair`, `daan`, `joep`, `people`, `props`, `world`, `sets`) zijn van eerdere versies en blijven staan als referentie.

## Privacy

De echte foto's van Daan en Joep staan **niet** in deze repository en zijn niet naar een externe dienst gestuurd. `.gitignore` sluit foto- en werkmappen uit.

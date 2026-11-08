# Agent Daan & Joep — De koekjesboeven

Een 3D-prentenboek voor een peuter van drie. Daan is politieagent, zijn knuffelaapje Joep is zijn hulpagent. Samen vangen ze twee boeven die alle koekjes van de bakker hebben gepakt.

Alle platen zijn gemaakt in **Blender 5.1 (Cycles)**, volledig procedureel vanuit Python: personages, haar (Hair Curves), pluchevacht, kleding, auto, straat, park, bakkerij en slaapkamer. Geen AI-beeldgenerator en geen externe modellen.

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
| `ontwerp/` | Ontwerpbeelden, het Blender-plan en de proefplaat van Daan en Joep. |
| `v1-threejs/` | De eerste, interactieve three.js-versie met losse platen. |

## Bladzijden

| Pagina | Tekst | Beeld |
|---|---|---|
| Omslag | *Agent Daan & Joep — De koekjesboeven* | Lage heldenhoek: Daan met handen in de zij, Joep salueert op zijn schouder; achterop sluipen de boeven weg. |
| 1-2 | Titelpagina | Schutblad met koekjes, sterren en petjes; Joep met een groot koekje. |
| 3-4 | Dit is Daan. En dit is Joep, het aapje van Daan. | Van bovenaf op het ronde kleed, ochtendzon door het raam. |
| 5 | Daan zet zijn politiepet op. | Close-up: de pet net boven zijn kuif. |
| 6 | Joep krijgt ook een pet. Nu zijn ze agent! | Kikvorsperspectief bij de voordeur, politieauto ernaast. |
| 7-8 | *Nie-nu, nie-nu!* Daar gaat de politieauto. | Camera op straathoogte rijdt mee; straat bewogen, auto scherp. |
| 9-10 | Oh nee! Bij de bakker zijn alle koekjes weg. | Vanuit de lege vitrine: Daan en Joep tegen het glas, de bakker erachter. |
| 11-12 | Kijk eens, kruimels! Wie heeft dat gedaan? | Op tegelhoogte: Daan op zijn buik, zijn oog groot achter het vergrootglas. |
| 13-14 | Joep klimt in de boom. *Hup, hup, hup!* | Langs de stam omhoog; Daan wijst. |
| 15-16 | Joep ziet iets. Daar, achter de struik! | Over Joeps schouder vanaf een tak omlaag. |
| 17-18 | Twee boeven met een zak vol koekjes. *Smik, smak, smul!* | Door de bladeren: de boeven smullen. |
| 19-20 | *Stop! Politie!* roept Daan. *Oe-oe-aa-aa!* roept Joep. | Vanuit de boeven gezien: Daan stapt door de struik, Joep springt. |
| 21 | De boeven schrikken. | Koekjes vliegen door de lucht. |
| 22 | ‘Sorry,’ zeggen ze. ‘We hadden zo’n honger.’ | Van bovenaf: twee sippe boeven, maskers omhoog. |
| 23-24 | Samen brengen ze de koekjes terug. Iedereen krijgt er één. Joep krijgt er twee! | Schuin van boven op de terrastafel. |
| 25-26 | Goed gedaan, agent Daan! Goed gedaan, agent Joep! | Feest voor de bakkerij, confetti, medailles. |
| 27-28 | Nu is het bedtijd. Welterusten, agent Daan. Welterusten, Joep. | Maanlicht, nachtlampje, Daan slaapt met Joep in zijn arm. |
| 29-30 | Einde | Slotvignet en schutblad. |

## Zelf opnieuw maken

```bash
# één plaat (preview of eindkwaliteit) — vanuit de map prentenboek
"C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" -b --factory-startup -P blender/run.py -- sp07_auto uit.png --q final
# alle platen
blender/batch.sh final renders omslag sp03_dit_is_daan p05_pet_op ...
# boek, PDF's, website en artifact uit de renders
python boek/build.py
```

- `blender/lib/` — de bibliotheek: `core` (meshes, buizen, haar, camera, licht), `mats` (Cycles-materialen), `head` + `hair` (Daans hoofd en haar), `daan`, `joep`, `people` (boeven en bakker), `props`, `world`, `sets`, `stage`.
- `blender/scenes/` — één script per plaat.
- `boek/build.py` — nabewerking (gloed, vignet), tekstopmaak, PDF's, website en artifact. Lettertype in de pagina's: Museo Sans Rounded.

## Privacy

De echte foto's van Daan en Joep staan **niet** in deze repository en zijn niet naar een externe dienst gestuurd. `.gitignore` sluit foto- en werkmappen uit.

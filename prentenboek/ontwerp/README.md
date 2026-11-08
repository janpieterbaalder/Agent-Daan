# Ontwerp en Blender-plan

Startpunt voor de Blender-versie van *Agent Daan & Joep*. Doel: platen op het niveau van een gestileerde 3D-animatiefilm, met zachte huid, echte haarplukken, pluchebont en stofstructuur.

## Referenties

| Bestand | Inhoud |
|---|---|
| `jongen-ontwerp.jpg` | **Hoofdontwerp van de jongen** (gekozen door Jan Pieter): voor- en driekwartaanzicht in politiepak met pet. Gezicht, verhoudingen, kleding en pet volgen dit beeld. |
| `jongen-kapsel.jpg` | Alleen als referentie voor het haar zonder pet (bladzijde 1 en 13). Het gezicht komt uit een ander ontwerp; bij verschil wint `jongen-ontwerp.jpg`. |
| `joep-ontwerp.jpg` | Joep: voor- en zijaanzicht. |

Beide zijn met AI gemaakt op basis van een tekstbeschrijving. Er zijn geen foto's gebruikt of geüpload. De echte foto's staan niet in deze repository.

## De jongen (ongeveer 3 jaar)

- **Verhoudingen:** groot hoofd (ca. 1/3 van de lengte), korte benen, rond buikje, mollige handjes.
- **Gezicht:** zacht en rond, volle wangen met een roze blos, licht huidtype. Grote grijsblauwe ogen met een glanzende catchlight, haast onzichtbare lichtblonde wenkbrauwen, klein knopneusje, lief gesloten lachje, oren staan iets uit.
- **Haar:** platinablond tot bijna wit.
  - Met pet: zachte blonde lokken die onder de pet uitkomen, bij de slapen en in de nek, plus een kort pluizig pony'tje.
  - Zonder pet: zijkanten en achterhoofd heel kort, bovenop een losse kuif naar voren en omhoog (zie `jongen-kapsel.jpg`).
- **Kleding:**
  - Donkerblauw politieoverhemd met twee borstzakken met klep, zilveren knoopjes, schouderlusjes en een gouden ster links.
  - Donkerblauwe broek, zwarte veterschoentjes, zwarte riem met zilveren gesp en een zwarte portofoon op de rechterheup.
  - Donkerblauwe pet met glanzende zwarte klep, zwarte band en een gouden schildje met ster.
  - Op de laatste bladzijde draagt hij een lichtblauwe pyjama.

## Joep (knuffelaapje, ca. 15 cm)

- **Pluche:** kort en fluwelig, karamel- tot kastanjebruin, een beetje sleets.
- **Gezicht:** crème, in de vorm van een breed afgerond hart over ogen, wangen, snuit en kin. Bovenop het voorhoofd bruin.
- **Borduursel:** zwarte stipogen, een driehoekig neusje en een dun lachlijntje, als satijnsteek.
- **Oren:** klein, rond en bruin, laag aan de zijkant, staan opzij uit.
- **Lijf en ledematen:** klein boonvormig lijf. Lange dunne slungelarmen en -benen met ronde uiteinden; de benen zijn langer dan het lijf.
- **Overig:** plat flapperig staartje (iets donkerder), wit ophanglusje bovenop het hoofd, zichtbare naden.
- **Pet:** vanaf bladzijde 2 een piepklein donkerblauw politiepetje met gouden ster.

## Aanpak in Blender (Cycles) — zoals gebouwd

Alles staat in `../blender/` en wordt vanaf de commandline gebouwd (`blender -b -P run.py`).

- **Hoofd** (`lib/head.py`): vervormde bol met volle wangen, knopneusje, mondgroef en oogkassen; blos, lippen en sproetjes als kleurattribuut; huid met subsurface. Ogen met procedurele iris, glanzende cornea en amandelvormige oogleden; mond open/dicht per uitdrukking.
- **Haar** (`lib/hair.py`): Hair Curves. Kuif als ca. 250 lokken van parallelle strengen die over een 'haarschil' naar voren lopen en vooraan omhoog krullen; zijkanten als kort dons; donkerdere wortels via de Hair Info-intercept. Onder de pet alleen plukjes bij de slapen.
- **Lijf** (`lib/daan.py`, `lib/body.py`): buizen langs splines met IK voor armen en benen (rekbaar, cartoonstijl), mollige handjes met vingers, schoentjes; uniform met kraag, beleg, knoopjes, borstzakken met klep, schouderlusjes, ster, riem met gesp en portofoon. Pyjama voor bedtijd.
- **Joep** (`lib/joep.py`): pluche basis met hartvormig crème gezichtsmasker en naden als attributen, ca. 250.000 korte vachtharen (Hair Curves) met kleur per haar, geborduurde oogjes, neusje en lach, lusje, plat staartje, petje.
- **Bijfiguren** (`lib/people.py`): lange en dikke boef (streepshirt, maskertje, muts, stoppels), bakker (koksmuts, snor, schort).
- **Decor** (`lib/world.py`, `lib/sets.py`, `lib/props.py`): visgraatklinkers steen voor steen, stoeptegels, grassprieten als Hair Curves, bomen en struiken met losse blaadjes, Hollandse trap- en klokgevels, bakkerij met luifel, slaapkamer, kindermaat-politieauto in Nederlandse striping, koekjes, kruimels, jutezak, vergrootglas met echte lens, medailles, confetti.
- **Licht en camera**: zon + luchtgradiënt + vlaklampen, scherptediepte per plaat, bewegingsonscherpte bij de auto, AgX-kleurbeheer; gloed en vignet in `../boek/build.py`.

`proefplaat-daan-joep.jpg` is de eerste proefrender van Daan en Joep samen.

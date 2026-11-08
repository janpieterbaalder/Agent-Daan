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

## Aanpak in Blender (Cycles)

- **Huid:** Principled BSDF met subsurface en een lichte bump. Blos via een vertex color of een texture.
- **Ogen:** aparte oogbol met iris-texture, glanzende cornea en catchlight.
- **Haar:** Hair Curves met clumping en roughness. Kuif als geleidecurves naar voren en omhoog, zijkanten als kort dons.
- **Joep:** eenvoudige subdivided vormen met korte, dichte fur (Hair Curves) en een sheen-shader. Borduursel als licht verhoogde geometrie.
- **Stof:** weefselstructuur via een noise- of wave-texture op bump, naden als randgeometrie.
- **Licht en camera:** zachte key light, rim light en HDRI-achtige omgeving. Scherptediepte, 4:3, 2400×1800.
- **Scènes:** de 14 bladzijden uit `../README.md`. Elke scène op een rond decor (de "stip"), zoals in de huidige versie.

"""Report lines that read like German.

``AGENTS.md`` requires English everywhere in the repository. Until work package
2 of milestone 0.5 it granted one exception, for test docstrings and test
comments. The exception is withdrawn: every audit of milestone 0.4 read the
tests, a test is the sharpest statement of what an obligation means, and half
of them could not be read by a reviewer who does not read German.

Withdrawing the rule and translating 1847 lines are two different sizes of
work. The rule was withdrawn first and the translation ran module by module,
with ``NOT_YET_TRANSLATED`` below holding what was left of it. The list is empty
since work package 2 finished, so the rule now covers every file the repository
has.

It stays here, empty, with the test that keeps it honest: a module that has
been translated and left in the list fails. That test is what forced the list
to empty itself, and it is what the list is for if another language ever gets
an exception.

Only comments and docstrings are read. Code is not prose, and reading it
produced false reports on identifiers such as ``items`` and ``xreplace``.
Text inside double backticks is dropped as well, because it quotes code.

How the word list came about, and what it is worth
--------------------------------------------------

The first version of this check was a list written from memory. It was
measured against twenty German lines that had survived a translation and that
the maintainer found by reading. It caught **none of the twenty**. The cause
was not the threshold that work package 1 had blamed. It was the list: words
as common as ``von``, ``eines``, ``nichts``, ``siehe`` and ``welche`` were
simply not in it, and a list written from memory has no way of knowing what it
omits.

The list below is not written. It is derived, and the derivation is the reason
to trust it further than the last one. Every word of every comment and
docstring of the modules still to be translated was collected. Every word that
also occurs in the English prose of this repository was removed. What remains
are words this project uses in German and never in English.

Measured after the derivation:

* recall on the twenty lines, which are not in the corpus because they were
  repaired before it was built: eighteen of twenty;
* false reports on the English prose of ``src/``, ``scripts/``, ``docs/`` and
  the modules already translated: none.

The two it does not catch are worth naming, because they are the shape of what
this check cannot do. ``Test.`` is a German noun that is spelled like an
English one. ``# zusammenfaellt.`` is a German word that happens not to occur
in the corpus the list was derived from. No word list finds the first, and the
second is the general case: a derived list knows the German that was there and
not the German that could be.

So this is a net with holes, and it is not the only control. The instrument
that found twenty-eight further German lines after this list was built is
``scripts/foreign_words.py``, which reports prose words that do not occur in
the English part of the repository. It is too noisy to be a gate -- 133 reports
on the translated modules, all of them English -- and it is exactly right as a
list to read once per module. That is how ``Randfaelle``, ``Determinismus``
and ``Komposition`` came to light.

Eighty-three words were removed from the derived list by hand because they are
also English: ``die``, ``hat``, ``war``, ``male``, ``post``, ``rot``, ``lock``,
``norm``, ``null`` and the like. Each would have been a false report waiting
for the sentence that uses it.

Four of them were found by the check itself rather than in advance: ``smoke``,
``dmp``, ``fired`` and ``speak``. All four have the same cause. The corpus the
list was derived from is the prose of the modules not yet translated, and parts
of that prose were already English, so English words entered the German list.
They surface one module at a time, as the sentences that use them come under
the check, and each is struck out here when it does.

That is a defect of the derivation and not of the idea. It is bounded: the
corpus shrinks to nothing as the work package finishes, and a word can be
struck only once.

This module is scanned like every other, and it was not always. It exempted
itself, on the reasoning that its word list is German by necessity and a check
reporting its own definition is unusable. That reasoning stopped applying once
the check began reading comments and docstrings only: the word list is an
assignment, so it is not prose and is invisible here, and the faulty examples
in the negative controls are arguments inside calls.

The exemption survived that change and did harm. It hid three German comment
lines in this module for the whole of work package 2, and they were found by
``scripts/foreign_words.py`` and not by any check. A file-wide exemption is a
blind spot even when the reason for it has gone, which is why there is none
now.
"""

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# ``AGENTS.md`` names ``docs/``, ``README.md`` and ``CHANGELOG.md`` in the rule
# and no gate read any of them until now. The rule covered the code and the
# configuration in practice, which is less than it says.
SCANNED = (
    "src/kellermap/*.py",
    "src/kellermap/bcw/*.py",
    "scripts/*.py",
    "tests/*.py",
    "docs/*.md",
    "README.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "pyproject.toml",
    "Makefile",
    ".gitignore",
    ".github/workflows/ci.yml",
)

# The translation runs module by module. What stands here is the remainder.
NOT_YET_TRANSLATED = frozenset({})

PROPER_NAMES = (
    "van den Essen",
    "de Bondt",
)
"""Names that are not prose, and that the word list would read as German.

``van den Essen`` carries ``den`` and ``Essen``, both ordinary German words,
and no threshold distinguishes a Dutch surname from a German sentence. Striking
either from the list would cost more than the name does.

The list is deliberately short and holds names, never phrases. A name that
needs to be here has to be a name: if a technical term ever wants an exemption,
the term is the thing to rewrite.
"""

# Derived, not written. See the module docstring for how and for what it is
# worth.
GERMAN_WORDS = """
    abbildung abbildungen abbrechen abbruch aber abfragt abgelehnt
    abgeleitet abgeleitete abgelesen abgelesene abgelesenen abgelesener
    abgeschnitten abgeschrieben abhaengigkeit abhaengigkeiten
    abhaengigkeitsgraph abhaengigkeitsgraphen ablegen ablehnt ablehnung
    ableitung ablesbar ablesen abnahmebedingung abschneidung abschnitt
    abschrift absicht absichtlich absoluten abtrag abzug acht achtzehn
    aendern aendert aenderung aeussere alle allein allen alles allgemeinen
    als alten anbieten andere anderen anderes anders andersherum anfang
    anfassen anfasst anfuegt angeblich angelegt angemerkt angenommen
    angeschlagen anker ankommt anlegt anlegte anleitung annahmen
    annotationen anrichtete anschlaegt anschliessend ansetzt ansicht
    anspruch anstelle anweisung anwendet anwendungen arbeiten arbeitspaket
    arbeitspakete arbeitsverzeichnisses archiv archivs arithmetik attribut
    auch auditbefunden auf aufbau auffaellt auffiele auffing aufgefallen
    aufgefuellt aufgerufen aufgeschobenen aufgeschobener aufgeschrieben
    aufhaelt aufruf aufrufe aufrufer aufrufs aufschreibbar aufsetzt
    aufsteigend auftritt aufwand aufzaehlbar aufzaehler aufzaehlung
    aufzuloesen aus ausdruck ausdruckskonstruktor ausdruecke ausdruecken
    ausfuehrbar ausfuehrbare ausfuehren ausgabe ausgabepruefung ausgelesen
    ausgeschrieben ausgeschriebenem ausgibt auslassen ausliefert ausnahme
    auspacken aussage aussagelos ausschliesslich ausschliesst
    ausschlussliste aussen ausserhalb aussieht ausstellen auswahl ausweist
    auswertung automorphismen autoritaet azyklisch baeue bau baubar bauen
    baum baustein bausteine baut baute bauwerkzeug bedeutet bedingung
    befund befunden beginnt behaupten behauptet behauptete behauptung
    behauptungen behoben bei beide beiden beides beilaeufig beim beispiel
    beisst bekaeme bekamen bekannt bekannte bekannten bekommt belang beleg
    belegt benannt benannte benennt benutzt benutzte bereich bereiche
    bereichen bereits bericht beruehren beruht beschaedigte beschleunigung
    beschreiben beschreibt beschrieben bestaetigen besteht betrifft bevor
    beweises beweist bewiesen bewusst bezeichner bezeichneten beziehen
    bibliothek bietet bild bilder bildkoordinaten bindet bis bisher
    bisherigen bleiben bleibt blieb bloecke bloss brach brauchbar brauchen
    braucht brauchte bricht bruchkoerper bzw codefingerabdruck dabei
    dafuer dagegen daher dahinter damit danach daneben dann daran darauf
    daraus darf darin darstellung darstellungen darueber darum das dass
    dasselbe dastehen dasteht datei dateien dateiname daten davon davor
    dazu dazukommt dazwischen decke deckt dekorator dem demselben den
    denen denkbar denn denselben der deren derselbe derselben des deshalb
    desselben dessen determinante determinanten determinantenpruefung
    determinantenstrategie determinantenstrategien deutscher diagonale
    dient dies diese dieselbe dieselben diesem diesen dieser dieses
    diesmal dimensionale dimensionen dimensionsfolge dinaten dinge direkt
    divergent dokumentation dokumentationswidersprueche doppelung
    doppelungen dort dorthin drei dreieckig dreiecksfoermig dritte drucken
    druckt druckte duerfen durch durchgeht durchgereicht durchlaeuft
    durchlauf durchsuchter durfte ebene ebenfalls ebenso echte echten
    eigene eigenem eigenen eigenes eigens eigenschaft eigentliche ein
    eindeutigkeit eine eineinhalb einem einen einer eines einfache
    einfuehren einfuehrende einfuehrung einfuehrungsreihenfolge eingabe
    eingaben eingabepruefung eingefuehrt eingefuehrte eingefuehrten
    eingefuehrter einheitsmatrix einheitstests einmal eins einschraenkt
    eintrag einzeln einzelne einzelnen einzige einzigen einziger einziges
    elementar elementarautomorphismen elementare elementarer elemente elf
    ende endet endete endpunkt entfernen entfernt entfernte entgegen
    enthaelt entkraeftet entscheidbar entscheidet entsprechend entstanden
    entstehen entsteht entweder entwicklung entwurf entwurfsentscheidung
    erben erbt ereignisse erfasst erfinden erfolgreich erfolgsfall
    erfolgspfad erfuellen erfuellt erfundene ergaenzen ergaenzt ergaenzung
    ergeben ergebnis erhalten erhaltung erkannt erkennung erklaert erlaubt
    erlaubte ermittelbare erreichbar erreichen erreicht erreichte ersetzen
    ersetzt erspart erst erste ersten erster ertrag erwaehnen erweitert
    erweiterte erweiterung erweiterungen erzeugen erzeuger erzeugt
    erzwingt erzwungen etwa etwas exakt existenz existierenden existiert
    exponenten extern externen externes faehrt faelle faellen faellt
    faende faengt faerbt faktor faktoren faktorisiert faktorisierung
    faktorplaetze falle fallen fallunterscheidung falsch falsche falschem
    falschen familie familien fand fasst fassung faustregel fehlenden
    fehler fehlermeldung fehlmeldung fehlschlaegt fehlschlag
    fehlschlagfaelle fehlschluss fehlt fehlte feld fenster fertig feste
    festen festgehalten festhaelt festschreibt fett fiel filtrationsgrad
    filtrierung filtrierungsgrad filtrierungsstufe finden findet fixierte
    fixierten fixierter flache folgen folgenden folgt fordert formel
    formeln frage fragen frei freispricht fremde fremden fremdes
    fremdsymbole frische frischem frischen frischepruefung frueh frueher
    fruehere frueherer fuehren fuehrende fuehrenden fuehrt fuellen fuenf
    fuenfte fuenfzehnter fuer fussnote gab gaebe galt ganz ganzen ganzer
    gar garantiert geaendert geaenderte gebaut gebaute gebauten geben
    geblieben gebracht gebraucht gecacht gedacht gedaechtnis
    gedankenstrich gedrucktem gefahren gefahrenen gefragt gefunden
    gefundene gefundenen gegen gegenbeispiel gegeneinander gegenkontrolle
    gegenkontrollen gegenprobe gegenteil gehalten gehoeren gehoert geht
    gekauft gekaufter geladen geladenen gelegt geliefert gelieferten
    geloescht geloest gemeldet gemeldete gemeldeten gemessen genannt genau
    genauso generatoren genuegt genug geordnetes gepasst gepflegt geprueft
    gepruefte geprueften gerade gerechnet gerechnete gerechnetes
    gerenderten gesamte geschlossen geschrieben gesehen gestalt gesucht
    gesuchten geteilt geteilte geteilten geteilter geteiltes getragen
    getragenen getrennte gewaehlt gewicht gewichte gewichteter
    gewoehnliche geworden gezeigt gibt gleich gleichdimensionale gleiche
    gleichem gleicher gleichgueltig gleichheit grade gradfolge greift
    grenze grenzfall groesse gruen gruende grund gruppenelemente gueltig
    gueltige gueltigen gueltiges guenstiger gut gutartig haben haelfte
    haelt haengen haenger haengt haengte haette haeufigsten halten handelt
    handgeschrieben handrechnung hatte hatten hebt heisst heraus
    herauskommt herausrechnet herausreichen hereinkommt hergeben hergibt
    herkunft hervorgeht hier hierher hiesigen hiess hiesse hilfe hilft
    hinaus hineingeschrieben hing hingen hingeschrieben hinschreiben
    hinter hinteren hinterlaesst homogen homogenitaet homomorphismus
    hundert identitaet identitaeten ignorieren ignorierliste ihn ihnen ihr
    ihre ihrem ihren ihrer immer implementierung impliziert indem inhalt
    injektiv innere innerhalb inspektion instanz intern interne internen
    invarianten invertierbar invertierbarkeit inzwischen irgendein
    irgendeinen irgendetwas isolierte isolierung ist jacobi jacobiblock
    jede jedem jeden jeder jedes jemand jetzt juli kam kamen kandidat
    kandidaten kandidatenaufzaehler kann kaputten karte karten kehrwert
    kein keine keinem keinen keiner keines kennt kette ketten klasse
    klausel klauseln kleinen kleiner kleineren klon klonen klons kodierung
    koeffizient koeffizienten koeffizientenbereich koeffizientenbereichs
    koeffizientendomain koennen koennte kollision kollisionsbild
    kollisionsbilder kollisionspunkt kollisionspunkte kommen kommentar
    kommentare kommt komplement komponente komponenten komponieren
    komponiert komposition konsistenz konstant konstante konstanten
    konstruktion konstruktor konstruktorinvariante kontext kontrolle
    kontrollieren konversion koordinate koordinaten koordinatenaenderung
    kopfblock kopie kopien kopieren korollar korrektur korrigiert kosten
    kostet kreuzprobe kubisch kubische kubischer kuerzer laedt laenge
    laengere laesst laeufe laeuft lagen landen landet lang lange langsamen
    lassen lauf laufen lautet lautlos leben leck leere leerem leerer
    leerraum leerzeichen leerzeile legen legt lehnte leisten leistet
    lesbar letzte letzten letzteres lief liefe liefern liefert lieferte
    liegen liegt liess liessen liest lineare linearen linearer
    linearisierung linearisierungsteil linearteil linearterm linearterme
    linkskomposition liste listen listet literatur lizenz lockerung loest
    lokalisiert lokalisierung luecke machen macht mal mapsto marke
    markiert maschinengeprueften maschinenlesbaren mathematischer matrizen
    mehr mehreren meilenstein meilensteins meint meinte meldet meldete
    meldeten meldung menge merkt messung methode methoden millisekunden
    mindestens mitbenutzen miteinander mitgenommen mitliest mitsollte
    mitteln mitten mittraegt mitzupflegen modul monome monomkodierung
    monomordnung muessen muesste muss musste muster mutationen
    mutationsprobe nach nachdem nacheinander nachgerechnet nachgeschlagen
    nachgezogen nachher nachrechnen nachrechnet nachrechnung nachtraeglich
    nachweis nachweislich nachweist nachzuziehen naechtlichen naheliegende
    naht namen namens namenspolitik ndef negativkontrolle nennen nenner
    nennt neu neue neuen neuer neunzehn neunzehndimensionale
    neunzehndimensionalen nicht nichtinjektivitaet nichts nie niemand
    nilpotenz nimmt nirgends noch noetig normalisiert normalisierte
    normalisierung normalisierungsschritt normativen notierte notiz
    nullbasiert nullen nullkomponenten nummer nummerierung nur oben
    oberste objekt objekte obwohl oder oeffentliche oeffentlichen oefter
    ohne ohnehin optimierung ordnung ort paarweise packen paket
    paketierungsfehler parametrisieren passt permutiert pfad plaetze
    plaetzen platz platzhalter platzkoordinaten polynom polynome
    polynomgleichheit polynomidentitaet positionen positivliste praedikat
    preis proben produkt produkte projekt projekts projektstand protokoll
    provenienz pruefbar pruefen pruefpfad prueft pruefte pruefung
    pruefungen punkt punkte punkten punktes quadrat quellarchiv
    quelldateien quelle rationale rationalen rationaler raum rechnen
    rechnet rechnete rechnung reduktion reduktionsziel referenz
    referenzpfad referenzreduktion regel regressionskandidat
    regressionstest reicht reihe reihenfolge reinem rekonstruieren
    rekonstruiert rekonstruktion rekursiv relativ reparierte repositorys
    reproduzieren restterme rettet richtig richtung richtungen ringe rohen
    rolle rueckgabewert rueckgaengig rueckwaerts rueckwaertsgehen
    rueckwaertssuche rueckweg ruft ruhe ruht rumpf rumpfes runde runden
    sache saehe saemtlich sagen sagt sagte sah sammlung satzende satzes
    scheinbar scheitern scheitert scheiterte schickt schlaegt schleife
    schliessen schnelle schon schraegstrich schreiben schreibt
    schreibweise schreibweisen schritt schritte schritten schrittes
    schrittfamilie schrittfolge schritts schrittweise schwaechere
    schwaecheren schwerpunkt sechs sechzehn sehen seine seinem seinen
    seiner seit seite seitenangaben seither sekunde sekunden
    sekundenbruchteile selben selbst selbstpruefung selbstveroeffentlichte
    senkt sequentiell setzbar setzen setzt sich sicher sichtbar sie sieben
    siebenundfuenfzig siebzehn siebzehndimensionalen siehe sieht
    signalwort signatur simultan sind skalar skaliert skripte sobald
    sofort solange solche solchen solcher solches soll sollte sondern
    sonst sorgt sortierung soweit spaeter spaetere spaeteren spaeterer
    spaeteres spalten spart spielt spitzenterm sprung spuerbar
    stabilisierende stabilisierten stabilisierung
    stabilisierungskoordinaten stabilisierungsvariablen staerkeren stammen
    statt stehen steht steigt stelle stellen stellte stichproben stieg
    stimmen stimmt stimmte strategie strategien strategiewahl streckung
    struktur stueck stuende stuetzt stufe substituiert subtrahiert suche
    suchen suchlauf suchtreiber summe symbole symbolischen syntaktische
    syntaxbaum tabelle taeuschen tatsache tatsaechlich tatsaechliche
    taucht tausch teile teilen teilmenge teilt terminiert testet
    testlaeufe testsammlung texte textfassung tiefe tippfehler topologisch
    topologische traeger traegerblock traegerindizes traegerkomponente
    traegerkomponenten traegerkoor traegerkoordinaten traegern
    traegervariable traegervariablen traegerwert traegt traf tragen
    translationsschritt transportiert trauen treffen treiber
    treiberskripte trifft trotzdem tupel tut typs ueber ueberall ueberein
    uebereinstimmen uebereinstimmt uebereinstimmten uebereinstimmung
    uebergang uebergeht ueberhaupt ueberleben ueberlebt ueberlieferten
    uebernahm uebernimmt uebernommen ueberschreitet ueberschrieben
    ueberschriebene ueberschrift uebersetzung uebrigen umbau umbrochen
    umgangen umgebung umgebungen umgebungsvariablen umgekehrt
    umgeschrieben umkehrbar umnummerieren umschreibung umsetzungen
    umsortieren umsortiert umsortierung unabhaengig unabhaengige
    unberuehrt unbrauchbar unerreichbar ungefunden ungeprueft ungewichtete
    ungleich ungueltige unipotenten unipotenter unmoeglich unten unter
    unterbringt unterklasse untermonoid unterscheiden unterscheidet
    unterscheidung unterschied unterschieden untersucht ununterscheidbar
    unveraenderlich unveraenderliche unveraenderlichkeit unveraendert
    unvollstaendig urbild urbilder ursache ursprung validiert validierung
    variablen variablenliste variablennamen variablenreihenfolge
    veraenderlich veraenderliche veraenderlichem veraenderliches
    veraendern veraendert veraenderte veralten veralteten veralteter
    verarbeiten verbindlich verbindliche verbindung verdoppelnden
    verdoppelt vereinbar verfaelschte verfahren vergeben vergessene
    vergibt vergleich vergleichen vergleicht verglichen verifikation
    verifiziert verlaesst verlangt verlangte verlauf verletzt verlieren
    verlinkt verlorene verlorengegangen vermeidet vermutung
    veroeffentlicht veroeffentlichte veroeffentlichten verpflichtung
    verpflichtungen verrechnen verschachtelte verschiebt verschiebung
    verschieden verschiedene verschiedenem verschiedenen verschiedener
    verschoben verschobene verschweigen verschwinden verschwindet
    verschwunden versehen versionsnummer versteckt versuch versuchten
    vertauscht vertragsversprechen vervollstaendigen verwarf verweis
    verzeichnis viel vier vierte viertelstunde vierzig virtuellen vollen
    voller vollstaendig vollstaendige vom von voneinander vor vorangeht
    voraus voraussetzung vorbedingung vordere vorgabe vorgekommen
    vorgelegt vorgelegtem vorgelegten vorgelegter vorgibt vorhandenen
    vorher vorhergesehen vorrat vorratswert vorrichtung vorwaerts
    vorwaertsaufzaehler vorwaertsraums vorzeichen vorzeichenkonvention
    waechst waehlt waehrend waere waeren wahl wahr wandelte wandern
    wandert waren warum weg wege weghebt weichen weil weise weiss weiter
    weiterer weiterhin welche wenig wenn wer werden werkzeug werte werten
    wertevorrat wertgleich wertlos wertobjekt werts wertsemantik wichen
    widerlegt wie wieder wiederbenutzten wiederholt wiederholte
    wiederverwendete wiese wir wird wirklich wirkungslos woanders woerter
    woertlich woher woran worauf worden wortgrenze wortgrenzen wuerde
    wuerden wurde wurden zaehlen zaehler zaehlt zaehlte zahl zahlen
    zeichen zeigen zeigt zeile zeilen zeitpunkt zerlegt zertifikat ziel
    zielabbildung ziele zielen zielkomponente zielkoordinate ziels zielt
    zielte zierde zierrat zitiert zitierte zitierung zuerst zufaellig
    zufaelliges zufallstreffer zugeschrieben zugleich zugriff zulaessig
    zulaessige zulaessiges zulaesst zulassen zuletzt zum zurueck
    zurueckbekommt zurueckgelegt zurueckgezogene zuruecklegen zusaetzlich
    zusaetzlichen zusaetzlicher zusage zusammen zusammenbau
    zusammenfassung zusammenfassungen zusammenfuehrte zusammengesetzten
    zusammenhang zustand zuwachs zuweisung zwar zweck zwei zweier
    zweierlei zweimal zweite zweiten zweiter zwilling zwingen zwingt
    zwischen zwischenabbildungen zwoelf
""".split()

GERMAN_WORD = re.compile(r"\b(" + "|".join(GERMAN_WORDS) + r")\b", re.IGNORECASE)

# Endings that are common in German and effectively absent from English. They
# catch a German word the derivation never saw.
GERMAN_ENDING = re.compile(r"\b\w{4,}(ung|ungen|keit|heit|schaft|lich|isch|ieren)\b")

QUOTED_CODE = re.compile(r"``[^`]*``")


def suspicious(line: str) -> bool:
    """Return whether ``line`` reads like German."""
    text = QUOTED_CODE.sub(" ", line)

    return bool(GERMAN_WORD.search(text) or GERMAN_ENDING.search(text))


def _span(node: ast.AST) -> range:
    """Return the line numbers a node covers."""
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", None) or start

    return range(start, end + 1)


def without_names(line: str) -> str:
    """Return the line with the proper names of ``PROPER_NAMES`` taken out."""
    for name in PROPER_NAMES:
        line = line.replace(name, " ")

    return line


def prose(path: Path) -> list[tuple[int, str]]:
    """Return the prose lines of ``path``, with their numbers.

    Prose is what a person reads: comments, docstrings, the message of an
    ``assert``, and the arguments of a ``raise``. Code is not prose, and
    reading it reported identifiers such as ``items`` and ``xreplace``.

    Assertion messages were left out until they had to be added. Four German
    lines survived work package 2 in them, two of which the word list would
    have caught. A message is read by whoever the check fails for, so it is
    text under the rule like any other, the way the ``@echo`` lines of the
    Makefile were in work package 1.

    Strings anywhere else are data. ``tests/test_scripts.py`` passes German
    source text to the fingerprint tool, and translating it would destroy the
    test.

    For anything that is not Python the whole file is prose. ``pyproject.toml``
    and the Makefile carry comments and nothing this check would misread.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if path.suffix != ".py":
        return list(enumerate(lines, 1))

    numbers: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            numbers.add(token.start[0])

    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, holders) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                numbers.update(_span(first))
        elif isinstance(node, ast.Assert) and node.msg is not None:
            numbers.update(_span(node.msg))
        elif isinstance(node, ast.Raise) and node.exc is not None:
            for argument in getattr(node.exc, "args", []):
                numbers.update(_span(argument))

    return [(number, lines[number - 1]) for number in sorted(numbers)]


def german_lines(path: Path) -> list[tuple[int, str]]:
    """Return the prose lines of ``path`` that read like German.

    The names come out here and not in ``prose``, which has two returns: one
    for Python and an earlier one that hands back a whole file. Patching the
    later return left every ``.md`` file unexempted, and ``docs/references.md``
    kept failing on a surname.

    What is reported is the line as written. The removal serves the test and
    not the reader, who needs to see the text that is actually there.
    """
    return [
        (number, line.strip())
        for number, line in prose(path)
        if suspicious(without_names(line))
    ]


def scanned() -> list[Path]:
    """Return every file the rule covers, in a stable order."""
    found: list[Path] = []
    for pattern in SCANNED:
        found += [
            path
            for path in ROOT.glob(pattern)
            if path.is_file() and "__pycache__" not in path.parts
        ]

    return sorted(set(found))


def translated() -> list[Path]:
    """Return the files the rule already covers in full."""
    return [path for path in scanned() if path.name not in NOT_YET_TRANSLATED]


# --------------------------------------------------------------------------
# The rule
# --------------------------------------------------------------------------


@pytest.mark.parametrize("path", translated(), ids=lambda path: path.name)
def test_no_line_reads_like_german(path: Path) -> None:
    """The rule of ``AGENTS.md``, for every file it already covers."""
    found = german_lines(path)
    shown = "\n".join(f"  {number}: {line[:80]}" for number, line in found[:5])

    assert not found, f"{path.name} has {len(found)} German lines:\n{shown}"


def test_every_file_is_either_covered_or_listed() -> None:
    """No file falls between the rule and the remainder.

    The list names modules, so a name that matches nothing is a leftover from a
    rename and would silently shrink what is checked.
    """
    names = {path.name for path in scanned()}

    assert NOT_YET_TRANSLATED <= names, sorted(NOT_YET_TRANSLATED - names)
    assert names == {path.name for path in translated()} | NOT_YET_TRANSLATED


def test_the_remainder_is_still_a_remainder() -> None:
    """A module that has been translated has to leave the list.

    Without this, the list is a permanent exemption that nobody notices. With
    it, the last module translated makes the list empty by force, and the
    exception ``AGENTS.md`` used to grant disappears with it.
    """
    finished = sorted(
        name for name in NOT_YET_TRANSLATED if not german_lines(ROOT / "tests" / name)
    )

    assert not finished, f"translated and still listed: {finished}"


def test_the_remainder_is_only_ever_tests() -> None:
    """Work package 1 covered everything outside ``tests/``.

    A file from ``src/`` or ``scripts/`` in the list would mean that repair
    came undone.
    """
    assert all(name.startswith("test_") for name in NOT_YET_TRANSLATED)


# --------------------------------------------------------------------------
# The negative controls
# --------------------------------------------------------------------------


def test_the_fragments_that_a_partial_replacement_leaves_are_caught() -> None:
    """The lines the maintainer found by reading, after this check said nothing.

    Every one of them is the tail of a block that was replaced only in part.
    The list this check used at the time caught none of the twenty.
    """
    for line in (
        "die, welche die Identitaet braucht.",
        "    nie -- extend findet also nichts zu beanstanden. Trotzdem liefern",
        "# Verschachtelte Koeffizientendomaenen",
        "    einzige Erlaubnis frueh aus.",
        "    gemeinsamen Monome streichen.",
        "    lag. Die gueltige Kette war die ganze Zeit im Raum.",
        "    Gegenbeispiel eines externen Audits.",
        "    beiden Faellen alles gesehen wurde.",
        "    stattdessen; siehe test_peeling.py.",
        "    siehe die Tests weiter unten.",
        "    erfolglose Suche nichts wirft.",
        "    hat es gebaut.",
        "    laufen.",
        "# Namen kommen von aussen",
    ):
        assert suspicious(line), line


def test_the_two_it_cannot_catch_are_named() -> None:
    """A check that hides its limits is worse than one that states them.

    ``Test.`` is a German noun spelled like an English one. ``zusammenfaellt``
    is German that the corpus behind the list never contained. Both were found
    by reading, and both are recorded here so that nobody takes a green run for
    a proof.
    """
    assert not suspicious("Test.")
    assert not suspicious("# zusammenfaellt.")

    # The same cause, on lines a second reading by the maintainer found: the
    # words stand in none of the modules the list was derived from.
    assert not suspicious("# Randfaelle")
    assert not suspicious("# RC-1: Determinismus")


def test_english_that_collides_with_german_is_left_alone() -> None:
    """The words removed from the derived list, in sentences that use them."""
    for line in (
        '"License :: OSI Approved :: MIT License",',
        "# The two gates below stand in AGENTS.md among the release checks.",
        "# The coefficient value does not change; this sequence is unique.",
        "# A man also has a hat, and there was a war.",
        "# The die is cast, the norm is null, and the post is locked.",
    ):
        assert not suspicious(line), line


def test_a_german_ending_is_caught_without_a_listed_word() -> None:
    """The second rule, on a word the derivation never saw."""
    assert suspicious("# Nachvollziehbarkeit.")
    assert not GERMAN_WORD.search("# Nachvollziehbarkeit.")


def test_code_is_not_prose() -> None:
    """Reading code produced reports on identifiers, so code is not read.

    ``items`` and ``xreplace`` were reported as German before this module read
    prose only. The message of the ``raise`` is prose and the statement around
    it is not, so the line carrying both is read and a plain assignment is not.
    """
    texts = [text for _, text in prose(ROOT / "src" / "kellermap" / "guards.py")]

    assert any("bound" in text for text in texts), "the prose is not read"
    assert not [text for text in texts if "wrong_type = {" in text]
    assert not [text for text in texts if "return bool(" in text]


def test_an_assertion_message_is_prose() -> None:
    """Four German lines survived work package 2 in messages like this one.

    A message is read by whoever the check fails for. Leaving it out meant the
    rule covered what a maintainer reads and not what a user reads.
    """
    texts = [text for _, text in prose(Path(__file__))]

    assert [text for text in texts if "German lines" in text]


def test_a_raise_argument_is_prose() -> None:
    """The same for the text an exception carries."""
    texts = [text for _, text in prose(ROOT / "src" / "kellermap" / "guards.py")]

    assert [text for text in texts if "must be polynomial maps" in text]


def test_a_string_argument_is_not_a_docstring() -> None:
    """Bracket depth, and the case that forced it.

    ``tests/test_scripts.py`` passes German source text as test data to the
    fingerprint tool. Written across two lines inside a call, the string is
    preceded by an ``NL`` token, and the first version of ``prose`` read every
    string in that position as a docstring. The data was reported as German
    prose, which it is not: it is an input, and translating it would destroy
    the test.
    """
    numbers = {number for number, _ in prose(ROOT / "tests" / "test_scripts.py")}
    lines = (ROOT / "tests" / "test_scripts.py").read_text(encoding="utf-8")

    for number, line in enumerate(lines.splitlines(), 1):
        if "Ein deutscher Docstring" in line:
            assert number not in numbers, line

    assert numbers, "the module has docstrings, so something is read"


def test_quoted_code_inside_prose_is_dropped() -> None:
    """A docstring quotes identifiers, and an identifier is not a word."""
    assert not suspicious("    The value of ``items`` is not German.")


def test_the_module_that_holds_the_list_is_scanned_too() -> None:
    """It exempted itself, and that hid German in it for a whole work package.

    The exemption was needed while the check read whole files. It is not needed
    now, and keeping it meant three German comment lines here went unreported
    from 0.4.0rc9 until the end of work package 2.
    """
    assert Path(__file__) in scanned()


def test_a_name_is_exempt_only_inside_the_name() -> None:
    """Otherwise the exemption is a hole and not a correction.

    ``den`` and ``Essen`` are ordinary German words and stay markers. What is
    exempt is the string ``van den Essen``, which is a surname, and it is taken
    out by exact match and not word by word.
    """
    assert not suspicious(without_names("the de Bondt-van den Essen gradient form"))
    assert suspicious(without_names("Wir haben den Fehler in der Kette gefunden"))
    assert suspicious(without_names("van den Essen hat den Satz dort bewiesen"))


def test_the_exemption_reaches_files_that_are_not_python() -> None:
    """Where the first patch for it did not.

    ``prose`` has two returns, one for Python and an earlier one that hands
    back a whole file. Removing the names at the later return left every
    markdown file unexempted, and ``docs/references.md`` went on failing on a
    surname. The removal happens in ``german_lines`` now, once, after both.
    """
    written = ROOT / "docs" / "references.md"

    assert written.suffix != ".py"
    assert prose(written)[0][1] == written.read_text(encoding="utf-8").splitlines()[0]
    assert not german_lines(written)


def test_the_word_list_is_not_prose() -> None:
    """Which is why the module can be scanned without reporting its own list.

    ``GERMAN_WORDS`` is an assignment and not a docstring, so ``prose`` does
    not read it. If that changed, every line of the list would be reported and
    the gate would be unusable.
    """
    numbers = {number for number, _ in prose(Path(__file__))}
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    listed = [
        number
        for number, line in enumerate(lines, 1)
        if line.startswith("    abbildung") or line.startswith("    zwischen")
    ]

    assert listed, "the word list has moved; this test needs its new anchor"
    assert not [number for number in listed if number in numbers]

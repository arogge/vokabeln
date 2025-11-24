#!/usr/bin/env python3.12

from subprocess import run
from xml.sax.saxutils import escape as xml_escape
from os import unlink

class Card:
    def __init__(self, cat):
        self.category = cat[:]
        self.eng = None
        self.deu = None
        self.example = None

    def add_data(self, data):
        if not self.eng:
            self.eng = data
        elif not self.deu:
            self.deu = data
        elif not self.example:
            self.example = data
        else:
            raise ValueError("Too many data sections!")

    def has_data(self):
        return self.eng is not None

def add_card(d, c):
    if c.has_data():
        d.append(c)

deck = []
category = ["", ""]
linebuffer = []
with open("Englisch.txt", "r", encoding="utf-8") as fp:

    card = Card(category)
    for raw_line in fp.readlines():
        line = raw_line.strip()
        if line.startswith("# "):
            card.add_data("\n".join(linebuffer))
            linebuffer = []
            add_card(deck, card)
            category[0] = line[2:]
            card = Card(category)
        elif line.startswith("## "):
            card.add_data("\n".join(linebuffer))
            linebuffer = []
            add_card(deck, card)
            category[1] = line[3:]
            card = Card(category)

        elif line == "==":
            card.add_data("\n".join(linebuffer))
            linebuffer = []
            add_card(deck, card)
            card = Card(category)
        elif line == "--":
            card.add_data("\n".join(linebuffer))
            linebuffer = []
        else:
            linebuffer.append(line)

def slicer(lst, length):
    if len(lst) < length:
        return lst
    for n in range(0, len(lst), length):
        yield lst[n:n+length]
    return lst[n:]

with open('Karten-Front.svg', 'r', encoding="utf-8") as file:
    front_svg_tmpl = file.read()
with open('Karten-Back.svg', 'r', encoding="utf-8") as file:
    back_svg_tmpl = file.read()

svgs = []
pdfs = []
for sheet, cards in enumerate(slicer(deck, 9)):
    replacements = {}
    for i, card in enumerate(cards):
        replacements[f"Category{i+1}"] = "".join(card.category)
        replacements[f"FrontTop{i+1}"] = card.deu
        replacements[f"FrontBottom{i+1}"] = ""
        replacements[f"BackTop{i+1}"] = card.eng
        replacements[f"BackBottom{i+1}"] = card.example
    front_svg = front_svg_tmpl
    back_svg = back_svg_tmpl

    for key,val in replacements.items():
        if not val:
            val = ""
        front_svg = front_svg.replace(f"@{key}@", xml_escape(val))
        back_svg = back_svg.replace(f"@{key}@", xml_escape(val))

    fname = f"Sheet{sheet:02d}"
    with open(f"{fname}-front.svg", "w+", encoding="utf-8") as file:
        file.write(front_svg)
    svgs.append(f"{fname}-front.svg")
    run(("inkscape", f"--export-filename={fname}-front.pdf", "--export-type=pdf", f"{fname}-front.svg"), check=True)
    pdfs.append(f"{fname}-front.pdf")
    with open(f"Sheet{sheet:02d}-back.svg", "w+", encoding="utf-8") as file:
        file.write(back_svg)
    svgs.append(f"{fname}-back.svg")
    run(("inkscape", f"--export-filename={fname}-back.pdf", "--export-type=pdf", f"{fname}-back.svg"), check=True)
    pdfs.append(f"{fname}-back.pdf")

cmdline = ["pdfjoin", "-o", "Sheets.pdf"]
cmdline.extend(pdfs)
run(cmdline, check=True)

for pdf in pdfs:
    unlink(pdf)
for svg in svgs:
    unlink(svg)

exit(5)

for card in deck[:9]:
    print("-----")
    print(" -- ".join(card.category))
    print(card.eng)
    print(card.deu)

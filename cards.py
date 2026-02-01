#!/usr/bin/env python3.12

"""Simple script to generate learning cards."""

from subprocess import run
from xml.sax.saxutils import escape as xml_escape
from os import unlink
from sys import argv


class Card:
    """A learning card's content."""
    def __init__(self, cat):
        self.category = cat[:]
        self.eng = None
        self.deu = None
        self.example = None

    def add_data(self, data):
        """Incrementally add data to the card."""
        if len(data) == 0:
            return
        if not self.eng:
            self.eng = data
        elif not self.deu:
            self.deu = data
        elif not self.example:
            self.example = data
        else:
            raise ValueError("Too many data sections!")

    def has_data(self):
        """Was any data added yet?"""
        return self.eng is not None


def add_card(d, c):
    """Helper to add data to an existing card"""
    if c.has_data():
        d.append(c)


def slicer(lst, length):
    """Generator to slice a list of cards into even chunks."""
    if len(lst) < length:
        return lst
    for n in range(0, len(lst), length):
        yield lst[n : n + length]
    return lst[n:]

def file_to_deck(filename):
    """Load a text-file and turn it into a deck of cards."""
    deck = []
    category = ["", ""]
    linebuffer = []
    with open(filename, "r", encoding="utf-8") as fp:
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
    return deck

def xml_to_docs(svg_xml, basename):
    """Create SVG and PDF from SVG XML structure."""
    with open(f"{basename}.svg", "w+", encoding="utf-8") as file:
        file.write(svg_xml)
    run(
        (
            "inkscape",
            f"--export-filename={basename}.pdf",
            "--export-type=pdf",
            f"{basename}.svg",
        ),
        check=True,
    )
    return f"{basename}.svg", f"{basename}.pdf"

def join_pdfs(input_files, output_file):
    """Merge multiple PDFs into one."""
    cmdline = ["pdfjoin", "--landscape", "-o", output_file]
    cmdline.extend(input_files)
    run(cmdline, check=True)


def main():
    """The main program."""

    assert argv[2] # fail early

    with open("Karten-Front.svg", "r", encoding="utf-8") as file:
        front_svg_tmpl = file.read()
    with open("Karten-Back.svg", "r", encoding="utf-8") as file:
        back_svg_tmpl = file.read()

    basenames = []
    for sheet, cards in enumerate(slicer(file_to_deck(argv[1]), 9)):
        replacements = {}
        for i, card in enumerate(cards):
            replacements[f"Category{i+1}l"] = card.category[0]
            replacements[f"Category{i+1}r"] = card.category[1]
            replacements[f"FrontTop{i+1}"] = card.deu
            replacements[f"FrontBottom{i+1}"] = ""
            replacements[f"BackTop{i+1}"] = card.eng
            replacements[f"BackBottom{i+1}"] = card.example
        front_svg = front_svg_tmpl
        back_svg = back_svg_tmpl

        for key, val in replacements.items():
            if not val:
                val = ""
            front_svg = front_svg.replace(f"@{key}@", xml_escape(val))
            back_svg = back_svg.replace(f"@{key}@", xml_escape(val))

        basename = f"Sheet{sheet:02d}-front"
        xml_to_docs(front_svg, basename)
        basenames.append(basename)

        basename = f"Sheet{sheet:02d}-back"
        xml_to_docs(back_svg, basename)
        basenames.append(basename)

    join_pdfs([f"{x}.pdf" for x in basenames], argv[2])

    for f in basenames:
        unlink(f"{f}.svg")
        unlink(f"{f}.pdf")

if __name__ == '__main__':
    main()

# SPDX-FileCopyrightText: 2023 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Fetch address books of Bern, 1861-1945, from www.e-rara.ch.


import csv
import requests
import os
import xml.etree.ElementTree as etree


def find_volumes():
    result = [
        ('1861', 1395835),
        ('1862', 3009035),
        ('1866', 1756728),
        ('1867-1868', 3009301),
        ('1868-1869', 1757043),
        ('1870', 3009651),
        ('1871', 3010016),
        ('1873', 3010408),
        ('1875', 3010824),
        ('1877', 3011278),
        ('1879', 3011774),
        ('1881', 3012292),
        ('1883-1884', 1396077),
        ('1886-1887', 3012704),
        ('1888-1889', 3013134),
        ('1891-1892', 3013642),
        ('1893-1894', 3014156),
        ('1893-1894/Supplement', 1396417),
        ('1895-1896', 3014735),
        ('1896-1897/Supplement', 3015341),
        ('1897-1898', 3015635),
        ('1899', 3016272),
    ]
    with open('Adressbuecher_Jahrgaenge_Links.csv') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(3)  # skip initial U+FFEF
        for row in csv.DictReader(csvfile, dialect=dialect):
            year = row['Jahrgang']
            volume = int(row['Jahrgangsband ID'])
            result.append((year, volume))
    return result


def fetch_volume_mets(volume):
    filepath = f"cache/mets-{volume}.xml"
    if not os.path.exists(filepath):
        req = requests.get(
            "https://www.e-rara.ch/oai?verb=GetRecord&metadataPrefix=mets" +
            f"&identifier={volume}")
        with open(filepath, 'wb') as f:
            f.write(req.content)
    with open(filepath, 'rb') as f:
        return f.read()


def fetch_page_xml(page):
    filepath = f"cache/fulltext-{page}.xml"
    if not os.path.exists(filepath):
        print(page)
        req = requests.get(f'https://www.e-rara.ch/bes_1/download/fulltext/alto3/{page}')
        with open(filepath, 'w') as f:
            f.write(req.text)
    with open(filepath, 'r') as f:
        return f.read()


def fetch_page_plaintext(page):
    filepath = f"cache/fulltext-{page}.txt"
    if not os.path.exists(filepath):
        req = requests.get(f'https://www.e-rara.ch/bes_1/download/fulltext/plain/{page}')
        with open(filepath, 'w') as f:
            f.write(req.text)
    with open(filepath, 'r') as f:
        return f.read()


def fetch_pages(year, volume):
    et = etree.fromstring(fetch_volume_mets(volume))
    chapters = set()
    for s in et.iter('{http://www.loc.gov/METS/}structMap'):
        if s.attrib['TYPE'] == 'LOGICAL':
            for c in s.iter('{http://www.loc.gov/METS/}div'):
                label = c.attrib.get('LABEL', '')
                if 'Einwohner' in label and 'Berufsarten' not in label:
                    chapters.add(c.attrib['ID'])
                    chapter = c.attrib['ID'].removeprefix('log')
    pages = []
    for link in et.iter('{http://www.loc.gov/METS/}smLink'):
        chapter  = link.attrib['{http://www.w3.org/1999/xlink}from']
        if chapter in chapters:
            page = link.attrib['{http://www.w3.org/1999/xlink}to']
            page = int(page.removeprefix('phys'))
            pages.append(page)
            fetch_page_xml(page)
            fetch_page_plaintext(page)
    return pages


if __name__ == '__main__':
    if not os.path.exists("cache"):
        os.mkdir("cache")
    for year, volume in find_volumes():
        pages = fetch_pages(year, volume)
        print(year, len(pages), pages[:5])



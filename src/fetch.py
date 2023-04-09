# SPDX-FileCopyrightText: 2023 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Fetch address books of Bern, 1861-1945, from www.e-rara.ch.

from collections import namedtuple
import csv
import requests
import os
import xml.etree.ElementTree as etree


Chapter = namedtuple('Chapter', ['id', 'title', 'date', 'year', 'volume', 'pages'])
Page = namedtuple('Page', ['id', 'label'])


def fetch_all():
    if not os.path.exists("cache"):
        os.mkdir("cache")
    for chapter in fetch_chapters():
        first_page = chapter.pages[0]
        for page in chapter.pages:
            if page == first_page or page.label != None:
                fetch_page_xml(page.id)
                fetch_page_plaintext(page.id)
        print(chapter.date, len(chapter.pages), chapter.pages[:3])


def fetch_chapters():
    chapters = []
    path = os.path.join(os.path.dirname(__file__), 'chapters.csv')
    with open(path) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        for row in csv.DictReader(csvfile, dialect=dialect):
            chapter_id = int(row['ChapterID'])
            volume_id = int(row['VolumeID'])
            date = row['Date']
            if len(date) == 4:
                date = '%04d-12-15' % (int(date) - 1)
            pages=fetch_chapter_pages(volume_id, chapter_id)
            chapter = Chapter(id=chapter_id,
                              title=row['ChapterTitle'],
                              date=date,
                              year=row['Year'],
                              volume=volume_id,
                              pages=pages)
            chapters.append(chapter)
    return chapters


def fetch_chapter_pages(volume_id, chapter_id):
    et = etree.fromstring(fetch_volume_mets(volume_id))
    page_labels = {}
    for smap in et.iter('{http://www.loc.gov/METS/}structMap'):
        if smap.attrib['TYPE'] == 'PHYSICAL':
            for div in smap.iter('{http://www.loc.gov/METS/}div'):
                if div.attrib['TYPE'] == 'page':
                    page_id = int(div.attrib['ID'].removeprefix('phys'))
                    if label := div.attrib.get('ORDERLABEL'):
                        page_labels[page_id] = label
    pages = []
    for link in et.iter('{http://www.loc.gov/METS/}smLink'):
        link_from  = link.attrib['{http://www.w3.org/1999/xlink}from']
        link_from_id = int(link_from.removeprefix("log"))
        if link_from_id == chapter_id:
            link_to = link.attrib['{http://www.w3.org/1999/xlink}to']
            page_id = int(link_to.removeprefix('phys'))
            page = Page(id=page_id, label=page_labels.get(page_id))

            # The first page in a chapter typically has no label (page number):
            # - https://www.e-rara.ch/bes_1/periodical/pageview/26021757
            is_first_page = (len(pages) == 0)

            # Other pages always have a label, unless they’re an advertisment:
            # - https://www.e-rara.ch/bes_1/periodical/pageview/25875701
            # - https://www.e-rara.ch/bes_1/periodical/pageview/25877342
            is_advertisment_page = (page.label == None)

            if is_first_page or not is_advertisment_page:
                pages.append(page)

    # If the first page in the chapter has no number, synthesize it: '[123]'.
    if not pages[0].label:
        pages[0] = Page(id=pages[0].id,
                        label = f'[%d]' % (int(pages[1].label) - 1))
    return pages


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


def fetch_page_xml(page_id):
    filepath = f"cache/fulltext-{page_id}.xml"
    if not os.path.exists(filepath):
        req = requests.get(f'https://www.e-rara.ch/bes_1/download/fulltext/alto3/{page_id}')
        with open(filepath+'.tmp', 'w') as f:
            f.write(req.text)
        os.rename(filepath+'.tmp', filepath)  # atomic
    with open(filepath, 'r') as f:
        return f.read()


def fetch_page_plaintext(page_id):
    filepath = f"cache/fulltext-{page_id}.txt"
    if not os.path.exists(filepath):
        req = requests.get(f'https://www.e-rara.ch/bes_1/download/fulltext/plain/{page_id}')
        with open(filepath, 'w') as f:
            f.write(req.text)
    with open(filepath, 'r') as f:
        return f.read()


if __name__ == '__main__':
    fetch_all()

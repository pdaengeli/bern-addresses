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


ALTO_SPACE = '{http://www.loc.gov/standards/alto/ns-v3#}SP'
ALTO_STRING = '{http://www.loc.gov/standards/alto/ns-v3#}String'
ALTO_TEXTLINE = '{http://www.loc.gov/standards/alto/ns-v3#}TextLine'


class Extractor(object):
    def __init__(self, cachedir):
        self.cachedir = cachedir
        self.ads_denylist = self.read_ads_denylist()

    def run(self):
        if not os.path.exists(self.cachedir):
            os.mkdir(self.cachedir)
        for chapter in self.find_chapters():
            for page in chapter.pages:
                self.process_page(chapter, page)
            break

    def process_page(self, chapter, page):
        et = etree.fromstring(self.fetch_page_xml(page.id))
        print(f'# Date: {chapter.date} Page: {page.id}/{page.label}')
        for line in et.findall(f'.//{ALTO_TEXTLINE}'):
            tokens = []
            for e in line:
                if e.tag == ALTO_STRING:
                    tokens.append(e.attrib['CONTENT'])
                elif e.tag == ALTO_SPACE:
                    tokens.append(' ')
            print(''.join(tokens))

    def find_chapters(self):
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
                pages = self.find_chapter_pages(volume_id, chapter_id)
                chapter = Chapter(id=chapter_id,
                                  title=row['ChapterTitle'],
                                  date=date,
                                  year=row['Year'],
                                  volume=volume_id,
                                  pages=pages)
                chapters.append(chapter)
        return chapters

    def find_chapter_pages(self, volume_id, chapter_id):
        et = etree.fromstring(self.fetch_volume_mets(volume_id))
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
                if page_id not in self.ads_denylist:
                    page = Page(id=page_id, label=page_labels.get(page_id))
                    pages.append(page)

        # If the first page has no number, synthesize it: '[123]'.
        if not pages[0].label:
            pages[0] = Page(id=pages[0].id,
                            label = f'[%d]' % (int(pages[1].label) - 1))

        return pages

    def fetch_volume_mets(self, volume):
        filepath = f"{self.cachedir}/mets-{volume}.xml"
        if not os.path.exists(filepath):
            req = requests.get(
                "https://www.e-rara.ch/oai?verb=GetRecord&metadataPrefix=mets" +
                f"&identifier={volume}")
            with open(filepath, 'wb') as f:
                f.write(req.content)
        with open(filepath, 'rb') as f:
            return f.read()

    def fetch_page_xml(self, page_id):
        filepath = f"{self.cachedir}/fulltext-{page_id}.xml"
        if not os.path.exists(filepath):
            req = requests.get(f'https://www.e-rara.ch/bes_1/download/fulltext/alto3/{page_id}')
            with open(filepath+'.tmp', 'w') as f:
                f.write(req.text)
            os.rename(filepath+'.tmp', filepath)  # atomic
        with open(filepath, 'r') as f:
            return f.read()

    def read_ads_denylist(self):
        result = set()
        for line in open(os.path.join(os.path.dirname(__file__), 'ads.txt')):
            line = line.strip()
            if line and line[0] != '#':
                result.add(int(line))
        return result


if __name__ == '__main__':
    ex = Extractor(cachedir="cache")
    ex.run()

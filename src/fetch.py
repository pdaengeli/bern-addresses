# SPDX-FileCopyrightText: 2023 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Fetch address books of Bern, 1861-1945, from www.e-rara.ch.

from collections import namedtuple
import csv
import requests
import os
import re
import sqlite3
import xml.etree.ElementTree as etree
import urllib


Chapter = namedtuple('Chapter', ['id', 'title', 'date', 'year', 'volume', 'pages'])
Page = namedtuple('Page', ['id', 'label'])


ALTO_SPACE = '{http://www.loc.gov/standards/alto/ns-v3#}SP'
ALTO_STRING = '{http://www.loc.gov/standards/alto/ns-v3#}String'
ALTO_TEXTLINE = '{http://www.loc.gov/standards/alto/ns-v3#}TextLine'


class Extractor(object):
    def __init__(self, cachedir):
        self.cachedir = cachedir
        self.ads_denylist = self.read_ads_denylist()
        self.families = self.read_families()

    def run(self):
        if not os.path.exists(self.cachedir):
            os.mkdir(self.cachedir)
        self.process_proofread()
        for chapter in self.find_chapters():
            for page in chapter.pages:
                self.process_page(chapter, page)
            break

    def process_page(self, chapter, page):
        et = etree.fromstring(self.fetch_page_xml(page.id))
        #print(f'# Date: {chapter.date} Page: {page.id}/{page.label}')
        for line in et.findall(f'.//{ALTO_TEXTLINE}'):
            tokens = []
            for e in line:
                if e.tag == ALTO_STRING:
                    tokens.append(e.attrib['CONTENT'])
                elif e.tag == ALTO_SPACE:
                    tokens.append(' ')
            #print(''.join(tokens))

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

    def process_proofread(self):
        dirpath = os.path.join(os.path.dirname(__file__), '..', 'proofread')
        for date in sorted(os.listdir(dirpath)):
            path = os.path.join(dirpath, date)
            for line in open(path):
                if line[0] == '#':
                    pass
                elif line[0] == '—':
                    pass
                else:
                    name = self.get_family_name(line)
                    if name not in self.families:
                        print(name)

    def get_family_name(self, line):
        if line.startswith('v.'):
            name = 'von ' + line[2:].split()[0]
        elif line.startswith('de '):
            name = 'de ' + line[2:].split()[0]
        else:
            name = line.split()[0]
        return name.removesuffix(',')

    def read_ads_denylist(self):
        result = set()
        for line in open(os.path.join(os.path.dirname(__file__), 'ads.txt')):
            line = line.strip()
            if line and line[0] != '#':
                result.add(int(line))
        return result

    def read_families(self):
        result = {}
        filepath = os.path.join(os.path.dirname(__file__), 'families.txt')
        for line in open(filepath):
            line = line.strip()
            if line and line[0] != '#':
                name, wikidata_id = line.split(';')
                result[name] = wikidata_id
        return result


def make_request(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "BernAddressBookBot/1.0")
    req.add_header("From", "sascha@brawer.ch")
    return req


def fetch_wikidata_entity(qid):
    req = make_request(
        f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.ttl')
    req.add_header("Accept", "text/turtle")
    response = urllib.request.urlopen(req)
    return response.read().decode('utf-8')


def fetch_wikidata_family_names(cachedir):
    if not os.path.exists(cachedir):
        os.mkdir(cachedir)
    path = os.path.join(cachedir, "wikidata_family_names.csv")
    if os.path.exists(path):
        return
    db = sqlite3.connect(f"{cachedir}/wikidata_family_names.db")
    db.execute("CREATE TABLE IF NOT EXISTS Names(qid PRIMARY KEY NOT NULL, name)")
    db.execute("CREATE TABLE IF NOT EXISTS State(key PRIMARY KEY NOT NULL, val)")
    db.commit()
    family_name_classes = [
        'Q106319018',  # hyphenated surname
		'Q29042997',   # double surname
		'Q101352',     # family name
	]
    for k in family_name_classes:
        _fetch_wikidata_family_name_list(db, k)


def _fetch_wikidata_family_name_list(db, klass):
    state_key = f'page_{klass}'
    page = db.execute("SELECT val FROM State WHERE key=?", [state_key])
    page = page.fetchone()
    page = page[0] if page else None
    if page != 'DONE':
        page = int(page) if page else 0
        regexp = re.compile(r'wd:(Q\d+)\s+wdt:P31\s+wd:' + klass + r'\s*\.')
        while True:
            page = page + 1
            print(f"Query Wikidata for instances of {klass}, page {page}")
            req = make_request(
                "https://query.wikidata.org/bigdata/ldf?" +
                f"object=wd:{klass}&predicate=wdt:P31&page={page}")
            req.add_header("Accept", "text/turtle")
            with urllib.request.urlopen(req) as response:
                turtle = response.read().decode('utf-8')
            db.execute("REPLACE INTO State (key,val) VALUES (?, ?)",
                       [state_key, page])
            for qid in regexp.findall(turtle):
                db.execute("INSERT OR IGNORE INTO Names (qid, name) " +
                           "VALUES (?, NULL)", [qid])
            db.commit()
            if '<http://www.w3.org/ns/hydra/core#nextPage>' not in turtle:
                db.execute("REPLACE INTO State (key,val) " +
                           "VALUES (?, 'DONE')", [state_key])
                db.commit()
                break


if __name__ == '__main__':
    cachedir = "cache"
    fetch_wikidata_family_names(cachedir)
    #ex = Extractor(cachedir)
    #ex.run()

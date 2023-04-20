# SPDX-FileCopyrightText: 2023 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Process Bern address books (1861-1945), using data produced by fetch.py.

import csv
import os
import re


class Processor(object):
    def __init__(self, cachedir):
        self.families = self.read_families()
        self.max_family_name_wordcount = max(
            len(f.split()) for f in self.families.keys())

    def read_families(self):
        result = {}
        filepath = os.path.join(os.path.dirname(__file__), 'families.txt')
        for line in open(filepath):
            line = line.strip()
            if line and line[0] != '#':
                name, wikidata_id = line.split(';')
                result[name.lower()] = (name, wikidata_id)
        return result

    def process_proofread(self):
        dirpath = os.path.join(os.path.dirname(__file__), '..', 'proofread')
        page_re = re.compile(
            r'^# Date: (\d{4}-\d\d-\d\d) Page: (\d+)/([\[\]\d]+)$')
        for filename in sorted(os.listdir(dirpath)):
            path = os.path.join(dirpath, filename)
            publication_date, page_id, page_label = None, None, None
            line_num = 0
            family = None
            for line in open(path):
                line_num += 1
                line = line.strip()
                if len(line) == 0:
                    continue
                if line[0] == '#':
                    if m := page_re.match(line):
                        publication_date, page_id, page_label = m.groups()
                        family = None
                        continue
                    else:
                        raise ValueError(
                            f'{path}:{line_num}: Unknown # directive')
                if line[0] in ('—', '–', '-'):
                    rest = line[1:].strip()
                else:
                    family, rest = self.split_family_name(line)

    def split_family_name(self, line):
        line = line.removeprefix(',')
        line = line.replace(' - ', '-')
        if line.startswith('v.'):
            line = 'von ' + line[3:].strip()
        words = line.split(',')[0].split()
        for n in reversed(range(self.max_family_name_wordcount)):
            name_key = ' '.join(words[:n+1]).lower()
            if name := self.families.get(name_key):
                return (name, ' '.join(words[n+1:]))
        self.report_unknown_family(line)
        return ((words[0], None), ' '.join(words[1:]))

    def report_unknown_family(self, line):
        print(line)

if __name__ == '__main__':
    p = Processor(cachedir='cache')
    p.process_proofread()

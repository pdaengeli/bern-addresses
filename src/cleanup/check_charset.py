# SPDX-FileCopyrightText: 2023 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# Check how many records contain unexpected characters.


import argparse

from collections import Counter
import os


ALLOWED_CHARS = set(
    ',.:;–—-&/()[]↯ 📞«»’ 0123456789½'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    'abcdefghijklmnopqrstuvwxyzäöüéèß')


def check():
    dirpath = os.path.join(os.path.dirname(__file__), '..', '..', 'proofread')
    stats = {}
    for filename in sorted(os.listdir(dirpath)):
        if not filename.endswith('.txt'):
            continue
        date = filename.removesuffix('.txt')
        year = int(date[:4])
        # if not year < 1870: continue
        num_records = 0
        num_bad_records = 0
        with open(os.path.join(dirpath, filename)) as f:
            for line in f:
                start_char = line[0]
                if start_char == '#':
                    continue
                num_records += 1
                ok = line.endswith('\n')
                line = line[:-1]
                ok = ok and all(c in ALLOWED_CHARS for c in line)
                ok = ok and line.count('(') == line.count(')')
                ok = ok and line.count('[') == line.count(']')
                ok = ok and line.count('«') == line.count('»')
                if not ok:
                    num_bad_records += 1
                    # print(line)
        stats[date] = (num_bad_records, num_records)
    return stats


def print_stats(stats):
    print('Date          Bad Records     %')
    num_records, num_bad_records = 0, 0
    for date, (bad, total) in sorted(stats.items()):
        bad_percent = float(bad) / total * 100.0
        print('%s %6d %7d %5.1f' % (date, bad, total, bad_percent))
        num_bad_records += bad
        num_records += total
    bad_percent = float(num_bad_records) * 100.0 / num_records
    print('Total      %6d %7d %5.1f' % (num_bad_records, num_records, bad_percent))


if __name__ == '__main__':
    stats = check()
    print_stats(stats)



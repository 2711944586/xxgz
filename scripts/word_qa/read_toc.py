# -*- coding: utf-8 -*-
"""Read the TOC entries (title + baked page) from the DOCX XML."""
import re
import zipfile

from common import DOCX, write_json

with zipfile.ZipFile(DOCX) as z:
    x = z.read('word/document.xml').decode('utf8')

# Each TOC line is a paragraph containing: HYPERLINK anchor, title text, PAGEREF anchor, page digits
# Strategy: iterate paragraphs, keep those with a PAGEREF field.
paras = re.findall(r'<w:p[ >].*?</w:p>', x, re.S)
entries = []
for p in paras:
    if 'PAGEREF' not in p:
        continue
    anchor = re.search(r'PAGEREF\s+(_Toc\d+)', p)
    # visible text
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)
    joined = ''.join(texts)
    entries.append({
        'anchor': anchor.group(1) if anchor else None,
        'text': joined,
    })

print('TOC paragraphs with PAGEREF:', len(entries))
for e in entries[:6]:
    print('  ', e['anchor'], '|', e['text'][:70])
write_json("toc_entries.json", entries)

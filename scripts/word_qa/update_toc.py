# -*- coding: utf-8 -*-
"""Update ONLY the TOC page-number fields in the Word file.

The TOC is a set of HYPERLINK + PAGEREF fields. Calling Fields.Update() makes
Word recompute every PAGEREF from the document's own bookmarks, so the TOC page
numbers match the current body text. Nothing else in the document is edited.
"""
import json
import win32com.client as win32
import pythoncom

from common import DOCX, write_json

pythoncom.CoInitialize()
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
word.Options.UpdateFieldsAtPrint = False
try:
    doc = word.Documents.Open(str(DOCX))
    print('opened, pages =', doc.ComputeStatistics(2))

    before = {}
    # snapshot current TOC text so we can report what changed
    for f in doc.Fields:
        try:
            code = f.Code.Text.strip()
        except Exception:
            continue
        if code.upper().startswith('PAGEREF'):
            before[code] = f.Result.Text.strip()

    # Update only the fields inside the TOC story range (main text), not headers.
    updated = 0
    for f in doc.Fields:
        try:
            code = f.Code.Text.strip()
        except Exception:
            continue
        if code.upper().startswith(('PAGEREF', 'HYPERLINK')):
            f.Update()
            updated += 1
    print('fields updated:', updated)

    after = {}
    for f in doc.Fields:
        try:
            code = f.Code.Text.strip()
        except Exception:
            continue
        if code.upper().startswith('PAGEREF'):
            after[code] = f.Result.Text.strip()

    changes = [(k, before.get(k), after.get(k)) for k in after if before.get(k) != after.get(k)]
    print('changed page numbers:', len(changes))
    for k, b, a in changes:
        print('   %-28s %s -> %s' % (k, b, a))

    write_json('toc_changes.json', {'changes': changes, 'total': len(after)})

    doc.Save()
    doc.Close(False)
finally:
    word.Quit()
print('saved')

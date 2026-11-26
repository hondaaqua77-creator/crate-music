#!/usr/bin/env python3
"""Create / update Custom Product Pages (カスタムプロダクトページ) through the App Store Connect API.

usage: asc-cpp.py create   -> create (or reuse) the 3 pages below, set promo text, upload screenshots
       asc-cpp.py submit   -> submit every page version that is ready for review
Screenshots come from app/store/cpp/<key>/ (same file naming as app/store/screenshots).
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
import jwt

API = 'https://api.appstoreconnect.apple.com/v1'
TMP = os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
APP_ID = os.environ.get('ASC_APP_ID', '6830933661')
ROOT = Path(__file__).resolve().parents[1] / 'store' / 'cpp'
SETS = {'APP_IPHONE_67': 'phone_6.9inch_', 'APP_IPHONE_65': 'phone_6.5inch_', 'APP_IPAD_PRO_3GEN_129': 'pad_13inch_'}
PAGES = {
    'choir': ('合唱向け', '合唱の楽譜を、パートの声域に合わせて移調。写真を撮ってシャープ・フラットを押すだけで、音符も調号も書き直され、PDFで団員にLINEで送れます。無料。'),
    'singer': ('弾き語り向け', '原キーだと高くて歌えない曲も、写真1枚で歌いやすいキーに。シャープ・フラットのボタンで移調して、そのままPDFで保存。カラオケ・弾き語りの練習に。無料。'),
    'teacher': ('講師向け', '生徒の声に合わせて、レッスン用の楽譜をその場で移調。印刷した楽譜を撮るだけで、音符も調号も書き換え。PDFで生徒に送れます。無料。'),
}


def token():
    key = open(os.path.join(TMP, 'keys', f'AuthKey_{KEY_ID}.p8')).read()
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1200, 'aud': 'appstoreconnect-v1'},
                      key, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})


def call(method, path, body=None):
    url = path if path.startswith('http') else API + path
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f'::error::{method} {path} -> {e.code}: {e.read().decode(errors="replace")[:1200]}')
        raise


def put_chunk(op, data):
    req = urllib.request.Request(op['url'], method=op['method'], data=data,
                                 headers={h['name']: h['value'] for h in op['requestHeaders']})
    with urllib.request.urlopen(req) as r:
        r.read()


def upload_sets(loc_id, folder):
    sets = call('GET', f'/appCustomProductPageLocalizations/{loc_id}/appScreenshotSets')['data']
    by_type = {s['attributes']['screenshotDisplayType']: s for s in sets}
    for dtype, prefix in SETS.items():
        files = sorted(folder.glob(prefix + '*.png'))
        s = by_type.get(dtype) or call('POST', '/appScreenshotSets', {'data': {'type': 'appScreenshotSets',
            'attributes': {'screenshotDisplayType': dtype},
            'relationships': {'appCustomProductPageLocalization': {'data': {'type': 'appCustomProductPageLocalizations', 'id': loc_id}}}}})['data']
        for old in call('GET', f'/appScreenshotSets/{s["id"]}/appScreenshots?limit=20')['data']:
            call('DELETE', f'/appScreenshots/{old["id"]}')
        ids = []
        for f in files:
            data = f.read_bytes()
            shot = call('POST', '/appScreenshots', {'data': {'type': 'appScreenshots',
                'attributes': {'fileName': f.name, 'fileSize': len(data)},
                'relationships': {'appScreenshotSet': {'data': {'type': 'appScreenshotSets', 'id': s['id']}}}}})['data']
            for op in shot['attributes']['uploadOperations']:
                put_chunk(op, data[op['offset']:op['offset'] + op['length']])
            call('PATCH', f'/appScreenshots/{shot["id"]}', {'data': {'type': 'appScreenshots', 'id': shot['id'],
                'attributes': {'uploaded': True, 'sourceFileChecksum': hashlib.md5(data).hexdigest()}}})
            ids.append(shot['id'])
        call('PATCH', f'/appScreenshotSets/{s["id"]}/relationships/appScreenshots',
             {'data': [{'type': 'appScreenshots', 'id': i} for i in ids]})
        print('  uploaded', dtype, len(ids))


def existing_pages():
    return {p['attributes']['name']: p for p in call('GET', f'/apps/{APP_ID}/appCustomProductPages?limit=50')['data']}


def editable_version(page_id):
    for v in call('GET', f'/appCustomProductPages/{page_id}/appCustomProductPageVersions?limit=10')['data']:
        if v['attributes'].get('state') in ('PREPARE_FOR_SUBMISSION', 'REJECTED', None):
            return v
    return None


def create():
    have = existing_pages()
    for key, (name, promo) in PAGES.items():
        if name in have:
            page = have[name]
            print('reuse page', name, page['id'])
        else:
            page = call('POST', '/appCustomProductPages', {
                'data': {'type': 'appCustomProductPages', 'attributes': {'name': name},
                         'relationships': {'app': {'data': {'type': 'apps', 'id': APP_ID}},
                                           'appCustomProductPageVersions': {'data': [{'type': 'appCustomProductPageVersions', 'id': '${v1}'}]}}},
                'included': [
                    {'type': 'appCustomProductPageVersions', 'id': '${v1}',
                     'relationships': {'appCustomProductPageLocalizations': {'data': [{'type': 'appCustomProductPageLocalizations', 'id': '${l1}'}]}}},
                    {'type': 'appCustomProductPageLocalizations', 'id': '${l1}', 'attributes': {'locale': 'ja', 'promotionalText': promo}},
                ]})['data']
            print('created page', name, page['id'])
        ver = editable_version(page['id'])
        if not ver:
            vers = call('GET', f'/appCustomProductPages/{page["id"]}/appCustomProductPageVersions?limit=10')['data']
            states = [v['attributes'].get('state') for v in vers]
            print('  versions:', states)
            if any(st in ('WAITING_FOR_REVIEW', 'IN_REVIEW', 'READY_FOR_REVIEW') for st in states):
                print('  in review — skip'); continue
            # live page: open a new version to update (the live one keeps showing until the new one is approved)
            ver = call('POST', '/appCustomProductPageVersions', {'data': {'type': 'appCustomProductPageVersions',
                       'relationships': {'appCustomProductPage': {'data': {'type': 'appCustomProductPages', 'id': page['id']}}}}})['data']
            print('  new version', ver['id'], ver['attributes'].get('state'))
        locs = call('GET', f'/appCustomProductPageVersions/{ver["id"]}/appCustomProductPageLocalizations')['data']
        loc = next((l for l in locs if l['attributes']['locale'] == 'ja'), None)
        if not loc:
            loc = call('POST', '/appCustomProductPageLocalizations', {'data': {'type': 'appCustomProductPageLocalizations',
                  'attributes': {'locale': 'ja', 'promotionalText': promo},
                  'relationships': {'appCustomProductPageVersion': {'data': {'type': 'appCustomProductPageVersions', 'id': ver['id']}}}}})['data']
        else:
            call('PATCH', f'/appCustomProductPageLocalizations/{loc["id"]}', {'data': {'type': 'appCustomProductPageLocalizations',
                 'id': loc['id'], 'attributes': {'promotionalText': promo}}})
        upload_sets(loc['id'], ROOT / key)
        page = call('GET', f'/appCustomProductPages/{page["id"]}')['data']
        print(f'  page={name} url={page["attributes"].get("url")} version_state={ver["attributes"].get("state")}')


def submit():
    sub = call('POST', '/reviewSubmissions', {'data': {'type': 'reviewSubmissions', 'attributes': {'platform': 'IOS'},
               'relationships': {'app': {'data': {'type': 'apps', 'id': APP_ID}}}}})['data']
    n = 0
    for name, page in existing_pages().items():
        ver = editable_version(page['id'])
        if not ver:
            continue
        call('POST', '/reviewSubmissionItems', {'data': {'type': 'reviewSubmissionItems',
             'relationships': {'reviewSubmission': {'data': {'type': 'reviewSubmissions', 'id': sub['id']}},
                               'appCustomProductPageVersion': {'data': {'type': 'appCustomProductPageVersions', 'id': ver['id']}}}}})
        print('added', name); n += 1
    if not n:
        sys.exit('::error::nothing to submit')
    call('PATCH', f'/reviewSubmissions/{sub["id"]}', {'data': {'type': 'reviewSubmissions', 'id': sub['id'], 'attributes': {'submitted': True}}})
    print('submitted custom product pages', sub['id'])


if __name__ == '__main__':
    {'create': create, 'submit': submit}[sys.argv[1]]()

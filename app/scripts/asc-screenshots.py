#!/usr/bin/env python3
"""Upload App Store screenshots through the App Store Connect API.

Runs in CI (needs ASC_KEY_ID, ASC_ISSUER_ID, the key file at $RUNNER_TEMP/keys, and pyjwt).
For the app's current "prepare for submission" iOS version, it finds (or creates) the
Japanese localization, and for each display type below uploads the matching files from
app/store/screenshots in order. Existing screenshots of a type are replaced.
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
import jwt

API = 'https://api.appstoreconnect.apple.com/v1'
TMP = os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
APP_ID = os.environ.get('ASC_APP_ID', '6830933661')
LOCALE = 'ja'
ROOT = Path(__file__).resolve().parents[1] / 'store' / 'screenshots'
SETS = {  # display type -> filename prefix
    'APP_IPHONE_67': 'phone_6.9inch_',
    'APP_IPHONE_65': 'phone_6.5inch_',
    'APP_IPAD_PRO_3GEN_129': 'pad_13inch_',
}


def token():
    key = open(os.path.join(TMP, 'keys', f'AuthKey_{KEY_ID}.p8')).read()
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 1200, 'aud': 'appstoreconnect-v1'},
                      key, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})


def call(method, path, body=None):
    url = path if path.startswith('http') else API + path
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f'::error::{method} {path} -> {e.code}: {e.read().decode(errors="replace")[:800]}')
        raise


def put_chunk(op, data):
    req = urllib.request.Request(op['url'], method=op['method'], data=data,
                                 headers={h['name']: h['value'] for h in op['requestHeaders']})
    with urllib.request.urlopen(req) as r:
        r.read()


def main():
    vers = call('GET', f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=5')['data']
    ver = next((v for v in vers if v['attributes']['appStoreState'] in
                ('PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED')), None)
    if not ver:
        sys.exit('::error::no editable iOS version found')
    print('version', ver['attributes']['versionString'], ver['id'])
    locs = call('GET', f'/appStoreVersions/{ver["id"]}/appStoreVersionLocalizations')['data']
    loc = next((l for l in locs if l['attributes']['locale'] == LOCALE), None)
    if not loc:
        loc = call('POST', '/appStoreVersionLocalizations', {'data': {'type': 'appStoreVersionLocalizations',
               'attributes': {'locale': LOCALE},
               'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': ver['id']}}}}})['data']
    sets = call('GET', f'/appStoreVersionLocalizations/{loc["id"]}/appScreenshotSets')['data']
    by_type = {s['attributes']['screenshotDisplayType']: s for s in sets}

    for dtype, prefix in SETS.items():
        files = sorted(ROOT.glob(prefix + '*.png'))
        if not files:
            print('skip', dtype, '(no files)'); continue
        s = by_type.get(dtype)
        if not s:
            s = call('POST', '/appScreenshotSets', {'data': {'type': 'appScreenshotSets',
                   'attributes': {'screenshotDisplayType': dtype},
                   'relationships': {'appStoreVersionLocalization': {'data': {'type': 'appStoreVersionLocalizations', 'id': loc['id']}}}}})['data']
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
            print('uploaded', dtype, f.name)
        call('PATCH', f'/appScreenshotSets/{s["id"]}/relationships/appScreenshots',
             {'data': [{'type': 'appScreenshots', 'id': i} for i in ids]})
    print('screenshots done')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Upload the App Review screenshot for an in-app purchase through the App Store Connect API.

Runs in CI (needs ASC_KEY_ID, ASC_ISSUER_ID, the key file at $RUNNER_TEMP/keys, and pyjwt).
Replaces any existing review screenshot of the purchase with app/store/iap/noads_review.png.
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
import jwt

API = 'https://api.appstoreconnect.apple.com/v1'
TMP = os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
IAP_ID = os.environ.get('ASC_IAP_ID', '6830933954')  # 広告なし版
FILE = Path(__file__).resolve().parents[1] / 'store' / 'iap' / 'noads_review.png'


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
        if e.code == 404 and method == 'GET':
            return None
        print(f'::error::{method} {path} -> {e.code}: {e.read().decode(errors="replace")[:800]}')
        raise


def main():
    data = FILE.read_bytes()
    old = call('GET', f'/inAppPurchasesV2/{IAP_ID}/appStoreReviewScreenshot')
    if old and old.get('data'):
        call('DELETE', f'/inAppPurchaseAppStoreReviewScreenshots/{old["data"]["id"]}')
        print('removed old screenshot')
    shot = call('POST', '/inAppPurchaseAppStoreReviewScreenshots', {'data': {
        'type': 'inAppPurchaseAppStoreReviewScreenshots',
        'attributes': {'fileName': FILE.name, 'fileSize': len(data)},
        'relationships': {'inAppPurchaseV2': {'data': {'type': 'inAppPurchases', 'id': IAP_ID}}}}})['data']
    for op in shot['attributes']['uploadOperations']:
        req = urllib.request.Request(op['url'], method=op['method'],
                                     data=data[op['offset']:op['offset'] + op['length']],
                                     headers={h['name']: h['value'] for h in op['requestHeaders']})
        with urllib.request.urlopen(req) as r:
            r.read()
    call('PATCH', f'/inAppPurchaseAppStoreReviewScreenshots/{shot["id"]}', {'data': {
        'type': 'inAppPurchaseAppStoreReviewScreenshots', 'id': shot['id'],
        'attributes': {'uploaded': True, 'sourceFileChecksum': hashlib.md5(data).hexdigest()}}})
    print('iap screenshot uploaded', shot['id'])


if __name__ == '__main__':
    main()

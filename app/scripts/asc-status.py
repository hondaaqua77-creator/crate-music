#!/usr/bin/env python3
"""Print App Store review status (version, build, in-app purchase) via the App Store Connect API."""
import json, os, time, urllib.request, urllib.error
import jwt

API = 'https://api.appstoreconnect.apple.com/v1'
TMP = os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
APP_ID = os.environ.get('ASC_APP_ID', '6830933661')


def token():
    key = open(os.path.join(TMP, 'keys', f'AuthKey_{KEY_ID}.p8')).read()
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 600, 'aud': 'appstoreconnect-v1'},
                      key, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})


def get(path):
    req = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + token()})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'body': e.read().decode(errors='replace')[:300]}


for v in get(f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=5').get('data', []):
    a = v['attributes']
    print(f"VERSION {a['versionString']} state={a.get('appVersionState') or a.get('appStoreState')} created={a.get('createdDate')}")
for s in get(f'/apps/{APP_ID}/reviewSubmissions?limit=5').get('data', []):
    a = s['attributes']
    print(f"SUBMISSION state={a.get('state')} submitted={a.get('submittedDate')} platform={a.get('platform')}")
for i in get(f'/apps/{APP_ID}/inAppPurchasesV2?limit=10').get('data', []):
    a = i['attributes']
    print(f"IAP {a.get('productId')} state={a.get('state')}")
for b in get(f'/builds?filter[app]={APP_ID}&sort=-uploadedDate&limit=3').get('data', []):
    a = b['attributes']
    print(f"BUILD {a.get('version')} processing={a.get('processingState')} expired={a.get('expired')}")
# screenshot sets of the newest version
vs = get(f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=1').get('data', [])
if vs:
    for l in get(f"/appStoreVersions/{vs[0]['id']}/appStoreVersionLocalizations").get('data', []):
        for s in get(f"/appStoreVersionLocalizations/{l['id']}/appScreenshotSets").get('data', []):
            n = len(get(f"/appScreenshotSets/{s['id']}/appScreenshots?limit=20").get('data', []))
            print(f"SHOTS {vs[0]['attributes']['versionString']} {l['attributes']['locale']} {s['attributes']['screenshotDisplayType']} n={n}")
if os.environ.get('ASC_DUMP_META'):
    for l in get(f"/appStoreVersions/{vs[0]['id']}/appStoreVersionLocalizations").get('data', []):
        a = l['attributes']
        print('META_BEGIN'); print('PROMO:', a.get('promotionalText')); print('KEYWORDS:', a.get('keywords')); print('WHATSNEW:', a.get('whatsNew')); print('DESC:'); print(a.get('description')); print('META_END')
    for i in get(f'/apps/{APP_ID}/appInfos').get('data', []):
        for l in get(f"/appInfos/{i['id']}/appInfoLocalizations").get('data', []):
            print('NAME:', l['attributes'].get('name'), '| SUBTITLE:', l['attributes'].get('subtitle'))

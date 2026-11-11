#!/usr/bin/env python3
"""Set the App Store promotional text (ja) of the newest iOS version. Needs PROMO_TEXT env (<=170 chars)."""
import json, os, time, urllib.request, urllib.error
import jwt
API='https://api.appstoreconnect.apple.com/v1'; TMP=os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']; APP_ID=os.environ.get('ASC_APP_ID','6830933661')
TEXT=os.environ['PROMO_TEXT'].strip(); assert 0 < len(TEXT) <= 170, len(TEXT)
def token():
    key=open(os.path.join(TMP,'keys',f'AuthKey_{KEY_ID}.p8')).read(); now=int(time.time())
    return jwt.encode({'iss':ISSUER,'iat':now,'exp':now+600,'aud':'appstoreconnect-v1'},key,algorithm='ES256',headers={'kid':KEY_ID,'typ':'JWT'})
def call(m,p,b=None):
    r=urllib.request.Request(API+p,method=m,data=json.dumps(b).encode() if b else None,headers={'Authorization':'Bearer '+token(),'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as x: d=x.read(); return json.loads(d) if d else {}
    except urllib.error.HTTPError as e: print('::error::',m,p,e.code,e.read().decode(errors='replace')[:500]); raise
v=call('GET',f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=1')['data'][0]
for l in call('GET',f"/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data']:
    if l['attributes']['locale']=='ja':
        call('PATCH',f"/appStoreVersionLocalizations/{l['id']}",{'data':{'type':'appStoreVersionLocalizations','id':l['id'],'attributes':{'promotionalText':TEXT}}})
        print('promo set on',v['attributes']['versionString'])

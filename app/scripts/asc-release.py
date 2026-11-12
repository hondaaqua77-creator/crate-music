#!/usr/bin/env python3
"""App Store release helper (App Store Connect API).

  meta    : create the version named VERSION (if missing) in "prepare for submission" and set the
            Japanese metadata from app/store/meta (name, subtitle, keywords, description, what's new, promo).
  attach  : attach the newest VALID build of VERSION to that version and set manual release.
  submit  : create a review submission with that version and submit it.
Env: ASC_KEY_ID, ASC_ISSUER_ID, RUNNER_TEMP, VERSION (e.g. 1.0.2), optional ASC_APP_ID.
"""
import json, os, sys, time, urllib.request, urllib.error
from pathlib import Path
import jwt

API='https://api.appstoreconnect.apple.com/v1'; TMP=os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
APP_ID=os.environ.get('ASC_APP_ID','6830933661'); VERSION=os.environ['VERSION']
META=Path(__file__).resolve().parents[1]/'store'/'meta'

def token():
    key=open(os.path.join(TMP,'keys',f'AuthKey_{KEY_ID}.p8')).read(); now=int(time.time())
    return jwt.encode({'iss':ISSUER,'iat':now,'exp':now+900,'aud':'appstoreconnect-v1'},key,algorithm='ES256',headers={'kid':KEY_ID,'typ':'JWT'})
def call(m,p,b=None):
    r=urllib.request.Request(p if p.startswith('http') else API+p,method=m,data=json.dumps(b).encode() if b is not None else None,
        headers={'Authorization':'Bearer '+token(),'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(r) as x: d=x.read(); return json.loads(d) if d else {}
    except urllib.error.HTTPError as e: print('::error::',m,p,e.code,e.read().decode(errors='replace')[:800]); raise

def version():
    for v in call('GET',f'/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&limit=10')['data']:
        if v['attributes']['versionString']==VERSION: return v
    return None

def meta():
    v=version()
    if not v:
        v=call('POST','/appStoreVersions',{'data':{'type':'appStoreVersions','attributes':{'platform':'IOS','versionString':VERSION,'releaseType':'MANUAL'},
            'relationships':{'app':{'data':{'type':'apps','id':APP_ID}}}}})['data']; print('created version',VERSION)
    m=json.load(open(META/'meta.json')); desc=open(META/'description.txt').read().strip()
    loc=next((l for l in call('GET',f"/appStoreVersions/{v['id']}/appStoreVersionLocalizations")['data'] if l['attributes']['locale']=='ja'),None)
    attrs={'description':desc,'keywords':m['keywords'],'whatsNew':m['whatsNew'],'promotionalText':m['promotionalText']}
    if loc: call('PATCH',f"/appStoreVersionLocalizations/{loc['id']}",{'data':{'type':'appStoreVersionLocalizations','id':loc['id'],'attributes':attrs}})
    else: call('POST','/appStoreVersionLocalizations',{'data':{'type':'appStoreVersionLocalizations','attributes':dict(locale='ja',**attrs),
            'relationships':{'appStoreVersion':{'data':{'type':'appStoreVersions','id':v['id']}}}}})
    print('version metadata set')
    for info in call('GET',f'/apps/{APP_ID}/appInfos')['data']:
        if info['attributes'].get('appStoreState') in ('PREPARE_FOR_SUBMISSION','DEVELOPER_REJECTED','REJECTED','METADATA_REJECTED','WAITING_FOR_REVIEW','READY_FOR_DISTRIBUTION','READY_FOR_SALE',None) or True:
            for l in call('GET',f"/appInfos/{info['id']}/appInfoLocalizations")['data']:
                if l['attributes']['locale']=='ja':
                    try:
                        call('PATCH',f"/appInfoLocalizations/{l['id']}",{'data':{'type':'appInfoLocalizations','id':l['id'],'attributes':{'name':m['name'],'subtitle':m['subtitle']}}})
                        print('name/subtitle set on appInfo',info['id'])
                    except Exception: print('::warning::could not set name on appInfo',info['id'])

def attach():
    v=version(); assert v, 'version missing'
    builds=call('GET',f'/builds?filter[app]={APP_ID}&filter[preReleaseVersion.version]={VERSION}&filter[processingState]=VALID&sort=-uploadedDate&limit=1')['data']
    assert builds, 'no processed build for '+VERSION
    b=builds[0]; call('PATCH',f"/appStoreVersions/{v['id']}/relationships/build",{'data':{'type':'builds','id':b['id']}})
    print('attached build',b['attributes']['version'])

def submit():
    v=version(); assert v
    sub=call('POST','/reviewSubmissions',{'data':{'type':'reviewSubmissions','attributes':{'platform':'IOS'},'relationships':{'app':{'data':{'type':'apps','id':APP_ID}}}}})['data']
    call('POST','/reviewSubmissionItems',{'data':{'type':'reviewSubmissionItems','relationships':{'reviewSubmission':{'data':{'type':'reviewSubmissions','id':sub['id']}},
        'appStoreVersion':{'data':{'type':'appStoreVersions','id':v['id']}}}}})
    call('PATCH',f"/reviewSubmissions/{sub['id']}",{'data':{'type':'reviewSubmissions','id':sub['id'],'attributes':{'submitted':True}}})
    print('submitted',VERSION,'submission',sub['id'])

if __name__=='__main__':
    {'meta':meta,'attach':attach,'submit':submit}[sys.argv[1]]()

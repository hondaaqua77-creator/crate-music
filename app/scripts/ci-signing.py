#!/usr/bin/env python3
"""App Store distribution signing for CI, through the App Store Connect API.

  setup   : creates a temporary Apple Distribution certificate + App Store provisioning
            profile, imports them into a throwaway keychain, and switches the App target's
            Release configuration to manual signing with them.
  cleanup : revokes that certificate and deletes the profile (App Store / TestFlight builds
            that were already uploaded are not affected), so certificates never pile up.

Needs: ASC_KEY_ID, ASC_ISSUER_ID, RUNNER_TEMP, TEAM_ID, BUNDLE_ID env vars,
the key file at $RUNNER_TEMP/keys/AuthKey_<id>.p8, and `pip install pyjwt cryptography`.
"""
import base64, json, os, subprocess, sys, time, urllib.request, urllib.error
import jwt  # PyJWT

API = 'https://api.appstoreconnect.apple.com/v1'
TMP = os.environ['RUNNER_TEMP']
KEY_ID, ISSUER = os.environ['ASC_KEY_ID'], os.environ['ASC_ISSUER_ID']
TEAM, BUNDLE = os.environ['TEAM_ID'], os.environ.get('BUNDLE_ID', 'com.hondaatsushi.crate')
STATE = os.path.join(TMP, 'signing-state.json')
PBX = 'app/ios/App/App.xcodeproj/project.pbxproj'
RELEASE_BLOCK = '504EC3181FED79650016851F /* Release */'  # App target, Release


def token():
    key = open(os.path.join(TMP, 'keys', f'AuthKey_{KEY_ID}.p8')).read()
    now = int(time.time())
    return jwt.encode({'iss': ISSUER, 'iat': now, 'exp': now + 900, 'aud': 'appstoreconnect-v1'},
                      key, algorithm='ES256', headers={'kid': KEY_ID, 'typ': 'JWT'})


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors='replace')
        print(f'::error::App Store Connect API {method} {path} -> {e.code}: {msg[:600]}')
        raise


def sh(*args, **kw):
    print('+', ' '.join(a if 'pass' not in a else '***' for a in args))
    return subprocess.run(args, check=True, **kw)


def setup():
    run = os.environ.get('GITHUB_RUN_NUMBER', str(int(time.time())))
    key, csr = os.path.join(TMP, 'dist.key'), os.path.join(TMP, 'dist.csr')
    sh('openssl', 'genrsa', '-out', key, '2048')
    sh('openssl', 'req', '-new', '-key', key, '-out', csr, '-subj', f'/CN=CRATE CI {run}/C=JP')
    csr_txt = open(csr).read()
    cert = call('POST', '/certificates', {'data': {'type': 'certificates', 'attributes': {
        'certificateType': 'DISTRIBUTION', 'csrContent': csr_txt}}})['data']
    state = {'certificate': cert['id']}
    json.dump(state, open(STATE, 'w'))
    der = os.path.join(TMP, 'dist.cer')
    open(der, 'wb').write(base64.b64decode(cert['attributes']['certificateContent']))

    bid = call('GET', f'/bundleIds?filter[identifier]={BUNDLE}&limit=5')['data']
    bid = [b for b in bid if b['attributes']['identifier'] == BUNDLE][0]['id']
    name = f'CRATE AppStore CI {run}'
    prof = call('POST', '/profiles', {'data': {'type': 'profiles',
        'attributes': {'name': name, 'profileType': 'IOS_APP_STORE'},
        'relationships': {'bundleId': {'data': {'type': 'bundleIds', 'id': bid}},
                          'certificates': {'data': [{'type': 'certificates', 'id': cert['id']}]}}}})['data']
    state['profile'] = prof['id']
    json.dump(state, open(STATE, 'w'))
    content = base64.b64decode(prof['attributes']['profileContent'])
    uuid = prof['attributes']['uuid']
    for d in ('~/Library/MobileDevice/Provisioning Profiles', '~/Library/Developer/Xcode/UserData/Provisioning Profiles'):
        d = os.path.expanduser(d); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, uuid + '.mobileprovision'), 'wb').write(content)

    # certificate + key -> keychain
    pem, p12, pw = os.path.join(TMP, 'dist.pem'), os.path.join(TMP, 'dist.p12'), 'ci-' + run
    sh('openssl', 'x509', '-inform', 'DER', '-in', der, '-out', pem)
    sh('openssl', 'pkcs12', '-export', '-inkey', key, '-in', pem, '-out', p12, '-passout', 'pass:' + pw)
    kc = os.path.join(TMP, 'signing.keychain-db')
    sh('security', 'create-keychain', '-p', pw, kc)
    sh('security', 'set-keychain-settings', '-lut', '21600', kc)
    sh('security', 'unlock-keychain', '-p', pw, kc)
    sh('security', 'import', p12, '-P', pw, '-A', '-t', 'cert', '-f', 'pkcs12', '-k', kc)
    sh('security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', pw, kc,
       stdout=subprocess.DEVNULL)
    existing = subprocess.run(['security', 'list-keychains', '-d', 'user'], capture_output=True, text=True).stdout
    sh('security', 'list-keychains', '-d', 'user', '-s', kc, *[k.strip().strip('"') for k in existing.split()])

    # App target, Release: manual signing with this profile (package targets are left alone)
    s = open(PBX).read()
    i = s.index(RELEASE_BLOCK); j = s.index('name = Release;', i)
    block = s[i:j]
    new = block.replace('CODE_SIGN_STYLE = Automatic;',
        'CODE_SIGN_STYLE = Manual;\n\t\t\t\t"CODE_SIGN_IDENTITY[sdk=iphoneos*]" = "Apple Distribution";\n'
        f'\t\t\t\tDEVELOPMENT_TEAM = {TEAM};\n\t\t\t\tPROVISIONING_PROFILE_SPECIFIER = "{name}";')
    assert new != block, 'CODE_SIGN_STYLE not found in App Release config'
    open(PBX, 'w').write(s[:i] + new + s[j:])

    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>method</key><string>app-store-connect</string>
  <key>destination</key><string>upload</string>
  <key>teamID</key><string>{TEAM}</string>
  <key>signingStyle</key><string>manual</string>
  <key>signingCertificate</key><string>Apple Distribution</string>
  <key>provisioningProfiles</key><dict><key>{BUNDLE}</key><string>{name}</string></dict>
  <key>manageAppVersionAndBuildNumber</key><false/>
</dict></plist>'''
    open(os.path.join(TMP, 'ExportOptions.plist'), 'w').write(plist)
    print(f'signing ready: certificate {cert["id"]}, profile "{name}"')


def cleanup():
    if not os.path.exists(STATE):
        return
    st = json.load(open(STATE))
    for kind in ('profile', 'certificate'):
        if st.get(kind):
            try:
                call('DELETE', f'/{kind}s/{st[kind]}')
                print(f'removed {kind} {st[kind]}')
            except Exception:
                print(f'::warning::could not remove {kind} {st[kind]}')


if __name__ == '__main__':
    {'setup': setup, 'cleanup': cleanup}[sys.argv[1]]()

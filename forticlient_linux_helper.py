#!/usr/bin/python3
"""FortiClient Linux IPsec + SAML helper, v1.0, 2026-10-30.
Unofficial workaround validated in one user session on 7.4.3.5411.
No key, username, gateway or customer profile is embedded in this file.
Run /usr/bin/python3 forticlient_linux_helper.py --help.
"""
import argparse
import copy
import datetime
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

DB = Path('/var/lib/forticlient/config.db')
SETTING = 'ipsecvpn.connections.connection'
BACKUPS = Path('/var/lib/forticlient/local-psk-backups')
FORMAT_KEY = b'fc_1A2Brown3Fox4Jumped5Over6A7Lazy8Dog'
SOURCE = ('https://community.fortinet.com/support-forum-92/'
          'forticlient-linux-never-decrypts-the-ipsec-preshared-key-from-an-saml-xml-profile-ike-auth-fails-with-failed-to-decrypt-pre-shared-key-229475')

def aes_class():
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        try:
            from Crypto.Cipher import AES
        except ImportError:
            raise RuntimeError('Encryption library missing. Run the setup action with /usr/bin/python3 first.')
    return AES

def crypt_bytes(key, data):
    cipher = aes_class().new(key, aes_class().MODE_ECB)
    result = bytearray()
    for offset in range(0, len(data), 16):
        stream = cipher.encrypt((offset // 16 + 1).to_bytes(16, 'little'))
        result.extend(a ^ b for a, b in zip(data[offset:offset+16], stream))
    return bytes(result)

def derive(salt):
    material = hashlib.pbkdf2_hmac('sha1', FORMAT_KEY, salt, 1000, 50)
    return material[:24], material[24:48], material[48:]

def encode_key(plain, salt=None):
    salt = os.urandom(12) if salt is None else salt
    key, mac_key, verifier = derive(salt)
    encrypted = crypt_bytes(key, plain.encode('utf-8'))
    tag = hmac.new(mac_key, encrypted, hashlib.sha1).digest()[:10]
    return 'Enc ' + (salt + verifier + encrypted + tag).hex()

def decode_key(value):
    if not value.startswith('Enc '):
        raise RuntimeError('Unexpected encrypted key format.')
    raw = bytes.fromhex(value[4:])
    if len(raw) < 25:
        raise RuntimeError('Encrypted value too short.')
    salt, verifier, encrypted, tag = raw[:12], raw[12:14], raw[14:-10], raw[-10:]
    key, mac_key, expected_verifier = derive(salt)
    if not hmac.compare_digest(verifier, expected_verifier):
        raise RuntimeError('Encryption verification failed.')
    if not hmac.compare_digest(tag, hmac.new(mac_key, encrypted, hashlib.sha1).digest()[:10]):
        raise RuntimeError('Integrity verification failed.')
    return crypt_bytes(key, encrypted).decode('utf-8')

def root_required():
    if os.geteuid() != 0:
        raise RuntimeError('Run this action with sudo /usr/bin/python3.')

def read_profiles(db):
    row = db.execute('SELECT value FROM vpn WHERE config=?', (SETTING,)).fetchone()
    if not row or not row[0]:
        raise RuntimeError('No imported IPsec profile found. Import the Windows backup in FortiClient first.')
    profiles = json.loads(row[0])
    if not isinstance(profiles, list) or not all(isinstance(p, dict) for p in profiles):
        raise RuntimeError('Unrecognized profile structure. Nothing will be changed.')
    return profiles

def profile_auth(profiles, name):
    matches = [p for p in profiles if p.get('name') == name]
    if len(matches) != 1:
        raise RuntimeError('Profile name missing or ambiguous. Nothing will be changed.')
    try:
        auth = matches[0]['ike_settings']['auth_data']
        if not isinstance(auth, dict) or not isinstance(auth['preshared_key'], str):
            raise KeyError('preshared_key')
    except (KeyError, TypeError):
        raise RuntimeError('Expected pre-shared-key field missing. Nothing will be changed.')
    return auth

def choose_profile(profiles, requested):
    names = [p.get('name') for p in profiles if isinstance(p.get('name'), str)]
    if requested:
        profile_auth(profiles, requested)
        return requested
    print('Imported IPsec profiles:')
    for i, name in enumerate(names, 1):
        print(f'  {i}. {name}')
    if not names:
        raise RuntimeError('No named IPsec profiles found.')
    answer = input('Profile number: ').strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(names):
        raise RuntimeError('Invalid profile number.')
    name = names[int(answer)-1]
    profile_auth(profiles, name)
    return name

def connect(path=None):
    path = DB if path is None else path
    return sqlite3.connect(f'file:{path}?mode=rw', uri=True, timeout=10)

def backup_database():
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(BACKUPS, 0o700)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    path = BACKUPS / f'config-before-change-{stamp}.db'
    source = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    target = sqlite3.connect(path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    os.chmod(path, 0o600)
    print(f'Backup created: {path}')
    return path

def service(action, check=True):
    return subprocess.run(['systemctl', action, 'forticlient'], check=check)

def stop_client():
    service('stop')
    for args in (['pkill', '-TERM', '-f', '^/opt/forticlient/gui/FortiClient'],
                 ['pkill', '-TERM', '-x', 'fortitray'],
                 ['pkill', '-TERM', '-f', '^/opt/forticlient/fortitraylauncher($| )']):
        result = subprocess.run(args)
        if result.returncode not in (0, 1):
            raise RuntimeError('Could not stop a FortiClient component.')
    import time
    time.sleep(1)
    for name in ('fortitray',):
        if subprocess.run(['pgrep', '-x', name], stdout=subprocess.DEVNULL).returncode == 0:
            raise RuntimeError('A tray component is still running. Close it and retry.')
    if subprocess.run(['pgrep', '-f', '^/opt/forticlient/fortitraylauncher($| )'], stdout=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError('Tray launcher is still running. Close it and retry.')
    if subprocess.run(['pgrep', '-f', '^/opt/forticlient/gui/FortiClient'], stdout=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError('FortiClient GUI is still running. Close it and retry.')

def replace_key(name, encrypted):
    db = connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        profiles = read_profiles(db)
        auth = profile_auth(profiles, name)
        auth['preshared_key'] = encrypted
        cursor = db.execute('UPDATE vpn SET value=? WHERE config=?', (json.dumps(profiles), SETTING))
        if cursor.rowcount != 1:
            raise RuntimeError('Unexpected update count.')
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

def setup():
    root_required()
    print('Installs GTK 2 for fortitray and the Python encryption library using apt.')
    subprocess.run(['apt-get', 'install', 'libgtk2.0-0t64', 'python3-pycryptodome'], check=True)
    aes_class()
    print('Dependencies ready. No VPN profile changed.')

def doctor():
    root_required()
    print('READ ONLY CHECK — no credentials or profile values are printed.')
    try:
        aes_class()
        print('Python encryption library: OK')
    except RuntimeError as exc:
        print(exc)
    tray = Path('/opt/forticlient/fortitray')
    print('Tray executable:', 'present' if tray.exists() else 'missing')
    if tray.exists():
        result = subprocess.run(['ldd', str(tray)], capture_output=True, text=True)
        missing = [line.strip() for line in result.stdout.splitlines() if 'not found' in line]
        print('Missing tray libraries:', '; '.join(missing) if missing else 'none reported')
    subprocess.run(['systemctl', 'is-active', 'forticlient'], check=False)
    if DB.exists():
        db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
        try:
            profiles = read_profiles(db)
            print('Imported IPsec profile count:', len(profiles))
        finally:
            db.close()
    else:
        print('Configuration database: not found')

def fix(requested):
    root_required()
    aes_class()
    print('Unofficial local PSK-format workaround. Disconnect VPN and close FortiClient first.')
    print('The encryption format uses a built-in key; treat the database and backups as secrets.')
    # Inspect and gather secret before stopping the service; no live database edits yet.
    db = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    try:
        profiles = read_profiles(db)
    finally:
        db.close()
    name = choose_profile(profiles, requested)
    if not sys.stdin.isatty():
        raise RuntimeError('Run in an interactive terminal; do not pipe a key into this script.')
    plain = getpass.getpass('VPN pre-shared key (hidden): ')
    confirm = getpass.getpass('Repeat pre-shared key (hidden): ')
    if not plain or plain != confirm:
        raise RuntimeError('Keys empty or different. Nothing changed.')
    encrypted = encode_key(plain)
    if decode_key(encrypted) != plain:
        raise RuntimeError('Encryption self-check failed. Nothing changed.')
    del plain, confirm
    if input(f'Back up and replace only the key for {name!r}? Type YES: ') != 'YES':
        print('Cancelled. Nothing changed.')
        return
    try:
        stop_client()
        backup_database()
        replace_key(name, encrypted)
        print('SUCCESS: only the selected profile pre-shared key was updated.')
    finally:
        result = service('start', check=False)
        if result.returncode:
            print('Service restart failed. Run sudo systemctl start forticlient.')
    print('Open FortiClient from the application menu as your normal user and reconnect.')

def restore(path, requested):
    root_required()
    backup_path = Path(path).resolve()
    if not backup_path.is_file():
        raise RuntimeError('Backup file not found.')
    if backup_path == DB.resolve():
        raise RuntimeError('Choose a backup, not the live database.')
    old = sqlite3.connect(f'file:{backup_path}?mode=ro', uri=True)
    try:
        profiles = read_profiles(old)
        name = choose_profile(profiles, requested)
        encrypted = profile_auth(profiles, name)['preshared_key']
    finally:
        old.close()
    if input(f'Restore ONLY the saved key for {name!r}? Type YES: ') != 'YES':
        print('Cancelled.')
        return
    try:
        stop_client()
        backup_database()
        replace_key(name, encrypted)
        print('SUCCESS: previous key restored; other current profile settings preserved.')
    finally:
        service('start', check=False)

def self_test():
    # No service, production database, network or real credentials are accessed.
    samples = ['test-only-key', 'a', 'x'*16, 'x'*17, 'x'*65, 'Test-ä-秘密']
    for sample in samples:
        encoded = encode_key(sample, bytes(range(12)))
        assert decode_key(encoded) == sample
        broken = encoded[:-2] + ('00' if encoded[-2:] != '00' else '01')
        try:
            decode_key(broken)
        except RuntimeError:
            pass
        else:
            raise AssertionError('Tamper check failed')
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'fixture.db'
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE vpn(config TEXT UNIQUE, value TEXT)')
        fixture = [{'name':'Test profile', 'ike_settings':{'auth_data':{'preshared_key':'old','other':'keep'}},'other':'keep'}, {'name':'Other profile','other':'keep'}]
        db.execute('INSERT INTO vpn VALUES(?,?)', (SETTING,json.dumps(fixture)))
        parsed = read_profiles(db)
        changed = copy.deepcopy(parsed)
        profile_auth(changed, 'Test profile')['preshared_key'] = 'new'
        assert changed[1] == parsed[1]
        assert changed[0]['ike_settings']['auth_data']['other'] == 'keep'
        assert parsed == fixture
        try:
            profile_auth(parsed + [parsed[0]], 'Test profile')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Ambiguous profile not rejected')
        db.close()
    print('PASS: encryption round trips, tamper rejection, profile parsing and isolation.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='action', required=True)
    for command in ('setup','doctor','self-test'):
        subs.add_parser(command)
    fix_parser = subs.add_parser('fix')
    fix_parser.add_argument('--profile', help='Exact imported IPsec profile name; otherwise choose interactively.')
    restore_parser = subs.add_parser('restore')
    restore_parser.add_argument('--backup', required=True, help='Backup .db path printed by an earlier run.')
    restore_parser.add_argument('--profile')
    args = parser.parse_args()
    if args.action == 'setup': setup()
    elif args.action == 'doctor': doctor()
    elif args.action == 'fix': fix(args.profile)
    elif args.action == 'restore': restore(args.backup, args.profile)
    else: self_test()

if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        # Never dump profile values or user secrets in a traceback.
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)

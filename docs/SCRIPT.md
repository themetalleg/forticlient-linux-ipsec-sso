# Script Documentation

Complete technical documentation for `forticlient_linux_helper.py`.

## Overview

`forticlient_linux_helper.py` is a Python 3 utility that manages FortiClient IPsec VPN configuration on Linux, with a focus on converting pre-shared keys from Windows format to Linux format.

**Version**: 1.0  
**Release date**: October 30, 2026  
**Status**: Unofficial workaround, validated on one user session  
**Python**: 3.6+  
**License**: See LICENSE file

## Usage

```bash
/usr/bin/python3 forticlient_linux_helper.py <action> [options]

# Or with the script in the current directory:
/usr/bin/python3 ./forticlient_linux_helper.py <action> [options]
```

## Actions

### setup

Install system dependencies required for FortiClient VPN and the helper script.

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py setup
```

**What it does**:
- Installs `libgtk2.0-0t64` (GTK 2 library for FortiClient tray)
- Installs `python3-pycryptodome` (cryptography support)
- Does NOT modify any FortiClient configuration or profiles

**Prerequisites**: sudo privileges, internet connection

**Output**: Installation progress and status

### fix

Convert a Windows-format pre-shared key to Linux format.

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py fix
```

**Interactive prompts**:
1. Lists all imported IPsec profiles
2. Asks you to select a profile by number
3. Prompts for the original VPN pre-shared key (hidden input)
4. Prompts to re-enter the key for confirmation
5. Displays a summary and asks for confirmation with `YES`

**What it does**:
1. Verifies the entered key works with Linux encryption
2. Stops the FortiClient service
3. Creates a complete SQLite database backup
4. Updates the selected profile's `preshared_key` field
5. Restarts the FortiClient service
6. Prints the backup path for future reference

**Database backup location**:
```
/var/lib/forticlient/local-psk-backups/
```

**Prerequisites**:
- sudo privileges
- FortiClient service running
- At least one imported IPsec profile
- The correct original pre-shared key
- FortiClient window must be closed

**Important notes**:
- Only the selected profile is modified
- Database transaction is all-or-nothing (either fully applied or completely rolled back)
- If any step fails before the write stage, the database remains unchanged
- Backup is created before any changes are applied

### restore

Restore a previously saved pre-shared key from a database backup.

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py restore
```

**Interactive prompts**:
1. Asks for the full path to the backup file
2. Lists all imported IPsec profiles
3. Asks you to select a profile by number
4. Displays a summary and asks for confirmation with `YES`

**What it does**:
1. Verifies the backup file exists and is readable
2. Creates a backup of the current database (before restoring)
3. Stops the FortiClient service
4. Restores only the `preshared_key` field from the backup
5. Preserves all other current settings
6. Restarts the FortiClient service
7. Prints the current backup path

**Backup file format**:
- Path: `/var/lib/forticlient/local-psk-backups/config.db.backup.<timestamp>`
- Permissions: root only (mode 600)
- Format: Complete SQLite database snapshot

**Prerequisites**:
- sudo privileges
- Valid backup file path
- FortiClient service running
- FortiClient window must be closed

**Important notes**:
- Restoring the Windows key also restores the "failed to decrypt pre-shared key" error
- This is a rollback to the previous state, not an alternative fix
- You can restore, then fix again if needed

### doctor

Run read-only diagnostics to check system state.

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py doctor
```

**What it checks**:
- Encryption library (`Cryptodome` or `Crypto`) availability
- Required GTK 2 library (`libgtk-x11-2.0.so.0`)
- FortiClient service state
- Number of imported IPsec profiles (does not print profile details)

**Output**: Pass/fail status for each check

**Prerequisites**: sudo privileges (required to check service status and access database)

**Important notes**:
- Does NOT print any keys or profile values
- Does NOT modify the database or configuration
- Does NOT attempt to connect to any VPN
- Purely read-only diagnostics

## Technical Details

### Database Location

```
/var/lib/forticlient/config.db
```

**Format**: SQLite 3 database  
**Permissions**: Readable/writable by root only  
**Backup location**: `/var/lib/forticlient/local-psk-backups/`

### Key Conversion Process

#### Windows Format
- Encryption method: AES ECB mode
- Key format key: `fc_1A2Brown3Fox4Jumped5Over6A7Lazy8Dog` (built-in)
- Derivation: PBKDF2-HMAC-SHA1 with 1000 iterations
- Salt: 12 bytes extracted from encrypted value

#### Linux Format
- Same encryption method and key format
- Re-encrypts using the same built-in key
- Result is compatible with FortiClient Linux decryption

#### Conversion Steps
1. Extract pre-shared key from Windows backup
2. Decrypt using Windows format
3. Verify the plaintext key
4. Re-encrypt using Linux format (which is identical to Windows)
5. Store the new encrypted value in the database

### Cryptography Libraries

The script supports both Python cryptography namespaces:

```python
try:
    from Cryptodome.Cipher import AES  # pycryptodome
except ImportError:
    from Crypto.Cipher import AES      # pycryptography
```

**Supported libraries**:
- `pycryptodome`: Recommended (installed by `setup` action)
- `pycryptography`: Alternative, must be installed separately

### AES ECB Encryption

The key conversion uses AES in ECB (Electronic Codebook) mode:

```python
cipher = AES.new(key, AES.MODE_ECB)
```

**Note**: ECB mode is generally not recommended for security reasons, but FortiClient uses it. This script maintains compatibility with the existing encryption scheme.

### Database Backup

Backups are full SQLite database copies:

```bash
# Backup filename format
config.db.backup.<YYYYMMDD>_<HHMMSS>

# Example
config.db.backup.20261030_134215
```

**Backup process**:
1. Stop FortiClient service
2. Copy entire database to backup directory
3. Set permissions: 600 (root only)
4. Restart FortiClient service

**Backup contents**:
- Complete database state at the time of backup
- Includes all profiles, settings, and credentials
- Suitable for rollback

### Configuration Storage

The script modifies the `ipsecvpn.connections.connection` setting:

```sql
-- Example database structure
SELECT setting, value FROM forticlient_settings 
WHERE setting LIKE 'ipsecvpn.connections.connection%';
```

**Modified field**: `preshared_key` (in the specific connection's encrypted blob)  
**Unchanged fields**:
- Connection name
- Gateway address
- IPsec proposals
- SAML/SSO settings
- Certificate validation settings
- Other connections/profiles

## Security Considerations

### Key Handling

- **Hidden terminal input**: Pre-shared key prompts use `getpass.getpass()` (no echo)
- **Memory**: Key remains in memory only during execution
- **Database**: Encrypted key uses the same encryption as Windows (not more secure)
- **Backup files**: Restricted to root (mode 600), should be removed when no longer needed

### Credential Isolation

Three separate credentials are handled:
1. **Windows backup password**: Used only during FortiClient import, not by this script
2. **VPN pre-shared key**: Only required during `fix` or `restore` actions
3. **SSO credentials**: Handled entirely by FortiClient GUI, not by this script

### Error Handling

- Database writes are transactional (all-or-nothing)
- Service restart is attempted even if write fails
- No incomplete states are possible
- Backup is created before any write

### Audit Trail

The script does not maintain a log file. Diagnostic messages are printed to stdout/stderr only.

## Performance

### Typical Execution Times

- `setup`: 30-60 seconds (depends on package download speed)
- `fix`: 2-5 seconds
- `restore`: 2-5 seconds
- `doctor`: < 1 second

### Resource Usage

- **Memory**: ~50 MB during key conversion
- **Disk I/O**: Database backup can be 10-100 MB
- **CPU**: Minimal (encryption is fast)

## Compatibility

### Python Version

- **Minimum**: Python 3.6
- **Tested on**: Python 3.10+
- **Recommended**: Python 3.10 or later

### Operating Systems

- **Ubuntu**: 20.04 LTS, 22.04 LTS, 24.04 LTS, 26.04 LTS
- **Kubuntu**: 20.04 LTS and later
- **Debian**: Likely compatible (not tested)
- **Other Linux**: Untested (may work if FortiClient supports it)

### FortiClient Versions

- **Tested**: 7.4.3.5411 (Linux), 7.4.3.4726 (Windows)
- **Likely compatible**: 7.4.x series
- **Not tested**: 7.2.x, 7.0.x, older versions

### Cryptography Library Versions

- **pycryptodome**: 3.15+
- **pycryptography**: Not recommended, but supported if available

## Dependencies

### System Packages

Installed by `setup` action:
- `libgtk2.0-0t64` or compatible GTK 2 library
- `python3-pycryptodome`

### Python Modules

Built-in (no installation required):
- `argparse`
- `copy`
- `datetime`
- `getpass`
- `hashlib`
- `hmac`
- `json`
- `os`
- `pathlib`
- `sqlite3`
- `subprocess`
- `sys`

### External Python Modules

- `Cryptodome.Cipher` or `Crypto.Cipher` (installed by setup)

## Troubleshooting

### Import Error: Encryption library missing

**Error**:
```
ImportError: Encryption library missing. Run the setup action with /usr/bin/python3 first.
```

**Solution**:
```bash
sudo /usr/bin/python3 forticlient_linux_helper.py setup
```

### Database Lock: Cannot read database

**Error**:
```
sqlite3.OperationalError: database is locked
```

**Cause**: FortiClient service is accessing the database

**Solution**:
1. Close FortiClient GUI
2. Stop FortiClient service (may require full restart)
3. Retry the action

### Permission Denied: Cannot write to backup directory

**Error**:
```
PermissionError: [Errno 13] Permission denied: '/var/lib/forticlient/local-psk-backups/...'
```

**Cause**: Not running with sudo, or directory permissions issue

**Solution**:
```bash
# Ensure you are using sudo
sudo /usr/bin/python3 forticlient_linux_helper.py fix

# Check directory permissions
ls -ld /var/lib/forticlient/local-psk-backups/
```

### No profiles found

**Error**:
```
No imported IPsec profiles found in the database.
```

**Cause**: No profiles have been imported yet

**Solution**:
1. Import a profile from the FortiClient GUI
2. Retry the action

## Source Code

The script is single-file Python with the following structure:

1. **Imports**: Standard library only
2. **Constants**: Database path, backup directory, encryption key
3. **Utility functions**: Encryption, key derivation
4. **Database functions**: Profile listing, key conversion
5. **Action handlers**: `setup`, `fix`, `restore`, `doctor`
6. **Main entry point**: Command-line argument parsing

See the script source code for implementation details.

## Limitations

- **Single user**: Script operates under the user running the command (must be sudo)
- **One profile at a time**: `fix` and `restore` operate on a single profile
- **No SSO handling**: SSO authentication is handled by FortiClient GUI
- **No certificate management**: Certificate validation is unchanged by this script
- **No profile creation**: Only modifies existing profiles
- **No network changes**: Routing, split tunnel, or other network settings are unchanged

## Related Resources

- [Fortinet Community Forum Discussion](https://community.fortinet.com/support-forum-92/)
- [FortiClient Linux User Guide](https://docs.fortinet.com/)
- [IPsec IKEv2 Specification](https://tools.ietf.org/html/rfc7539)

## Version History

### Version 1.0 (October 30, 2026)

- Initial release
- Support for FortiClient 7.4.3.5411 on Linux
- Windows backup import conversion
- Database backup and restore
- Diagnostic tools

---

**Disclaimer**: This is an unofficial community workaround. Use at your own risk and ensure your IT department approves any VPN client modifications.

# FortiClient Linux IPsec SSO

Migrate an existing FortiClient IPsec VPN connection from Windows to Linux while retaining SAML single sign-on.

> **Version 1.2** • October 2026  
> Unofficial workaround for FortiClient 7.4.3+  
> No keys, usernames, gateways or customer profiles are embedded in this repository.

## Overview

This repository provides a step-by-step guide and companion helper script to:

1. **Export** your Windows FortiClient VPN configuration
2. **Import** the profile into FortiClient on Linux (Ubuntu/Kubuntu)
3. **Convert** the pre-shared key format using the helper script
4. **Connect** via IPsec IKEv2 with SAML single sign-on

The key conversion is an unofficial community workaround, validated on:
- **Windows**: FortiClient VPN 7.4.3.4726
- **Linux**: FortiClient VPN 7.4.3.5411 on Kubuntu/Ubuntu 26.04.1 LTS
- **Other versions** may require different packages or configuration handling

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Limitations](#limitations)

## Prerequisites

### Required Access
- An existing working FortiClient VPN connection on Windows
- Ability to export the Windows configuration with a backup password
- Access to your SSO account and credentials
- A password for the Windows configuration backup (separate from VPN pre-shared key and SSO password)

### System Requirements
- Ubuntu 20.04 LTS or later / Kubuntu with sudo privileges
- Internet connection to download dependencies
- FortiClient VPN for Linux (VPN-only .deb package from [Fortinet downloads](https://www.fortinet.com/support/product-downloads))

## Quick Start

```bash
# 1. Download the helper script
wget https://raw.githubusercontent.com/themetalleg/forticlient-linux-ipsec-sso/main/src/forticlient_linux_helper.py

# 2. Install dependencies
sudo /usr/bin/python3 forticlient_linux_helper.py setup

# 3. Import your Windows backup (follow steps in GUIDE.md)
# - Export .conf backup from Windows FortiClient
# - Import into Linux FortiClient

# 4. Convert the pre-shared key
sudo /usr/bin/python3 forticlient_linux_helper.py fix

# 5. Connect via FortiClient GUI
# - Open FortiClient from the application menu
# - Connect and complete SSO authentication
```

For detailed instructions, see [GUIDE.md](./docs/GUIDE.md).

## Installation

### Step 1: Download FortiClient for Linux

1. Visit [Fortinet Product Downloads](https://www.fortinet.com/support/product-downloads)
2. Download the **VPN-only Linux .deb package** (this guide uses version 7.4.3.5411)
3. Open the `.deb` file in Discover or install via terminal:
   ```bash
   sudo apt install ./forticlient_vpn_7.4.3.5411_amd64.deb
   ```

### Step 2: Save the Helper Script

1. Clone this repository or download `forticlient_linux_helper.py`:
   ```bash
   git clone https://github.com/themetalleg/forticlient-linux-ipsec-sso.git
   cd forticlient-linux-ipsec-sso
   ```

2. Verify the script is executable (no special permissions required):
   ```bash
   ls -l src/forticlient_linux_helper.py
   ```

### Step 3: Install Dependencies

```bash
sudo /usr/bin/python3 src/forticlient_linux_helper.py setup
```

This installs:
- **libgtk2.0-0t64**: GTK 2 library required by FortiClient tray application
- **python3-pycryptodome**: Cryptography support for key conversion

## Usage

### Export Configuration from Windows

1. Open **FortiClient Settings** → **System** → **Backup (Sichern)**
2. Save the `.conf` backup file
3. Set a secure backup password (keep this separate from your VPN pre-shared key)

### Import Configuration on Linux

1. Copy the `.conf` backup file to your Linux computer (use local storage, not network mounts)
2. Open FortiClient normally from the application menu
3. Select **Configure VPN** → **XML** → **Import XML Configuration**
4. Choose the local `.conf` file and enter the backup password
5. Verify the connection appears in the VPN list

### Convert the Pre-Shared Key

Once imported, run the conversion:

```bash
# First, disconnect and close FortiClient
sudo /usr/bin/python3 src/forticlient_linux_helper.py fix
```

The script will:
1. List all imported IPsec profiles
2. Prompt you to select the correct profile (enter the number)
3. Ask for the VPN pre-shared key **twice** (input is hidden for security)
4. Request confirmation (type `YES` to apply)
5. Create a database backup
6. Update only the selected profile's pre-shared key
7. Restart the FortiClient service
8. Print the backup path for future reference

### Connect to VPN

1. Open FortiClient from the application menu
2. Select your profile and click **Connect**
3. Complete any certificate confirmation
4. Complete SAML/SSO authentication in the browser
5. Wait for FortiClient to show **Connected**
6. Verify by accessing an internal resource only available through the VPN

### Additional Commands

**Check system health:**
```bash
sudo /usr/bin/python3 src/forticlient_linux_helper.py doctor
```

**Restore previous key (rollback):**
```bash
sudo /usr/bin/python3 src/forticlient_linux_helper.py restore
# Then provide the full backup path when prompted
```

## Troubleshooting

### Connection stalls with "failed to decrypt pre-shared key"

**Solution**: Run the `fix` action to convert the key format.

### Permission denied errors

**Cause**: `.conf` backup on a network drive that the FortiClient service cannot access  
**Solution**: Copy the backup to local storage first, then re-import.

### No tray icon or certificate prompt

**Cause**: GTK 2 library missing or FortiClient not restarted after dependency installation  
**Solution**:
1. Restart FortiClient completely
2. Run setup again: `sudo /usr/bin/python3 src/forticlient_linux_helper.py setup`
3. Run doctor to diagnose: `sudo /usr/bin/python3 src/forticlient_linux_helper.py doctor`

### VPN shows "Connected" but no network access

**Causes**:
- IPsec tunnel is not actually established
- Certificate validation issue
- SSO authentication incomplete

**Steps**:
1. Check the IPsec log: `sudo journalctl -u forticlient -f`
2. Verify with the browser's SSO success page
3. Access a resource that only exists behind the VPN
4. Do not re-import the old backup (this overwrites your converted key)

### Helper script error before database write

If an error occurs before any database changes:
- The profile remains unchanged
- No rollback needed
- Check encryption library availability via `doctor`
- Review error messages and keep the backup path

### Desktop freezes or display session becomes unresponsive

**Solution**: Stop FortiClient from a terminal:
```bash
sudo systemctl stop forticlient
```

A display-session change is not required by this procedure.

## Security Notes

### Credential Handling

- **Never paste** the pre-shared key, SSO password, or backup password into commands, support tickets, or chat sessions
- The script prompts for the pre-shared key with **hidden terminal input** (no characters displayed)
- The `Enc` value in the database uses a built-in application key and is **not secure storage** against local file access
- Treat configuration databases, backups, and exports as **confidential files**

### File Sharing

- The helper script and guide contain **no customer data**: no keys, gateways, accounts, or profiles
- Never share your actual database, logs, export files, or backup files
- Only share the script and documentation if you need community help

### Certificate Validation

- This script does **not disable certificate checking**
- This script does **not install a trusted certificate** or correct server certificate issues
- Verify unexpected certificates with your VPN administrator before accepting
- A browser success page confirms SSO authentication, **not** that the IPsec tunnel is working

## Limitations

- Applicable only to **IPsec IKEv2 with SAML single sign-on** and pre-shared keys
- Other VPN types or authentication methods are not covered
- The key conversion is an **unofficial community workaround**, not a Fortinet-supported feature
- Use only for profiles that fail with "failed to decrypt pre-shared key"
- Different FortiClient versions may require different packages or configuration handling
- This procedure is limited to converting an existing working connection to Linux; it does not troubleshoot fundamental VPN or SSO issues

## Backups

Database backups are automatically created in:
```
/var/lib/forticlient/local-psk-backups/
```

Each backup:
- Is restricted to root only (mode 600)
- Contains a full database snapshot before key conversion
- Can be used for rollback via the `restore` action
- Should be kept confidential and removed when no longer needed

## Rollback

To restore your original pre-shared key:

```bash
sudo /usr/bin/python3 src/forticlient_linux_helper.py restore
# Provide the backup path when prompted
```

**Important**: Restoring the original Windows key also **restores the original decryption problem**. This is a rollback, not an alternative fix.

## Further Help

### Diagnostic Commands

```bash
# Check library availability and service state
sudo /usr/bin/python3 src/forticlient_linux_helper.py doctor

# View FortiClient service logs
sudo journalctl -u forticlient -f

# Check IPsec tunnel status
sudo ip xfrm state list

# Monitor VPN connection
sudo journalctl -u forticlient-watchdog -f
```

### Documentation

- [Detailed Step-by-Step Guide](./docs/GUIDE.md)
- [Python Script Documentation](./docs/SCRIPT.md)
- [FAQ](./docs/FAQ.md)

### Community

- [Fortinet Community Forum](https://community.fortinet.com/support-forum-92/)
- Original discussion: [FortiClient Linux pre-shared key decryption issue](https://community.fortinet.com/support-forum-92/forticlient-linux-never-decrypts-the-ipsec-preshared-key-from-an-saml-xml-profile-ike-auth-fails-with-failed-to-decrypt-pre-shared-key-229475)

## License

This project is provided as-is for community use. See [LICENSE](./LICENSE) for details.

## Contributing

Found an issue or have an improvement? Please open an [Issue](https://github.com/themetalleg/forticlient-linux-ipsec-sso/issues) or [Pull Request](https://github.com/themetalleg/forticlient-linux-ipsec-sso/pulls).

---

**Disclaimer**: This is an unofficial workaround based on community research. It is not affiliated with Fortinet and is provided without warranty. Use at your own risk and ensure your IT department approves any VPN client modifications.

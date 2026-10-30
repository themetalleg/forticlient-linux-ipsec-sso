# Detailed Step-by-Step Guide

This is the full version of the guide from the Word document, converted to Markdown format for better GitHub integration.

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Handle Credentials Correctly](#handle-credentials-correctly)
3. [Download and Install FortiClient VPN](#download-and-install-forticlient-vpn)
4. [Prepare the Client and Import the Connection](#prepare-the-client-and-import-the-connection)
5. [Convert the Imported Key and Connect](#convert-the-imported-key-and-connect)
6. [Common Connection Problems](#common-connection-problems)
7. [Rollback and Further Troubleshooting](#rollback-and-further-troubleshooting)

## Before You Start

### What You Need

- **Access to the existing working FortiClient VPN connection** and its configuration backup function
- **Ubuntu/Kubuntu with sudo privileges** and internet access
  - Install FortiClient VPN using the VPN-only Linux .deb download (see below)
- **Three separate credentials**:
  1. The VPN pre-shared key
  2. Access to the SSO account
  3. The password you choose for the Windows configuration backup
  
  These are three different secrets. Keep them separate and secure.

- **The helper script** saved in a local folder on the Linux computer
  - No renaming is required
  - No special executable permissions are needed

### Why This Process?

FortiClient on Linux decrypts pre-shared keys differently than Windows. When you import a Windows backup, the key remains in Windows format and fails with:
```
failed to decrypt pre-shared key
```

The companion helper script converts the key to Linux format by:
1. Extracting the Windows-format key from the Windows backup
2. Verifying it against the configuration
3. Re-encrypting it using Linux's encryption method
4. Storing the Linux-format key in the FortiClient database

## Handle Credentials Correctly

### Security Best Practices

- **Never paste** the pre-shared key, SSO password, or backup password into:
  - Command lines or shell history
  - Support tickets or chat messages
  - Log files or configuration exports
  - Any location where it could be stored or forwarded

- **The helper script uses hidden input**: When prompted for the pre-shared key, the terminal intentionally shows no characters as you type. This is correct—type carefully.

- **The Enc value is not secure**: The generated encrypted key uses a built-in application key, so it should be treated the same as plaintext if someone can read the database file. Treat configuration databases, backups, and exports as **confidential**.

- **Share only the script and guide**: The helper script and this guide contain no customer key, gateway, account, or profile information. Do not include your actual database, export, logs, or backup files when distributing these tutorial files.

## Download and Install FortiClient VPN

### Step 1: Get FortiClient for Linux

1. Go to [Fortinet Product Downloads](https://www.fortinet.com/support/product-downloads)
2. Find and download the **VPN für Linux .deb** package
   - This guide uses version **7.4.3.5411** as the reference
   - The file name may change; look for the VPN-only Debian package
3. Save the `.deb` file to your Downloads folder

### Step 2: Install FortiClient

**Option A: Using the GUI (Discover)**
1. Open the downloaded `.deb` file in the **Discover** application
2. Click **Install**
3. Authenticate with your sudo password when prompted
4. Wait for installation to complete

**Option B: Using the terminal**
```bash
cd ~/Downloads
sudo apt install ./forticlient_vpn_*.deb
```

### Step 3: Verify Installation

Once installed, continue with the companion script below. If FortiClient VPN is already installed, you can proceed directly to the next section.

## Prepare the Client and Import the Connection

### Step 1: Open a Terminal in the Script Folder

1. **Using Dolphin file manager**:
   - Navigate to the folder containing `forticlient_linux_helper.py`
   - Press `F4` to open a terminal in that location
   - Or: Right-click → **Open Terminal Here**

2. **Using Konsole**:
   - Open Konsole from the application menu
   - Navigate to the script folder: `cd ~/path/to/script/folder`

3. **Verify the script is present**:
   ```bash
   ls -l forticlient_linux_helper.py
   ```

### Step 2: Install the Two Dependencies

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py setup
```

This command:
1. **Installs system packages**:
   - `libgtk2.0-0t64`: GTK 2 library required by the FortiClient tray application
   - `python3-pycryptodome`: Python cryptography library for key conversion

2. **Approves apt's package installation prompt**: Simply press `Y` and `Enter` when asked

3. **Does NOT**:
   - Edit or modify any VPN profile
   - Change any FortiClient settings
   - Connect to any VPN

4. **Supports both Python crypto libraries**:
   - The script works with both `Cryptodome` and `Crypto` Python namespaces
   - Setup installs `pycryptodome`, which provides the `Cryptodome` namespace

### Step 3: Import the Windows Backup

#### On Windows

1. Open **FortiClient Settings**
2. Go to **System** → **Backup (Sichern)**
3. Click **Backup** or **Sichern**
4. Choose a location and **set a secure backup password**
   - This password is separate from your VPN pre-shared key
   - Remember this password for the next step
5. Save the `.conf` file

**Important**: The file extension `.conf` is correct for an encrypted backup. The encrypted backup does not become readable XML by renaming it.

#### On Linux

1. Copy the `.conf` backup file from the network folder or SharePoint to your local Linux computer
   - **Important**: Use local storage, not a mounted network folder
   - Background services (like FortiClient) may not be able to access network mounts even if you can see them in the file manager

2. Open **FortiClient** normally from the application menu
   - This is the GUI application, not a terminal
   - If FortiClient is already running, close it first

3. Navigate to **Configure VPN** → **XML** → **Import XML Configuration**

4. Choose the local `.conf` file from step 1

5. Enter the backup password you created on Windows

6. Verify the connection profile appears in the VPN list

### Step 4: Check the Tray and Attempt SSO

#### Start the FortiClient Tray

If FortiClient was open during dependency installation, completely quit and reopen it:
```bash
# Close any running FortiClient processes
killall fortitray
killall forticlient
```

If no tray icon or certificate prompt appears, run the tray as your normal desktop user (not sudo):
```bash
/opt/forticlient/fortitray
```

Leave that terminal window open.

#### Try to Connect

1. Look for the FortiClient icon in the system tray (near the clock)
2. Click the tray icon and select your imported profile
3. Click **Connect**
4. A certificate confirmation may appear (especially if this is your first connection)
5. Review and accept the certificate (this is separate from the pre-shared key issue)
6. Your default browser will open with an SSO login page
7. Sign in with your SSO credentials
8. After successful authentication, you'll see a success page in the browser

**Important**: 
- Certificate trust is a separate decision from the pre-shared key conversion
- The browser success page confirms SSO authentication worked, **not** that the IPsec tunnel is up
- If you see `failed to decrypt pre-shared key` in the logs, proceed to Step 5

## Convert the Imported Key and Connect

### Step 5: Apply the Key Format Workaround

#### Prepare to Run Fix

1. **Disconnect the VPN**: If it's still trying to connect, click **Disconnect** in FortiClient
2. **Close the FortiClient window**: Quit the GUI application completely
3. Leave the tray terminal running (it will restart after the script finishes)

#### Run the Fix Command

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py fix
```

This will:

1. **List all imported IPsec profiles**:
   ```
   Found 2 imported IPsec profiles:
   [0] CompanyVPN
   [1] CustomerVPN
   ```

2. **Ask which profile to convert**:
   ```
   Select profile number (0-1): 
   ```
   Enter the number of your profile

3. **Ask for the original VPN pre-shared key**:
   ```
   Enter the VPN pre-shared key (input hidden): 
   ```
   - Type the key carefully (you won't see characters)
   - Press `Enter`

4. **Ask for the pre-shared key again**:
   ```
   Re-enter the pre-shared key to confirm (input hidden): 
   ```
   - Type the exact same key again
   - Press `Enter`

5. **Show a summary and ask for confirmation**:
   ```
   Profile: CompanyVPN
   Pre-shared key length: 32 characters
   
   WARNING: This will update the FortiClient database.
   Type YES to confirm: 
   ```
   - Type `YES` in uppercase (nothing else will be accepted)
   - Press `Enter`

#### What Happens Behind the Scenes

Once you confirm:

1. The script verifies the key works with Linux's encryption method
2. It stops the FortiClient service: `sudo systemctl stop forticlient`
3. It creates a **complete database backup** (see Backups section below)
4. It updates **only** the selected profile's `preshared_key` field in a database transaction
5. It restarts the service: `sudo systemctl start forticlient`
6. It prints the backup path

**Important notes**:
- Only the selected profile is modified
- Gateway addresses, proposals, SSO settings, and certificate validation are NOT changed
- Other profiles in the database are NOT touched
- The change is applied in a database transaction (all-or-nothing)
- If any step fails before the write, the database remains unchanged

#### Database Backups

Backups are stored in:
```
/var/lib/forticlient/local-psk-backups/
```

Each backup:
- Is a complete SQLite database snapshot from before the key conversion
- Is restricted to root only (mode 600 permissions)
- Has a timestamp in its filename: `config.db.backup.20261030_134215`
- Can be used to rollback if needed

**Record the backup path** printed by the fix command. You'll need it if you want to rollback.

### Step 6: Verify the Actual Tunnel

#### Important Distinction

Before proceeding, understand that FortiClient shows "Connected" when:
- SSO authentication succeeded (browser showed success page)
- FortiClient thinks the connection is ready

But "Connected" does **NOT** mean:
- The actual IPsec tunnel is up and working
- Network traffic is actually flowing through the VPN

#### Verify the Tunnel

1. **Open FortiClient from the application menu** (as your normal user, not sudo)

2. **Click Connect** on your profile

3. **Complete the certificate decision** (if prompted)
   - Verify the certificate matches your VPN administrator's expectations
   - Accept or reject based on your trust

4. **Complete the SSO flow**:
   - Your browser opens the SSO login page
   - Sign in with your SSO credentials
   - Wait for the browser to show a success page

5. **Wait for FortiClient itself to show Connected**:
   - Do not just look at the browser success page
   - Wait until the FortiClient GUI shows the status as **Connected**

6. **Verify with an actual internal resource**:
   ```bash
   # Example: connect to an internal service only available through VPN
   curl https://internal-server.company.local/health
   
   # Or open a web page that only exists behind the VPN
   # Or connect to an internal database
   ```

   Only access that is reachable **only** through this VPN will prove the tunnel works.

**Both checks are needed**:
- The browser's SSO success page proves authentication
- Access to internal resources proves the IPsec tunnel is actually up

## Common Connection Problems

### Problem: Permission denied when importing

**Cause**: The `.conf` backup file is on a network drive that the FortiClient service cannot access.

**Solution**:
1. Copy the backup to local storage first: `cp /mnt/network/backup.conf ~/Local/backup.conf`
2. Import from the local copy
3. Then proceed with the fix action

### Problem: No tray icon or certificate prompt appears

**Cause**: Either GTK 2 library is missing or FortiClient wasn't fully restarted.

**Solution**:
1. Completely close FortiClient (kill any running processes):
   ```bash
   killall fortitray forticlient
   ```

2. Run setup again to ensure all dependencies are installed:
   ```bash
   sudo /usr/bin/python3 forticlient_linux_helper.py setup
   ```

3. Start the tray manually:
   ```bash
   /opt/forticlient/fortitray
   ```

4. Run doctor to diagnose:
   ```bash
   sudo /usr/bin/python3 forticlient_linux_helper.py doctor
   ```

### Problem: Connection stalls with "failed to decrypt pre-shared key"

**Cause**: The Windows-format pre-shared key has not been converted.

**Solution**:
1. Disconnect from VPN
2. Close FortiClient window
3. Run the fix action:
   ```bash
   sudo /usr/bin/python3 forticlient_linux_helper.py fix
   ```

### Problem: FortiClient shows Connected but there is no network access

**Possible causes**:
- The IPsec tunnel is not actually established (check `sudo ip xfrm state list`)
- Server certificate validation is failing silently
- SSO authentication did not complete properly
- Split tunnel or routing rules are not configured

**Diagnostic steps**:
1. Check the IPsec log:
   ```bash
   sudo journalctl -u forticlient -f
   ```

2. List active IPsec tunnels:
   ```bash
   sudo ip xfrm state list
   ```

3. Verify certificate acceptance with your VPN administrator

4. Do NOT re-import the old Windows backup (this overwrites your converted key)

5. After any new import, re-run the fix action if needed

6. Export fresh logs after one failed attempt for support

## Rollback and Further Troubleshooting

### Restore the Previous Pre-Shared Key

If the conversion didn't work, you can rollback to the original Windows-format key.

**Get the backup path**:
- You should have recorded it from when the fix command ran
- Or find it in: `/var/lib/forticlient/local-psk-backups/`

**Run the restore command**:
```bash
sudo /usr/bin/python3 forticlient_linux_helper.py restore
```

When prompted, enter the exact backup path:
```
Enter the full backup path: /var/lib/forticlient/local-psk-backups/config.db.backup.20261030_134215
```

The restore will:
1. Create **another** full database backup
2. Restore only the saved key field into the current profile
3. Preserve all other current settings
4. Restart the FortiClient service

**Important**: Restoring the original Windows key also **restores the original decryption problem** (failed to decrypt pre-shared key). This is a rollback, not an alternative connection fix.

### Read-Only Diagnostics

The doctor command checks your system without making any changes:

```bash
sudo /usr/bin/python3 forticlient_linux_helper.py doctor
```

Doctor checks:
- Encryption library availability
- Missing tray dependencies
- FortiClient service state
- Number of imported IPsec profiles

Doctor does **NOT**:
- Print any keys or profile values
- Change the database
- Initiate a VPN connection

### If the Helper Stops with an Error

**Before the write stage** (before database changes):
- The profile remains unchanged
- No rollback is needed
- Fix the issue and try again

**During the write stage** (database transaction):
- Database writes are transactional (all-or-nothing)
- Either the entire change applies, or nothing changes

**If stopping components fails**:
- The script aborts and attempts to restart the service
- If service restart fails, manually restart:
  ```bash
  sudo systemctl start forticlient
  ```

**How to get help**:
- Keep the error text and backup path
- Do NOT include credentials in your error report
- Ask on the [Fortinet Community Forum](https://community.fortinet.com/support-forum-92/)

### Desktop Freezes and Display Sessions

If the desktop becomes unresponsive:
1. Stop FortiClient from a terminal:
   ```bash
   sudo systemctl stop forticlient
   ```

2. Save any open work

3. Log out or reboot if necessary

A display-session change is not required by this procedure. If you are using Wayland and experience issues, you can try switching to X11, but this is not required for the VPN conversion to work.

### Service and Log Inspection

**Check FortiClient service status**:
```bash
sudo systemctl status forticlient
```

**View live service logs**:
```bash
sudo journalctl -u forticlient -f
```

**View live tray logs**:
```bash
sudo journalctl -u forticlient-watchdog -f
```

**Check active IPsec tunnels**:
```bash
sudo ip xfrm state list
```

**Check IPsec policies**:
```bash
sudo ip xfrm policy list
```

---

## Summary

The complete workflow:

1. ✅ Export Windows FortiClient backup → `.conf` file with password
2. ✅ Install FortiClient on Linux
3. ✅ Run `setup` to install dependencies
4. ✅ Import the `.conf` backup into Linux FortiClient
5. ✅ Attempt SSO connection (may fail with pre-shared key error)
6. ✅ Run `fix` to convert the pre-shared key
7. ✅ Connect again via FortiClient GUI
8. ✅ Verify with internal resources only accessible through VPN

If issues arise, use `doctor` for diagnostics and refer to [Troubleshooting](#troubleshooting) or the [FAQ](./FAQ.md).

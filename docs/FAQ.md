# Frequently Asked Questions (FAQ)

## General Questions

### Q: Is this an official Fortinet product or support?

**A:** No. This is an unofficial community workaround based on research and validated by community members. It is not affiliated with Fortinet and is not supported by Fortinet. Use at your own risk and ensure your IT department approves any VPN client modifications.

### Q: What versions of FortiClient are supported?

**A:** This guide has been tested on:
- **Windows**: FortiClient VPN 7.4.3.4726
- **Linux**: FortiClient VPN 7.4.3.5411

Other versions in the 7.4.x series may work, but different versions may require different packages or handling. Test carefully in a lab environment first if possible.

### Q: Can I use this with FortiClient 7.2.x or older?

**A:** Unknown. The script was written for 7.4.3.5411. Older versions may use different encryption or database formats. Do not attempt without testing in a lab first.

### Q: Does this work with FortiClient Web VPN (SSL VPN)?

**A:** No. This guide covers only **IPsec IKEv2** connections. Web VPN (SSL) is a different protocol and is not covered by this workaround.

### Q: Does this work with other authentication methods (certificate, password, etc.)?

**A:** No. This guide covers only **SAML single sign-on** with pre-shared keys. Other authentication methods are not covered.

### Q: Can I share this script and guide with my company?

**A:** Yes, you can share the script and guide. However:
- Do NOT include your actual database, configuration backups, logs, or exports
- Do NOT include any customer-specific information
- The guide and script contain no embedded credentials
- Advise recipients to follow the security practices outlined in the guide

### Q: Is there an official alternative?

**A:** Contact Fortinet support to ask about:
- Official Linux client improvements
- Supported alternatives for your use case
- Certificate-based authentication instead of pre-shared keys

---

## Installation Questions

### Q: Do I need to install anything on Windows?

**A:** No. You only need:
- Access to FortiClient on Windows to export the backup
- Network access to copy the backup to your Linux computer

The script and dependencies are installed only on Linux.

### Q: What if I already have FortiClient installed on Linux?

**A:** That's fine. You can still use this guide. Just run the `setup` action to ensure all dependencies are installed:
```bash
sudo /usr/bin/python3 forticlient_linux_helper.py setup
```

### Q: Can I install this on Windows?

**A:** The script is designed for Linux only. It accesses the Linux FortiClient database at `/var/lib/forticlient/config.db`. The script will not work on Windows or macOS.

### Q: What if the dependency installation fails?

**A:** Try:
1. Update your package manager: `sudo apt update && sudo apt upgrade`
2. Retry setup: `sudo /usr/bin/python3 forticlient_linux_helper.py setup`
3. If still failing, try manual installation:
   ```bash
   sudo apt install libgtk2.0-0t64 python3-pycryptodome
   ```
4. Run `doctor` to check the state: `sudo /usr/bin/python3 forticlient_linux_helper.py doctor`

### Q: Do I need to rename the script?

**A:** No. The script works as-is with any filename. Just use the full path when running it.

---

## Configuration Questions

### Q: How do I export the Windows backup?

**A:** In FortiClient on Windows:
1. Open **Settings** → **System** → **Backup**
2. Click **Backup** (or **Sichern** if German language)
3. Choose a location and set a **secure password**
4. Save the `.conf` file

The `.conf` extension is correct for an encrypted backup.

### Q: Why can't I import from a network drive?

**A:** FortiClient service runs as a system service and may not have permissions to access network-mounted drives, even if you can access them in the file manager.

**Solution**: Copy the backup file to local storage first:
```bash
cp /mnt/network/backup.conf ~/backup.conf
```

Then import from the local file.

### Q: Can I import multiple profiles at once?

**A:** Yes. The `fix` and `restore` actions allow you to choose which profile to work with. You can:
1. Import multiple profiles
2. Run `fix` on each one individually
3. Or restore one profile back to its original state

### Q: What if I forget the backup password?

**A:** You'll need to create a new backup on Windows with a password you know. There's no way to recover a forgotten backup password.

### Q: Do I need to keep the `.conf` backup file after importing?

**A:** You don't need it on Linux after the import is complete. However, keep it safe on Windows in case you need to re-import.

---

## Connection Questions

### Q: How do I verify the VPN is actually connected?

**A:** Do not rely only on the FortiClient "Connected" status. Instead:

1. Access a resource that **only exists behind the VPN**:
   ```bash
   # Example: internal web server
   curl https://internal-server.company.local/
   
   # Example: internal API
   curl https://api-internal.company.com/health
   
   # Example: ping internal server
   ping 10.0.0.1  # (internal IP range)
   ```

2. If you can access it, the VPN is working
3. If you get "Connection refused" or "Host unreachable", the tunnel is not up

### Q: SSO worked, but there's no network access. What happened?

**A:** The browser success page confirms SSO authentication succeeded, but it does NOT confirm the IPsec tunnel is working.

**Possible causes**:
- IPsec tunnel negotiation failed (check logs)
- Certificate validation issue
- Split tunnel or firewall rules blocking traffic
- Wrong pre-shared key (convert it with `fix`)

**Check IPsec tunnel status**:
```bash
sudo ip xfrm state list
# Should show active IPsec state entries
```

### Q: Why does the tray not appear?

**A:** The GTK 2 library may not be installed, or FortiClient wasn't fully restarted.

**Solution**:
1. Close FortiClient completely: `killall fortitray forticlient`
2. Reinstall dependencies: `sudo /usr/bin/python3 forticlient_linux_helper.py setup`
3. Start the tray: `/opt/forticlient/fortitray`
4. Run doctor to diagnose: `sudo /usr/bin/python3 forticlient_linux_helper.py doctor`

### Q: Can I use split tunnel mode?

**A:** The script does not enable or disable split tunnel. Use FortiClient's GUI to configure split tunnel if your VPN supports it.

### Q: Do I need to change my desktop environment?

**A:** No. The script works on X11, Wayland, GNOME, KDE, XFCE, or any other desktop environment. If you experience display freezes, you can try switching desktops, but it's not required.

---

## Key and Encryption Questions

### Q: What's the difference between Windows and Linux key formats?

**A:** Both use the same AES ECB encryption method with the same built-in key. The difference is how FortiClient extracts and stores the key in the database.

The script re-encrypts the key using the Linux format, making it readable by the Linux client.

### Q: Is the encrypted key secure?

**A:** No. The key is encrypted using a built-in application key, not a user-provided encryption key. If someone has read access to the database file, they can decrypt the key.

**Treat it like plaintext**: The database file `/var/lib/forticlient/config.db` should be treated as confidential (it already is—it's owned by root with mode 600).

### Q: Can I change the pre-shared key?

**A:** No. This script converts the existing key; it does not change it. To use a different key:

1. Change the key on the VPN gateway
2. Export a new Windows backup with the new key
3. Re-import on Linux
4. Run `fix` again

### Q: Why do I need to enter the key twice?

**A:** For safety. Entering it twice ensures you typed it correctly (the first entry is confirmed against the second).

### Q: What if I enter the wrong key?

**A:** The script will catch the mismatch during verification and abort without writing to the database.

If you accidentally entered the wrong key and it failed, just run `fix` again and enter the correct key.

### Q: Will the key be stored in my shell history?

**A:** No. The script uses `getpass.getpass()` to read the key from the terminal without echoing characters. Your shell never sees the key; it goes directly to Python.

---

## Backup and Restore Questions

### Q: Where are backups stored?

**A:** In:
```
/var/lib/forticlient/local-psk-backups/
```

Example filename:
```
config.db.backup.20261030_134215
```

### Q: Can I manually restore a backup?

**A:** Yes, but it's risky. The backup is a complete SQLite database. You can:

1. Stop FortiClient: `sudo systemctl stop forticlient`
2. Copy the backup: `sudo cp /var/lib/forticlient/local-psk-backups/config.db.backup.20261030_134215 /var/lib/forticlient/config.db`
3. Restart: `sudo systemctl start forticlient`

But using the `restore` action is safer because it:
- Verifies the backup before restoring
- Creates a backup of the current state first
- Restores only the key field, preserving other changes

### Q: How many backups should I keep?

**A:** Keep the most recent backup from the `fix` action. You can safely delete older backups:

```bash
# List backups
ls -la /var/lib/forticlient/local-psk-backups/

# Delete old backups (keep the most recent)
sudo rm /var/lib/forticlient/local-psk-backups/config.db.backup.20261025_*
```

### Q: Are backups encrypted or compressed?

**A:** No. Backups are full SQLite database copies in unencrypted form. Treat them as confidential and store them securely.

### Q: Can I restore to a different profile?

**A:** No. Restore only works on the same profile. The backup contains the database state from that specific profile.

If you need to restore to a different profile, manually edit the backup file or re-import the Windows backup.

### Q: What if the backup file is corrupted?

**A:** SQLite is robust, but if the backup is corrupted:

1. Try to restore anyway (SQLite may recover partial data)
2. If it fails, you'll need to re-import the Windows backup and run `fix` again
3. Keep your most recent Windows backup safe

---

## Troubleshooting Questions

### Q: Connection works on Windows but fails on Linux. What's wrong?

**A:** Most common causes:

1. **Pre-shared key not converted**: Run `fix` to convert it
2. **Certificate not trusted**: Accept the server certificate when prompted
3. **SSO not completing**: Check if the browser login worked
4. **IPsec tunnel not up**: Check logs and IPsec state
5. **Different FortiClient version**: The version on Linux may not support the exact profile configuration

**Check logs**:
```bash
sudo journalctl -u forticlient -f
```

### Q: "failed to decrypt pre-shared key" error

**Cause**: Windows format key not converted yet.

**Solution**: Run `fix`:
```bash
sudo /usr/bin/python3 forticlient_linux_helper.py fix
```

### Q: "database is locked" error

**Cause**: FortiClient is accessing the database.

**Solution**:
1. Close FortiClient GUI
2. Retry the action
3. If it still fails, restart FortiClient service: `sudo systemctl restart forticlient`

### Q: "Permission denied" error

**Cause**: Not running with sudo.

**Solution**: Use sudo:
```bash
sudo /usr/bin/python3 forticlient_linux_helper.py fix
```

### Q: Desktop freezes during connection

**Cause**: FortiClient tray or service consuming resources.

**Solution**:
1. Open another terminal: `Ctrl+Alt+F2`
2. Login and stop FortiClient: `sudo systemctl stop forticlient`
3. Return to desktop: `Alt+F1`
4. Restart FortiClient: `/opt/forticlient/fortitray`

### Q: How do I check what's in the database?

**A:** The database is SQLite, but for safety, only view it with the `doctor` command or let FortiClient manage it. Manual inspection is not recommended because you might accidentally corrupt it.

For read-only inspection:
```bash
sudo sqlite3 /var/lib/forticlient/config.db
sqlite> .schema
sqlite> SELECT setting FROM forticlient_settings LIMIT 10;
sqlite> .quit
```

---

## Advanced Questions

### Q: Can I automate this with a script?

**A:** The helper script is designed for interactive use (it prompts for input). For automation, you'd need to:

1. Pipe the pre-shared key as input (unsafe—don't do this)
2. Modify the script to accept command-line arguments (read-only guide, not supported)
3. Use the approach manually each time

**Recommendation**: Run it interactively the first time. Once converted, you don't need to run it again unless you change the key.

### Q: Can I use a different encryption library?

**A:** Yes, the script supports both:
- `pycryptodome` (recommended, installed by setup)
- `pycryptography` (alternative)

The script auto-detects which one is available.

### Q: How can I contribute improvements?

**A:** See [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue/PR on GitHub.

### Q: Can this work with container-based deployments?

**A:** No. Containers run separate instances and have their own filesystems. The script modifies the host FortiClient database and requires direct access to `/var/lib/forticlient/`.

### Q: What about AppArmor/SELinux restrictions?

**A:** The script requires direct file and service access, which may be blocked by AppArmor or SELinux.

If you see permission errors:
1. Ensure you're using sudo
2. Check AppArmor status: `sudo aa-status`
3. Check SELinux status: `getenforce`
4. Temporarily disable for testing (if allowed): `sudo setenforce 0`

---

## Support Questions

### Q: Where do I report bugs or ask for help?

**A:** 
- **GitHub**: [forticlient-linux-ipsec-sso Issues](https://github.com/themetalleg/forticlient-linux-ipsec-sso/issues)
- **Fortinet Community**: [FortiClient Linux Forum](https://community.fortinet.com/support-forum-92/)
- **Official Fortinet support**: Contact your support channel (they may not support this unofficial workaround, but they might have alternatives)

When reporting issues:
- Include the error message and output
- Describe your environment (OS, FortiClient version)
- Do NOT include credentials, keys, passwords, or actual configuration
- Do NOT include your real database or backup files

### Q: Will this be officially supported by Fortinet?

**A:** Unknown. This workaround may eventually be incorporated into FortiClient or an official solution may be released. Check with Fortinet for official alternatives.

### Q: Can I modify the script for my needs?

**A:** Yes, it's open-source (see LICENSE). However:
- Make sure your modifications don't introduce security issues
- Test thoroughly before using
- Consider contributing improvements back to the project

---

## Legal and Licensing

### Q: What's the license?

**A:** See [LICENSE](../LICENSE) file. Generally, this is provided as-is for community use.

### Q: Can I use this commercially?

**A:** Depends on the license. Check [LICENSE](../LICENSE) for specific terms.

### Q: Is there a warranty?

**A:** No. This is provided as-is without warranty. Use at your own risk.

### Q: Can I distribute this?

**A:** Yes, as long as you comply with the license terms.

---

**Have another question?** Please open an issue on GitHub or check the [Detailed Guide](./GUIDE.md) and [Script Documentation](./SCRIPT.md).

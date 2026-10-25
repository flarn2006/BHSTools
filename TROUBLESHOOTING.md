# Troubleshooting

## Getting rid of a "CF" / "CH" communication trouble and the ~24-hour beep

A very common situation on these panels: the monitoring service (Brinks/ADT/etc.) has been
discontinued, but the panel is still configured to report to a central station. The
communicator can no longer reach the host, so the panel raises a **communication-failure
trouble** — shown as **CF** or **CH** on the keypad — and **re-annunciates it about every
24 hours**. Pressing CANCEL silences it for the day, but it keeps coming back.

**The step most people miss is the power-cycle at the end.** Removing or disabling the
communicator in the configuration is not enough on its own — the panel's *live* trouble
monitoring doesn't re-evaluate until it restarts. Until then the keypad keeps showing the
trouble and CANCEL won't make it stick (a failed/disabled communicator never sends an
"all-OK," so the panel keeps the trouble "active").

### Procedure

1. **See what's configured.** Download the configuration and look at the Communicator
   (`0xC9`) and Device (`0xD3`) records — e.g. with `download.py` (see below) or the
   "Download Programming" button in `s3121.py`. Note which communicator(s) are set to
   report (a phone dialer, a cellular "GSM Gateway", an IP module, etc.).

2. **Stop the reporting.** Either is fine:
   - *Preferred, fully reversible* — in programming, go to **Comm/Pager → [comm #]** and set
     **Comm Enable = No** (and/or **Test Report Enable = No**).
   - *Direct from the bus* — delete the communicator:
     `./command.py <port> 401 <comm#>`
   - If a **physical** communicator module (e.g. a cellular gateway) keeps reporting on the
     bus even after the comm config is removed, also delete its device:
     `./command.py <port> 411 <device#>`

3. **For a "CH" trouble specifically**, try this first — it's zero-risk and reversible:
   ```
   ./command.py <port> 6 00000000
   ```
   This clears a host panel ID that a remote host may have loaded into the configuration
   (command `6` ACKs with command `7`). Note: on at least one BHS-4000A the panel ID at
   panel-config offset `0x22` is already `00 00 00 00` (with `FF FF FF FF` at `0x26`), in
   which case this is a no-op and the cause is an active communicator as above. If your CH
   persists and you suspect the ID is 8 bytes, the byte range after `0x22` is worth
   investigating.

4. **Power-cycle the panel.** Disconnect **both** the AC transformer **and** the backup
   battery, wait ~30 seconds, then reconnect (AC, then battery). This is what makes the
   configuration change take effect and clears the latched trouble.

5. **Verify.** The panel status should come back clean:
   ```
   ./command.py <port> 700        # expect:  00 00   (no trouble)
   ```
   The keypad should show the time and "Ready" with no TROUBLE.

### Two things to watch after the power-cycle
- **Old backup battery.** On an older panel the battery may be well past its 3–5 year life
  and show up as a new *low-battery* trouble after the reboot. Worth replacing anyway.
- **Clock reset.** The power-cycle resets the clock; set it back with
  `./command.py <port> 1002`.

---

## Programmer emulator (`s3121.py`) quirks

If the on-screen programmer won't cooperate:

- **Blank display on connect** → press **ESC** a few times to wake it.
- **Buttons seem dead / menus don't respond** → the panel can get stuck holding a previous
  programmer session. This often happens if `s3121.py` was restarted while a session was
  live: the panel keeps the old (dead) session and stops talking to the programmer address,
  so nothing you press registers. **Power-cycle the panel** (or wait for the session to time
  out) and reconnect fresh.
- **Entering the access code** → send it as a **quick burst**. Typed slowly, the entry
  buffer times out and resets between digits. Code entry is masked, so the cursor won't
  move — judge success by the screen changing, not by the cursor.
- **Scripting keystrokes over HTTP** → the `/key` endpoint reads the raw request body, so
  post it as `Content-Type: text/plain`. A form-encoded POST (`application/x-www-form-
  urlencoded`, which is `curl --data`'s default) arrives empty and registers as a null key.

---

## Recovering the installer/access code without the browser

You don't need the on-screen programmer to get your installer code — the configuration
download includes it. `download.py` performs the download headlessly and prints the code:

```
./download.py <port> [output_prefix]
```

It impersonates the S3121 programmer, asks the panel to upload every configuration record,
recovers the installer code, and (optionally) writes a hexdump report plus a raw file. It
**retransmits through dropped frames**, which matters on a marginal 2-wire (D+/D-) link —
where the one-shot web download can stall partway through — so it reliably pulls the full
record set.

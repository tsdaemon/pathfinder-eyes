# Upgrade system packages after SD card replacement

The Pi's 32GB SD card is nearly full (root partition at 100%, ~1.7GB free after clearing
pip/uv caches and old journal logs) — not enough for the pending apt upgrade (850 packages,
324 security updates, ~1 year backlog, needs ~2GB). A 128GB replacement card is on order.

Once migrated to the new card:

```bash
sudo apt update
sudo apt list --upgradable   # sanity check scope before committing
sudo apt upgrade             # or full-upgrade if it wants to remove/replace packages
```

Reboot afterward if a kernel package is included.

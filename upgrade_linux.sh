#!/bin/bash
# ============================================================
# TransitOps Fleet – Module Upgrade Script for Linux Odoo
# Run this ON the Linux server where Odoo is installed
# ============================================================

# Step 1: Find where Odoo custom addons are located
echo "=== Finding Odoo addons path ==="
find / -name "transitops_fleet" -type d 2>/dev/null

# Step 2: Find the Odoo config file
echo "=== Finding Odoo config ==="
find /etc /opt /home -name "*.conf" 2>/dev/null | xargs grep -l "addons_path" 2>/dev/null

# Step 3: Restart Odoo service after upgrade
# sudo systemctl restart odoo

# Step 4: Upgrade the module
# sudo -u odoo /usr/bin/odoo -c /etc/odoo/odoo.conf -d YOUR_DB_NAME -u transitops_fleet --stop-after-init

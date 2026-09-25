#!/bin/bash
set -e

sudo tee /etc/systemd/system/apix-pipeline.service > /dev/null << 'EOF'
[Unit]
Description=APIx Periodic Airfare Scraping and Index Calculation
After=network.target

[Service]
Type=oneshot
User=ec2-user
WorkingDirectory=/home/ec2-user/apix
ExecStart=/home/ec2-user/apix/.venv/bin/python /home/ec2-user/apix/scripts/run_daily_scrape.py
StandardOutput=journal
StandardError=journal
EOF

sudo tee /etc/systemd/system/apix-pipeline.timer > /dev/null << 'EOF'
[Unit]
Description=Run APIx Scraper and Index Engine at 8am, 2pm, 8pm IST
Requires=apix-pipeline.service

[Timer]
OnCalendar=*-*-* 08,14,20:00:00 Asia/Kolkata
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now apix-pipeline.timer
sudo systemctl list-timers apix-pipeline.timer --no-pager
echo APIx automated timer configured successfully!
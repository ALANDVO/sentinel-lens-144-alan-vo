#!/bin/bash
cd /var/lib/alan-portfolio/workspaces/alan/sentinel-lens-144-alan-vo/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

#!/bin/bash
set -e

echo "آپدیت pip و نصب پکیج‌ها..."
python -m pip install --upgrade pip setuptools wheel

echo "نصب requirements.txt..."
pip install -r requirements.txt

echo "بیلد تموم شد! Dragonfly داره پرواز می‌کنه"
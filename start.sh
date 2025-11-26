#!/bin/bash
pip install -r requirements.txt --no-cache-dir
ollama serve & sleep 8
ollama pull phi3:mini
python main.py
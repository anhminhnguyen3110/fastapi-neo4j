#!/bin/bash

source .venv/Scripts/activate
uvicorn app.main:app --host localhost --port 8001

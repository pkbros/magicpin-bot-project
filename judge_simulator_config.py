#!/usr/bin/env python3
"""
magicpin AI Challenge — LLM-Powered Judge Simulator
====================================================
"""

import os
import sys
import json
import time
import re
import socket
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from urllib import request as urlrequest, error as urlerror
from abc import ABC, abstractmethod

# Attempt to load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# ██████  CONFIGURATION - EDIT THIS SECTION ██████
# =============================================================================

# Your bot's URL (where your bot is running)
BOT_URL = os.environ.get("BOT_URL", "http://localhost:8083")

# FORCE JUDGE TO USE GEMINI TO AVOID RATE LIMITS WITH BOT
LLM_PROVIDER = "gemini" 

# Your API key
LLM_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Model to use
LLM_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

# Which test to run by default
TEST_SCENARIO = os.environ.get("TEST_SCENARIO", "full_evaluation")

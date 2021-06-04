from pathlib import Path

def is_utf(fname):
   return fname == fname.encode('ascii', 'replace').decode("utf-8")
  
import unicodedata
norm_form, other_form = 'NFC', 'NFD'

import filecmp


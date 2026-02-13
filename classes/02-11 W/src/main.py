import sys
from pathlib import Path

print(file__file__)

print(Path(__file__).resolve())

'''

ROOT = Path(__file__).resolve().parents[1]   # lesson_root/
sys.path.insert(0, str(ROOT))

from packages import utils
'''
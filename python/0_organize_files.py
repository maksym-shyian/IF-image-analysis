import os
import re
import shutil

pattern = re.compile(r"(.+?)_(\d{3})(?:_|\.|$)")

for filename in os.listdir("."):
    if not os.path.isfile(filename):
        continue

    match = pattern.search(filename)
    if not match:
        continue

    prefix, num = match.groups()

    folder_name = f"{prefix}_{num}_(analysis)"
    os.makedirs(folder_name, exist_ok=True)

    shutil.move(filename, os.path.join(folder_name, filename))

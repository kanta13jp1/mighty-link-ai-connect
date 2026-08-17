import requests
import os
import sys

user = "admin"
pwd = "mighty-link-pass"

resp = requests.get("https://mightylink-app.com/", auth=(user, pwd), timeout=30)
print(f"Status Code: {resp.status_code}")
if resp.status_code == 200:
    print(f"Length: {len(resp.text)}")
    print("Contains '研修ガイド':", "研修ガイド" in resp.text)
    print("Contains 'Mighty Skill-Bridge':", "Mighty Skill-Bridge" in resp.text)

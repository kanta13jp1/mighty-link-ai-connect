"""Update index.html and src/index.html to reflect 694 emails and 2026-09-02 arrivals."""

from pathlib import Path

def update():
    for path_str in ['index.html', 'src/index.html']:
        p = Path(path_str)
        if not p.exists():
            continue
        c = p.read_text(encoding='utf-8')
        c = c.replace('691件全件解析', '694件全件解析')
        c = c.replace('691件の営業メール', '694件の営業メール')
        c = c.replace('691 <small>件</small>', '694 <small>件</small>')
        c = c.replace('total_count: 691', 'total_count: 694')
        c = c.replace('"2026-07-25": 11,', '"2026-09-02": 3,\n                "2026-07-25": 11,')
        p.write_text(c, encoding='utf-8')
        print(f'[+] Updated {path_str} to 694 items.')

if __name__ == '__main__':
    update()

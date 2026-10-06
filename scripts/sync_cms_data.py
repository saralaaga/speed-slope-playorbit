#!/usr/bin/env python3
"""Split the legacy SpeedSlope JSON files into Git-backed CMS data files."""
import json
import os
import pathlib
import re


def _write_file(target, data, mode=0o644):
    """Write bytes to an already-validated path, confined by dir_fd so even
    a swapped parent directory cannot redirect the write."""
    dir_fd = os.open(target.parent, os.O_RDONLY)
    try:
        fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode, dir_fd=dir_fd)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    finally:
        os.close(dir_fd)



BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMS = os.path.join(BASE, 'cms-data')


def read_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def write_json(path, data):
    cms_root = pathlib.Path(CMS).resolve()
    target = pathlib.Path(path).resolve()
    target.relative_to(cms_root)
    os.makedirs(target.parent, exist_ok=True)
    _write_file(target, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def pair_list(items, first, second):
    result = []
    for item in items or []:
        if isinstance(item, dict):
            result.append({first: item.get(first, ''), second: item.get(second, '')})
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            result.append({first: item[0], second: item[1]})
    return result


def title_case(slug):
    return ' '.join(part.capitalize() for part in slug.split('-'))


def clean_dir(path):
    os.makedirs(path, exist_ok=True)
    for name in os.listdir(path):
        if name.endswith('.json'):
            os.remove(os.path.join(path, name))


def main():
    games = read_json(os.path.join(BASE, 'games_data.json'))
    site = read_json(os.path.join(BASE, 'site_config.json'))

    games_dir = os.path.join(CMS, 'games')
    categories_dir = os.path.join(CMS, 'categories')
    sites_dir = os.path.join(CMS, 'sites')
    clean_dir(games_dir)
    clean_dir(categories_dir)
    os.makedirs(sites_dir, exist_ok=True)

    site_data = dict(site)
    site_data.setdefault('slug', 'speedslope-net')
    site_data.setdefault('domain', re.sub(r'^https?://', '', site.get('site_url', '')).strip('/'))
    write_json(os.path.join(sites_dir, 'speedslope-net.json'), site_data)

    categories = sorted({cat for game in games for cat in game.get('cats', [])})
    for cat in categories:
        write_json(os.path.join(categories_dir, f'{cat}.json'), {
            'slug': cat,
            'name': title_case(cat),
            'active': True,
        })

    for index, game in enumerate(games):
        data = dict(game)
        data['sort_order'] = index
        data['controls'] = pair_list(game.get('controls'), 'key', 'action')
        data['faqs'] = pair_list(game.get('faqs'), 'question', 'answer')
        write_json(os.path.join(games_dir, f'{game["slug"]}.json'), data)

    print(f'Wrote {len(games)} games, {len(categories)} categories, and 1 site to cms-data/')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Generate sample data in Neo4j, create an embed URL via the app, open the embed view in a headless browser and capture a high-resolution full-graph PNG.

Usage:
  python scripts/generate_and_capture.py --persons 200 --movies 50 --edges 400 --out graph_full.png --host 127.0.0.1 --port 8003

Requirements:
  pip install neo4j requests playwright
  python -m playwright install chromium

This script is intentionally self-contained and uses the Bolt driver to write data and Playwright to capture a canvas export at a high pixel density.

"""

import os
import sys
import argparse
import base64
import time
import json
import random
from typing import List

try:
    from neo4j import GraphDatabase
except Exception:
    print("Missing 'neo4j' driver. Install with: pip install neo4j")
    raise

try:
    import requests
except Exception:
    print("Missing 'requests'. Install with: pip install requests")
    raise

# Playwright import delayed so we can give actionable error if missing


def bulk_create(tx, persons, movies, relationships):
    # Create persons and movies with UNWIND for efficiency
    tx.run("""
    UNWIND $persons AS p
    MERGE (pp:Person {idx: p.idx})
    SET pp.name = p.name
    """, persons=persons)

    tx.run("""
    UNWIND $movies AS m
    MERGE (mm:Movie {idx: m.idx})
    SET mm.title = m.title
    """, movies=movies)

    # Create relationships
    tx.run("""
    UNWIND $rels AS r
    MATCH (p:Person {idx: r.pidx}), (m:Movie {idx: r.midx})
    MERGE (p)-[rel:ACTED_IN {rel_idx: r.idx}]->(m)
    SET rel.role = r.role
    """, rels=relationships)


def generate_sample(person_count=200, movie_count=50, edge_count=400):
    persons = [{'idx': i, 'name': f'Person {i}'} for i in range(1, person_count + 1)]
    movies = [{'idx': i, 'title': f'Movie {i}'} for i in range(1, movie_count + 1)]

    relationships = []
    for i in range(1, edge_count + 1):
        p = random.randint(1, person_count)
        m = random.randint(1, movie_count)
        relationships.append({'idx': i, 'pidx': p, 'midx': m, 'role': random.choice(['Actor','Cameo','Guest'])})

    return persons, movies, relationships


def write_data_to_neo4j(uri, user, password, persons, movies, relationships):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Support both older and newer neo4j driver transaction APIs
        try:
            # older drivers
            session.write_transaction(bulk_create, persons, movies, relationships)
        except AttributeError:
            # neo4j v5+: use execute_write
            session.execute_write(bulk_create, persons, movies, relationships)
    driver.close()


def create_embed(api_host, api_port, cypher_query, expires_in_days=7):
    url = f"http://{api_host}:{api_port}/api/embed"
    payload = {'cypherQuery': cypher_query, 'expiresInDays': expires_in_days}
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data.get('success'):
        raise RuntimeError(f"Failed to create embed: {data}")
    embed = data['data']
    # The API's embedUrl may point to a different base; construct local view URL to be safe
    token = embed['embedToken']
    view_url = f"http://{api_host}:{api_port}/view/{token}"
    return token, view_url


def capture_full_graph(view_url, out_path, wait_seconds=4, width=3840, height=2160, device_scale=2):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("Missing 'playwright'. Install with: pip install playwright and run 'playwright install chromium'")
        raise

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        context = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=device_scale)
        page = context.new_page()
        print(f"Opening {view_url} ...")
        page.goto(view_url, wait_until='networkidle')

        # Wait for loading to disappear or error
        try:
            page.wait_for_selector('#loading', state='hidden', timeout=15000)
        except Exception:
            print('Warning: loading spinner did not disappear within timeout')

        # Ensure no error shown
        if page.is_visible('#error'):
            err = page.locator('#error-message').inner_text()
            raise RuntimeError(f"Embed page error: {err}")

        # Expand the viz container to a large size to get more detail (vis will redraw)
        print('Expanding viz container and asking network to fit/redraw...')
        # Use a single argument object for evaluate (Playwright Python expects 2 args max)
        page.evaluate(
            """
            (args) => {
                const w = args.w, h = args.h;
                const c = document.getElementById('viz');
                if (!c) return;
                c.style.width = w + 'px';
                c.style.height = h + 'px';
                const ev = new Event('resize');
                window.dispatchEvent(ev);
                // try to call network.fit if available
                if (window.network && typeof window.network.fit === 'function') {
                    try { window.network.fit({animation:false}); } catch(e) { /* ignore */ }
                    if (typeof window.network.stabilize === 'function') {
                        try { window.network.stabilize(); } catch(e) { /* ignore */ }
                    }
                }
            }
            """,
            {"w": width * device_scale, "h": height * device_scale},
        )

        time.sleep(wait_seconds)

        # Grab the canvas data URL (high-resolution) and save
        print('Extracting canvas data URL...')
        data_url = page.evaluate('''() => {
            try {
                const canvas = document.getElementById('viz').getElementsByTagName('canvas')[0];
                if (!canvas) return null;
                return canvas.toDataURL('image/png');
            } catch (e) { return null; }
        }''')

        if data_url:
            _, b64 = data_url.split(',', 1)
            img = base64.b64decode(b64)
            with open(out_path, 'wb') as f:
                f.write(img)
            print(f'Saved full-graph PNG to {out_path} ({len(img)} bytes)')
        else:
            # fallback: full page screenshot
            print('Canvas not available; falling back to full page screenshot')
            page.screenshot(path=out_path, full_page=True)
            print(f'Saved full-page PNG to {out_path}')

        context.close()
        browser.close()


def main(argv: List[str]):
    parser = argparse.ArgumentParser(description='Populate Neo4j and capture embed screenshot')
    parser.add_argument('--persons', type=int, default=200)
    parser.add_argument('--movies', type=int, default=50)
    parser.add_argument('--edges', type=int, default=400)
    parser.add_argument('--out', type=str, default='graph_full.png')
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8003)
    parser.add_argument('--neo-uri', type=str, default=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'))
    parser.add_argument('--neo-user', type=str, default=os.environ.get('NEO4J_USER', 'neo4j'))
    parser.add_argument('--neo-pass', type=str, default=os.environ.get('NEO4J_PASSWORD', 'neo4j_password'))
    parser.add_argument('--wait', type=int, default=4, help='Seconds to wait after redraw before capture')
    args = parser.parse_args(argv)

    print('Generating sample data...')
    persons, movies, relationships = generate_sample(args.persons, args.movies, args.edges)
    print(f'Persons: {len(persons)}, Movies: {len(movies)}, Relationships: {len(relationships)}')

    print('Writing data to Neo4j...')
    write_data_to_neo4j(args.neo_uri, args.neo_user, args.neo_pass, persons, movies, relationships)
    print('Data written to Neo4j')

    # Create embed
    cypher = 'MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN p,r,m LIMIT 1000'
    print('Creating embed token...')
    token, view_url = create_embed(args.host, args.port, cypher)
    print('Embed token:', token)
    print('View URL:', view_url)

    # Capture full graph
    capture_full_graph(view_url, args.out, wait_seconds=args.wait, width=3840, height=2160, device_scale=2)


if __name__ == '__main__':
    main(sys.argv[1:])

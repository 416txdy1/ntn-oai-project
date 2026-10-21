"""Loopback-only telemetry server or unprivileged visible Playwright browser."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import time


def serve(run,output):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/state':
                try:data=json.loads((run/'state.json').read_text())
                except (FileNotFoundError,ValueError):data={}
                data['server_monotonic_ns']=time.monotonic_ns()
                body=json.dumps(data).encode();kind='application/json'
            elif self.path=='/':
                body=Path(__file__).with_name('player.html').read_bytes();kind='text/html; charset=utf-8'
            elif self.path=='/font':
                body=Path('/home/kayoko/ntn-live-demo-tools/fonts/NotoSansCJKsc-Regular.otf').read_bytes();kind='font/otf'
            elif self.path=='/dashboard.js':
                body=Path(__file__).with_name('dashboard.js').read_bytes();kind='text/javascript; charset=utf-8'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_POST(self):
            if self.path!='/metrics':self.send_error(404);return
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<100000:self.send_error(400);return
            try:row=json.loads(self.rfile.read(size))
            except ValueError:self.send_error(400);return
            row['host_receive_monotonic_ns']=time.monotonic_ns()
            with (output/'browser-events.jsonl').open('a') as stream:stream.write(json.dumps(row,separators=(',',':'))+'\n')
            self.send_response(204);self.end_headers()
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()


def browser(run,headless):
    if os.geteuid()==0:raise RuntimeError('Browser must run as ordinary user')
    from playwright.sync_api import sync_playwright
    running=True
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=headless,chromium_sandbox=True,ignore_default_args=['--mute-audio'],
            args=['--autoplay-policy=no-user-gesture-required','--disable-background-timer-throttling',
                  '--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows',
                  '--disable-features=AudioServiceOutOfProcess'])
        page=browser.new_page(viewport={'width':1160,'height':850})
        page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded',timeout=30000)
        next_shot=time.monotonic()+10;number=0
        while running:
            if time.monotonic()>=next_shot:
                number+=1;page.screenshot(path=str(run/f'player-{number:03d}.png'))
                next_shot=time.monotonic()+20
            page.wait_for_timeout(200)
        page.screenshot(path=str(run/'player-final.png'))
        browser.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['serve','browser'])
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path)
    parser.add_argument('--headless',action='store_true');args=parser.parse_args()
    if args.action=='serve':serve(args.run,args.output)
    else:browser(args.run,args.headless)

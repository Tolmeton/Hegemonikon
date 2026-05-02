#!/usr/bin/env python3
import asyncio
import logging
import sys
from aiohttp import web
import hpack

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

async def handle_request(request: web.Request):
    logging.info(f"Incoming connection: {request.method} {request.path}")
    logging.info("Headers:")
    for k, v in request.headers.items():
        logging.info(f"  {k}: {v}")
    
    body = await request.read()
    logging.info(f"Body length: {len(body)} bytes")
    if len(body) > 0:
        logging.info(f"Body hex: {body.hex()}")
        # try to decode proto (just printable chars)
        printable = ''.join(chr(c) if 32 <= c <= 126 else '.' for c in body)
        logging.info(f"Body text: {printable}")
    
    # 501 Not Implemented を返して LS の挙動（リトライかパニックか）を観察
    return web.Response(status=501, text="Not Implemented")

app = web.Application()
# キャッチオール
app.router.add_route('*', '/{tail:.*}', handle_request)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 36989
    logging.info(f"Starting fake extension server on port {port}...")
    web.run_app(app, port=port)

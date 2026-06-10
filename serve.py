import http.server, socketserver, os, sys
# absolute chdir first (avoids os.getcwd at import that the sandbox blocks)
os.chdir('/Users/azakee007/Documents/GitHub/FIFA 2026 WC/wc_site')
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', port), http.server.SimpleHTTPRequestHandler) as httpd:
    httpd.serve_forever()

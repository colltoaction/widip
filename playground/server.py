
import http.server
import socketserver
import subprocess
import json
import os
import urllib.parse

PORT = 8000
PARSER_BIN = "./bin/yaml/parse"

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/parse':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            yaml_content = post_data.decode('utf-8')
            
            try:
                # Run the parser
                process = subprocess.Popen(
                    [PARSER_BIN],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=yaml_content)
                
                response = {
                    'success': process.returncode == 0,
                    'stdout': stdout,
                    'stderr': stderr
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path == '/':
            self.path = '/playground/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()

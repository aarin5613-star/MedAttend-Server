import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import uuid
import os

STUDENTS_FILE = 'students.json'
SETTINGS_FILE = 'settings.json'

def load_data(filepath, default_value):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return default_value

def save_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f)

# In-memory database
students = load_data(STUDENTS_FILE, [])
campus_location = None
class_settings = load_data(SETTINGS_FILE, {
    "subject": "Anatomy 101",
    "professor": "Dr. Suresh",
    "time": "10:00 AM - 11:00 AM"
})

class SimpleRESTHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        # Allow CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_OPTIONS(self):
        self._set_headers()
        
    def do_GET(self):
        global campus_location, class_settings
        if self.path == '/api/students':
            self._set_headers()
            self.wfile.write(json.dumps(students).encode())
        elif self.path == '/api/settings/location':
            self._set_headers()
            self.wfile.write(json.dumps(campus_location or {}).encode())
        elif self.path == '/api/settings/class':
            self._set_headers()
            self.wfile.write(json.dumps(class_settings).encode())
        else:
            self.send_response(404)
            self.end_headers()
            
    def do_POST(self):
        global campus_location, class_settings
        if self.path == '/api/students':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            new_student = json.loads(post_data)
            
            if 'id' not in new_student:
                new_student['id'] = str(uuid.uuid4())
                
            students.append(new_student)
            save_data(STUDENTS_FILE, students)
            self._set_headers()
            self.wfile.write(json.dumps(new_student).encode())
            
        elif self.path.startswith('/api/students/') and '/checkin' in self.path:
            student_id = self.path.split('/')[3]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            checkin_data = json.loads(post_data)
            
            for s in students:
                if s.get('id') == student_id:
                    s['isPresent'] = True
                    s['checkInTime'] = checkin_data.get('time', 'Unknown')
                    break
            
            save_data(STUDENTS_FILE, students)
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        elif self.path == '/api/settings/location':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            campus_location = json.loads(post_data)
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        elif self.path == '/api/settings/class':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            class_settings = json.loads(post_data)
            print("Updated Class Settings:", class_settings)
            
            # Reset attendance for all students for the new class session!
            for student in students:
                student['isPresent'] = False
                student['checkInTime'] = None
                
            save_data(STUDENTS_FILE, students)
            save_data(SETTINGS_FILE, class_settings)
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        elif self.path == '/api/settings/clear':
            students.clear()
            save_data(STUDENTS_FILE, students)
            print("Database completely cleared!")
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())
            
        else:
            self.send_response(404)
            self.end_headers()

import os

def run(server_class=HTTPServer, handler_class=SimpleRESTHandler):
    port = int(os.environ.get("PORT", 8080))
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting API Server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

import os
import multiprocessing

# Bind a la dirección que Railway espera
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Workers y threads
workers = 2
threads = 2
worker_class = "sync"

# Timeouts
timeout = 120
graceful_timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True

# Process naming
proc_name = "backend_taller"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Debugging
reload = False

print(f"Gunicorn config loaded - binding to {bind}")

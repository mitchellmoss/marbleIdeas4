from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from server_production import app as main_app
from admin_panel import app as admin_app

# Create a dispatcher app
app = DispatcherMiddleware(main_app, {
    '/admin': admin_app
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 8000, app, use_reloader=True, use_debugger=True)
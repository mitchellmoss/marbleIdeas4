from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import plotly.graph_objs as go
import plotly.utils
import json
import os
from log_parser import parse_logs, get_event_counts, get_page_views, get_time_series_data, get_user_agents, get_scroll_depth_distribution, get_marble_clicks, get_route_travels
import glob
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'fallback_secret_key')  # Set a secret key for sessions
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'fallback_password')  # Get admin password from environment variable

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            app.logger.debug(f"Session after login: {session}")
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    print("Parsing logs...")
    df = parse_logs()
    
    if df.empty:
        return "No data found in log files. Please check the log file format and contents."

    print("Generating graphs...")
    
    # Event Counts
    event_counts = get_event_counts(df)
    event_pie = go.Pie(labels=list(event_counts.keys()), values=list(event_counts.values()))
    event_pie_json = json.dumps(event_pie, cls=plotly.utils.PlotlyJSONEncoder)
    
    
    # Page Views
    page_views = get_page_views(df)
    page_bar = go.Bar(x=list(page_views.keys()), y=list(page_views.values()))
    page_bar_json = json.dumps(page_bar, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Time Series Data
    time_series_data = get_time_series_data(df)
    if time_series_data:
        time_series = go.Scatter(
            x=[d.get('timestamp') for d in time_series_data],
            y=[d.get('pageview', 0) for d in time_series_data],
            mode='lines+markers',
            name='Page Views'
        )
        time_series_json = json.dumps(time_series, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        time_series_json = json.dumps({})
    
    # User Agents
    user_agents = get_user_agents(df)
    user_agents_bar = go.Bar(x=list(user_agents.keys()), y=list(user_agents.values()))
    user_agents_bar_json = json.dumps(user_agents_bar, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Scroll Depth Distribution
    scroll_depth = get_scroll_depth_distribution(df)
    if scroll_depth:
        scroll_depth_box = go.Box(y=list(scroll_depth.values()))
        scroll_depth_box_json = json.dumps(scroll_depth_box, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        scroll_depth_box_json = json.dumps({})
    
    # Marble Clicks
    marble_clicks = get_marble_clicks(df)
    marble_clicks_json = json.dumps(marble_clicks, cls=plotly.utils.PlotlyJSONEncoder)

    # Route Travels
    route_travels = get_route_travels(df)
    route_travels_json = json.dumps(route_travels, cls=plotly.utils.PlotlyJSONEncoder)

    print("Rendering template...")
    return render_template('admin_dashboard.html',
                           event_pie=event_pie_json,
                           page_bar=page_bar_json,
                           time_series=time_series_json,
                           user_agents_bar=user_agents_bar_json,
                           scroll_depth_box=scroll_depth_box_json,
                           scroll_depth_stats=json.dumps(scroll_depth),
                           marble_clicks=marble_clicks_json,
                           route_travels=route_travels_json)

@app.route('/raw_logs')
def raw_logs():
    app.logger.debug("Entering raw_logs route")
    if not session.get('logged_in'):
        app.logger.debug("User not logged in")
        return jsonify({'error': 'Unauthorized'}), 401

    app.logger.debug("User is logged in, processing log files")
    log_files = glob.glob('marble_gallery.log*')
    app.logger.debug(f"Found {len(log_files)} log files")
    logs = []

    for log_file in sorted(log_files, reverse=True):
        app.logger.debug(f"Processing log file: {log_file}")
        with open(log_file, 'r') as f:
            for line in f:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    timestamp_str, log_data = parts
                    try:
                        timestamp = datetime.strptime(timestamp_str.strip(), '%Y-%m-%d %H:%M:%S')
                        log_dict = {'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'data': log_data.strip()}
                        logs.append(log_dict)
                    except ValueError:
                        app.logger.error(f"Error parsing timestamp: {timestamp_str}")
                        continue

    app.logger.debug(f"Returning {len(logs)} log entries")
    return jsonify(logs[:1000])  # Return the latest 1000 log entries

@app.route('/log_event', methods=['POST'])
def log_event():
    data = request.json
    event_type = data.get('event_type')
    event_data = data.get('data')

    # Log the event
    app.logger.info(f"Event: {event_type}, Data: {event_data}")

    return jsonify({'status': 'success'})

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error and stacktrace
    app.logger.error('An error occurred during request', exc_info=True)
    # Return a custom error page
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
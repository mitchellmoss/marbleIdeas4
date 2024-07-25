import glob
import os
import pandas as pd
from datetime import datetime

def parse_logs():
    log_files = glob.glob('marble_gallery.log*')
    data = []

    print(f"Current working directory: {os.getcwd()}")
    print(f"Found {len(log_files)} log files")
    if not log_files:
        print("No log files found. Check the file path and naming convention.")
        return pd.DataFrame()

    for log_file in log_files:
        print(f"Parsing file: {log_file}")
        try:
            with open(log_file, 'r') as f:
                print(f"Successfully opened {log_file}")
                for line_num, line in enumerate(f, 1):
                    print(f"Line {line_num}: {line.strip()}")
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        timestamp_str, log_data = parts
                        try:
                            timestamp = datetime.strptime(timestamp_str.strip(), '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            print(f"Error parsing timestamp in file {log_file}, line {line_num}: {timestamp_str}")
                            continue
                        
                        # Parse log data
                        log_dict = {'timestamp': timestamp}
                        log_parts = log_data.split('[in')
                        if len(log_parts) > 1:
                            log_data = log_parts[0].strip()
                        for item in log_data.split(', '):
                            if ': ' in item:
                                key, value = item.split(': ', 1)
                                log_dict[key.strip()] = value.strip()
                            else:
                                print(f"Unexpected format in file {log_file}, line {line_num}: {item}")
                        
                        data.append(log_dict)
                    else:
                        print(f"Unexpected line format in file {log_file}, line {line_num}: {line}")
        except IOError as e:
            print(f"Error opening file {log_file}: {e}")

    df = pd.DataFrame(data)
    print(f"Parsed {len(df)} log entries")
    print(f"Columns in DataFrame: {df.columns.tolist()}")
    if not df.empty:
        print("First row of DataFrame:")
        print(df.iloc[0])
    else:
        print("No data was parsed from the log files.")
    return df

def get_event_counts(df):
    return df['Event'].value_counts().to_dict()

def get_marble_clicks(df):
    marble_clicks = df[df['Event'] == 'marble_click']['Marble Name'].value_counts().to_dict()
    return {'x': list(marble_clicks.keys()), 'y': list(marble_clicks.values()), 'type': 'bar'}

def get_route_travels(df):
    route_travels = df[df['Event'] == 'route_travel']['Page'].value_counts().to_dict()
    return {'x': list(route_travels.keys()), 'y': list(route_travels.values()), 'type': 'bar'}

def get_page_views(df):
    if 'Page' not in df.columns or 'Event' not in df.columns:
        print("Warning: 'Page' or 'Event' column not found in DataFrame")
        return {}
    return df[df['Event'] == 'pageview']['Page'].value_counts().to_dict()

def get_time_series_data(df):
    if 'timestamp' not in df.columns or 'Event' not in df.columns:
        print("Warning: 'timestamp' or 'Event' column not found in DataFrame")
        return []
    df_grouped = df.groupby([df['timestamp'].dt.date, 'Event']).size().unstack(fill_value=0)
    return df_grouped.reset_index().to_dict('records')

def get_user_agents(df):
    if 'User-Agent' not in df.columns:
        print("Warning: 'User-Agent' column not found in DataFrame")
        return {}
    return df['User-Agent'].value_counts().head(5).to_dict()

def get_scroll_depth_distribution(df):
    if 'Scroll Depth' not in df.columns:
        print("Warning: 'Scroll Depth' column not found in DataFrame")
        return {}
    scroll_depth = df['Scroll Depth'].copy()
    scroll_depth = scroll_depth[scroll_depth != 'NaN']
    scroll_depth = pd.to_numeric(scroll_depth, errors='coerce')
    scroll_depth = scroll_depth.dropna()
    return scroll_depth.describe().to_dict()
from datetime import datetime

timestamp = 1674193043842

# Convert timestamp to datetime object
date_time = datetime.fromtimestamp(timestamp/1000)

# Use strftime to format the datetime object
formatted_time = date_time.strftime("%d.%m %H:%M")

print(formatted_time)
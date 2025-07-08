# PCS Automatic Updates

## Overview
The Flask application now includes automatic daily updates of PCS points at 2:00 AM.

## Features

### 1. Automatic Daily Updates
- Updates run every day at 2:00 AM automatically
- No cron job configuration needed
- Works on any server (DigitalOcean, Render, etc.)

### 2. Manual Update API
Trigger update manually:
```bash
curl -X POST http://your-server:8086/api/update-pcs-points
```

### 3. Check Update Status
```bash
curl http://your-server:8086/api/update-status
```

Response:
```json
{
  "success": true,
  "last_update": {
    "time": "2025-01-08 12:30:56",
    "updated_riders": 183,
    "total_riders": 184
  },
  "next_scheduled_update": "02:00 AM daily"
}
```

## How It Works

1. **Background Thread**: Runs scheduled tasks without blocking the main app
2. **PCS Scraping**: Fetches top 2000 riders from ProCyclingStats 
3. **Smart Updates**: Only updates changed values
4. **Value Recalculation**: Updates points_per_credit and value_category

## Deployment

### DigitalOcean
1. Deploy the updated app.py
2. Install requirements: `pip install -r requirements.txt`
3. Restart the application
4. Updates will run automatically

### Testing
```bash
# Test locally
python test_update_api.py

# Test on server
curl -X POST http://your-server:8086/api/update-pcs-points
```

## Monitoring
- Check logs for update status
- Use `/api/update-status` endpoint
- Updates are logged with timestamp and rider count

## No Additional Configuration Needed!
Just deploy and it works. No cron jobs, no systemd timers, no external setup.
# CCIE Study Tracker App

Simple study tracker written in Flask. Specifically it was created for tracking CCIE topics but can be used for studies. This is a 80/20 Vibe coding project as I'm not this pro in Flask but needed a tool/app to track progress. 

## Features

- Track study items with details like 
   - Title
   - Notes
   - Hours spent
   - Progress
   - Confidence levels 
      - Theoretical
      - Practical 
- App password protection (optional)
- Sortable item list
- Search study items by title
- Bulk and selective delete operations
- Summary statistics (total items, hours, average progress)
- Bulk import from Excel. This feature was added just for importing the CCIE practical exam topics excel that is provided by the Cisco team. Unfortunately not all study tracks has the same file content structure.
- Calendar (which is the most  useful part) 
   - Key dates (exam, bootcamp, etc..) can be added to it and it shows on the main page and the remain days.
   - Shows the updates on the different topics
- Dark/light theme toggle
- Stats on learning progress

https://github.com/user-attachments/assets/c5ab42fe-9c7f-41aa-8eeb-075074183a59



## Install

1. Clone or download the project. ```git clone https://github.com/routingalchemy/CCIE_study_tracker```
2. Choose between native or docker run.
   - Native: Install dependencies into a virtual environment:
   ```bash
   cd CCIE_study_tracker
   python3 -m venv study_tracker
   source study_tracker/bin/activate
   pip install -r requirements.txt
   ```
   - Docker (working docker install)
   ```bash
   cd CCIE_study_tracker 
   docker build -t ccie_tracker .
   ```
3. The app will run on http://localhost:5000

## Configuration

Edit `config.py` or set environment variables:

- `ENABLE_PASSWORD_PROTECTION`: Enable/disable password protection (default: True)
- `APP_PASSWORD`: Set the password (default: 'admin')
- `SECRET_KEY`: Flask secret key (change in production)
- `DEBUG`: Enable debug mode (default: False)
- `DATABASE_PATH`: SQLite database path (default: 'study_tracker.db')
- `DEFAULT_THEME`: Default theme 'light' or 'dark' (default: 'light')

## Running the App

### Traditional Method (Local)


```bash
#activate virtual environment
python3 app.py
```

The app will run on http://localhost:5000

### Docker Deployment

 - build the image ``` docker build -t ccie_tracker . ```
 - simply running the container (for  environmental variables check docker compose file)
 ```bash
 docker run -d --name tracker -p 5000:5000  ccie_tracker:latest  #minimal run
 docker run -d --name tracker -p 5000:5000 -e  ENABLE_PASSWORD_PROTECTION=False ccie_tracker:latest  #no password authenticaltion
 docker run -d --name tracker -p 5000:5000 -e APP_PASSWORD=iamcciegod ccie_tracker:latest #set awesome password
 ```
 - or using docker compose 
```bash
#after editing the docker-compose.yml
docker-compose up -d
```

#### Environment Variables for Docker

- `SECRET_KEY`: Change to a secure random string for production
- `APP_PASSWORD`: Set your application password
- `ENABLE_PASSWORD_PROTECTION`: Set to 'false' to disable password protection
- `DEFAULT_THEME`: Set to 'light' or 'dark'
- `DEBUG` = Set Flask Debug mode
- `DATABASE_URL` = Set desired database to use (never tested, only used sqlite) 

## Bulk Import

The bulk import feature allows you to upload Excel files (.xlsx or .xls) and map columns to study item fields:

1. Click "Import" in the navigation
2. Upload an Excel file
3. **Select the worksheet** to import from (if the file has multiple sheets)
4. **Specify the row number** where your data starts (usually 2 if row 1 has headers)
5. **Map columns using Excel letters** (A, B, C, etc.) 
6. Multiple columns can be selected for Title and Notes - they will be concatenated
7. **Rows with empty titles will be skipped automatically**
8. The system handles missing data gracefully with sensible defaults



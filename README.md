# 🔑 K3Y Schedule Updater

A Python-based tool used to fetch, clean, and process SKCC K3Y event schedules.  
This project automates the extraction of time slots and prepares the data for analysis or publication.

---
## 📁 Project Structure

k3y-schedule-updater/   
│  
├── scraper.py # Main script that fetches and processes schedule data  
├── requirements.txt # Python dependencies  
├── README.md # Project documentation  
│  
└── data/  
└── schedule-cache.json # Cached schedule output  

## 🛠️ Setup

### Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

## 📜 Usage

Run the scraper:
```bash
python scraper.py
```

#### The script will:

- Fetch the latest K3Y schedule
- Process each operator's session times
- Save updates into `data/schedule-cache.json`

## 🧪 Development Notes

Python 3.10+ recommended

## 📄 License

MIT License. See LICENSE file if added.

## 🙏 Acknowledgments

This project supports SKCC operators during Straight Key Month and is part of ongoing work to help identify available K3Y operating sessions.
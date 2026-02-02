# Network Traffic Analyzer 📊

A professional Python tool for real-time network traffic monitoring, statistical analysis, and visualization. This project is designed for network diagnostics, link dimensioning (Busy Hour calculation), and traffic pattern recognition.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey)

## 📌 Key Features

* **Real-time Packet Sniffing:** Captures Ethernet/IP frames using raw sockets in promiscuous mode.
* **Statistical Analysis:** Calculates average throughput, standard deviation, and packet size distribution.
* **Busy Hour (GNR) Detection:** Algorithmic identification of the continuous 60-minute window with the highest traffic load – essential for proper network dimensioning.
* **Confidence Intervals:** Estimates the 95% confidence interval for mean traffic load to assess connection stability and filter out random outliers.
* **Data Visualization:** Generates comprehensive time-series plots using **Matplotlib**.
* **CSV Export:** Automatically logs captured data (`timestamp`, `src_ip`, `dst_ip`, `length`) to CSV files for further processing.

## 🛠️ Tech Stack

The project relies on the following technologies and libraries:

* **Python 3** (Core logic)
* **Pandas** (Data manipulation and time-series aggregation)
* **Matplotlib / Seaborn** (Data visualization)
* **Scapy / Sockets** (Network layer interaction)
* **SciPy / NumPy** (Statistical calculations)

## 📂 Project Structure

* `main.py`: The entry point of the application.
* `dokumentacja.pdf`: Full technical documentation of the project (in Polish).
* `intensywnosc_wywolan.txt`: Sample dataset representing call intensity.
* `czas_obslugi.txt`: Sample dataset representing service times.
* `icon.icns`: Application icon resources.

*(Note: Build artifacts like `dist/` and `build/` are excluded from the repository)*

## 🚀 Installation & Usage

### Prerequisites
* Python 3.8 or higher
* Administrative privileges (Root/Sudo) are required to access the network card in promiscuous mode.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/network-traffic-analyzer.git](https://github.com/YOUR_USERNAME/network-traffic-analyzer.git)
    cd network-traffic-analyzer
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the analyzer:**
    *Note: Sudo is required for raw socket access on macOS/Linux.*
    ```bash
    sudo python main.py
    ```

## 📊 Sample Output

### 1. Traffic Load Visualization & Busy Hour
The graph below demonstrates the daily traffic distribution with the identified "Busy Hour" marked, allowing for precise network capacity planning.

![Traffic Graph Example](graph_example.png)
*(Note: Place a screenshot of your graph in the project folder named `graph_example.png`)*

### 2. Data Structure (CSV)
The raw data is stored in a clean CSV format for easy parsing:
```csv
Timestamp, Source_IP, Dest_IP, Protocol, Length
1678886400, 192.168.1.15, 142.250.180.14, TCP, 1500
1678886401, 10.0.0.5, 192.168.1.1, UDP, 64
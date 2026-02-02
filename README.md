# Traffic Analyzer 📡

**Advanced Telecommunication Traffic Dimensioning Tool**

A desktop application designed to automate the analysis of telecommunication traffic and calculate the **Time Consistent Busy Hour (TCBH)** according to **ITU-T E.490/E.500** standards. The tool aids in network dimensioning by providing statistical reliability assessments (Confidence Intervals) and distinguishing between human (H2H) and machine (M2M) traffic.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![University](https://img.shields.io/badge/Wrocław%20University%20of%20Science%20and%20Technology-Pwr-red)

## 🎯 Project Purpose

In modern networks (GSM/LTE/5G/VoIP), dimensioning based on daily averages leads to errors, while dimensioning based on absolute yearly peaks is economically inefficient.

**Traffic Analyzer** solves this by:
* Aggregating measurement data from multiple days (CSV files).
* Calculating key engineering metrics: **TCBH** (Time Consistent Busy Hour), **ADPH**, and **FDMH**.
* Estimating measurement reliability using **Confidence Intervals** (t-Student distribution).
* Visualizing traffic profiles to identify anomalies.

## 🛠️ Key Features

### 1. Advanced TCBH Calculation (Sliding Window)
Unlike the simple "clock hour" method (FDMH), this application implements the **Time Consistent Busy Hour** method. It finds the continuous 60-minute window (sliding with 1-minute step) where the average traffic across N days is maximized.


$$TCBH_{val} = \max_{t \in \langle 0, 1380 \rangle} \left( \frac{1}{N} \sum_{d=1}^{N} A_d(t, t+60) \right)$$

### 2. Time Gating (H2H vs M2M)
The application allows users to define analysis timeframes (e.g., 8:00 AM – 4:00 PM). This "Time Gating" filters out artificial traffic peaks caused by automated nightly processes (machine traffic/backups), ensuring voice channels are dimensioned for actual human usage.

### 3. Statistical Reliability
Traffic is stochastic. The tool calculates the **95% Confidence Interval** for the TCBH using the **t-Student distribution**, allowing engineers to assess the risk of under-dimensioning.
* **Green Indicator:** Narrow interval, stable traffic.
* **Red Indicator:** Wide interval, chaotic traffic (requires over-provisioning).

### 4. Simulation Mode (Monte Carlo)
Includes an educational "Simulation Mode" that generates 31 virtual measurement days using polynomial distribution and Gaussian noise. This allows users to test algorithms without external CSV data.

## 🏗️ Technology Stack & Architecture

The system follows the **MVC (Model-View-Controller)** pattern:

* **GUI:** `CustomTkinter` (Modern UI with Dark Mode and High-DPI support).
* **Data Processing:** `Pandas` (CSV normalization, dataframes).
* **Math Core:** `NumPy` & `SciPy` (Vectorized calculations, convolution for sliding window, t-Student quantiles).
* **Visualization:** `Matplotlib` (Embedded flat-design charts).

### Algorithmic Optimization
Instead of slow loops, the TCBH algorithm utilizes **discrete convolution** (`np.convolve`) to process the sliding window efficiently.

## 🚀 Installation & Usage

### Prerequisites
* Python 3.10 or higher
* Dependencies listed in `requirements.txt`

### Running the App
1.  Clone the repository:
    ```bash
    git clone [https://github.com/definitelynotchase/traffic-analyzer.git](https://github.com/definitelynotchase/traffic-analyzer.git)
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the main script:
    ```bash
    python main.py
    ```

### User Manual
1.  **Engineering Mode:**
    * Set "Analysis Parameters" (e.g., Start: 8, End: 16) to eliminate night anomalies.
    * Click "Upload Measurement Folder" and select a directory containing daily CSV files.
    * Read TCBH results and check the Confidence Interval color on the dashboard.

2.  **Simulation Mode:**
    * Click "Simulation (Auto)" to generate synthetic data and visualize the algorithms in action.

## 📂 Data Format
The application automatically detects separators (`;` vs `,`) and decimal formats. Input CSV files should contain a column for traffic volume (e.g., `ruch_erl`).

## 👥 Authors
**Wrocław University of Science and Technology**
* **Illia Żukowski**

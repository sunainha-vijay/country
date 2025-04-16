# Country Finance Agent

A Streamlit-based web application that provides financial information about countries, including currency rates, stock market indices, and geographical location data.

![Country Finance Agent Screenshot](https://raw.githubusercontent.com/yourusername/country-finance-agent/main/screenshot.png)

## Features

- **Currency Information**: Get the official currency name and ISO code for any country
- **Real-time Exchange Rates**: View exchange rates from the country's currency to USD, INR, GBP, and EUR
- **Stock Exchange Data**: List major stock exchanges and indices for the selected country
- **Real-time Stock Index Values**: Display current values of major stock indices
- **Geographic Visualization**: See the main stock exchange location on an interactive map

## Technology Stack

### Framework
- **Streamlit**: Used for creating the web interface

### Language Models
- **Google Gemini**: The application uses Google's Gemini 2.0 Flash model for generating structured information about countries

### APIs Used
- **Gemini API**: For generating country-specific financial information
- **Exchange Rate APIs**:
  - Exchange Rate API (api.exchangerate.host)
  - Open Exchange Rates API (open.er-api.com)
  - Frankfurter API (api.frankfurter.app)
- **Yahoo Finance API**: For fetching real-time stock index values
- **Google Maps Geocoding API**: For converting stock exchange addresses to map coordinates

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/country-finance-agent.git
cd country-finance-agent
```

2. Install the required packages:
```bash
pip install streamlit requests yfinance python-dotenv
```

3. Create a `.env` file in the root directory with your API keys:
```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## How to Get API Keys

### Gemini API Key
1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Create a new project
4. Enable the Gemini API
5. Create an API key

### Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Geocoding API and Maps JavaScript API
4. Create an API key with restrictions for these services

## Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

1. Enter a country name in the input field (e.g., "Japan", "India", "UK", "USA")
2. The application will retrieve and display:
   - Currency information and exchange rates
   - Stock exchanges and indices with their current values
   - A map showing the location of the main stock exchange

## Example Countries to Try

- Japan
- India
- USA
- UK
- China
- South Korea
- Australia
- Brazil
- Germany
- Singapore

## Limitations

- Exchange rates for some uncommon currencies might not be available
- Stock index symbols might not resolve correctly for all exchanges
- The application requires internet access to fetch real-time data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

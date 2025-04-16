import streamlit as st
import requests
import yfinance as yf
import re
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables (for security)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "API")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "API")

# Set page configuration
st.set_page_config(
    page_title="🌐 Country Finance Agent",
    page_icon="📊",
    layout="wide"
)

def ask_gemini(prompt):
    """Query the Gemini API with a prompt and return the response."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        # Create a structured prompt for better response extraction
        structured_prompt = f"""
        For the country: {prompt}, provide the following information in a structured JSON format:
        
        1. Currency: The official currency name and its ISO code (exactly 3 letters)
        2. Stock Exchanges: List all major stock exchanges with their full names and index symbols
        3. Main Exchange Location: The specific address of the main stock exchange headquarters
        
        Format your response as a JSON object with the following structure:
        {{
            "currency": {{
                "name": "Currency Name",
                "code": "ISO"
            }},
            "exchanges": [
                {{
                    "name": "Exchange Name",
                    "indices": [
                        {{
                            "name": "Index Name",
                            "symbol": "Symbol"
                        }}
                    ]
                }}
            ],
            "main_exchange_location": "Full address of main exchange"
        }}
        
        The currency code must be the standard 3-letter ISO code (like USD, EUR, JPY, etc.).
        Please provide accurate and up-to-date information.
        """
        
        data = {"contents": [{"parts": [{"text": structured_prompt}]}]}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Extract text from the response
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Try to extract JSON from the response
        try:
            # Find JSON content in the response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
                
            # Parse the JSON
            parsed_data = json.loads(json_str)
            return parsed_data, response_text
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw text
            return None, response_text
            
    except Exception as e:
        st.error(f"Error querying Gemini API: {str(e)}")
        return None, f"Error: {str(e)}"

def get_exchange_rates(currency_code):
    """Get exchange rates for a given currency code to USD, INR, GBP, and EUR."""
    try:
        # Primary API: Exchange Rate API
        url = f"https://api.exchangerate.host/latest?base={currency_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            
            # Check if rates contains our target currencies
            if rates and all(k in rates for k in ["USD", "INR", "GBP", "EUR"]):
                return {
                    "USD": rates.get("USD"),
                    "INR": rates.get("INR"),
                    "GBP": rates.get("GBP"),
                    "EUR": rates.get("EUR")
                }
                
        # Fallback API: Open Exchange Rates API
        # This is a free API with limited functionality but good for backup
        url = f"https://open.er-api.com/v6/latest/{currency_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            
            return {
                "USD": rates.get("USD"),
                "INR": rates.get("INR"),
                "GBP": rates.get("GBP"),
                "EUR": rates.get("EUR")
            }
            
        # Second fallback: For USD base currency using Frankfurter API
        if currency_code == "USD":
            url = "https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,INR"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                return {
                    "USD": 1.0,  # USD to USD is always 1
                    "INR": rates.get("INR"),
                    "GBP": rates.get("GBP"),
                    "EUR": rates.get("EUR")
                }
        
        # If we get here, both APIs failed or returned invalid data
        st.warning(f"Exchange rate APIs failed for {currency_code}")
        return {}
            
    except Exception as e:
        st.error(f"Error fetching exchange rates: {str(e)}")
        return {}

def get_stock_index_values(indices):
    """Get current values for stock indices."""
    values = {}
    
    for index in indices:
        symbol = index.get("symbol", "")
        name = index.get("name", "Unknown Index")
        
        if not symbol:
            values[name] = "No symbol available"
            continue
            
        try:
            # For Yahoo Finance, some symbols need special formatting
            # This is a simplified approach - a more comprehensive mapping would be better
            yf_symbol = symbol
            if not any(x in symbol for x in ["^", "."]):
                # Try to guess the Yahoo Finance format
                if "NIFTY" in name.upper():
                    yf_symbol = "^NSEI"
                elif "SENSEX" in name.upper():
                    yf_symbol = "^BSESN"
                elif "NIKKEI" in name.upper():
                    yf_symbol = "^N225"
                elif "FTSE" in name.upper():
                    yf_symbol = "^FTSE"
                elif "DOW" in name.upper():
                    yf_symbol = "^DJI"
                elif "S&P" in name.upper() or "SPX" in name.upper():
                    yf_symbol = "^GSPC"
                elif "NASDAQ" in name.upper():
                    yf_symbol = "^IXIC"
                elif "KOSPI" in name.upper():
                    yf_symbol = "^KS11"
                elif "SHANGHAI" in name.upper():
                    yf_symbol = "000001.SS"
                elif "HANG SENG" in name.upper():
                    yf_symbol = "^HSI"
                elif "DAX" in name.upper():
                    yf_symbol = "^GDAXI"
                elif "CAC" in name.upper():
                    yf_symbol = "^FCHI"
            
            data = yf.Ticker(yf_symbol)
            price = data.info.get('regularMarketPrice')
            
            if price:
                values[name] = price
            else:
                values[name] = "Data unavailable"
        except Exception as e:
            values[name] = f"Error: {str(e)[:50]}..."
    
    return values

def normalize_currency_code(code):
    """Ensure currency code is correctly formatted"""
    if not code:
        return ""
    
    # Strip any non-alphabetic characters
    code = re.sub(r'[^A-Za-z]', '', code)
    
    # Convert to uppercase and take first 3 letters
    code = code.upper()[:3]
    
    # Validate against common currency codes
    common_codes = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR", 
                   "KRW", "MXN", "BRL", "SGD", "HKD", "THB", "RUB", "ZAR", "NZD"]
    
    if code in common_codes:
        return code
    
    # Return the code anyway, after normalization
    return code

def get_maps_link(location_name):
    """Get Google Maps link and coordinates for a location."""
    try:
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(geocode_url)
        data = response.json()

        if data['status'] == 'OK':
            lat = data['results'][0]['geometry']['location']['lat']
            lng = data['results'][0]['geometry']['location']['lng']
            formatted_address = data['results'][0]['formatted_address']
            maps_link = f"https://www.google.com/maps?q={lat},{lng}"
            return maps_link, lat, lng, formatted_address
        else:
            st.warning(f"Geocoding API returned status: {data['status']}")
            return None, None, None, None
    except Exception as e:
        st.error(f"Error with geocoding: {str(e)}")
        return None, None, None, None

# UI Components
st.title("💱 Country Currency & Stock Market Agent")
st.subheader("Get financial information for any country")

# Input for country
country = st.text_input("Enter a country name:", placeholder="e.g. Japan, India, UK, USA...")

# Main app logic
if country:
    with st.spinner("🌐 Gathering information about the country..."):
        # Get information from LLM
        structured_data, raw_llm_response = ask_gemini(country)
    
    # Create a two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display the raw LLM response in an expandable section
        with st.expander("Show LLM Raw Response"):
            st.code(raw_llm_response, language="json")
        
        # Process the structured data if available
        if structured_data:
            # Currency information
            currency_data = structured_data.get("currency", {})
            currency_name = currency_data.get("name", "Unknown")
            currency_code = normalize_currency_code(currency_data.get("code", ""))
            
            st.subheader(f"📍 Currency Information for {country}")
            st.info(f"**Official Currency:** {currency_name} ({currency_code})")
            
            # Exchange rates
            if currency_code:
                with st.spinner(f"💱 Getting exchange rates for {currency_code}..."):
                    rates = get_exchange_rates(currency_code)
                    
                if rates and any(rates.values()):
                    st.markdown(f"### 💵 1 {currency_code} equals:")
                    for k, v in rates.items():
                        if v is not None:
                            st.markdown(f"- **{k}**: {v:.4f}")
                        else:
                            st.markdown(f"- **{k}**: Data unavailable")
                else:
                    # Try reversing the exchange rate calculation for some difficult currencies
                    st.warning(f"Attempting alternative method for {currency_code} exchange rates...")
                    try:
                        # Get USD-based rates and calculate inverse
                        usd_rates = get_exchange_rates("USD")
                        if usd_rates and currency_code in usd_rates:
                            usd_to_currency = usd_rates[currency_code]
                            if usd_to_currency and usd_to_currency > 0:
                                currency_to_usd = 1 / usd_to_currency
                                st.markdown(f"### 💵 1 {currency_code} equals:")
                                st.markdown(f"- **USD**: {currency_to_usd:.4f}")
                                # For other currencies, calculate based on the USD rate
                                if "EUR" in usd_rates and usd_rates["EUR"]:
                                    eur_rate = usd_rates["EUR"] / usd_rates[currency_code]
                                    st.markdown(f"- **EUR**: {eur_rate:.4f}")
                                if "GBP" in usd_rates and usd_rates["GBP"]:
                                    gbp_rate = usd_rates["GBP"] / usd_rates[currency_code]
                                    st.markdown(f"- **GBP**: {gbp_rate:.4f}")
                                if "INR" in usd_rates and usd_rates["INR"]:
                                    inr_rate = usd_rates["INR"] / usd_rates[currency_code]
                                    st.markdown(f"- **INR**: {inr_rate:.4f}")
                            else:
                                st.warning(f"Could not calculate exchange rates for {currency_code}")
                        else:
                            st.warning(f"Could not fetch USD exchange rates for {currency_code}")
                    except Exception as e:
                        st.error(f"Error in alternative exchange rate calculation: {str(e)}")
            
            # Stock exchanges and indices
            exchanges = structured_data.get("exchanges", [])
            if exchanges:
                st.subheader("📊 Stock Exchanges and Indices")
                
                # Extract all indices from all exchanges
                all_indices = []
                for exchange in exchanges:
                    exchange_name = exchange.get("name", "Unknown Exchange")
                    indices = exchange.get("indices", [])
                    
                    st.markdown(f"### {exchange_name}")
                    
                    if indices:
                        # Display indices for this exchange
                        for index in indices:
                            index_name = index.get("name", "Unknown Index")
                            index_symbol = index.get("symbol", "No symbol")
                            st.markdown(f"- **{index_name}** ({index_symbol})")
                            all_indices.append(index)
                    else:
                        st.write("No indices information available")
                
                # Get and display stock index values
                if all_indices:
                    with st.spinner("📈 Fetching current index values..."):
                        index_values = get_stock_index_values(all_indices)
                    
                    if index_values:
                        st.subheader("📉 Current Index Values")
                        for name, value in index_values.items():
                            st.markdown(f"- **{name}**: {value}")
            else:
                st.warning("No stock exchange information available")
            
            # Main exchange location
            main_location = structured_data.get("main_exchange_location", "")
            if main_location:
                st.subheader("🗺️ Main Stock Exchange Location")
                st.info(main_location)
    
    with col2:
        # Display map for main exchange location
        if structured_data and structured_data.get("main_exchange_location"):
            location = structured_data.get("main_exchange_location")
            with st.spinner("🗺️ Loading map..."):
                map_url, lat, lng, formatted_address = get_maps_link(location)
                
            if map_url and lat and lng:
                st.subheader("📍 Map Location")
                st.write(formatted_address)
                
                # Display map
                map_data = {"lat": [lat], "lon": [lng]}
                st.map(map_data)
                
                # Google Maps link
                st.markdown(f"[📍 Open in Google Maps]({map_url})")
            else:
                st.warning("Could not display map location")

# Add a footer
st.markdown("---")
st.markdown("#### 💡 Try searching for countries like Japan, India, USA, UK, China, or South Korea")
st.markdown("This app uses Gemini API, Yahoo Finance, Exchange Rates API, and Google Maps")

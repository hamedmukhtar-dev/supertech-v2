# HUMAIN Lifestyle — Your Gateway to KSA 🌍🇸🇦

**HUMAIN Lifestyle** is an AI-powered B2C platform prototype that acts as a **digital gateway to the Kingdom of Saudi Arabia**:

> From the first travel idea… to flights, rail, hotels, entertainment, Umrah & Hajj, and even investor services — all in one unified experience.

---

## 🌐 Live Demo

> Deployed on Render (Streamlit):  
> **https://humain-lifestyle.onrender.com**  
> *(Demo mode – no real external integrations yet)*

---

## 🎯 Vision

**humain-lifestyle — your gateway to KSA**

A unified lifestyle platform for:

- Travelers & visitors  
- Umrah & Hajj pilgrims  
- Business visitors & investors  
- Future residents & digital nomads  

The platform is designed to **own the end-to-end relationship with the user**, then connect to different providers (flights, rail, hotels, banks, government services) as needed.

---

## 🧩 Main Features (Current Demo)

### 1) B2C Travel Core

- **🧭 Trip Planner (B2C)**  
  - User enters: origin, destination city in KSA, budget, number of days, interests.  
  - AI generates a day-by-day trip plan in Arabic (via OpenAI API).  
  - Optionally save as a **Saved Itinerary**.

- **📝 Saved Itineraries**  
  - View all saved AI-generated trip plans.  
  - See traveler info, route, budget, interests, and full plan text.

### 2) Experiences & Activities in KSA

- **🎟️ Experiences & Activities**  
  - Seed catalog of experiences in:
    - Riyadh, Jeddah, Makkah, Madina, Dammam, Al Khobar, Abha, Taif, AlUla, Tabuk, NEOM Region, Diriyah  
  - Categories: Entertainment, Culture, Nature, Adventure, Religious, Family, Leisure, Futuristic.  
  - Each experience has:
    - City, category, description, approx. price (USD), provider, and mock booking link.

### 3) Packages / Programs

- **📦 Packages / Programs**  
  - Convert a **Saved Itinerary** into a sellable package:
    - Program name, city, days, budget, price-from (USD)  
    - Base hotel (optional)  
    - Linked activities (from catalog)  
    - Target segment: Individuals, Families, Groups, VIP, Umrah  
    - Status: Draft / Active  
  - Shows:
    - Linked activities  
    - Original AI plan text  
  - Designed as “products” ready to be sold or exported to partners.

### 4) Flights & Rail (Lead Capture Modules)

> These are **internal modules** to collect structured leads.  
> Later they can be connected to real systems (NDC/GDS, SAR, etc.).

- **✈️ Flights to KSA**
  - Origin city, destination city in KSA  
  - Trip type (one-way / round-trip)  
  - Dates, passengers, cabin class  
  - Contact details (name, email, phone)  
  - Saved as `booking_requests` with `source = "Flights"`.

- **🚄 Saudi Rail**
  - From/to station inside KSA  
  - Travel date, passengers, seat class  
  - Contact details  
  - Saved as `booking_requests` with `source = "Rail"`.

### 5) Umrah & Hajj

- **🕋 Umrah & Hajj — Program Request**
  - Program type: Umrah, Hajj (future), Umrah + Tourism  
  - Origin city, entry city (Jeddah, Madina, Riyadh…)  
  - Nights in Makkah & Madina  
  - Number of guests  
  - Accommodation preference (economy / mid / 5* / VIP near Haram)  
  - Approx. budget for full program  
  - Contact details  
  - Saved as `booking_requests` with `source = "Umrah/Hajj"`.

Designed to be later integrated with official platforms (e.g. Nusuk) and licensed partners.

### 6) Investor Gateway

- **💼 Invest in KSA — Business Gateway**
  - Profile type: Individual / Company  
  - Target city: Riyadh, Jeddah, Al Khobar, Dammam, NEOM, Diriyah, Other  
  - Requested services:
    - Company setup  
    - Commercial registration  
    - Office rental  
    - Coworking / shared workspaces  
    - Residential apartment rental  
    - Bank account setup  
    - Legal/regulatory consulting  
    - Work visas / staffing  
  - Investment budget (USD)  
  - Time horizon (3 months / 6 months / 1 year / undefined)  
  - Contact details & project notes  
  - Saved as `booking_requests` with `source = "Investor"`.

This makes the platform not just a travel engine, but a **business & lifestyle gateway to KSA**.

### 7) Admin / Back Office

- **📥 Booking Requests (Admin)**  
  - Unified view of all leads:
    - Travel, flights, rail, Umrah/Hajj, investors, manual entries…  
  - Filter by:
    - Source (Web, Flights, Rail, Umrah/Hajj, Investor, etc.)  
    - Status (New, In Progress, Confirmed, Cancelled)

- **🏨 Hotels & Contracts (Admin)**  
  - Manage hotels (basic data + API flag).  
  - Manage basic contracts:
    - Contract name, type (Net / Commission / Hybrid), currency  
    - Validity dates  
    - Payment terms, cancellation policy, notes  

> Future versions will add pricing logic: net rates, commission%, markup, allotment, release days, etc.

### 8) AI Assistant

- **🤖 AI Assistant — HUMAIN Lifestyle**
  - General-purpose assistant inside the platform.  
  - Explains the concept, helps with travel ideas, etc.  
  - Powered by OpenAI for now; planned to support **HUMAIN ONE / ALLAM** in future.

---

## 🏛 Data Model (High-level)

SQLite tables:

- `hotels`  
- `contracts`  
- `activities`  
- `itineraries`  
- `packages`  
- `booking_requests`  *(central lead table for all funnels)*

This makes it easy to later:

- Plug into external systems (Flights, Rail, Umrah, Banking…)  
- Attach analytics, dashboards, CRM, etc.

---

## 🧱 Tech Stack

- **Frontend / UI:** [Streamlit](https://streamlit.io/)  
- **Language:** Python 3  
- **Database:** SQLite (file: `humain_lifestyle.db`)  
- **AI Integration:** OpenAI API (`gpt-4.1-mini` in demo)  
- **Deployment:** Render (Web Service, Python)  
- **Environment:** `.env` and `OPENAI_API_KEY` for local/dev

Planned / Future integrations:

- HUMAIN ONE / HUMAIN platform  
- ALLAM & regional LLMs  
- NDC / GDS for flights  
- SAR & Saudi rail systems  
- Nusuk / official Umrah & Hajj systems  
- KSA banks / wallets (MADA, STC Pay, etc.)

---

## 🚀 Local Development

### 1. Clone the repository

```bash
git clone https://github.com/hamedmukhtar-dev/supertech-v2.git
cd supertech-v2

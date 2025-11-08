# Bhopal Bus POC - Frontend

Modern Next.js frontend for the AI-powered bus routing and scheduling system.

## Features

- 🎨 Beautiful UI with Tailwind CSS
- 🔐 Authentication (Admin & Passenger)
- 🗺️ Google Maps Integration
- 📊 Real-time Data Visualization
- 📱 Fully Responsive Design
- ⚡ Fast Performance with Next.js 15

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
# Copy .env.local and update with your API keys
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── page.tsx           # Landing page
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── admin/             # Admin dashboard
│   └── passenger/         # Passenger interface
├── components/            # Reusable components
├── lib/                   # Utilities and API client
└── public/                # Static assets
```

## Tech Stack

- **Framework**: Next.js 15
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Maps**: Google Maps JavaScript API
- **Icons**: Lucide React
- **Charts**: Recharts

## API Integration

The frontend connects to the FastAPI backend running on `http://localhost:8000`.

Make sure the backend is running before starting the frontend.

## Available Pages

- `/` - Landing page
- `/login` - Login (Admin/Passenger)
- `/register` - Passenger registration
- `/admin` - Admin dashboard
- `/passenger` - Passenger interface

## License

MIT\n
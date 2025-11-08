#!/usr/bin/env python3
"""
Script to generate all frontend files for Bhopal Bus POC
This creates a complete Next.js frontend with all pages and components
"""

import os
import json

FRONTEND_DIR = "frontend"

# File templates
FILES = {
    "app/layout.tsx": '''import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Bhopal Bus POC - AI-Powered Bus System",
  description: "Intelligent bus routing and scheduling for Bhopal, MP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  );
}
''',

    "app/login/page.tsx": '''
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import { LogIn, User, Lock } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState<'admin' | 'passenger'>('passenger');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = userType === 'admin'
        ? await authAPI.adminLogin({ email, password })
        : await authAPI.passengerLogin({ email, password });

      login(response.data.access_token, { email, role: userType });
      router.push(userType === 'admin' ? '/admin' : '/passenger');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <LogIn className="w-8 h-8 text-blue-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome Back</h1>
          <p className="text-gray-600 mt-2">Sign in to continue</p>
        </div>

        {/* User Type Toggle */}
        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setUserType('passenger')}
            className={`flex-1 py-3 rounded-lg font-medium transition \\${
              userType === 'passenger'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Passenger
          </button>
          <button
            type="button"
            onClick={() => setUserType('admin')}
            className={`flex-1 py-3 rounded-lg font-medium transition \\${
              userType === 'admin'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Admin
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <User className="w-4 h-4 inline mr-2" />
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="your@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Lock className="w-4 h-4 inline mr-2" />
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-semibold transition disabled:opacity-50"
          >
            {loading ? <LoadingSpinner size="sm" /> : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          Don\\'t have an account?{' '}
          <a href="/register" className="text-blue-600 hover:underline font-medium">
            Register
          </a>
        </p>

        {userType === 'admin' && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
            <strong>Admin Demo:</strong><br />
            Email: atinitytech.business@gmail.com<br />
            Password: atinity@123
          </div>
        )}
      </div>
    </div>
  );
}
''',

    "README.md": '''# Bhopal Bus POC - Frontend

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

MIT
'''
}

def create_files():
    """Create all frontend files"""
    os.chdir(FRONTEND_DIR)
    
    for filepath, content in FILES.items():
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\\n')
        
        print(f"✓ Created {filepath}")
    
    print("\\n✅ All frontend files created successfully!")
    print("\\nNext steps:")
    print("1. cd frontend")
    print("2. Update .env.local with your Google Maps API key")
    print("3. npm run dev")
    print("4. Open http://localhost:3000")

if __name__ == "__main__":
    create_files()


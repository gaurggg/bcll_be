'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { Bus, MapPin, Clock, Sparkles, TrendingUp, Users } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      if (user?.role === 'admin') {
        router.push('/admin');
      } else {
        router.push('/passenger');
      }
    } else {
      router.push('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex items-center justify-center mb-8">
            <div className="bg-white p-4 rounded-3xl shadow-2xl border-4 border-blue-200">
              <Image
                src="/bcll logo.png"
                alt="BCLL Logo"
                width={120}
                height={120}
                className="rounded-2xl"
                priority
              />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Bhopal Bus POC
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8">
            AI-Powered Bus Routing & Scheduling System for Bhopal, MP
          </p>
          <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
            Intelligent route planning, real-time bus tracking, and personalized recommendations
            powered by Google Maps and Gemini AI
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleGetStarted}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition shadow-lg hover:shadow-xl"
            >
              Get Started
            </button>
            <Link
              href="/register"
              className="bg-white hover:bg-gray-50 text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg text-lg font-semibold transition text-center"
            >
              Register Now
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Key Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-blue-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Sparkles className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              AI Route Planning
            </h3>
            <p className="text-gray-600">
              Gemini AI analyzes multiple routes and ranks them based on distance, traffic,
              and efficiency to find the optimal path
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-green-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Clock className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Smart Scheduling
            </h3>
            <p className="text-gray-600">
              AI predicts optimal bus frequency and fleet size based on peak hours,
              route demand, and traffic patterns
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-purple-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <MapPin className="w-7 h-7 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Real-time Tracking
            </h3>
            <p className="text-gray-600">
              Track buses in real-time with accurate ETA predictions using Google Maps
              integration and live traffic data
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-orange-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <TrendingUp className="w-7 h-7 text-orange-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Personalized Recommendations
            </h3>
            <p className="text-gray-600">
              Get AI-powered bus recommendations based on your travel history,
              preferences, and current location
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-red-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Users className="w-7 h-7 text-red-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Admin Dashboard
            </h3>
            <p className="text-gray-600">
              Comprehensive admin portal for managing routes, schedules, buses,
              and viewing analytics
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition">
            <div className="bg-indigo-100 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Bus className="w-7 h-7 text-indigo-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Passenger Portal
            </h3>
            <p className="text-gray-600">
              Easy-to-use interface for passengers to search buses, view routes,
              and track their travel history
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-12 text-center text-white">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to Transform Public Transport?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join us in revolutionizing bus transportation in Bhopal with AI
          </p>
          <button
            onClick={handleGetStarted}
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-4 rounded-lg text-lg font-semibold transition shadow-lg"
          >
            Start Your Journey
          </button>
        </div>
      </section>
    </div>
  );
}

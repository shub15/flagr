import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import FeaturesGrid from './components/FeaturesGrid';
import HowItWorksSection from './components/HowItWorksSection';
import MoondreamSection from './components/MoondreamSection';
import FinalCTA from './components/FinalCTA';
import Footer from './components/Footer';
import Login from './pages/Login';
import Upload from './pages/Upload';
import Split from './pages/Split';
import Dashboard from './pages/Dashboard';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Landing page component
function LandingPage() {
  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Fixed Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-[#dcedf0] via-[#eef6f6] to-[#d8f0e9]"></div>

        {/* Soft blurred blobs */}
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-200/30 rounded-full mix-blend-multiply filter blur-[80px] animate-pulse"></div>
        <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-teal-200/30 rounded-full mix-blend-multiply filter blur-[80px]"></div>
        <div className="absolute top-[40%] left-[30%] w-[300px] h-[300px] bg-blue-200/20 rounded-full mix-blend-multiply filter blur-[60px]"></div>
      </div>

      {/* Main Content Wrapper */}
      <main className="relative z-10 w-full max-w-5xl mx-auto px-6 flex flex-col items-center">
        <Navbar />
        <Hero />
        <FeaturesGrid />
        <HowItWorksSection />
        <MoondreamSection />
        <FinalCTA />
        <Footer />
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/split" element={<ProtectedRoute><Split /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;


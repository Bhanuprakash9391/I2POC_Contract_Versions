import React, { useState, useEffect } from 'react';
import GoldenPurpleChat from "./components/InitialChat";
import DraftChat from "./components/DraftChat/DraftChat";
import ContractCatalog from "./components/ContractCatalog";
import ContractReviewerDashboard from "./components/ContractReviewerDashboard";
import FileUploadSection from "./components/FileUploadSection";
import LoginPage from "./components/LoginPage";
import { ChatProvider } from "./ChatContext";
import { useChat } from "./ChatContext";
import "./App.css";

// Wrapper component to access context
function AppContent() {
  const { initialChatStep, userContext, setUserContext } = useChat();
  const [currentView, setCurrentView] = useState('contract-submission');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check for existing user session on component mount
  useEffect(() => {
    const savedUser = localStorage.getItem('user_context');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUserContext(userData);
      setIsAuthenticated(true);
    }
  }, [setUserContext]);

  // Update authentication state when userContext changes
  useEffect(() => {
    setIsAuthenticated(!!userContext);
  }, [userContext]);

  // Logout function
  const handleLogout = () => {
    setUserContext(null);
    localStorage.removeItem('user_context');
    setIsAuthenticated(false);
  };

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Navigation component
  const Navigation = () => (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-3">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-gray-800">Contract Generation Platform</h1>
          </div>
          <div className="flex items-center space-x-6">
            <div className="hidden sm:flex sm:space-x-4">
                <button
                onClick={() => setCurrentView('contract-submission')}
                className={`${
                  currentView === 'contract-submission'
                    ? 'text-blue-600 border-blue-500'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium`}
              >
                Submit Contract
              </button>
              <button
                onClick={() => setCurrentView('file-upload')}
                className={`${
                  currentView === 'file-upload'
                    ? 'text-blue-600 border-blue-500'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium`}
              >
                Upload Documents
              </button>
              <button
                onClick={() => setCurrentView('contract-catalog')}
                className={`${
                  currentView === 'contract-catalog'
                    ? 'text-blue-600 border-blue-500'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium`}
              >
                Contract Catalog
              </button>
              <button
                onClick={() => setCurrentView('contract-reviewer')}
                className={`${
                  currentView === 'contract-reviewer'
                    ? 'text-blue-600 border-blue-500'
                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                } inline-flex items-center px-3 py-2 border-b-2 text-sm font-medium`}
              >
                Contract Reviewer
              </button>
            </div>
            
            {/* User info and logout */}
            <div className="flex items-center space-x-3">
              <div className="text-sm text-gray-700">
                <span className="font-medium">{userContext?.role}</span>
                <span className="mx-1">•</span>
                <span>{userContext?.department}</span>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'contract-submission':
        return initialChatStep !== "done" ? <GoldenPurpleChat /> : <DraftChat />;
      case 'file-upload':
        return <FileUploadSection />;
      case 'contract-catalog':
        return <ContractCatalog />;
      case 'contract-reviewer':
        return <ContractReviewerDashboard />;
      default:
        return initialChatStep !== "done" ? <GoldenPurpleChat /> : <DraftChat />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main>
        {renderCurrentView()}
      </main>
    </div>
  );
}

function App() {
  return (
    <ChatProvider>
      <AppContent />
    </ChatProvider>
  );
}

export default App;

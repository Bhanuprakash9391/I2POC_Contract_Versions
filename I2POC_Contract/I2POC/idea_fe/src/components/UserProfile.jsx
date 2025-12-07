import React, { useState, useEffect } from 'react';
import { useChat } from "../ChatContext";

const UserProfile = () => {
  const { setUserContext } = useChat();
  const [userProfile, setUserProfile] = useState({
    user_id: '',
    department: 'Other',
    role: '',
    location: '',
    language: 'en'
  });

  const departments = [
    'Engineering',
    'Manufacturing', 
    'Sales',
    'Marketing',
    'Finance',
    'Human Resources',
    'IT',
    'Operations',
    'Supply Chain',
    'Other'
  ];

  const roles = [
    'Employee',
    'Manager',
    'Director',
    'Engineer',
    'Analyst',
    'Specialist',
    'Consultant'
  ];

  const locations = [
    'Unknown',
    'North America',
    'Europe',
    'Asia Pacific',
    'Latin America',
    'Middle East'
  ];

  const languages = [
    { code: 'en', name: 'English' },
    { code: 'de', name: 'German' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    setUserContext(userProfile);
    const message = userProfile.language === 'de' 
      ? 'Benutzerprofil gespeichert! Ihr DexKo-Kontext wird den Ideeneinreichungsprozess beeinflussen.'
      : 'User profile saved! Your DexKo context will influence the idea submission process.';
    alert(message);
  };

  const handleChange = (field, value) => {
    setUserProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Get current language
  const currentLanguage = userProfile.language || 'en';

  // Translations
  const translations = {
    en: {
      title: "DexKo User Profile",
      subtitle: "Set up your DexKo context to personalize your experience",
      employeeId: "Employee ID",
      employeeIdPlaceholder: "Enter your DexKo employee ID",
      department: "Department",
      role: "Role",
      selectRole: "Select your role",
      location: "Location",
      language: "Preferred Language",
      saveButton: "Save Profile & Continue",
      benefitsTitle: "How your profile helps:",
      benefits: [
        "Department-specific questions and KPIs",
        "Role-appropriate evaluation criteria",
        "Language-specific content",
        "Location-aware suggestions"
      ]
    },
    de: {
      title: "DexKo Benutzerprofil",
      subtitle: "Richten Sie Ihren DexKo-Kontext ein, um Ihre Erfahrung zu personalisieren",
      employeeId: "Mitarbeiter-ID",
      employeeIdPlaceholder: "Geben Sie Ihre DexKo-Mitarbeiter-ID ein",
      department: "Abteilung",
      role: "Rolle",
      selectRole: "Wählen Sie Ihre Rolle",
      location: "Standort",
      language: "Bevorzugte Sprache",
      saveButton: "Profil speichern & Fortfahren",
      benefitsTitle: "Wie Ihr Profil hilft:",
      benefits: [
        "Abteilungsspezifische Fragen und KPIs",
        "Rollenangemessene Bewertungskriterien",
        "Sprachspezifische Inhalte",
        "Standortbewusste Vorschläge"
      ]
    }
  };

  const t = translations[currentLanguage];

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{t.title}</h2>
          <p className="mt-2 text-sm text-gray-600">
            {t.subtitle}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Employee ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t.employeeId}
            </label>
            <input
              type="text"
              value={userProfile.user_id}
              onChange={(e) => handleChange('user_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={t.employeeIdPlaceholder}
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t.department}
            </label>
            <select
              value={userProfile.department}
              onChange={(e) => handleChange('department', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t.role}
            </label>
            <select
              value={userProfile.role}
              onChange={(e) => handleChange('role', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t.selectRole}</option>
              {roles.map(role => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t.location}
            </label>
            <select
              value={userProfile.location}
              onChange={(e) => handleChange('location', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {locations.map(location => (
                <option key={location} value={location}>{location}</option>
              ))}
            </select>
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t.language}
            </label>
            <select
              value={userProfile.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {languages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              {t.saveButton}
            </button>
          </div>
        </form>

        {/* Profile Benefits */}
        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="text-sm font-medium text-blue-800 mb-2">
            {t.benefitsTitle}
          </h3>
          <ul className="text-xs text-blue-700 space-y-1">
            {t.benefits.map((benefit, index) => (
              <li key={index}>• {benefit}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;

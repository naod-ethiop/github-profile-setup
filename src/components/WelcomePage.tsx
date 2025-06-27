
import React, { useState } from 'react';
import { Trophy, Gamepad2, Users, Gift, CheckCircle, ArrowRight } from 'lucide-react';

interface WelcomePageProps {
  onComplete: () => void;
}

const WelcomePage: React.FC<WelcomePageProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: 'Welcome to Bingo Game!',
      description: 'Experience the ultimate multiplayer bingo with voice announcements in multiple languages',
      icon: Trophy,
      features: [
        'Real-time multiplayer gameplay',
        'Voice announcements in Amharic, Tigrinya & English',
        'Telegram bot integration',
        'Secure wallet system'
      ]
    },
    {
      title: 'How to Play',
      description: 'Learn the basics of our bingo game',
      icon: Gamepad2,
      features: [
        'Join or create game rooms',
        'Mark numbers as they are called',
        'Complete patterns to win',
        'Win prizes from the prize pool'
      ]
    },
    {
      title: 'Winning Patterns',
      description: 'Different ways to win in bingo',
      icon: Gift,
      features: [
        'Horizontal Line: Complete any row',
        'Vertical Line: Complete any column', 
        'Diagonal Line: Complete diagonal',
        'Full House: Mark all numbers'
      ]
    }
  ];

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      localStorage.setItem('welcomeCompleted', 'true');
      onComplete();
    }
  };

  const skip = () => {
    localStorage.setItem('welcomeCompleted', 'true');
    onComplete();
  };

  const currentStepData = steps[currentStep];
  const IconComponent = currentStepData.icon;

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
          {/* Progress indicator */}
          <div className="flex justify-center mb-8">
            <div className="flex space-x-2">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-3 h-3 rounded-full ${
                    index <= currentStep ? 'bg-blue-500' : 'bg-white/20'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="bg-gradient-to-r from-blue-500 to-purple-500 p-6 rounded-full">
                <IconComponent className="w-12 h-12 text-white" />
              </div>
            </div>

            <h1 className="text-3xl font-bold text-white mb-4">
              {currentStepData.title}
            </h1>
            
            <p className="text-white/80 text-lg mb-8">
              {currentStepData.description}
            </p>

            <div className="space-y-4">
              {currentStepData.features.map((feature, index) => (
                <div key={index} className="flex items-center justify-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-white/90">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <button
              onClick={skip}
              className="text-white/60 hover:text-white transition-colors"
            >
              Skip Tutorial
            </button>

            <button
              onClick={nextStep}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-3 px-6 rounded-lg font-semibold transition-all flex items-center space-x-2"
            >
              <span>{currentStep === steps.length - 1 ? 'Get Started' : 'Next'}</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;

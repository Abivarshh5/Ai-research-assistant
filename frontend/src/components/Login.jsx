import React, { useState } from 'react';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email.trim() && email.includes('@')) {
      onLogin(email.trim());
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl border border-gray-100 p-8 text-center">
        <h1 className="text-2xl font-extrabold text-ink mb-2">AI Research Assistant</h1>
        <p className="text-sm text-gray-500 mb-8">Enter your email to start: </p>

        <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-ink transition-all text-center"
          />
          <button
            type="submit"
            className="w-full bg-ink text-white font-medium py-3 rounded-lg hover:bg-black transition-colors"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;

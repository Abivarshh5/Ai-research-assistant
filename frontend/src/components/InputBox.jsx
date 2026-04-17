import React, { useState } from 'react';
import { Search } from 'lucide-react';

const InputBox = ({ onSearch, isLoading }) => {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onSearch(topic.trim());
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto py-20 px-4">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter a research topic..."
          disabled={isLoading}
          className="w-full h-16 pl-6 pr-40 text-lg bg-white border border-gray-200 rounded-lg focus:outline-none focus:border-gray-400 transition-colors placeholder:text-gray-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !topic.trim()}
          className="absolute right-2 top-2 h-12 px-6 bg-ink text-white rounded-md font-medium hover:bg-black transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Processing...' : 'Generate Report'}
        </button>
      </form>
    </div>
  );
};

export default InputBox;

import axios from 'axios';

const API_BASE_URL = "https://ai-research-assistant-frontend-8hle.vercel.app/";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const requestResearchStream = async (topic, options = { push: false, email: false }, onStatus) => {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch(`${api.defaults.baseURL}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          push_enabled: options.push,
          email_enabled: options.email
        })
      });

      if (!response.ok) {
         throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'final') {
                resolve(data);
                return;
              } else if (data.type === 'error') {
                reject(new Error(data.detail || 'Streaming error'));
                return;
              } else if (data.status) {
                if (onStatus) onStatus(data.status);
              }
            } catch (e) {
              console.error("Error parsing SSE chunk:", e, line);
            }
          }
        }
      }
      
      // If we exit loop without resolving:
      reject(new Error('Stream ended without final report'));
    } catch (error) {
      console.error('Streaming API Error:', error);
      reject(error);
    }
  });
};

export const requestResearch = async (topic, options = { push: true, email: true }) => {
  try {
    const response = await api.post('/run', { 
      topic,
      push_enabled: options.push,
      email_enabled: options.email
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const refineResearch = async (sessionId, feedback, onProgress) => {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch(`${api.defaults.baseURL}/refine`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          feedback 
        })
      });

      if (!response.ok) {
         throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'refine_done' || data.type === 'single_refinement_result') {
                resolve(data.data || data);
                return;
              } else if (data.type === 'error') {
                reject(new Error(data.message || 'Refinement error'));
                return;
              } else if (onProgress) {
                onProgress(data);
              }
            } catch (e) {
              console.error("Error parsing refinement chunk:", e);
            }
          }
        }
      }
      reject(new Error('Refinement ended without completion.'));
    } catch (error) {
      console.error('Refinement API Error:', error);
      reject(error);
    }
  });
};

export const deliverPush = async (sessionId) => {
  try {
    const response = await api.post('/deliver/push', { session_id: sessionId });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const deliverEmail = async (sessionId, recipientEmail) => {
  try {
    const response = await api.post('/deliver/email', { 
      session_id: sessionId,
      recipient_email: recipientEmail
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export const selectVariant = async (sessionId, selectedReport) => {
  try {
    const response = await api.post('/select_variant', {
      session_id: sessionId,
      selected_report: selectedReport
    });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export default api;

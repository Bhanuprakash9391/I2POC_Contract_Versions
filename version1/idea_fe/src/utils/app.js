import axios from 'axios';

// const BASE_URL = 'http://127.0.0.1:8000';
const BASE_URL = '/apcontract';

// 1. Submit an idea
export const submitIdea = async (query) => {
    try {
        const res = await axios.post(`${BASE_URL}/idea-submission/`, {
            query,
        });
        return res.data;
    } catch (err) {
        console.error('Error submitting idea:', err);
        throw err;
    }
};

// 2. Approve the idea
export const approveIdea = async (session_id, input) => {
    try {
        const res = await axios.post(`${BASE_URL}/approve-idea`, {
            session_id,
            query: input,
        });
        return res.data;
    } catch (err) {
        console.error('Error approving idea:', err);
        throw err;
    }
};

// 3. Generate titles
export const generateTitles = async (session_id) => {
    try {
        const res = await axios.post(`${BASE_URL}/generate-titles`, {
            session_id,
            input_data: {
                additionalProp1: {},
            },
        });
        return res.data;
    } catch (err) {
        console.error('Error generating titles:', err);
        throw err;
    }
};

// 4. Select a title
export const selectTitle = async (session_id, title) => {
    try {
        const res = await axios.post(`${BASE_URL}/select-title`, {
            session_id,
            input_data: {
                additionalProp1: {},
                title: title,
            },
        });
        return res.data;
    } catch (err) {
        console.error('Error selecting title:', err);
        throw err;
    }
};
// 5. chat with draft agent
export const chatWithDraftAgent = async (session_id, query = "", is_interrupt = true, idea_structuring) => {
    console.log("chatWithDraftAgent", { session_id, query, is_interrupt, idea_structuring })
    
    // Add sleep time between API calls to prevent rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay
    
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                "session_id": session_id,
                "query": query,
                "is_interrupt": is_interrupt,
                "idea_structuring": idea_structuring
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let result = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data.trim()) {
                        result = data;
                        reader.cancel(); // We only need the first data event
                        break;
                    }
                }
            }
            if (result) break;
        }

        console.log("chatWithDraftAgent result=====>", result)
        
        // Handle empty or invalid responses
        if (!result || result.trim() === '') {
            throw new Error('Empty response from server');
        }
        
        return result;
    } catch (err) {
        console.error('Error in chatWithDraftAgent:', err);
        throw err;
    }
};

const ML_API_URL = import.meta.env.VITE_ML_API_URL || 'http://localhost:8000';
const ML_API_KEY = import.meta.env.VITE_ML_API_KEY || 'default_test_key';

/**
 * Sends a prediction request to the ML service.
 * @param {Object} payload 
 * @returns {Promise<Object>} The prediction response from the ML engine.
 */
export async function getMLPrediction(payload) {
    try {
        const response = await fetch(`${ML_API_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': ML_API_KEY,
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('ML Service Error:', error);
        // Rethrow or return a fallback mechanism, depending on how strict we want to be
        throw error;
    }
}

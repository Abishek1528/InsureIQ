/**
 * MAPPING LOGIC (CRITICAL)
 * Frontend -> Backend Transformation
 */
const transformPayload = (formData) => {
    // Generate session ID for memory persistence
    const session_id = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
        session_id: session_id,
        full_name: formData.name,
        age: parseInt(formData.age),
        lifestyle: formData.lifestyle,
        medical_history: formData.pre_existing_conditions || "None",
        income: formData.income_band,
        location: formData.city_tier
    };
};

const API_BASE_URL = "http://localhost:8000";

export const getRecommendation = async (formData) => {
    const payload = transformPayload(formData);
    
    console.log("Sending transformed payload to backend:", payload);

    try {
        const response = await fetch(`${API_BASE_URL}/recommend`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Backend Error Detail:", errorData);
            throw new Error(errorData.detail ? JSON.stringify(errorData.detail) : "Failed to get recommendations");
        }

        const data = await response.json();
        // Return both the recommendation data AND the session_id used
        return { ...data, session_id: payload.session_id };
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
};

export const sendChatMessage = async (sessionId, query) => {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                session_id: sessionId,
                query: query
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Chat Error Detail:", errorData);
            throw new Error(errorData.detail ? JSON.stringify(errorData.detail) : "Failed to send message");
        }

        return await response.json();
    } catch (error) {
        console.error("Chat Error:", error);
        throw error;
    }
};

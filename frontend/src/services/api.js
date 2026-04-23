/**
 * MAPPING LOGIC (CRITICAL)
 * Frontend -> Backend Transformation
 */
const transformPayload = (formData) => {
    // 1. Map Income Band to approximate numeric income
    const incomeMap = {
        "<3 LPA": 200000,
        "3–6 LPA": 450000,
        "6–10 LPA": 800000,
        "10+ LPA": 1200000
    };

    // 2. Map Lifestyle to derived dependents
    const lifestyleMap = {
        "Sedentary": 2,
        "Moderate": 1,
        "Active": 0
    };

    // 3. Generate session ID for memory persistence
    const session_id = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
        session_id: session_id,
        age: parseInt(formData.age),
        gender: "Not Specified",
        income: incomeMap[formData.income_band] || 0,
        dependents: lifestyleMap[formData.lifestyle] ?? 0,
        medical_history: formData.pre_existing_conditions || "None",
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
            throw new Error(errorData.detail || "Failed to get recommendations");
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
            throw new Error(errorData.detail || "Failed to send message");
        }

        return await response.json();
    } catch (error) {
        console.error("Chat Error:", error);
        throw error;
    }
};

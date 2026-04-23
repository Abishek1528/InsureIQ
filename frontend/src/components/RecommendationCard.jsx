import React from 'react';

const RecommendationCard = ({ recommendation }) => {
    if (!recommendation) return null;

    // Basic parsing if recommendation is a long string (optional)
    // Here we assume it's the structured recommendation string
    return (
        <div className="recommendation-card">
            <div className="card-header">
                <span className="badge">🏆 TOP RECOMMENDATION</span>
            </div>
            <div className="card-body">
                <p className="recommendation-text">{recommendation}</p>
            </div>
        </div>
    );
};

export default RecommendationCard;

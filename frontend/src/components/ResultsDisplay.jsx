import React from 'react';

const ResultsDisplay = ({ data }) => {
    if (!data) return null;

    // Helper to render markdown-like tables as HTML tables if needed
    // For now, we render the raw string as we rely on the backend's structured string
    const renderSection = (title, content) => (
        <div className="result-section">
            <h3>{title}</h3>
            <div className="section-content">
                {content.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                ))}
            </div>
        </div>
    );

    return (
        <div className="results-container">
            <div className="success-banner">
                🎉 Analysis Complete! Here is your personalized insurance roadmap.
            </div>
            
            {data.ranking_table && renderSection("Policy Ranking", data.ranking_table)}
            
            {data.top_recommendation && (
                <div className="top-recommendation">
                    <h3>🏆 Top Recommendation</h3>
                    <p>{data.top_recommendation}</p>
                </div>
            )}

            {data.detailed_reasoning && renderSection("Detailed Reasoning & Citations", data.detailed_reasoning)}
        </div>
    );
};

export default ResultsDisplay;

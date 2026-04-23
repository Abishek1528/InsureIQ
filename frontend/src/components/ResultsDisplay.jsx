import React from 'react';
import ComparisonTable from './ComparisonTable';
import CoverageTable from './CoverageTable';
import RecommendationCard from './RecommendationCard';
import Explanation from './Explanation';

const ResultsDisplay = ({ data, loading, error }) => {
    if (loading) {
        return (
            <div className="status-container">
                <div className="spinner"></div>
                <p>Analyzing policies for you...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="status-container error-state">
                <p>⚠️ {error}</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="status-container">
                <p>No results available. Please submit the form to get started.</p>
            </div>
        );
    }

    return (
        <div className="results-wrapper">
            {/* BONUS: Top Recommendation Card */}
            <RecommendationCard recommendation={data.recommendation} />

            {/* Section 1: Comparison Table */}
            <ComparisonTable data={data.comparison_table} />

            {/* Section 2: Coverage Table */}
            <CoverageTable data={data.coverage_table} />

            {/* Section 3: Explanation */}
            <Explanation text={data.explanation} />
        </div>
    );
};

export default ResultsDisplay;

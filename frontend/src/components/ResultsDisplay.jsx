import React from 'react';
import ComparisonTable from './ComparisonTable';
import CoverageTable from './CoverageTable';
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
            {/* Section 1: Comparison Table */}
            <ComparisonTable data={data.comparison_table} />

            {/* Section 2: Coverage Detail Table */}
            <CoverageTable data={data.coverage_detail_table} />

            {/* Section 3: Why This Policy */}
            <div className="section-card">
                <h3>3. WHY THIS POLICY</h3>
                <Explanation text={data.why_this_policy} />
            </div>
        </div>
    );
};

export default ResultsDisplay;

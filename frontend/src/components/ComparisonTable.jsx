import React from 'react';

const ComparisonTable = ({ data }) => {
    if (!data || data.length === 0) return null;

    const renderValue = (val) => val && val.trim() !== "" ? val : "Not mentioned";

    return (
        <div className="section-card">
            <h3>1. COMPARISON TABLE</h3>
            <div className="table-responsive">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Policy Name</th>
                            <th>Insurer</th>
                            <th>Premium (Rs/yr)</th>
                            <th>Cover Amount</th>
                            <th>Waiting Period</th>
                            <th>Key Benefit</th>
                            <th>Suitability Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item, index) => (
                            <tr key={index}>
                                <td className="font-bold">{renderValue(item.policy_name)}</td>
                                <td>{renderValue(item.insurer)}</td>
                                <td>{renderValue(item.premium)}</td>
                                <td>{renderValue(item.cover_amount)}</td>
                                <td>{renderValue(item.waiting_period)}</td>
                                <td>{renderValue(item.key_benefit)}</td>
                                <td>{renderValue(item.suitability_score)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ComparisonTable;

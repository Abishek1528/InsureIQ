import React from 'react';

const CoverageTable = ({ data }) => {
    if (!data || data.length === 0) return null;

    const getVerdictClass = (verdict) => {
        const v = verdict.toLowerCase();
        if (v.includes('good') || v.includes('high') || v.includes('suitable')) return 'verdict-good';
        if (v.includes('average') || v.includes('medium')) return 'verdict-average';
        if (v.includes('poor') || v.includes('low') || v.includes('not suitable')) return 'verdict-poor';
        return '';
    };

    return (
        <div className="section-card">
            <h3>2. COVERAGE TABLE (FROM RAG)</h3>
            <div className="table-responsive">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Criteria</th>
                            <th>User Need</th>
                            <th>Policy Match</th>
                            <th>Verdict</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item, index) => (
                            <tr key={index}>
                                <td className="font-bold">{item.criteria}</td>
                                <td>{item.user_need}</td>
                                <td>{item.policy_match}</td>
                                <td className={`verdict-cell ${getVerdictClass(item.verdict)}`}>
                                    {item.verdict}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CoverageTable;

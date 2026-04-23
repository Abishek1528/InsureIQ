import React from 'react';

const CoverageTable = ({ data }) => {
    if (!data || data.length === 0) return null;

    return (
        <div className="section-card">
            <h3>2. COVERAGE DETAIL TABLE (FROM RAG)</h3>
            <div className="table-responsive">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item, index) => (
                            <tr key={index}>
                                <td className="font-bold">{item.category}</td>
                                <td>{item.details}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CoverageTable;

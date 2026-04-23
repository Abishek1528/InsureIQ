import React from 'react';

const Explanation = ({ text }) => {
    if (!text) return null;

    return (
        <div className="section-card">
            <h3>3. EXPLANATION</h3>
            <div className="explanation-block">
                {text.split('\n\n').map((para, i) => (
                    <p key={i} className="explanation-para">{para}</p>
                ))}
            </div>
        </div>
    );
};

export default Explanation;

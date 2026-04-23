import React, { useState } from 'react';

const InsuranceForm = ({ onSubmit, loading }) => {
    const [formData, setFormData] = useState({
        name: '',
        age: '',
        lifestyle: 'Moderate',
        pre_existing_conditions: '',
        income_band: '3–6 LPA',
        city_tier: 'Tier 2'
    });

    const [errors, setErrors] = useState({});

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.name.trim()) newErrors.name = 'Name is required';
        if (!formData.age) {
            newErrors.age = 'Age is required';
        } else if (formData.age < 1 || formData.age > 100) {
            newErrors.age = 'Age must be between 1 and 100';
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validate()) {
            onSubmit(formData);
        }
    };

    return (
        <div className="form-container">
            <h2>Personalize Your Policy</h2>
            <form onSubmit={handleSubmit}>
                <div className="field-group">
                    <label>Full Name</label>
                    <input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="Enter your name"
                        className={errors.name ? 'error' : ''}
                    />
                    {errors.name && <span className="error-text">{errors.name}</span>}
                </div>

                <div className="field-group">
                    <label>Age (1-100)</label>
                    <input
                        type="number"
                        name="age"
                        value={formData.age}
                        onChange={handleChange}
                        min="1"
                        max="100"
                        className={errors.age ? 'error' : ''}
                    />
                    {errors.age && <span className="error-text">{errors.age}</span>}
                </div>

                <div className="field-group">
                    <label>Lifestyle</label>
                    <select name="lifestyle" value={formData.lifestyle} onChange={handleChange}>
                        <option value="Sedentary">Sedentary</option>
                        <option value="Moderate">Moderate</option>
                        <option value="Active">Active</option>
                    </select>
                </div>

                <div className="field-group">
                    <label>Pre-existing Conditions</label>
                    <input
                        type="text"
                        name="pre_existing_conditions"
                        value={formData.pre_existing_conditions}
                        onChange={handleChange}
                        placeholder="e.g. diabetes, hypertension"
                    />
                </div>

                <div className="field-group">
                    <label>Income Band</label>
                    <select name="income_band" value={formData.income_band} onChange={handleChange}>
                        <option value="<3 LPA">&lt;3 LPA</option>
                        <option value="3–6 LPA">3–6 LPA</option>
                        <option value="6–10 LPA">6–10 LPA</option>
                        <option value="10+ LPA">10+ LPA</option>
                    </select>
                </div>

                <div className="field-group">
                    <label>City Tier</label>
                    <select name="city_tier" value={formData.city_tier} onChange={handleChange}>
                        <option value="Tier 1">Tier 1</option>
                        <option value="Tier 2">Tier 2</option>
                        <option value="Tier 3">Tier 3</option>
                    </select>
                </div>

                <button type="submit" disabled={loading} className="submit-btn">
                    {loading ? 'Analyzing Policies...' : 'Get Recommendations'}
                </button>
            </form>
        </div>
    );
};

export default InsuranceForm;

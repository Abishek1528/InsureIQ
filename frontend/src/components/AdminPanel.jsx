import React, { useState, useEffect, useCallback } from 'react';

const AdminPanel = () => {
  const [policies, setPolicies] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [adminToken, setAdminToken] = useState('admin-secret-token'); // Default for dev

  const fetchPolicies = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/policies', {
        headers: { 'x-admin-token': adminToken }
      });
      if (response.ok) {
        const data = await response.json();
        setPolicies(data.policies || []);
      }
    } catch (error) {
      console.error("Failed to fetch policies:", error);
    }
  }, [adminToken]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload-policy', {
        method: 'POST',
        headers: { 'x-admin-token': adminToken },
        body: formData
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Policy uploaded and indexed successfully!' });
        setFile(null);
        // Reset file input
        e.target.reset();
        fetchPolicies();
      } else {
        const err = await response.json();
        setMessage({ type: 'error', text: err.detail || 'Upload failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error during upload' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (fileName) => {
    if (!window.confirm(`Are you sure you want to delete ${fileName}? This will remove all embeddings from the vector DB.`)) return;

    try {
      const response = await fetch(`http://localhost:8000/admin/delete-policy/${fileName}`, {
        method: 'DELETE',
        headers: { 'x-admin-token': adminToken }
      });

      if (response.ok) {
        setMessage({ type: 'success', text: `Policy ${fileName} deleted completely.` });
        fetchPolicies();
      } else {
        const err = await response.json();
        setMessage({ type: 'error', text: err.detail || 'Deletion failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error during deletion' });
    }
  };

  return (
    <div className="admin-panel">
      <div className="section-card">
        <h2>🛡️ Admin Policy Management</h2>
        
        {/* Token Input for Security */}
        <div className="admin-auth">
          <label>Admin Token:</label>
          <input 
            type="password" 
            value={adminToken} 
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder="Enter admin secret"
          />
        </div>

        {message.text && (
          <div className={`message-banner ${message.type}`}>
            {message.type === 'success' ? '✅' : '❌'} {message.text}
          </div>
        )}

        {/* Upload Section */}
        <div className="admin-section">
          <h3>Upload New Policy (PDF)</h3>
          <form onSubmit={handleFileUpload} className="upload-form">
            <input 
              type="file" 
              accept=".pdf" 
              onChange={(e) => setFile(e.target.files[0])}
              required
            />
            <button type="submit" disabled={loading || !file}>
              {loading ? 'Uploading & Indexing...' : 'Upload & Process'}
            </button>
          </form>
        </div>

        {/* Policy List Section */}
        <div className="admin-section">
          <h3>Currently Indexed Policies</h3>
          <div className="policy-list">
            {policies.length === 0 ? (
              <p className="no-data">No policies found in vector DB.</p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>File Name</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((p, index) => (
                    <tr key={index}>
                      <td className="font-bold">{p}</td>
                      <td>
                        <button 
                          className="delete-btn" 
                          onClick={() => handleDelete(p)}
                        >
                          Delete Completely
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;

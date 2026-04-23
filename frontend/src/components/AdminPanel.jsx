import React, { useState, useEffect, useCallback } from 'react';

const AdminPanel = () => {
  const [policies, setPolicies] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [credentials, setCredentials] = useState({ username: 'admin', password: '' });
  const [token, setToken] = useState('');
  const [uploadMetadata, setUploadMetadata] = useState({ policy_name: '', insurer: '' });
  const [editingPolicy, setEditingPolicy] = useState(null);

  const fetchPolicies = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch('http://localhost:8000/admin/policies', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPolicies(data.policies || []);
      } else if (response.status === 401) {
        setIsLoggedIn(false);
        setToken('');
      }
    } catch (error) {
      console.error("Failed to fetch policies:", error);
    }
  }, [token]);

  useEffect(() => {
    if (isLoggedIn) {
      fetchPolicies();
    }
  }, [isLoggedIn, fetchPolicies]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch('http://localhost:8000/admin/login', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        setIsLoggedIn(true);
        setMessage({ type: 'success', text: 'Logged in successfully!' });
      } else {
        setMessage({ type: 'error', text: 'Invalid username or password' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Login failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file || !token) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('policy_name', uploadMetadata.policy_name || 'Unknown');
    formData.append('insurer', uploadMetadata.insurer || 'Unknown');

    try {
      const response = await fetch('http://localhost:8000/admin/upload-policy', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Policy uploaded and indexed successfully!' });
        setFile(null);
        setUploadMetadata({ policy_name: '', insurer: '' });
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

  const handleUpdateMetadata = async (source) => {
    if (!token || !editingPolicy) return;

    try {
      const response = await fetch(`http://localhost:8000/admin/update-policy/${source}`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          policy_name: editingPolicy.policy_name,
          insurer: editingPolicy.insurer
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Metadata updated successfully!' });
        setEditingPolicy(null);
        fetchPolicies();
      } else {
        const err = await response.json();
        setMessage({ type: 'error', text: err.detail || 'Update failed' });
      }
    } catch (error) { 
      setMessage({ type: 'error', text: 'Network error during update' });
    }
  };

  const handleDelete = async (fileName) => {
    if (!token) return;
    if (!window.confirm(`Are you sure you want to delete ${fileName}? This will remove all embeddings from the vector DB immediately.`)) return;

    try {
      const response = await fetch(`http://localhost:8000/admin/delete-policy/${fileName}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
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

  if (!isLoggedIn) {
    return (
      <div className="admin-panel">
        <div className="section-card">
          <h2>🛡️ Admin Login</h2>
          {message.text && (
            <div className={`message-banner ${message.type}`}>
              {message.type === 'success' ? '✅' : '❌'} {message.text}
            </div>
          )}
          <form onSubmit={handleLogin} className="login-form">
            <div className="field-group">
              <label>Username</label>
              <input 
                type="text" 
                value={credentials.username}
                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                required
              />
            </div>
            <div className="field-group">
              <label>Password</label>
              <input 
                type="password" 
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                required
              />
            </div>
            <button type="submit" disabled={loading} className="admin-toggle-btn" style={{width: '100%', marginTop: '10px'}}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-panel">
      <div className="section-card">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h2>🛡️ Admin Policy Management</h2>
          <button onClick={() => setIsLoggedIn(false)} className="delete-btn">Logout</button>
        </div>
        
        {message.text && (
          <div className={`message-banner ${message.type}`}>
            {message.type === 'success' ? '✅' : '❌'} {message.text}
          </div>
        )}

        {/* Upload Section */}
        <div className="admin-section">
          <h3>Upload New Policy (PDF, JSON, TXT)</h3>
          <form onSubmit={handleFileUpload} className="upload-form">
            <div className="field-group">
              <label>Policy File</label>
              <input 
                type="file" 
                accept=".pdf,.json,.txt" 
                onChange={(e) => setFile(e.target.files[0])}
                required
              />
            </div>
            <div className="field-group">
              <label>Policy Name</label>
              <input 
                type="text" 
                value={uploadMetadata.policy_name}
                onChange={(e) => setUploadMetadata({...uploadMetadata, policy_name: e.target.value})}
                placeholder="e.g. Star Health Senior Citizens"
              />
            </div>
            <div className="field-group">
              <label>Insurer</label>
              <input 
                type="text" 
                value={uploadMetadata.insurer}
                onChange={(e) => setUploadMetadata({...uploadMetadata, insurer: e.target.value})}
                placeholder="e.g. Star Health Insurance"
              />
            </div>
            <button type="submit" disabled={loading || !file} className="admin-toggle-btn">
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
                    <th>Upload Date</th>
                    <th>Type</th>
                    <th>Policy Name</th>
                    <th>Insurer</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((p, index) => (
                    <tr key={index}>
                      <td className="font-bold">{p.source}</td>
                      <td style={{fontSize: '0.85em'}}>{p.upload_date}</td>
                      <td><span className={`tag ${p.file_type.toLowerCase()}`}>{p.file_type}</span></td>
                      <td>
                        {editingPolicy?.source === p.source ? (
                          <input 
                            type="text" 
                            value={editingPolicy.policy_name} 
                            onChange={(e) => setEditingPolicy({...editingPolicy, policy_name: e.target.value})}
                          />
                        ) : p.policy_name}
                      </td>
                      <td>
                        {editingPolicy?.source === p.source ? (
                          <input 
                            type="text" 
                            value={editingPolicy.insurer} 
                            onChange={(e) => setEditingPolicy({...editingPolicy, insurer: e.target.value})}
                          />
                        ) : p.insurer}
                      </td>
                      <td>
                        <div style={{display: 'flex', gap: '5px'}}>
                          {editingPolicy?.source === p.source ? (
                            <>
                              <button className="admin-toggle-btn" onClick={() => handleUpdateMetadata(p.source)}>Save</button>
                              <button className="delete-btn" onClick={() => setEditingPolicy(null)}>Cancel</button>
                            </>
                          ) : (
                            <>
                              <button className="admin-toggle-btn" onClick={() => setEditingPolicy(p)}>Edit</button>
                              <button className="delete-btn" onClick={() => handleDelete(p.source)}>Delete</button>
                            </>
                          )}
                        </div>
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

import React, { useState, useEffect, useCallback } from 'react';

const AdminPanel = () => {
  const [policies, setPolicies] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [credentials, setCredentials] = useState({ username: 'admin', password: '' });
  const [token, setToken] = useState('');

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

    try {
      const response = await fetch('http://localhost:8000/admin/upload-policy', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Policy uploaded and indexed successfully!' });
        setFile(null);
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
    if (!token) return;
    if (!window.confirm(`Are you sure you want to delete ${fileName}? This will remove all embeddings from the vector DB.`)) return;

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

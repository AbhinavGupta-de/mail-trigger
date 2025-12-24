import React, { useEffect, useState } from 'react';
import { adminApi, User, Template } from '../api';
import Modal from '../components/Modal';

const Admin: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBulkTemplate, setShowBulkTemplate] = useState(false);
  const [showBulkRecipient, setShowBulkRecipient] = useState(false);
  const [templateForm, setTemplateForm] = useState({ name: '', category: 'other', subject: '', body: '', is_default: false });
  const [recipientForm, setRecipientForm] = useState({ name: '', email: '', type: 'to' as 'to' | 'cc', is_default: true });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [usersData, templatesData] = await Promise.all([
        adminApi.getUsers(),
        adminApi.getAllTemplates()
      ]);
      setUsers(usersData);
      setTemplates(templatesData);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (id: string) => {
    if (!confirm('Delete this user and all their data?')) return;
    try {
      await adminApi.deleteUser(id);
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const handleBulkCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await adminApi.bulkCreateTemplate(templateForm as any);
      alert(result.message);
      setShowBulkTemplate(false);
      loadData();
    } catch (error) {
      alert('Failed to create templates');
    }
  };

  const handleBulkCreateRecipient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await adminApi.bulkCreateRecipient(recipientForm);
      alert(result.message);
      setShowBulkRecipient(false);
    } catch (error) {
      alert('Failed to create recipients');
    }
  };

  if (loading) return <div className="container"><p className="loading">Loading...</p></div>;

  return (
    <div className="container">
      <h1 style={{ marginBottom: '2rem' }}>Admin Panel</h1>

      <div className="admin-section">
        <div className="page-header">
          <h2>Users ({users.length})</h2>
        </div>
        <div className="list-container">
          {users.map(user => (
            <div key={user.id} className="list-item">
              <div className="item-info">
                <strong>{user.name}</strong> - {user.email}
                {user.is_admin && <span className="badge default">Admin</span>}
              </div>
              <div className="item-actions">
                <button className="btn btn-sm btn-danger" onClick={() => handleDeleteUser(user.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="admin-section">
        <div className="page-header">
          <h2>Bulk Actions</h2>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn btn-primary" onClick={() => setShowBulkTemplate(true)}>
            Add Template to All Users
          </button>
          <button className="btn btn-primary" onClick={() => setShowBulkRecipient(true)}>
            Add Recipient to All Users
          </button>
        </div>
      </div>

      <div className="admin-section">
        <h2>All Templates ({templates.length})</h2>
        <div className="list-container">
          {templates.slice(0, 20).map(t => (
            <div key={t.id} className="list-item">
              <div className="item-info">
                <strong>{t.name}</strong>
                <span className="badge">{t.category}</span>
              </div>
            </div>
          ))}
          {templates.length > 20 && <p className="empty">And {templates.length - 20} more...</p>}
        </div>
      </div>

      <Modal isOpen={showBulkTemplate} onClose={() => setShowBulkTemplate(false)} title="Add Template to All Users">
        <form onSubmit={handleBulkCreateTemplate} style={{ padding: '1.5rem' }}>
          <div className="form-group">
            <label>Name</label>
            <input type="text" value={templateForm.name} onChange={e => setTemplateForm({ ...templateForm, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Category</label>
            <select value={templateForm.category} onChange={e => setTemplateForm({ ...templateForm, category: e.target.value })}>
              <option value="leave">Leave</option>
              <option value="complaint">Complaint</option>
              <option value="request">Request</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Subject</label>
            <input type="text" value={templateForm.subject} onChange={e => setTemplateForm({ ...templateForm, subject: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Body</label>
            <textarea rows={8} value={templateForm.body} onChange={e => setTemplateForm({ ...templateForm, body: e.target.value })} required />
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => setShowBulkTemplate(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create for All</button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showBulkRecipient} onClose={() => setShowBulkRecipient(false)} title="Add Recipient to All Users">
        <form onSubmit={handleBulkCreateRecipient} style={{ padding: '1.5rem' }}>
          <div className="form-group">
            <label>Name</label>
            <input type="text" value={recipientForm.name} onChange={e => setRecipientForm({ ...recipientForm, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={recipientForm.email} onChange={e => setRecipientForm({ ...recipientForm, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Type</label>
            <select value={recipientForm.type} onChange={e => setRecipientForm({ ...recipientForm, type: e.target.value as 'to' | 'cc' })}>
              <option value="to">TO</option>
              <option value="cc">CC</option>
            </select>
          </div>
          <div className="form-group checkbox">
            <input type="checkbox" checked={recipientForm.is_default} onChange={e => setRecipientForm({ ...recipientForm, is_default: e.target.checked })} />
            <label>Set as default</label>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => setShowBulkRecipient(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Create for All</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Admin;

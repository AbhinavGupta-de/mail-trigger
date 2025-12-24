import React, { useEffect, useState } from 'react';
import { recipientsApi, Recipient } from '../api';
import Modal from '../components/Modal';

const Recipients: React.FC = () => {
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecipient, setEditingRecipient] = useState<Recipient | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    type: 'to' as 'to' | 'cc',
    is_default: true
  });

  useEffect(() => {
    loadRecipients();
  }, []);

  const loadRecipients = async () => {
    try {
      const data = await recipientsApi.getAll();
      setRecipients(data);
    } catch (error) {
      console.error('Failed to load recipients:', error);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingRecipient(null);
    setFormData({ name: '', email: '', type: 'to', is_default: true });
    setIsModalOpen(true);
  };

  const openEditModal = (recipient: Recipient) => {
    setEditingRecipient(recipient);
    setFormData({
      name: recipient.name,
      email: recipient.email,
      type: recipient.type,
      is_default: recipient.is_default
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRecipient) {
        await recipientsApi.update(editingRecipient.id, formData);
      } else {
        await recipientsApi.create(formData);
      }
      setIsModalOpen(false);
      loadRecipients();
    } catch (error) {
      alert('Failed to save recipient');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this recipient?')) return;
    try {
      await recipientsApi.delete(id);
      loadRecipients();
    } catch (error) {
      alert('Failed to delete recipient');
    }
  };

  const toRecipients = recipients.filter((r) => r.type === 'to');
  const ccRecipients = recipients.filter((r) => r.type === 'cc');

  if (loading) return <div className="container"><p className="loading">Loading...</p></div>;

  return (
    <div className="container">
      <div className="page-header">
        <h1>Recipients</h1>
        <button className="btn btn-primary" onClick={openCreateModal}>+ Add Recipient</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          <h2>TO Recipients</h2>
          <div className="list-container">
            {toRecipients.length === 0 ? (
              <p className="empty">No TO recipients. Add your warden!</p>
            ) : toRecipients.map((r) => (
              <div key={r.id} className="list-item">
                <div className="item-info">
                  <strong>{r.name}</strong> - {r.email}
                  {r.is_default && <span className="badge default">Default</span>}
                </div>
                <div className="item-actions">
                  <button className="btn btn-sm btn-outline" onClick={() => openEditModal(r)}>Edit</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2>CC Recipients</h2>
          <div className="list-container">
            {ccRecipients.length === 0 ? (
              <p className="empty">No CC recipients.</p>
            ) : ccRecipients.map((r) => (
              <div key={r.id} className="list-item">
                <div className="item-info">
                  <strong>{r.name}</strong> - {r.email}
                  {r.is_default && <span className="badge default">Default</span>}
                </div>
                <div className="item-actions">
                  <button className="btn btn-sm btn-outline" onClick={() => openEditModal(r)}>Edit</button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingRecipient ? 'Edit Recipient' : 'Add Recipient'}>
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          <div className="form-group">
            <label>Name</label>
            <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required placeholder="e.g., Warden" />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} required placeholder="warden@college.edu" />
          </div>
          <div className="form-group">
            <label>Type</label>
            <select value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value as 'to' | 'cc' })}>
              <option value="to">TO (Primary)</option>
              <option value="cc">CC (Copy)</option>
            </select>
          </div>
          <div className="form-group checkbox">
            <input type="checkbox" checked={formData.is_default} onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })} />
            <label>Use as default</label>
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => setIsModalOpen(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary">Save</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Recipients;

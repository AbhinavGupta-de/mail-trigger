import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { templatesApi, Template } from '../api';
import Modal from '../components/Modal';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    category: 'other',
    subject: '',
    body: '',
    is_default: false
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await templatesApi.getAll();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingTemplate(null);
    setFormData({
      name: '',
      category: 'other',
      subject: '',
      body: '',
      is_default: false
    });
    setIsModalOpen(true);
  };

  const openEditModal = (template: Template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      category: template.category,
      subject: template.subject,
      body: template.body,
      is_default: template.is_default
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTemplate) {
        await templatesApi.update(editingTemplate.id, formData);
      } else {
        await templatesApi.create(formData as any);
      }
      setIsModalOpen(false);
      loadTemplates();
    } catch (error) {
      console.error('Failed to save template:', error);
      alert('Failed to save template');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await templatesApi.delete(id);
      loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('Failed to delete template');
    }
  };

  if (loading) {
    return (
      <div className="container">
        <p className="loading">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="page-header">
        <h1>Email Templates</h1>
        <button className="btn btn-primary" onClick={openCreateModal}>
          + New Template
        </button>
      </div>

      {templates.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <p className="empty">No templates yet. Create your first template!</p>
          </div>
        </div>
      ) : (
        <div className="cards-grid">
          {templates.map((t) => (
            <div key={t.id} className="card">
              <div className="card-header">
                <h3>{t.name}</h3>
                <div>
                  <span className="badge">{t.category}</span>
                  {t.is_default && <span className="badge default">Default</span>}
                </div>
              </div>
              <div className="card-body">
                <p>
                  <strong>Subject:</strong> {t.subject}
                </p>
                <p className="preview">{t.body.substring(0, 100)}...</p>
                <p>
                  <small>Variables: {t.variables.join(', ') || 'None'}</small>
                </p>
              </div>
              <div className="card-footer">
                <Link to={`/send?template=${t.id}`} className="btn btn-sm">
                  Use
                </Link>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => openEditModal(t)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => handleDelete(t.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTemplate ? 'Edit Template' : 'Create Template'}
      >
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          <div className="form-group">
            <label htmlFor="name">Template Name</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="e.g., Leave Application"
            />
          </div>

          <div className="form-group">
            <label htmlFor="category">Category</label>
            <select
              id="category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
            >
              <option value="leave">Leave</option>
              <option value="complaint">Complaint</option>
              <option value="request">Request</option>
              <option value="announcement">Announcement</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="subject">Subject</label>
            <input
              type="text"
              id="subject"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              required
              placeholder="e.g., Leave Application - {{date}}"
            />
            <small>Use {'{{variable}}'} for dynamic content</small>
          </div>

          <div className="form-group">
            <label htmlFor="body">Body</label>
            <textarea
              id="body"
              rows={10}
              value={formData.body}
              onChange={(e) => setFormData({ ...formData, body: e.target.value })}
              required
              placeholder="Dear Sir/Madam,&#10;&#10;I, {{name}}, am writing to..."
            />
            <small>Available: {'{{name}}'}, {'{{email}}'}, {'{{date}}'}, or custom variables</small>
          </div>

          <div className="form-group checkbox">
            <input
              type="checkbox"
              id="is_default"
              checked={formData.is_default}
              onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
            />
            <label htmlFor="is_default">Set as default template</label>
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Template
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Templates;

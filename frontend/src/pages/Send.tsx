import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { templatesApi, emailApi, Template } from '../api';
import Modal from '../components/Modal';

const Send: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [toEmails, setToEmails] = useState<string[]>([]);
  const [ccEmails, setCcEmails] = useState<string[]>([]);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [templateVars, setTemplateVars] = useState<string[]>([]);
  const [newTo, setNewTo] = useState('');
  const [newCc, setNewCc] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await templatesApi.getAll();
      setTemplates(data);

      const templateId = searchParams.get('template');
      if (templateId) {
        selectTemplate(templateId);
      } else {
        const defaultTemplate = data.find(t => t.is_default);
        if (defaultTemplate) selectTemplate(defaultTemplate.id);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectTemplate = async (id: string) => {
    setSelectedTemplate(id);
    try {
      const preview = await emailApi.previewTemplate(id);
      setSubject(preview.subject);
      setBody(preview.body);
      setToEmails(preview.default_to.map(r => r.email));
      setCcEmails(preview.default_cc.map(r => r.email));

      const autoFillVars = ['name', 'email', 'date'];
      const userVars = preview.variables.filter(v => !autoFillVars.includes(v));
      setTemplateVars(userVars);
      setVariables({});
    } catch (error) {
      console.error('Failed to load template preview:', error);
    }
  };

  const addEmail = (type: 'to' | 'cc') => {
    const email = type === 'to' ? newTo.trim() : newCc.trim();
    if (!email) return;
    if (type === 'to') {
      if (!toEmails.includes(email)) setToEmails([...toEmails, email]);
      setNewTo('');
    } else {
      if (!ccEmails.includes(email)) setCcEmails([...ccEmails, email]);
      setNewCc('');
    }
  };

  const removeEmail = (type: 'to' | 'cc', email: string) => {
    if (type === 'to') setToEmails(toEmails.filter(e => e !== email));
    else setCcEmails(ccEmails.filter(e => e !== email));
  };

  const handleSend = async () => {
    if (toEmails.length === 0) {
      alert('Please add at least one recipient');
      return;
    }

    setSending(true);
    try {
      const result = await emailApi.send({
        template_id: selectedTemplate || undefined,
        to: toEmails,
        cc: ccEmails,
        subject,
        body,
        variables
      });

      if (result.success) {
        alert('Email sent successfully!');
        window.location.href = '/history';
      } else {
        alert(result.message || 'Failed to send email');
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
      setShowPreview(false);
    }
  };

  if (loading) return <div className="container"><p className="loading">Loading...</p></div>;

  return (
    <div className="container">
      <h1 style={{ marginBottom: '2rem' }}>Send Email</h1>

      <div className="send-container">
        <div className="template-selector">
          <h2>Select Template</h2>
          <div className="template-buttons">
            {templates.map(t => (
              <button
                key={t.id}
                type="button"
                className={`template-btn ${selectedTemplate === t.id ? 'selected' : ''}`}
                onClick={() => selectTemplate(t.id)}
              >
                {t.name}
                {t.is_default && <small>(Default)</small>}
              </button>
            ))}
          </div>
        </div>

        <div className="email-form-container">
          <div className="form-group">
            <label>To</label>
            <div className="recipient-tags">
              {toEmails.map(e => (
                <span key={e} className="tag">{e} <button type="button" onClick={() => removeEmail('to', e)}>&times;</button></span>
              ))}
            </div>
            <input
              type="email"
              value={newTo}
              onChange={e => setNewTo(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addEmail('to'))}
              placeholder="Add email and press Enter"
            />
          </div>

          <div className="form-group">
            <label>CC</label>
            <div className="recipient-tags">
              {ccEmails.map(e => (
                <span key={e} className="tag">{e} <button type="button" onClick={() => removeEmail('cc', e)}>&times;</button></span>
              ))}
            </div>
            <input
              type="email"
              value={newCc}
              onChange={e => setNewCc(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addEmail('cc'))}
              placeholder="Add CC email and press Enter"
            />
          </div>

          {templateVars.length > 0 && (
            <div className="form-group">
              <label>Fill Variables</label>
              <div className="variables-inputs">
                {templateVars.map(v => (
                  <div key={v} className="variable-input">
                    <label>{v}</label>
                    <input
                      type="text"
                      value={variables[v] || ''}
                      onChange={e => setVariables({ ...variables, [v]: e.target.value })}
                      placeholder={`Enter ${v}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="form-group">
            <label>Subject</label>
            <input type="text" value={subject} onChange={e => setSubject(e.target.value)} required />
          </div>

          <div className="form-group">
            <label>Body</label>
            <textarea rows={12} value={body} onChange={e => setBody(e.target.value)} required />
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => setShowPreview(true)}>Preview</button>
            <button type="button" className="btn btn-primary" onClick={handleSend} disabled={sending}>
              {sending ? 'Sending...' : 'Send Email'}
            </button>
          </div>
        </div>
      </div>

      <Modal isOpen={showPreview} onClose={() => setShowPreview(false)} title="Email Preview" size="lg">
        <div className="email-preview">
          <div className="preview-field"><strong>To:</strong> {toEmails.join(', ') || 'None'}</div>
          <div className="preview-field"><strong>CC:</strong> {ccEmails.join(', ') || 'None'}</div>
          <div className="preview-field"><strong>Subject:</strong> {subject}</div>
          <div className="preview-body">{body}</div>
        </div>
        <div className="form-actions" style={{ padding: '1.5rem' }}>
          <button className="btn btn-outline" onClick={() => setShowPreview(false)}>Edit</button>
          <button className="btn btn-primary" onClick={handleSend} disabled={sending}>
            {sending ? 'Sending...' : 'Send Now'}
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default Send;

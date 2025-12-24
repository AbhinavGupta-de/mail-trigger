import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { templatesApi, recipientsApi, emailApi, Template, EmailLog } from '../api';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [defaultRecipients, setDefaultRecipients] = useState<{
    to: { name: string; email: string }[];
    cc: { name: string; email: string }[];
  }>({ to: [], cc: [] });
  const [recentEmails, setRecentEmails] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [templatesData, recipientsData, logsData] = await Promise.all([
          templatesApi.getAll(),
          recipientsApi.getDefaults(),
          emailApi.getLogs()
        ]);
        setTemplates(templatesData);
        setDefaultRecipients(recipientsData);
        setRecentEmails(logsData.slice(0, 5));
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="container">
        <p className="loading">Loading...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="dashboard">
        <h1>Welcome, {user?.name}!</h1>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="action-cards">
            <Link to="/send" className="action-card">
              <div className="action-icon">+</div>
              <h3>Send Email</h3>
              <p>Send an email using a template</p>
            </Link>

            <Link to="/templates" className="action-card">
              <div className="action-icon">T</div>
              <h3>Manage Templates</h3>
              <p>Create and edit email templates</p>
            </Link>

            <Link to="/recipients" className="action-card">
              <div className="action-icon">@</div>
              <h3>Manage Recipients</h3>
              <p>Add warden and CC recipients</p>
            </Link>
          </div>
        </div>

        <div className="dashboard-section">
          <h2>Your Templates</h2>
          <div className="list-container">
            {templates.length === 0 ? (
              <p className="empty">
                No templates yet. <Link to="/templates">Create one</Link>
              </p>
            ) : (
              templates.slice(0, 3).map((t) => (
                <div key={t.id} className="list-item">
                  <div className="item-info">
                    <strong>{t.name}</strong>
                    <span className="badge">{t.category}</span>
                  </div>
                  <div className="item-actions">
                    <Link to={`/send?template=${t.id}`} className="btn btn-sm">
                      Use
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="dashboard-section">
          <h2>Default Recipients</h2>
          <div className="list-container">
            {defaultRecipients.to.length === 0 && defaultRecipients.cc.length === 0 ? (
              <p className="empty">
                No default recipients. <Link to="/recipients">Add some</Link>
              </p>
            ) : (
              [...defaultRecipients.to.map((r) => ({ ...r, type: 'to' })),
               ...defaultRecipients.cc.map((r) => ({ ...r, type: 'cc' }))].map((r, i) => (
                <div key={i} className="list-item">
                  <div className="item-info">
                    <strong>{r.name}</strong> - {r.email}
                    <span className={`badge ${r.type}`}>{r.type.toUpperCase()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="dashboard-section">
          <h2>Recent Emails</h2>
          <div className="list-container">
            {recentEmails.length === 0 ? (
              <p className="empty">No emails sent yet.</p>
            ) : (
              recentEmails.map((log) => (
                <div key={log.id} className="list-item">
                  <div className="item-info">
                    <strong>{log.subject}</strong>
                    <span className={`badge ${log.status}`}>{log.status}</span>
                    <small>{new Date(log.sent_at).toLocaleString()}</small>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

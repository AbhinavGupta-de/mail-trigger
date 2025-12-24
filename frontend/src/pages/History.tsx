import React, { useEffect, useState } from 'react';
import { emailApi, EmailLog } from '../api';

const History: React.FC = () => {
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      const data = await emailApi.getLogs();
      setLogs(data);
    } catch (error) {
      console.error('Failed to load email logs:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="container"><p className="loading">Loading...</p></div>;

  return (
    <div className="container">
      <h1 style={{ marginBottom: '2rem' }}>Email History</h1>

      {logs.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <p className="empty">No emails sent yet.</p>
          </div>
        </div>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Subject</th>
              <th>To</th>
              <th>CC</th>
              <th>Status</th>
              <th>Sent At</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => (
              <tr key={log.id}>
                <td>{log.subject}</td>
                <td>{log.to.join(', ')}</td>
                <td>{log.cc.join(', ') || '-'}</td>
                <td><span className={`badge ${log.status}`}>{log.status}</span></td>
                <td>{new Date(log.sent_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default History;

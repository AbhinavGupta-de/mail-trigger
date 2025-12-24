import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true
});

// Types
export interface User {
  id: string;
  email: string;
  name: string;
  is_admin: boolean;
  authenticated: boolean;
}

export interface Template {
  id: string;
  name: string;
  category: string;
  subject: string;
  body: string;
  variables: string[];
  is_default: boolean;
  created_at: string;
}

export interface Recipient {
  id: string;
  name: string;
  email: string;
  type: 'to' | 'cc';
  is_default: boolean;
  created_at: string;
}

export interface EmailLog {
  id: string;
  template_id: string | null;
  to: string[];
  cc: string[];
  subject: string;
  status: 'sent' | 'failed';
  sent_at: string;
}

// Auth API
export const authApi = {
  getMe: async (): Promise<User> => {
    const { data } = await api.get('/me');
    return data;
  },
  login: () => {
    window.location.href = '/auth/login';
  },
  logout: () => {
    window.location.href = '/auth/logout';
  }
};

// Templates API
export const templatesApi = {
  getAll: async (): Promise<Template[]> => {
    const { data } = await api.get('/templates');
    return data;
  },
  get: async (id: string): Promise<Template> => {
    const { data } = await api.get(`/templates/${id}`);
    return data;
  },
  create: async (template: Omit<Template, 'id' | 'variables' | 'created_at'>): Promise<Template> => {
    const { data } = await api.post('/templates', template);
    return data;
  },
  update: async (id: string, template: Partial<Template>): Promise<Template> => {
    const { data } = await api.put(`/templates/${id}`, template);
    return data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/templates/${id}`);
  }
};

// Recipients API
export const recipientsApi = {
  getAll: async (): Promise<Recipient[]> => {
    const { data } = await api.get('/recipients');
    return data;
  },
  getDefaults: async (): Promise<{ to: { name: string; email: string }[]; cc: { name: string; email: string }[] }> => {
    const { data } = await api.get('/recipients/defaults');
    return data;
  },
  create: async (recipient: Omit<Recipient, 'id' | 'created_at'>): Promise<Recipient> => {
    const { data } = await api.post('/recipients', recipient);
    return data;
  },
  update: async (id: string, recipient: Partial<Recipient>): Promise<Recipient> => {
    const { data } = await api.put(`/recipients/${id}`, recipient);
    return data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/recipients/${id}`);
  }
};

// Email API
export const emailApi = {
  send: async (data: {
    template_id?: string;
    to: string[];
    cc: string[];
    subject: string;
    body: string;
    variables: Record<string, string>;
  }): Promise<{ success: boolean; message_id?: string; message: string }> => {
    const { data: response } = await api.post('/email/send', data);
    return response;
  },
  sendWithTemplate: async (data: {
    template_id: string;
    to?: string[];
    cc?: string[];
    variables: Record<string, string>;
  }): Promise<{ success: boolean; message_id?: string; message: string }> => {
    const { data: response } = await api.post('/email/send-template', data);
    return response;
  },
  previewTemplate: async (id: string): Promise<{
    template_name: string;
    subject: string;
    body: string;
    variables: string[];
    default_to: { name: string; email: string }[];
    default_cc: { name: string; email: string }[];
  }> => {
    const { data } = await api.get(`/email/preview-template/${id}`);
    return data;
  },
  getLogs: async (): Promise<EmailLog[]> => {
    const { data } = await api.get('/email/logs');
    return data;
  }
};

// Admin API
export const adminApi = {
  getUsers: async (): Promise<User[]> => {
    const { data } = await api.get('/admin/users');
    return data;
  },
  deleteUser: async (id: string): Promise<void> => {
    await api.delete(`/admin/users/${id}`);
  },
  getAllTemplates: async (): Promise<Template[]> => {
    const { data } = await api.get('/admin/templates');
    return data;
  },
  bulkCreateTemplate: async (template: Omit<Template, 'id' | 'variables' | 'created_at'>): Promise<{ message: string }> => {
    const { data } = await api.post('/admin/templates/bulk-create', template);
    return data;
  },
  bulkCreateRecipient: async (recipient: Omit<Recipient, 'id' | 'created_at'>): Promise<{ message: string }> => {
    const { data } = await api.post('/admin/recipients/bulk-create', recipient);
    return data;
  }
};

export default api;

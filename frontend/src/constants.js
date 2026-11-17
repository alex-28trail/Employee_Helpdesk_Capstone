// Must match backend/app/schemas/enums.py and the PostgreSQL CHECK constraints.
export const STATUSES = ['New', 'In Progress', 'Resolved']
export const PRIORITIES = ['Low', 'Medium', 'High']
export const CATEGORIES = ['Hardware', 'Software', 'Network', 'Access', 'Other']

export const formatDate = (iso) =>
  iso ? new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '-'

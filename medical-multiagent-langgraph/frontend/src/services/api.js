import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE });

export const startSession = () => api.post('/sessions/start');

export const startConsultation = (patientCase) =>
  api.post('/consultation/start', { patient_initial_case: patientCase });

export const resumeWithAnswer = (threadId, patientAnswer) =>
  api.post(`/consultation/resume?thread_id=${threadId}`, { patient_answer: patientAnswer });

export const resumeWithPhysician = (threadId, physicianTreatment) =>
  api.post(`/consultation/resume?thread_id=${threadId}`, { physician_treatment: physicianTreatment });

export const getConsultation = (threadId) =>
  api.get(`/consultation/${threadId}`);

export const getReport = (threadId) =>
  api.get(`/consultation/${threadId}/report`);

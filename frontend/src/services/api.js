import axios from 'axios';

// Aponta para o servidor FastAPI que está rodando localmente
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

export const getTelemetry = async (year, gp, driver) => {
  try {
    const response = await api.get(`/telemetry?year=${year}&gp=${gp}&driver=${driver}`);
    return response.data;
  } catch (error) {
    console.error("Erro ao buscar telemetria:", error);
    throw error;
  }
};

export const getStrategyPrediction = async (year, gp, driver) => {
    try {
      const response = await api.get(`/predict-strategy?year=${year}&gp=${gp}&driver=${driver}`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar predição:", error);
      throw error;
    }
  };

export default api;
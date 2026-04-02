import { useState } from 'react';
import { getStrategyPrediction, getTelemetry } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [laps, setLaps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStrategyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [predictionResult, telemetryResult] = await Promise.all([
        getStrategyPrediction(2023, 'Brazil', 'VER'),
        getTelemetry(2023, 'Brazil', 'VER')
      ]);
      
      setData(predictionResult);
      
      const validLaps = telemetryResult.laps.filter(lap => lap.Time !== null);
      setLaps(validLaps);

    } catch (err) {
      setError('Falha ao carregar os dados do Pit Wall.');
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = async () => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/export-report', data, {
        responseType: 'blob',
      });
      
      const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(pdfBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `estrategia_${data.driver}.pdf`);
      document.body.appendChild(link);
      link.click();
      
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Erro no download:", err);
      alert("Erro ao baixar o relatório oficial.");
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#1e1e1e', color: '#fff', minHeight: '100vh' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '10px', marginBottom: '20px' }}>
        <h1 style={{ margin: 0 }}>F1 Pit Wall - Live Strategy</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          {data && (
            <button 
              onClick={downloadReport} 
              style={{ padding: '10px 20px', backgroundColor: '#4a4a4a', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
            >
              Baixar Relatório (PDF)
            </button>
          )}
          <button 
            onClick={fetchStrategyData} 
            disabled={loading}
            style={{ padding: '10px 20px', backgroundColor: '#e10600', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
          >
            {loading ? 'Analisando...' : 'Carregar Telemetria'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#ff4c4c', marginBottom: '20px' }}>{error}</div>}

      {data && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
            <h2>Status do Piloto ({data.driver})</h2>
            <p><strong>Composto Analisado:</strong> {data.prediction.composto_analisado}</p>
            <p><strong>Degradação:</strong> +{data.prediction.degradacao_segundos_por_volta}s por volta</p>
          </div>

          <div style={{ backgroundColor: data.action.includes('PIT STOP') ? '#ff4c4c' : '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
            <h2>Recomendação do Motor (ML)</h2>
            <h3 style={{ margin: 0 }}>{data.action}</h3>
          </div>
        </div>
      )}

      {laps.length > 0 && (
        <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px', height: '400px' }}>
          <h2 style={{ marginTop: 0 }}>Análise de Ritmo (Lap Times)</h2>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={laps} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="LapNumber" stroke="#ccc" />
              <YAxis stroke="#ccc" domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} />
              <Line type="monotone" dataKey="Time" stroke="#e10600" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
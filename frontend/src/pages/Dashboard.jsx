import { useState } from 'react';
import { getStrategyPrediction, getTelemetry } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

export default function Dashboard() {
  const [year, setYear] = useState('2023');
  const [gp, setGp] = useState('Brazil');
  const [driver, setDriver] = useState('VER');
  
  const [data, setData] = useState(null);
  const [laps, setLaps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStrategyData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [predictionResult, telemetryResult] = await Promise.all([
        getStrategyPrediction(year, gp, driver),
        getTelemetry(year, gp, driver)
      ]);
      
      setData(predictionResult);
      const validLaps = telemetryResult.laps.filter(lap => lap.Time !== null);
      setLaps(validLaps);
    } catch (err) {
      setError('Falha ao carregar dados. Verifique o Ano, GP (em inglês) e Sigla do Piloto.');
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
      link.setAttribute('download', `estrategia_${data.driver}_${gp}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      alert("Erro ao baixar o relatório oficial.");
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#1e1e1e', color: '#fff', minHeight: '100vh' }}>
      
      {/* Barra de Filtros e Controlos */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'flex-end', borderBottom: '1px solid #333', paddingBottom: '20px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', color: '#aaa' }}>ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', color: '#aaa' }}>GRANDE PRÉMIO</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} placeholder="Ex: Monaco" style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff' }} />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '12px', color: '#aaa' }}>PILOTO (SIGLA)</label>
          <input type="text" value={driver} onChange={(e) => setDriver(e.target.value.toUpperCase())} maxLength={3} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>

        <div style={{ display: 'flex', gap: '10px', marginLeft: 'auto' }}>
          {data && (
            <button onClick={downloadReport} style={{ padding: '10px 20px', backgroundColor: '#4a4a4a', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
              Relatório PDF
            </button>
          )}
          <button onClick={fetchStrategyData} disabled={loading} style={{ padding: '10px 20px', backgroundColor: '#e10600', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
            {loading ? 'A processar...' : 'Analisar Telemetria'}
          </button>
        </div>
      </div>

      {error && <div style={{ color: '#ff4c4c', marginBottom: '20px' }}>{error}</div>}

      {/* Cards de Status */}
      {data && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '20px' }}>
          <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px', borderLeft: '4px solid #e10600' }}>
            <h2 style={{ margin: '0 0 10px 0' }}>Status: {data.driver}</h2>
            <p><strong>Pneu:</strong> {data.prediction.composto_analisado} ({data.prediction.degradacao_segundos_por_volta}s/volta)</p>
          </div>
          <div style={{ backgroundColor: data.action.includes('PIT STOP') ? '#7a0000' : '#004a00', padding: '20px', borderRadius: '8px' }}>
            <h2 style={{ margin: '0 0 10px 0' }}>Decisão de Estratégia</h2>
            <h3 style={{ margin: 0 }}>{data.action}</h3>
          </div>
        </div>
      )}

      {/* Gráfico de Ritmo */}
      {laps.length > 0 && (
        <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px', height: '400px' }}>
          <h2 style={{ marginTop: 0 }}>Análise de Ritmo em Tempo Real</h2>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={laps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="LapNumber" stroke="#ccc" label={{ value: 'Volta', position: 'insideBottom', offset: -5, fill: '#ccc' }} />
              <YAxis stroke="#ccc" domain={['auto', 'auto']} label={{ value: 'Tempo (s)', angle: -90, position: 'insideLeft', fill: '#ccc' }} />
              <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} />
              <Line type="monotone" dataKey="Time" stroke="#e10600" strokeWidth={2} dot={false} animationDuration={1000} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
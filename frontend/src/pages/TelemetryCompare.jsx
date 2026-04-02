import { useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function TelemetryCompare() {
  const [year, setYear] = useState('2023');
  const [gp, setGp] = useState('Brazil');
  const [driver1, setDriver1] = useState('VER');
  const [driver2, setDriver2] = useState('NOR');
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTelemetry = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/telemetry-compare?year=${year}&gp=${gp}&driver1=${driver1}&driver2=${driver2}`);
      setData(response.data);
    } catch (err) {
      setError('Falha ao carregar telemetria cruzada. Verifique as siglas dos pilotos.');
    } finally {
      setLoading(false);
    }
  };

  const downloadTelemetryReport = async () => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/export-telemetry-report', data, {
        responseType: 'blob',
      });
      const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `telemetria_${data.driver1}_vs_${data.driver2}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      alert("Erro ao baixar o relatório de telemetria.");
    }
  };

  // Cores fixas para os pilotos para facilitar a leitura visual
  const colorD1 = "#f84b45";
  const colorD2 = "#3e7bf5"; 

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#1e1e1e', color: '#fff', minHeight: '100vh' }}>
      
      {/* Barra de Controles */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'flex-end', borderBottom: '1px solid #333', paddingBottom: '20px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa' }}>ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa' }}>GP</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa' }}>PILOTO 1</label>
          <input type="text" value={driver1} onChange={(e) => setDriver1(e.target.value.toUpperCase())} maxLength={3} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa' }}>PILOTO 2</label>
          <input type="text" value={driver2} onChange={(e) => setDriver2(e.target.value.toUpperCase())} maxLength={3} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>

        <button onClick={fetchTelemetry} disabled={loading} style={{ padding: '10px 20px', backgroundColor: '#00aeeef', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer', marginLeft: 'auto' }}>
          {loading ? 'Extraindo Sensores...' : 'Análise Profunda'}
        </button>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginLeft: 'auto' }}>
          {data && (
            <button onClick={downloadTelemetryReport} style={{ padding: '10px 20px', backgroundColor: '#4a4a4a', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
              Baixar Relatório (PDF)
            </button>
          )}
          <button onClick={fetchTelemetry} disabled={loading} style={{ padding: '10px 20px', backgroundColor: '#00aeeef', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
            {loading ? 'Extraindo Sensores...' : 'Análise Profunda'}
          </button>
        </div>

      {error && <div style={{ color: '#ff4c4c', marginBottom: '20px' }}>{error}</div>}

      {data && (
        <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
            <h2 style={{ margin: 0 }}>Análise de Telemetria Sincronizada</h2>
            <div style={{ textAlign: 'right' }}>
              <p style={{ margin: 0, color: colorD1 }}><strong>{data.driver1}:</strong> {data.lap_time_1}s</p>
              <p style={{ margin: 0, color: colorD2 }}><strong>{data.driver2}:</strong> {data.lap_time_2}s</p>
            </div>
          </div>
          
          {/* VELOCIDADE */}
          <div style={{ height: '300px', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0 0 10px 0' }}>Velocidade (km/h)</h3>
            <ResponsiveContainer width="100%" height="100%">
              {/* O syncId="f1-telemetry" conecta todos os gráficos */}
              <LineChart data={data.telemetry} syncId="f1-telemetry">
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tickFormatter={(val) => `${(val/1000).toFixed(1)}km`} stroke="#ccc" hide />
                <YAxis domain={['auto', 'auto']} stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} labelFormatter={(val) => `Distância: ${Math.round(val)}m`} />
                <Legend verticalAlign="top" height={36}/>
                <Line type="monotone" dataKey={`Speed_${data.driver1}`} stroke={colorD1} strokeWidth={2} dot={false} name={data.driver1} />
                <Line type="monotone" dataKey={`Speed_${data.driver2}`} stroke={colorD2} strokeWidth={2} dot={false} name={data.driver2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* ACELERADOR */}
          <div style={{ height: '150px', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0 0 10px 0' }}>Acelerador (%)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.telemetry} syncId="f1-telemetry">
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} hide />
                <YAxis domain={[0, 100]} stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} labelFormatter={() => ""} />
                <Line type="stepAfter" dataKey={`Throttle_${data.driver1}`} stroke={colorD1} strokeWidth={2} dot={false} />
                <Line type="stepAfter" dataKey={`Throttle_${data.driver2}`} stroke={colorD2} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* FREIO */}
          <div style={{ height: '150px', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0 0 10px 0' }}>Freio (%)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.telemetry} syncId="f1-telemetry">
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} hide />
                <YAxis domain={[0, 100]} stroke="#ccc" />
                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} labelFormatter={() => ""} />
                <Line type="stepAfter" dataKey={`Brake_${data.driver1}`} stroke={colorD1} strokeWidth={2} dot={false} />
                <Line type="stepAfter" dataKey={`Brake_${data.driver2}`} stroke={colorD2} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* GRÁFICO 4: MARCHA (nGear) */}
          <div style={{ height: '150px' }}>
            <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0 0 10px 0' }}>Marcha</h3>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.telemetry} syncId="f1-telemetry">
                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                <XAxis dataKey="Distance" type="number" domain={['dataMin', 'dataMax']} tickFormatter={(val) => `${(val/1000).toFixed(1)}km`} stroke="#ccc" />
                <YAxis domain={[1, 8]} stroke="#ccc" tickCount={8} />
                <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none', color: '#fff' }} labelFormatter={(val) => `Distância: ${Math.round(val)}m`} />
                <Line type="stepAfter" dataKey={`nGear_${data.driver1}`} stroke={colorD1} strokeWidth={2} dot={false} />
                <Line type="stepAfter" dataKey={`nGear_${data.driver2}`} stroke={colorD2} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

        </div>
      )}
    </div>
  );
}
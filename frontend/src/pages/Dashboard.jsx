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
    <div className="min-h-screen p-5 font-sans text-white bg-[#1e1e1e]">
      
      {/* Barra de Filtros e Controlos */}
      <div className="flex flex-wrap items-end gap-4 pb-5 mb-5 border-b border-[#333]">
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">GRANDE PRÉMIO</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} placeholder="Ex: Monaco" className="p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">PILOTO (SIGLA)</label>
          <input type="text" value={driver} onChange={(e) => setDriver(e.target.value.toUpperCase())} maxLength={3} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>

        <div className="flex gap-2 ml-auto">
          {data && (
            <button onClick={downloadReport} className="px-5 py-2 text-white bg-[#4a4a4a] border-none rounded cursor-pointer">
              Relatório PDF
            </button>
          )}
          <button onClick={fetchStrategyData} disabled={loading} className="px-5 py-2 text-white bg-[#e10600] border-none rounded cursor-pointer disabled:opacity-75">
            {loading ? 'A processar...' : 'Analisar Telemetria'}
          </button>
        </div>
      </div>

      {error && <div className="mb-5 text-[#ff4c4c]">{error}</div>}

      {/* Cards de Status */}
      {data && (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-5 mb-5">
          <div className="p-5 bg-[#2a2a2a] border-l-4 border-[#e10600] rounded-lg">
            <h2 className="m-0 mb-2 text-xl font-bold">Status: {data.driver}</h2>
            <p><strong>Pneu:</strong> {data.prediction.composto_analisado} ({data.prediction.degradacao_segundos_por_volta}s/volta)</p>
          </div>
          <div className={`p-5 rounded-lg ${data.action.includes('PIT STOP') ? 'bg-[#7a0000]' : 'bg-[#004a00]'}`}>
            <h2 className="m-0 mb-2 text-xl font-bold">Decisão de Estratégia</h2>
            <h3 className="m-0 text-lg">{data.action}</h3>
          </div>
        </div>
      )}

      {/* Gráfico de Ritmo */}
      {laps.length > 0 && (
        <div className="h-[400px] p-5 bg-[#2a2a2a] rounded-lg">
          <h2 className="mt-0 text-xl font-bold">Análise de Ritmo em Tempo Real</h2>
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
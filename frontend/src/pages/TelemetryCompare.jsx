import { useState } from 'react';
import axios from 'axios';
import { 
  LineChart, Line, 
  ScatterChart, Scatter, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';

export default function TelemetryCompare() {
  const [year, setYear] = useState('2025');
  const [gp, setGp] = useState('Brazil');
  const [driver1, setDriver1] = useState('VER');
  const [driver2, setDriver2] = useState('NOR');
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [activeIndex, setActiveIndex] = useState(null);

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
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Erro ao baixar o relatório de telemetria.");
    }
  };

  // Cores fixas para os pilotos para facilitar a leitura visual
  const colorD1 = "#e10600"; // Vermelho
  const colorD2 = "#0055ff"; // Azul

  return (
    <div className="min-h-screen p-5 font-sans text-white bg-[#1e1e1e]">
      
      {/* Barra de Controles */}
      <div className="flex flex-wrap items-end gap-4 pb-5 mb-5 border-b border-[#333]">
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">GP</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} className="p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">PILOTO 1</label>
          <input type="text" value={driver1} onChange={(e) => setDriver1(e.target.value.toUpperCase())} maxLength={3} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">PILOTO 2</label>
          <input type="text" value={driver2} onChange={(e) => setDriver2(e.target.value.toUpperCase())} maxLength={3} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>

        <div className="flex gap-2 ml-auto">
          {data && (
            <button onClick={downloadTelemetryReport} className="px-5 py-2 text-white bg-[#4a4a4a] border-none rounded cursor-pointer">
              Baixar PDF
            </button>
          )}
          <button onClick={fetchTelemetry} disabled={loading} className="px-5 py-2 text-white bg-[#61C75D] border-none rounded cursor-pointer disabled:opacity-75">
          {loading ? 'Processando Grid...' : 'Comparar Telemetria'}
        </button>
        </div>
      </div>

      {error && <div className="mb-5 text-[#ff4c4c]">{error}</div>}

      {data && (
        <div className="p-5 bg-[#2a2a2a] rounded-lg">
          
          <div className="flex justify-between mb-4">
            <h2 className="m-0 text-xl font-bold">Análise de Telemetria Sincronizada</h2>
            <div className="text-right">
              <p className="m-0" style={{ color: colorD1 }}><strong>{data.driver1}:</strong> {data.lap_time_1}s</p>
              <p className="m-0" style={{ color: colorD2 }}><strong>{data.driver2}:</strong> {data.lap_time_2}s</p>
            </div>
          </div>

          {/* MAPA DA PISTA */}
          <div className="h-[350px] mb-5 bg-[#1a1a1a] border border-[#333] rounded-lg">
            <h3 className="mt-4 ml-4 text-sm text-[#aaa]">Traçado do Circuito (GPS X/Y)</h3>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <XAxis type="number" dataKey={`X_${data.driver1}`} name="Eixo X" hide domain={['dataMin', 'dataMax']} />
                <YAxis type="number" dataKey={`Y_${data.driver1}`} name="Eixo Y" hide domain={['dataMin', 'dataMax']} />
                
                {/* Linha base da pista */}
                <Scatter 
                  name="Traçado" 
                  data={data.telemetry} 
                  line={{ stroke: '#555', strokeWidth: 4, strokeLinecap: 'round', strokeLinejoin: 'round' }} 
                  fill="#555" 
                  shape={() => null} 
                />

                {activeIndex !== null && data.telemetry[activeIndex] && (
                  <Scatter 
                    name="Posição Atual" 
                    data={[data.telemetry[activeIndex]]} 
                    fill="#e10600" 
                    shape="circle" 
                    isAnimationActive={false}
                  />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          
          {/* VELOCIDADE */}
          <div className="h-[300px] mb-5">
            <h3 className="mb-2 text-sm text-[#aaa]">Velocidade (km/h)</h3>
            <ResponsiveContainer width="100%" height="100%">
              {/* ADICIONE OS EVENTOS DE MOUSE AQUI */}
              <LineChart 
                data={data.telemetry} 
                syncId="f1-telemetry"
                onMouseMove={(state) => {
                  if (state && state.isTooltipActive) {
                    setActiveIndex(state.activeTooltipIndex);
                  }
                }}
                onMouseLeave={() => setActiveIndex(null)}
              >
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
          <div className="h-[150px] mb-5">
            <h3 className="mb-2 text-sm text-[#aaa]">Acelerador (%)</h3>
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
          <div className="h-[150px] mb-5">
            <h3 className="mb-2 text-sm text-[#aaa]">Freio (%)</h3>
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

          {/* MARCHA */}
          <div className="h-[150px]">
            <h3 className="mb-2 text-sm text-[#aaa]">Marcha</h3>
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
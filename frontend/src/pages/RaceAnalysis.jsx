import { useState } from 'react';
import axios from 'axios';

// Função auxiliar para definir a cor do pneu na interface
const getTireColor = (compound) => {
  switch(compound) {
    case 'SOFT': return '#e10600';
    case 'MEDIUM': return '#e2d014';
    case 'HARD': return '#ffffff';
    case 'INTERMEDIATE': return '#39b54a';
    case 'WET': return '#00aeeef';
    default: return '#888';
  }
};

export default function RaceAnalysis() {
  const [year, setYear] = useState('2025');
  const [gp, setGp] = useState('Brazil');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchRaceSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/race-summary?year=${year}&gp=${gp}`);
      setResults(response.data.results);
    } catch (err) {
      setError('Falha ao carregar a análise da corrida. Verifique os parâmetros.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-5 font-sans text-white bg-[#1e1e1e]">
      <div className="flex items-end gap-4 pb-5 mb-5 border-b border-[#333]">
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} className="w-20 p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <div>
          <label className="block mb-1 text-xs text-[#aaa]">GRANDE PRÉMIO</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} className="p-2 text-white bg-[#2a2a2a] border border-[#444] rounded" />
        </div>
        <button onClick={fetchRaceSummary} disabled={loading} className="px-5 py-2 text-white bg-[#0055ff] border-none rounded cursor-pointer disabled:opacity-75">
          {loading ? 'Processando Grid...' : 'Gerar Análise Completa'}
        </button>
      </div>

      {error && <div className="mb-5 text-[#ff4c4c]">{error}</div>}

      {results.length > 0 && (
        <div className="p-5 overflow-x-auto bg-[#2a2a2a] rounded-lg">
          <h2 className="mt-0 text-xl font-bold">Classificação e Estratégia de Pneus</h2>
          <table className="w-full mt-2 text-left border-collapse">
            <thead>
              <tr className="border-b border-[#444] text-[#aaa]">
                <th className="p-2">Pos</th>
                <th className="p-2">Piloto</th>
                <th className="p-2">Grid</th>
                <th className="p-2">Variação</th>
                <th className="p-2">Estratégia (Stints & Voltas)</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row, index) => (
                <tr key={index} className="border-b border-[#333]">
                  <td className="p-2 font-bold">{row.chegada}</td>
                  <td className="p-2">{row.piloto}</td>
                  <td className="p-2 text-[#aaa]">P{row.largada}</td>
                  <td className="p-2">
                    <span className={`font-bold ${row.saldo_posicoes > 0 ? 'text-[#39b54a]' : row.saldo_posicoes < 0 ? 'text-[#ff4c4c]' : 'text-[#aaa]'}`}>
                      {row.saldo_posicoes > 0 ? `+${row.saldo_posicoes}` : row.saldo_posicoes}
                    </span>
                  </td>
                  <td className="flex items-center gap-1 p-2">
                    {row.stints.map((stint, i) => (
                      <div key={i} 
                        className="flex items-center justify-center min-w-[30px] px-2 py-1 text-xs font-bold rounded-full"
                        style={{
                          backgroundColor: getTireColor(stint.composto),
                          color: stint.composto === 'HARD' || stint.composto === 'MEDIUM' ? '#000' : '#fff'
                        }}
                      >
                        {stint.voltas}v
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
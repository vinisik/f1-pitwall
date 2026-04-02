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
  const [year, setYear] = useState('2023');
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
    <div style={{ padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#1e1e1e', color: '#fff', minHeight: '100vh' }}>
      <div style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', borderBottom: '1px solid #333', paddingBottom: '20px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa', marginBottom: '5px' }}>ANO</label>
          <input type="number" value={year} onChange={(e) => setYear(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff', width: '80px' }} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: '#aaa', marginBottom: '5px' }}>GRANDE PRÉMIO</label>
          <input type="text" value={gp} onChange={(e) => setGp(e.target.value)} style={{ padding: '8px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#2a2a2a', color: '#fff' }} />
        </div>
        <button onClick={fetchRaceSummary} disabled={loading} style={{ padding: '10px 20px', backgroundColor: '#0055ff', color: '#fff', border: 'none', borderRadius: '5px', cursor: 'pointer' }}>
          {loading ? 'Processando Grid...' : 'Gerar Análise Completa'}
        </button>
      </div>

      {error && <div style={{ color: '#ff4c4c', marginBottom: '20px' }}>{error}</div>}

      {results.length > 0 && (
        <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px', overflowX: 'auto' }}>
          <h2 style={{ marginTop: 0 }}>Classificação e Estratégia de Pneus</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', marginTop: '10px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #444', color: '#aaa' }}>
                <th style={{ padding: '10px' }}>Pos</th>
                <th style={{ padding: '10px' }}>Piloto</th>
                <th style={{ padding: '10px' }}>Grid</th>
                <th style={{ padding: '10px' }}>Variação</th>
                <th style={{ padding: '10px' }}>Estratégia (Stints & Voltas)</th>
              </tr>
            </thead>
            <tbody>
              {results.map((row, index) => (
                <tr key={index} style={{ borderBottom: '1px solid #333' }}>
                  <td style={{ padding: '10px', fontWeight: 'bold' }}>{row.chegada}</td>
                  <td style={{ padding: '10px' }}>{row.piloto}</td>
                  <td style={{ padding: '10px', color: '#aaa' }}>P{row.largada}</td>
                  <td style={{ padding: '10px' }}>
                    <span style={{ 
                      color: row.saldo_posicoes > 0 ? '#39b54a' : row.saldo_posicoes < 0 ? '#ff4c4c' : '#aaa',
                      fontWeight: 'bold'
                    }}>
                      {row.saldo_posicoes > 0 ? `+${row.saldo_posicoes}` : row.saldo_posicoes}
                    </span>
                  </td>
                  <td style={{ padding: '10px', display: 'flex', gap: '5px', alignItems: 'center' }}>
                    {row.stints.map((stint, i) => (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        backgroundColor: getTireColor(stint.composto),
                        color: stint.composto === 'HARD' || stint.composto === 'MEDIUM' ? '#000' : '#fff',
                        padding: '4px 8px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold',
                        minWidth: '30px'
                      }}>
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
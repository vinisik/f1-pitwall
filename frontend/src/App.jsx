import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import RaceAnalysis from './pages/RaceAnalysis';

function App() {
  const [activeTab, setActiveTab] = useState('live');

  return (
    <div style={{ backgroundColor: '#121212', minHeight: '100vh' }}>
      {/* Menu Superior */}
      <nav style={{ padding: '15px 20px', backgroundColor: '#000', borderBottom: '2px solid #333', display: 'flex', gap: '20px' }}>
        <button 
          onClick={() => setActiveTab('live')}
          style={{ background: 'none', border: 'none', color: activeTab === 'live' ? '#e10600' : '#888', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', borderBottom: activeTab === 'live' ? '2px solid #e10600' : 'none', paddingBottom: '5px' }}
        >
          Engine de Estratégia
        </button>
        <button 
          onClick={() => setActiveTab('analysis')}
          style={{ background: 'none', border: 'none', color: activeTab === 'analysis' ? '#0055ff' : '#888', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer', borderBottom: activeTab === 'analysis' ? '2px solid #0055ff' : 'none', paddingBottom: '5px' }}
        >
          Análise Completa da Corrida
        </button>
      </nav>

      {/* Renderização Condicional das Abas */}
      {activeTab === 'live' ? <Dashboard /> : <RaceAnalysis />}
    </div>
  );
}

export default App;
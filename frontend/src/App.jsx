import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import RaceAnalysis from './pages/RaceAnalysis';
import TelemetryCompare from './pages/TelemetryCompare';

function App() {
  const [activeTab, setActiveTab] = useState('live');

  return (
    <div className="min-h-screen bg-[#121212]">
      {/* Menu Superior */}
      <nav className="flex gap-5 px-5 py-4 bg-black border-b-2 border-[#333]">
        <button 
          onClick={() => setActiveTab('live')}
          className={`pb-1 text-base font-bold bg-transparent border-none cursor-pointer ${activeTab === 'live' ? 'text-[#e10600] border-b-2 border-b-[#e10600]' : 'text-[#888] border-b-2 border-b-transparent'}`}
        >
          Engine de Estratégia
        </button>
        <button 
          onClick={() => setActiveTab('analysis')}
          className={`pb-1 text-base font-bold bg-transparent border-none cursor-pointer ${activeTab === 'analysis' ? 'text-[#0055ff] border-b-2 border-b-[#0055ff]' : 'text-[#888] border-b-2 border-b-transparent'}`}
        >
          Análise Completa da Corrida
        </button>
        <button 
          onClick={() => setActiveTab('telemetry')}
          // CORREÇÃO: O código hexadecimal agora é #00aeef (6 caracteres)
          className={`pb-1 text-base font-bold bg-transparent border-none cursor-pointer ${activeTab === 'telemetry' ? 'text-[#61C75D] border-b-2 border-b-[#00aeef]' : 'text-[#888] border-b-2 border-b-transparent'}`}
        >
          Comparador de Telemetria
        </button>
      </nav>

      {activeTab === 'live' && <Dashboard />}
      {activeTab === 'analysis' && <RaceAnalysis />}
      {activeTab === 'telemetry' && <TelemetryCompare />}
    </div>
  );
}

export default App;
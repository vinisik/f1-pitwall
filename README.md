# **F1 PitWall** 

## **Como Executar o Projeto**

### **1\. Criar o Ambiente Virtual**

```python \-m venv venv```

### **2\. Ativar o Ambiente Virtual**

* **No Windows:**  
```venv\\Scripts\\activate```

* **No Linux/macOS:**  
```source venv/bin/activate```

### **3\. Instalar as Dependências**

```pip install \-r requirements.txt```

### **4\. Executar a Aplicação**

```python \-m app.main\_desktop ```


## **Tecnologias Utilizadas**

* **Python 3.x:** Linguagem base do desenvolvimento do sistema.  
* **PySide6 (Qt for Python):** Framework utilizado para a construção de toda a interface gráfica (UI), gerenciamento de estados, ciclo de eventos e estilização via QSS.  
* **FastF1:** Biblioteca de alto desempenho especializada para a ingestão e processamento de dados oficiais de cronometragem, telemetria e calendários da FIA.  
* **Matplotlib:** Responsável pela geração e renderização assíncrona de todos os gráficos de performance (sensores, evolução de posições, distribuições de ritmo e deltas cumulativos).  
* **NumPy & Pandas:** Utilizados nos bastidores para manipulação vetorial eficiente das séries temporais de dados de sensores e filtragem de DataFrames de calendários.

## **Estrutura de Arquivos**

```
f1-pitwall/  
├── app/  
│   ├── ui/  
│   │   ├── assets/  
│   │   │   └── logo.png          \# Identidade visual da aplicação 
│   │   └── tabs.py               \# Estrutura visual e esqueleto das abas da UI  
│   ├── services/  
│   │   ├── f1\_data.py            \# Integração com a API FastF1 e filtros de calendário  
│   │   └── reports.py            \# Motores de exportação de relatórios analíticos em PDF  
│   ├── constants.py              \# Fonte única de dados estáticos, como as cores de pneus, circuitos e pilotos
│   ├── workers.py                \# Threads assíncronas (QThreads) para processamento pesado (Model)  
│   └── main\_desktop.py           \# Core da aplicação, conexões de sinais e eventos  
├── requirements.txt              \# Dependências e bibliotecas do projeto  
└── README.md                     \# Documentação do repositório
```



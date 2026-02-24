const fs = require('fs');
const enPath = './messages/en.json';
const trPath = './messages/tr.json';

const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
enData.landing = {
  "nav": {
    "markets": "MARKETS",
    "analysis": "ANALYSIS",
    "about": "ABOUT",
    "login": "LOGIN"
  },
  "hero": {
    "title": "FOREXS",
    "subtitle": "AI",
    "description": "Advanced algorithmic trading powered by neural networks",
    "cta": "START TRADING"
  },
  "cards": {
    "liveMarkets": {
      "title": "Live Markets",
      "desc": "Real-time AI analysis"
    },
    "aiAnalysis": {
      "title": "AI Analysis",
      "desc": "Deep pattern recognition"
    },
    "portfolio": {
      "title": "Portfolio",
      "desc": "Intelligent risk management"
    }
  }
};
fs.writeFileSync(enPath, JSON.stringify(enData, null, 2));

const trData = JSON.parse(fs.readFileSync(trPath, 'utf8'));
trData.landing = {
  "nav": {
    "markets": "PİYASALAR",
    "analysis": "ANALİZ",
    "about": "HAKKIMIZDA",
    "login": "GİRİŞ YAP"
  },
  "hero": {
    "title": "FOREXS",
    "subtitle": "AI",
    "description": "Sinir ağları ile desteklenen gelişmiş algoritmik ticaret",
    "cta": "TİCARETE BAŞLA"
  },
  "cards": {
    "liveMarkets": {
      "title": "Canlı Piyasalar",
      "desc": "Gerçek zamanlı AI analizi"
    },
    "aiAnalysis": {
      "title": "AI Analiz",
      "desc": "Derin formasyon tespiti"
    },
    "portfolio": {
      "title": "Portföy",
      "desc": "Akıllı risk yönetimi"
    }
  }
};
fs.writeFileSync(trPath, JSON.stringify(trData, null, 2));
console.log("Done");

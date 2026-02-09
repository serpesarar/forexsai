"use client";

import { useState } from "react";
import Link from "next/link";
import AuthGuard from "@/components/AuthGuard";
import {
  ArrowLeft,
  HelpCircle,
  MessageCircle,
  Mail,
  FileText,
  ChevronDown,
  ExternalLink,
  Search,
} from "lucide-react";

const FAQ_ITEMS = [
  {
    question: "ForexsAI nasıl çalışır?",
    answer: "ForexsAI, yapay zeka ve makine öğrenmesi algoritmalarını kullanarak NASDAQ ve XAUUSD piyasalarını analiz eder. Teknik göstergeler, piyasa verileri ve haber akışlarını değerlendirerek trading sinyalleri üretir."
  },
  {
    question: "Sinyaller ne kadar güvenilir?",
    answer: "Sinyallerimiz geçmiş verilere dayalı backtestlerden geçirilmiştir. Ancak hiçbir trading sinyali %100 garanti veremez. Risk yönetimi stratejileri kullanmanızı öneririz."
  },
  {
    question: "Pro üyelik ne avantajlar sağlıyor?",
    answer: "Pro üyelik ile Claude AI destekli detaylı analizler, sınırsız sinyal erişimi, öncelikli destek ve gelişmiş grafik araçlarına erişim sağlarsınız."
  },
  {
    question: "Çizimlerimi nasıl kaydedebilirim?",
    answer: "Grafikler sayfasında çizim yapabilmek ve kaydetmek için TradingView hesabınıza giriş yapmanız gerekir. Giriş yaptıktan sonra çizimleriniz otomatik olarak kaydedilir."
  },
  {
    question: "ML Strateji filtreleri ne işe yarar?",
    answer: "ML Strateji filtreleri, makine öğrenmesi modelimizin hangi faktörlere ağırlık vereceğini belirlemenizi sağlar. Ultra Güvenli modda yüksek güvenli sinyaller, Agresif modda daha fazla sinyal alırsınız."
  },
  {
    question: "Referans kodu nasıl kullanılır?",
    answer: "Referans kodunuzu arkadaşlarınızla paylaşın. Arkadaşınız bu kod ile kayıt olduğunda, her ikiniz de 1 ay ücretsiz Pro üyelik kazanırsınız."
  },
];

export default function HelpPage() {
  return (
    <AuthGuard>
      <HelpPageContent />
    </AuthGuard>
  );
}

function HelpPageContent() {
  const [searchQuery, setSearchQuery] = useState("");
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const filteredFAQ = FAQ_ITEMS.filter(
    item =>
      item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background text-white">
      <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 rounded-xl hover:bg-white/10 transition">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Yardım & Destek</h1>
            <p className="text-sm text-textSecondary">Sorularınıza yanıt bulun</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-textSecondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Soru ara..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 focus:border-accent focus:outline-none transition"
          />
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="mailto:support@forexsai.com"
            className="glass-premium rounded-xl p-4 flex items-center gap-3 hover:bg-white/5 transition group"
          >
            <div className="p-2 rounded-lg bg-blue-500/20 group-hover:bg-blue-500/30 transition">
              <Mail className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="font-medium">E-posta Destek</p>
              <p className="text-xs text-textSecondary">support@forexsai.com</p>
            </div>
          </a>

          <a
            href="https://t.me/forexsai"
            target="_blank"
            rel="noopener noreferrer"
            className="glass-premium rounded-xl p-4 flex items-center gap-3 hover:bg-white/5 transition group"
          >
            <div className="p-2 rounded-lg bg-purple-500/20 group-hover:bg-purple-500/30 transition">
              <MessageCircle className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="font-medium">Telegram</p>
              <p className="text-xs text-textSecondary">Topluluk grubu</p>
            </div>
          </a>

          <a
            href="https://forexsai.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="glass-premium rounded-xl p-4 flex items-center gap-3 hover:bg-white/5 transition group"
          >
            <div className="p-2 rounded-lg bg-green-500/20 group-hover:bg-green-500/30 transition">
              <FileText className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="font-medium">Dokümantasyon</p>
              <p className="text-xs text-textSecondary">Detaylı rehber</p>
            </div>
          </a>
        </div>

        {/* FAQ */}
        <div className="glass-premium rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-white/10">
            <h3 className="font-semibold flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-accent" />
              Sık Sorulan Sorular
            </h3>
          </div>

          <div className="divide-y divide-white/10">
            {filteredFAQ.length === 0 ? (
              <div className="p-8 text-center text-textSecondary">
                <HelpCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Aramanızla eşleşen soru bulunamadı</p>
              </div>
            ) : (
              filteredFAQ.map((item, index) => (
                <div key={index}>
                  <button
                    onClick={() => setOpenIndex(openIndex === index ? null : index)}
                    className="w-full p-4 flex items-center justify-between text-left hover:bg-white/5 transition"
                  >
                    <span className="font-medium pr-4">{item.question}</span>
                    <ChevronDown
                      className={`w-5 h-5 text-textSecondary flex-shrink-0 transition-transform ${
                        openIndex === index ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  {openIndex === index && (
                    <div className="px-4 pb-4 text-sm text-textSecondary">
                      {item.answer}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Contact Info */}
        <div className="glass-premium rounded-2xl p-6 text-center">
          <p className="text-textSecondary mb-4">
            Sorunuz hala çözülmedi mi? Bize ulaşın.
          </p>
          <a
            href="mailto:support@forexsai.com"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-accent text-white font-semibold hover:bg-accent/90 transition"
          >
            <Mail className="w-5 h-5" />
            Destek Talebi Oluştur
          </a>
        </div>

        {/* Footer Links */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-textSecondary">
          <a href="https://forexsai.com/terms" target="_blank" rel="noopener noreferrer" className="hover:text-white transition flex items-center gap-1">
            Kullanım Koşulları <ExternalLink className="w-3 h-3" />
          </a>
          <span>•</span>
          <a href="https://forexsai.com/privacy" target="_blank" rel="noopener noreferrer" className="hover:text-white transition flex items-center gap-1">
            Gizlilik Politikası <ExternalLink className="w-3 h-3" />
          </a>
          <span>•</span>
          <a href="https://forexsai.com/disclaimer" target="_blank" rel="noopener noreferrer" className="hover:text-white transition flex items-center gap-1">
            Risk Uyarısı <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
}

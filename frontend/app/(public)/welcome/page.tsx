"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  TrendingUp, Sparkles, Shield, Zap, BarChart3, Brain, 
  LineChart, Target, Users, ArrowRight, Check, Star,
  ChevronRight, Globe, Lock, Award, Clock, Activity
} from "lucide-react";

export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Navbar */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-slate-950/90 backdrop-blur-xl border-b border-slate-800" : ""
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">ForexSAI</span>
            </div>

            {/* Nav Links */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-slate-400 hover:text-white transition-colors">Özellikler</a>
              <a href="#pricing" className="text-slate-400 hover:text-white transition-colors">Erişim</a>
              <a href="#testimonials" className="text-slate-400 hover:text-white transition-colors">Yorumlar</a>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center gap-3">
              <Link 
                href="/login"
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
              >
                Giriş
              </Link>
              <Link
                href="/signup"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 font-medium transition-all"
              >
                Ücretsiz Başla
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-pink-600/20 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-3xl" />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-sm mb-8">
              <Sparkles className="w-4 h-4" />
              30 Milyon Veri ile Eğitilmiş AI Trading Platformu
            </div>

            {/* Headline */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
              Artık Saatlerce{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400">
                Analiz Yapmayın
              </span>
            </h1>

            <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
              9 ay boyunca 30 milyon veri ile eğittiğimiz ML modeli ve 350+ teknik formasyonu öğrenmiş yapay zeka ile 
              artık başkalarına güvenip paranızı kaybetmeyin. ForexSAI sizin için analiz eder.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <Link
                href="/signup"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 font-semibold text-lg flex items-center justify-center gap-2 group transition-all"
              >
                Ücretsiz Hesap Oluştur
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                href="#features"
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-slate-800 hover:bg-slate-700 font-semibold text-lg transition-all"
              >
                Özellikleri Keşfet
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                { value: "30M+", label: "Eğitim Verisi" },
                { value: "9 Ay", label: "Model Eğitimi" },
                { value: "350+", label: "Teknik Formasyon" },
                { value: "24/7", label: "Gerçek Zamanlı" },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-slate-500 text-sm">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Hero Image/Dashboard Preview */}
          <div className="mt-16 relative">
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent z-10" />
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 backdrop-blur-xl p-4 shadow-2xl">
              <div className="aspect-video rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                <div className="text-center">
                  <Activity className="w-16 h-16 text-purple-500 mx-auto mb-4 animate-pulse" />
                  <p className="text-slate-400">Canlı Dashboard Görünümü</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Neden ForexSAI?</h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              350+ formasyonu öğrenmiş ML modeli, duygu analizi yapan AI ve profesyonel araçlar tek platformda
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              {
                icon: Brain,
                title: "AI Haber & Duygu Analizi",
                description: "Haberleri ve piyasa olaylarını AI ile analiz edin. Sentiment analizi ile piyasa ruh halini anlık takip edin.",
                gradient: "from-purple-500 to-pink-500"
              },
              {
                icon: LineChart,
                title: "30M Veri ile Eğitilmiş ML",
                description: "9 ay boyunca 30 milyon veri ile eğittiğimiz LightGBM modeli ile profesyonel BUY/SELL sinyalleri.",
                gradient: "from-blue-500 to-cyan-500"
              },
              {
                icon: BarChart3,
                title: "350+ Formasyon Tanıma",
                description: "Order Block, Fair Value Gap, RTYHIIM ve 350'den fazla teknik formasyonu otomatik tespit.",
                gradient: "from-green-500 to-emerald-500"
              },
              {
                icon: Zap,
                title: "Gerçek Zamanlı Analiz",
                description: "Anlık fiyat verileri ve otomatik analiz. Artık saatlerce grafik başında beklemeye gerek yok.",
                gradient: "from-orange-500 to-amber-500"
              },
              {
                icon: Target,
                title: "Akıllı TP/SL Hesaplama",
                description: "Volatilite ve ATR'ye göre dinamik Take Profit ve Stop Loss seviyeleri. Riskinizi optimize edin.",
                gradient: "from-red-500 to-rose-500"
              },
              {
                icon: Shield,
                title: "Bağımsız Kararlar",
                description: "Başkalarının sinyallerine güvenmeyin. Kendi verilerinizle kendi kararlarınızı alın.",
                gradient: "from-indigo-500 to-violet-500"
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="group p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-all"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-slate-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Beta Campaign Section */}
      <section id="pricing" className="py-24 relative bg-slate-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Beta Announcement */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 text-green-300 text-sm mb-6">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
              Sınırlı Süre - Erken Erişim Kampanyası
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">
              Şu An <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">Tamamen Ücretsiz!</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              Beta döneminde tüm özelliklere ücretsiz erişin. Fiyatlandırma yakında belirlenecek - 
              <span className="text-white font-medium"> şimdi kayıt olan herkes özel avantajlardan yararlanacak!</span>
            </p>
          </div>

          {/* Single Beta Card */}
          <div className="max-w-2xl mx-auto">
            <div className="p-8 sm:p-10 rounded-3xl bg-gradient-to-b from-purple-900/50 via-slate-900/50 to-slate-900/50 border-2 border-purple-500/50 relative overflow-hidden">
              {/* Glow Effect */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl -z-10" />
              
              {/* Badge */}
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-6 py-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 text-sm font-bold shadow-lg shadow-green-500/30">
                🎉 BETA - TÜM ÖZELLİKLER ÜCRETSİZ
              </div>

              <div className="text-center mt-4 mb-8">
                <h3 className="text-3xl font-bold mb-2">Erken Erişim Paketi</h3>
                <p className="text-slate-400">Tüm Pro ve Enterprise özellikleri dahil</p>
              </div>

              {/* Coming Soon Badge */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-amber-500/10 border border-amber-500/30">
                  <Clock className="w-5 h-5 text-amber-400" />
                  <span className="text-amber-300 font-semibold">Fiyatlandırma Yakında</span>
                </div>
                <p className="text-slate-500 mt-3 text-sm">Beta döneminde tüm özellikler ücretsiz</p>
              </div>

              {/* Features Grid */}
              <div className="grid sm:grid-cols-2 gap-4 mb-8">
                {[
                  "✅ 30M+ veri ile eğitilmiş ML modeli",
                  "✅ 350+ teknik formasyon tanıma",
                  "✅ Gerçek zamanlı piyasa verileri",
                  "✅ Pattern tanıma (OB, FVG, RTYHIIM)",
                  "🧠 AI haber & duygu analizi",
                  "📊 Akıllı TP/SL hesaplama",
                  "📈 Profesyonel analiz araçları",
                  "🎁 Referral ödül sistemi",
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-2 text-slate-300">
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              {/* CTA */}
              <Link
                href="/signup"
                className="block w-full py-4 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-400 hover:to-emerald-400 text-center font-bold text-lg transition-all shadow-lg shadow-green-500/30"
              >
                Hemen Ücretsiz Kayıt Ol
              </Link>

              {/* Trust badges */}
              <div className="flex items-center justify-center gap-6 mt-6 text-sm text-slate-500">
                <div className="flex items-center gap-1">
                  <Shield className="w-4 h-4" />
                  <span>Güvenli</span>
                </div>
                <div className="flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  <span>Anında erişim</span>
                </div>
                <div className="flex items-center gap-1">
                  <Users className="w-4 h-4" />
                  <span>5000+ kullanıcı</span>
                </div>
              </div>
            </div>
          </div>

          {/* Early Access Notice */}
          <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-purple-900/30 to-blue-900/30 border border-purple-500/20 text-center max-w-3xl mx-auto">
            <h3 className="text-lg font-semibold text-white mb-2">Neden Şimdi Katılmalısınız?</h3>
            <p className="text-slate-400 text-sm">
              9 ay boyunca geliştirdiğimiz bu sistemi şu an <strong className="text-green-400">ücretsiz</strong> kullanabilirsiniz. 
              Fiyatlandırma yakında başlayacak - erken kayıt olanlar özel avantajlardan faydalanacak.
            </p>
          </div>

          {/* Referral Banner */}
          <div className="mt-8 p-6 rounded-2xl bg-gradient-to-r from-purple-900/50 to-pink-900/50 border border-purple-500/30 text-center">
            <div className="flex items-center justify-center gap-3 mb-3">
              <Users className="w-6 h-6 text-purple-400" />
              <h3 className="text-xl font-bold">Arkadaşlarını Davet Et, Bonus Kazan!</h3>
            </div>
            <p className="text-slate-400">
              5 arkadaşını davet et, fiyatlandırma başladığında <span className="text-purple-300 font-semibold">ekstra 1 ay ücretsiz</span> kazan!
            </p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Kullanıcılarımız Ne Diyor?</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                name: "Ahmet Y.",
                role: "Forex Trader",
                content: "Claude AI haber analizi gerçekten oyun değiştirici. NFP ve FOMC dönemlerinde çok işime yaradı.",
                rating: 5
              },
              {
                name: "Mehmet K.",
                role: "Emtia Yatırımcısı",
                content: "Order Block ve FVG tespiti çok doğru çalışıyor. Artık grafiklere saatlerce bakmama gerek yok.",
                rating: 5
              },
              {
                name: "Ayşe S.",
                role: "Portföy Yöneticisi",
                content: "ML sinyalleri ve adaptif TP/SL özelliği risk yönetimimi çok kolaylaştırdı. Kesinlikle tavsiye ederim.",
                rating: 5
              },
            ].map((testimonial, i) => (
              <div key={i} className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
                <div className="flex items-center gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, j) => (
                    <Star key={j} className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                  ))}
                </div>
                <p className="text-slate-300 mb-4">"{testimonial.content}"</p>
                <div>
                  <div className="font-semibold">{testimonial.name}</div>
                  <div className="text-sm text-slate-500">{testimonial.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-900/20 to-pink-900/20" />
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative text-center">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            Başkalarına Güvenmeyi Bırakın
          </h2>
          <p className="text-xl text-slate-400 mb-10">
            30 milyon veri ile eğitilmiş AI modelimiz sizin için analiz yapsın. Ücretsiz başlayın.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 font-semibold text-lg group transition-all"
          >
            Ücretsiz Başla
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold">ForexSAI</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-500">
              <Link href="/terms" className="hover:text-white transition-colors">Kullanım Şartları</Link>
              <Link href="/privacy" className="hover:text-white transition-colors">Gizlilik</Link>
              <Link href="/contact" className="hover:text-white transition-colors">İletişim</Link>
            </div>
            <p className="text-sm text-slate-500">
              © 2024 ForexSAI. Tüm hakları saklıdır.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

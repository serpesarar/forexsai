"use client";

import { useEffect, useRef } from "react";

export function StarfieldBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;

        const resizeCanvas = () => {
            // Piksel yoğunluğuna göre ayarla ki yüksek çözünürlükte keskin dursun
            const dpr = window.devicePixelRatio || 1;
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            ctx.scale(dpr, dpr);
            canvas.style.width = `${window.innerWidth}px`;
            canvas.style.height = `${window.innerHeight}px`;
        };

        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();

        class Star {
            x: number;
            y: number;
            radius: number;
            opacity: number;
            fadeSpeed: number;
            baseOpacity: number;

            constructor() {
                this.x = Math.random() * window.innerWidth;
                this.y = Math.random() * window.innerHeight;
                // Yıldızlar 0.3px ile 1.2px arası, çok doğal bir görüntü
                this.radius = Math.random() * 0.9 + 0.3;

                // %10 ile %80 arası değişen temel parlaklıklar
                this.baseOpacity = Math.random() * 0.7 + 0.1;
                this.opacity = this.baseOpacity;

                // Çok yavaş yanıp sönme hızı
                this.fadeSpeed = (Math.random() * 0.008) + 0.002;

                // Rastgele başlangıç yönü (parlıyor mu sönüyor mu)
                if (Math.random() > 0.5) {
                    this.fadeSpeed = -this.fadeSpeed;
                }
            }

            update() {
                this.opacity += this.fadeSpeed;

                // Maksimum/Minimum değişimi temel parlaklık üzerinden sınırla
                if (this.opacity >= 1 || this.opacity <= 0.1) {
                    this.fadeSpeed = -this.fadeSpeed;
                }
            }

            draw() {
                if (!ctx) return;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);

                // Doğal beyaz-gri bir ışık
                ctx.fillStyle = `rgba(230, 240, 255, ${this.opacity})`;

                // Büyük yıldızlara hafif blur parlaması ekle
                if (this.radius > 0.8 && this.opacity > 0.5) {
                    ctx.shadowBlur = Math.random() * 5 + 3;
                    // Biraz mavi-cyan karıştırarak siber/metalik hissiyatı koru
                    ctx.shadowColor = `rgba(100, 200, 255, ${this.opacity * 0.5})`;
                } else {
                    ctx.shadowBlur = 0;
                }

                ctx.fill();
            }
        }

        // Mobil cihazda daha az, masaüstünde daha fazla yıldız yoğunluğu
        const starCount = Math.floor((window.innerWidth * window.innerHeight) / 10000);
        const stars: Star[] = [];

        for (let i = 0; i < starCount; i++) {
            stars.push(new Star());
        }

        const animate = () => {
            // Hafif motion trail bırakarak estetik bir his katıyoruz (0.3 opacity yerine net temizleme için tam silme yapalım, yıldızlar sabit dursun)
            ctx.clearRect(0, 0, window.innerWidth * (window.devicePixelRatio || 1), window.innerHeight * (window.devicePixelRatio || 1));

            stars.forEach(star => {
                star.update();
                star.draw();
            });
            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.removeEventListener("resize", resizeCanvas);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ opacity: 0.8 }}
        />
    );
}

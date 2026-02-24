"use client";

import { useEffect, useRef } from "react";
import Spline from "@splinetool/react-spline";

export default function SplineViewerClient() {
    const splineRef = useRef<any>(null);
    const animFrameRef = useRef<number>(0);
    const cameraRef = useRef<any>(null);

    function onLoad(spline: any) {
        splineRef.current = spline;

        // 1. KAMERAYI BUL ve ayarla
        try {
            const camera = spline.getCamera();
            if (camera) {
                cameraRef.current = camera;

                // Başlangıç pozisyonu (uzaktan başla - büyüklük sorunu için)
                camera.position.set(0, 300, 1200);

                // FOV ayarı (geniş açı - perspektif için)
                if (camera.fov) {
                    camera.fov = 50; // 50-60 arası dene
                    camera.updateProjectionMatrix();
                }

                // Kameranın bakış açısını merkeze ayarla
                camera.lookAt(0, 0, 0);
            }
        } catch (e) {
            console.log("Kamera erişimi yok, obje döndürülüyor");
        }

        // 2. ANİMASYON - Kamera etrafında dönme
        let angle = 1;
        const radius = 900; // Kameranın uzaklığı (büyük = uzak, küçük = yakın)

        const animate = () => {
            if (cameraRef.current) {
                // Kamerayı dairesel hareket ettir (Y ekseni etrafında)
                angle += 0.001; // Hız (0.0005-0.002 arası dene)

                cameraRef.current.position.x = Math.sin(angle) * radius;
                cameraRef.current.position.z = Math.cos(angle) * radius;
                cameraRef.current.lookAt(0, 50, 0); // Adama bak (Y:50 göz hizası için)
            } else {
                // Kamera yoksa, Turn Table döndür (yedek)
                const turnTable = spline.findObjectByName("Turn Table");
                if (turnTable) {
                    turnTable.rotation.y -= 0.004;
                }
            }

            animFrameRef.current = requestAnimationFrame(animate);
        };

        animate();
    }

    useEffect(() => {
        return () => {
            if (animFrameRef.current) {
                cancelAnimationFrame(animFrameRef.current);
            }
        };
    }, []);

    return (
        <div className="absolute inset-0 z-0 w-full h-full overflow-hidden bg-black">
            <Spline
                scene="https://prod.spline.design/qwXYdfDuVtIZ2NZZ/scene.splinecode"
                onLoad={onLoad}
                style={{
                    width: "100%",
                    height: "100%",
                    transform: "scale(0.85)", // Ekran büyükse küçült (0.7-0.9 arası dene)
                    transformOrigin: "center center",
                }}
            />
        </div>
    );
}
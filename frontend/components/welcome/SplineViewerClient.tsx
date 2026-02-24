"use client";

import { useEffect, useRef } from "react";
import Spline from "@splinetool/react-spline";

export default function SplineViewerClient() {
    const splineRef = useRef<any>(null);
    const animFrameRef = useRef<number>(0);

    function onLoad(spline: any) {
        splineRef.current = spline;

        // Turn Table veya dönebilecek ana objeyi bul
        const body = spline.findObjectByName("Body");
        const turnTable = spline.findObjectByName("Turn Table");
        const group = spline.findObjectByName("Group");

        // Önce Turn Table'ı dene, yoksa Body, yoksa Group
        const target = turnTable || body || group;

        if (target) {
            const rotate = () => {
                // Yavaşça sağa dönme (negatif = sağa doğru)
                target.rotation.y -= 0.004;
                animFrameRef.current = requestAnimationFrame(rotate);
            };
            rotate();
        }
    }

    // Bileşen unmount olduğunda animasyonu durdur
    useEffect(() => {
        return () => {
            if (animFrameRef.current) {
                cancelAnimationFrame(animFrameRef.current);
            }
        };
    }, []);

    return (
        <div
            className="absolute inset-0 z-0"
            style={{ pointerEvents: "none" }}
        >
            <Spline
                scene="https://prod.spline.design/qwXYdfDuVtIZ2NZZ/scene.splinecode"
                onLoad={onLoad}
                style={{
                    width: "100%",
                    height: "100%",
                }}
            />
        </div>
    );
}

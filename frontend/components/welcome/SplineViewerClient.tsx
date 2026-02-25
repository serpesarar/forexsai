"use client";

import { useEffect, useRef } from "react";

export default function SplineViewerClient() {
    const viewerRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        // 1) viewer script
        const script = document.createElement("script");
        script.type = "module";
        script.src =
            "https://unpkg.com/@splinetool/viewer@1.12.60/build/spline-viewer.js";
        document.head.appendChild(script);

        // 2) Try to “kick” playback once viewer is ready (some browsers require a gesture)
        const tryStart = () => {
            const v = viewerRef.current as any;
            // Some versions expose play(); safe-guard
            if (v && typeof v.play === "function") v.play();
        };

        // Try a few times after load
        const t1 = setTimeout(tryStart, 300);
        const t2 = setTimeout(tryStart, 1200);

        return () => {
            clearTimeout(t1);
            clearTimeout(t2);
        };
    }, []);

    return (
        <div className="absolute inset-0 z-0 w-full h-full overflow-hidden bg-black">
            {/* @ts-ignore */}
            <spline-viewer
                ref={(el: any) => (viewerRef.current = el)}
                url="https://prod.spline.design/Z4FBqLBO3-pdkdTM/scene.splinecode"
                autoplay
                // iOS/Safari inline video davranışı için iyi
                style={{ width: "100%", height: "100%" }}
            />
        </div>
    );
}
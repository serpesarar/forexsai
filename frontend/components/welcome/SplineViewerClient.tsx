"use client";

import { useEffect } from "react";

export default function SplineViewerClient() {
    useEffect(() => {
        const script = document.createElement("script");
        script.type = "module";
        script.src = "https://unpkg.com/@splinetool/viewer@1.12.60/build/spline-viewer.js";
        document.head.appendChild(script);
    }, []);

    return (
        <div className="absolute inset-0 z-0 w-full h-full overflow-hidden bg-black">
            {/* @ts-ignore */}
            <spline-viewer
                url="https://prod.spline.design/Z4FBqLBO3-pdkdTM/scene.splinecode"
                style={{ width: "100%", height: "100%" }}
            />
        </div>
    );
}